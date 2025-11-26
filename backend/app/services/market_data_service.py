"""
Async Market Data Service for Capricorn Portfolio Manager

Integrates with TwelveData API for real-time stock quotes:
- Multi-symbol batch fetching
- TTL-based refresh throttling
- Market hours detection
- Daily run tracking to prevent quota exhaustion
- Background refresh with status tracking
"""

import os
import asyncio
import threading
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta, timezone, time
from decimal import Decimal
from dataclasses import dataclass, field
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.portfolio_models import MarketPrice
from app.services.transaction_service import TransactionService


# ============= BACKGROUND REFRESH STATUS TRACKING =============

@dataclass
class RefreshStatus:
    """Tracks the status of a background market price refresh"""
    is_running: bool = False
    total_symbols: int = 0
    completed_symbols: int = 0
    current_batch: int = 0
    total_batches: int = 0
    started_at: Optional[datetime] = None
    last_batch_at: Optional[datetime] = None
    error: Optional[str] = None
    updated_symbols: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert status to API response format"""
        remaining_batches = max(0, self.total_batches - self.current_batch)
        # Each batch after the first requires 60 second wait
        seconds_remaining = remaining_batches * 60 if remaining_batches > 0 else 0
        
        return {
            "is_running": self.is_running,
            "total_symbols": self.total_symbols,
            "completed_symbols": self.completed_symbols,
            "current_batch": self.current_batch,
            "total_batches": self.total_batches,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "seconds_remaining": seconds_remaining,
            "minutes_remaining": round(seconds_remaining / 60, 1),
            "progress_percent": round((self.completed_symbols / self.total_symbols * 100) if self.total_symbols > 0 else 0, 1),
            "error": self.error,
            "updated_symbols": self.updated_symbols,
            "status_message": self._get_status_message(seconds_remaining)
        }
    
    def _get_status_message(self, seconds_remaining: int) -> str:
        """Generate user-friendly status message"""
        if not self.is_running and self.error:
            return f"Error: {self.error}"
        if not self.is_running and self.completed_symbols > 0:
            return f"Done: {self.completed_symbols} prices updated"
        if not self.is_running:
            return "Ready"
        if self.current_batch == 0:
            return "Starting..."
        
        # Calculate pending symbols
        pending = self.total_symbols - self.completed_symbols
        
        if pending > 0 and seconds_remaining > 0:
            # Format time remaining
            if seconds_remaining >= 60:
                mins = int(seconds_remaining / 60)
                secs = seconds_remaining % 60
                time_str = f"{mins}m {secs}s" if secs > 0 else f"{mins}m"
            else:
                time_str = f"{seconds_remaining}s"
            return f"Fetched {self.completed_symbols}/{self.total_symbols} • Pending {pending} in {time_str}"
        elif pending > 0:
            return f"Fetching {pending} remaining..."
        else:
            return f"Finishing..."


# Global status tracker (in-memory, resets on container restart)
_refresh_status = RefreshStatus()
_refresh_lock = threading.Lock()


def get_refresh_status() -> Dict[str, Any]:
    """Get current refresh status (thread-safe)"""
    with _refresh_lock:
        return _refresh_status.to_dict()


def reset_refresh_status():
    """Reset refresh status to initial state"""
    global _refresh_status
    with _refresh_lock:
        _refresh_status = RefreshStatus()


def _update_status(**kwargs):
    """Update refresh status (thread-safe)"""
    global _refresh_status
    with _refresh_lock:
        for key, value in kwargs.items():
            if hasattr(_refresh_status, key):
                setattr(_refresh_status, key, value)


async def run_background_refresh(db_url: str, force: bool = False, batch_delay: int = 60):
    """
    Background task that fetches market prices with rate limiting
    
    This runs in a separate asyncio task and updates the global status
    as it progresses through batches.
    
    Args:
        db_url: Database connection URL
        force: If True, refresh all symbols regardless of TTL
        batch_delay: Seconds to wait between batches (default 60 for free tier)
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    global _refresh_status
    
    # Check if already running
    with _refresh_lock:
        if _refresh_status.is_running:
            print("⚠️ Background refresh already in progress, skipping")
            return
        _refresh_status = RefreshStatus(is_running=True, started_at=datetime.utcnow())
    
    engine = None
    try:
        # Create new database connection for this task
        engine = create_async_engine(db_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            service = MarketDataService(db)
            
            # Get symbols and batches
            all_symbols, batches = await service.get_symbols_to_refresh(force=force)
            
            if not all_symbols:
                _update_status(
                    is_running=False,
                    total_symbols=0,
                    completed_symbols=0,
                    total_batches=0
                )
                print("✅ No symbols need refreshing")
                return
            
            _update_status(
                total_symbols=len(all_symbols),
                total_batches=len(batches)
            )
            
            print(f"🔄 Background refresh starting: {len(all_symbols)} symbols in {len(batches)} batches")
            
            all_updated: List[str] = []
            
            for batch_idx, batch in enumerate(batches):
                # Wait before fetching (except first batch)
                if batch_idx > 0 and batch_delay > 0:
                    print(f"⏳ Waiting {batch_delay}s before batch {batch_idx + 1}...")
                    await asyncio.sleep(batch_delay)
                
                _update_status(
                    current_batch=batch_idx + 1,
                    last_batch_at=datetime.utcnow()
                )
                
                # Fetch this batch
                print(f"📡 Fetching batch {batch_idx + 1}/{len(batches)}: {batch}")
                quotes = service.adapter.fetch_single_batch(batch)
                
                # Update database for each quote
                for sym, price in quotes.items():
                    success = await service.update_price_in_db(sym, price)
                    if success:
                        all_updated.append(sym)
                
                _update_status(
                    completed_symbols=len(all_updated),
                    updated_symbols=all_updated.copy()
                )
                
                print(f"✅ Batch {batch_idx + 1} complete: {len(quotes)} prices fetched")
            
            _update_status(is_running=False)
            print(f"🎉 Background refresh complete: {len(all_updated)} prices updated")
            
    except Exception as e:
        print(f"❌ Background refresh error: {e}")
        _update_status(is_running=False, error=str(e))
    finally:
        if engine:
            await engine.dispose()


def start_background_refresh(db_url: str, force: bool = False):
    """
    Start a background refresh task
    
    This creates a new asyncio task that runs the refresh in the background.
    The caller returns immediately while the refresh continues.
    
    Args:
        db_url: Database connection URL
        force: If True, refresh all symbols regardless of TTL
    """
    # Check if already running
    with _refresh_lock:
        if _refresh_status.is_running:
            return False, "Refresh already in progress"
    
    # Create and schedule the background task
    loop = asyncio.get_event_loop()
    loop.create_task(run_background_refresh(db_url, force=force))
    
    return True, "Background refresh started"


class ConfigLoader:
    @staticmethod
    def load_config() -> Dict[str, str]:
        """Load configuration from TwelveData_Config.txt or environment"""
        cfg: Dict[str, str] = {
            'PROVIDER': 'twelve_data',
            'API_KEY': '',
            'TIMEZONE': 'America/New_York',
            'TTL_SECONDS': '300',
            'MAX_BATCH': '20',
            'REFRESH_MODE': 'market_hours_auto',
            'MARKET_START': '09:30',
            'MARKET_END': '16:00',
            'DAILY_CLOSE_ENABLED': 'true',
            'DAILY_CLOSE_TIME': '16:05',
            'SYMBOLS_SOURCE': 'holdings',
            'CUSTOM_SYMBOLS': '',
        }

        # Environment overrides
        for k in list(cfg.keys()):
            env_val = os.getenv(f'MARKET_DATA_{k}')
            if env_val:
                cfg[k] = env_val

        # File overrides - look for config file in backend/market_data/
        cfg_path = os.path.join(os.path.dirname(__file__), '..', '..', 'market_data', 'TwelveData_Config.txt')
        cfg_path = os.path.abspath(cfg_path)
        
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip().upper()
                        v = v.strip()
                        if k in cfg:
                            cfg[k] = v

        return cfg


class TwelveDataAdapter:
    """Adapter for TwelveData API"""
    BASE_URL = 'https://api.twelvedata.com'

    def __init__(self, api_key: str, max_batch: int = 8):
        self.api_key = api_key
        self.max_batch = max_batch

    def chunk_symbols(self, symbols: List[str]) -> List[List[str]]:
        """Split symbols into batches"""
        batch = max(1, int(self.max_batch))
        return [symbols[i:i + batch] for i in range(0, len(symbols), batch)]

    def fetch_single_batch(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetch quotes for a single batch of symbols (no delay, no chunking)
        
        Args:
            symbols: List of ticker symbols (should be <= max_batch size)
            
        Returns:
            Dictionary mapping ticker to price
        """
        results: Dict[str, float] = {}
        if not symbols:
            return results
            
        params = {
            'symbol': ','.join(symbols),
            'apikey': self.api_key,
        }
        url = f'{self.BASE_URL}/quote'
        
        try:
            print(f"🌐 Fetching quotes for batch: {symbols}")
            with httpx.Client(timeout=15.0) as client:
                r = client.get(url, params=params)
                print(f"🌐 TwelveData response status: {r.status_code}")
                r.raise_for_status()
                data = r.json()
                print(f"🌐 TwelveData response data: {str(data)[:200]}...")
            
            # Parse response
            def extract_price(obj: dict):
                if not isinstance(obj, dict):
                    return None
                for key in ('price', 'close', 'previous_close'):
                    if key in obj and obj[key] is not None:
                        try:
                            return float(obj[key])
                        except Exception:
                            pass
                return None
            
            # Handle different response formats
            if isinstance(data, dict) and 'data' in data:
                payload = data.get('data')
                if isinstance(payload, list):
                    for item in payload:
                        sym = (item or {}).get('symbol')
                        pr = extract_price(item or {})
                        if sym and pr is not None:
                            results[sym.upper()] = float(pr)
                elif isinstance(payload, dict):
                    for sym, obj in payload.items():
                        pr = extract_price(obj or {})
                        if sym and pr is not None:
                            results[str(sym).upper()] = float(pr)
            elif isinstance(data, dict) and 'symbol' in data:
                # Single symbol response - TwelveData returns flat object
                # Check for any of the price fields (price, close, previous_close)
                sym = data.get('symbol')
                pr = extract_price(data)
                if sym and pr is not None:
                    results[sym.upper()] = float(pr)
                    print(f"✅ Parsed single-symbol response: {sym} = ${pr}")
            elif isinstance(data, dict):
                for sym in symbols:
                    obj = data.get(sym) or data.get(sym.upper())
                    pr = extract_price(obj or {})
                    if pr is not None:
                        results[sym.upper()] = float(pr)
        except Exception as e:
            print(f"Error fetching quotes for batch {symbols}: {e}")
            
        return results

    def fetch_quotes(self, symbols: List[str], delay_between_batches: int = 0) -> Dict[str, float]:
        """
        Fetch latest quotes for multiple symbols from TwelveData API
        
        Args:
            symbols: List of ticker symbols
            delay_between_batches: Seconds to wait between batch calls (for rate limiting)
            
        Returns:
            Dictionary mapping ticker to price
        """
        results: Dict[str, float] = {}
        chunks = self.chunk_symbols(symbols)
        
        for idx, chunk in enumerate(chunks):
            # Add delay between batches to respect rate limits (except first batch)
            if idx > 0 and delay_between_batches > 0:
                print(f"⏳ Waiting {delay_between_batches}s before next batch...")
                import time
                time.sleep(delay_between_batches)
            params = {
                'symbol': ','.join(chunk),
                'apikey': self.api_key,
            }
            url = f'{self.BASE_URL}/quote'
            
            try:
                # Use httpx for HTTP requests (already installed)
                print(f"🌐 Fetching quotes for: {chunk}")
                with httpx.Client(timeout=15.0) as client:
                    r = client.get(url, params=params)
                    print(f"🌐 TwelveData response status: {r.status_code}")
                    r.raise_for_status()
                    data = r.json()
                    print(f"🌐 TwelveData response data: {str(data)[:200]}...")
                
                # Parse response - TwelveData returns different formats
                def extract_price(obj: dict):
                    if not isinstance(obj, dict):
                        return None
                    for key in ('price', 'close', 'previous_close'):
                        if key in obj and obj[key] is not None:
                            try:
                                return float(obj[key])
                            except Exception:
                                pass
                    return None
                
                # Handle different response formats
                if isinstance(data, dict) and 'data' in data:
                    payload = data.get('data')
                    if isinstance(payload, list):
                        for item in payload:
                            sym = (item or {}).get('symbol')
                            pr = extract_price(item or {})
                            if sym and pr is not None:
                                results[sym.upper()] = float(pr)
                    elif isinstance(payload, dict):
                        for sym, obj in payload.items():
                            pr = extract_price(obj or {})
                            if sym and pr is not None:
                                results[str(sym).upper()] = float(pr)
                elif isinstance(data, dict) and all(k in data for k in ['symbol', 'price']):
                    sym = data.get('symbol')
                    pr = extract_price(data)
                    if sym and pr is not None:
                        results[sym.upper()] = float(pr)
                elif isinstance(data, dict):
                    # Symbol-keyed map fallback
                    for sym in chunk:
                        obj = data.get(sym) or data.get(sym.upper())
                        pr = extract_price(obj or {})
                        if pr is not None:
                            results[sym.upper()] = float(pr)
            except Exception as e:
                print(f"Error fetching quotes for {chunk}: {e}")
                continue
                
        return results


class MarketDataService:
    """Async service for market data operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cfg = ConfigLoader.load_config()
        self.provider = self.cfg.get('PROVIDER', 'twelve_data').lower()
        self.api_key = self.cfg.get('API_KEY', '')
        self.ttl_seconds = int(self.cfg.get('TTL_SECONDS', '300') or '300')
        self.max_batch = int(self.cfg.get('MAX_BATCH', '20') or '20')

        if self.provider == 'twelve_data':
            self.adapter = TwelveDataAdapter(self.api_key, self.max_batch)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _get_symbols(self) -> List[str]:
        """Get list of symbols to track (from portfolio holdings)"""
        src = self.cfg.get('SYMBOLS_SOURCE', 'holdings')
        custom = self.cfg.get('CUSTOM_SYMBOLS', '')
        
        if src == 'custom' and custom:
            return [s.strip().upper() for s in custom.split(',') if s.strip()]
        
        # Default: get tickers from transactions with positive quantity
        transaction_service = TransactionService(self.db)
        tickers = await transaction_service.get_currently_held_tickers()
        return [t.upper() for t in tickers]
    
    async def _get_stale_symbols(self, symbols: List[str], force: bool = False) -> List[str]:
        """
        Determine which symbols need refreshing based on TTL
        
        Args:
            symbols: List of symbols to check
            force: If True, refresh all symbols regardless of age
            
        Returns:
            List of symbols that need refreshing
        """
        if not symbols:
            return []
        if force:
            return [s.upper() for s in symbols]
        
        stale: List[str] = []
        cutoff = datetime.utcnow() - timedelta(seconds=self.ttl_seconds)
        
        # Get existing prices with timestamps
        result = await self.db.execute(
            select(MarketPrice.ticker_symbol, MarketPrice.last_updated)
        )
        rows = result.all()
        
        existing: Dict[str, datetime] = {}
        for sym, ts in rows:
            # Timestamps are timezone-naive in our DB
            existing[sym.upper()] = ts
        
        for sym in symbols:
            ts = existing.get(sym.upper())
            if ts is None or ts < cutoff:
                stale.append(sym.upper())
        
        return stale
    
    async def refresh_quotes(self, force: bool = False, quick_mode: bool = True) -> Tuple[int, List[str]]:
        """
        Refresh stock quotes from TwelveData API
        
        Args:
            force: If True, refresh all symbols regardless of TTL
            quick_mode: If True, fetch all symbols in one batch (no delays)
                       If False, use rate-limited batching with delays
            
        Returns:
            Tuple of (updated_count, list_of_updated_symbols)
        """
        if not self.api_key:
            raise ValueError("Market data API key not configured")

        symbols = await self._get_symbols()
        print(f"📊 Market Data: Found {len(symbols)} symbols from holdings: {symbols}")
        symbols = list(dict.fromkeys(symbols))  # Remove duplicates
        to_check = await self._get_stale_symbols(symbols, force=force)
        print(f"📊 Market Data: {len(to_check)} symbols need refresh (force={force})")
        
        if not to_check:
            return 0, []

        # Mark symbols as checked (update timestamp) before API call
        checked_at = datetime.utcnow()  # Timezone-naive for PostgreSQL
        for sym in to_check:
            result = await self.db.execute(
                select(MarketPrice).where(MarketPrice.ticker_symbol == sym)
            )
            mp = result.scalar_one_or_none()
            
            if mp:
                mp.last_updated = checked_at
            else:
                # Create placeholder
                mp = MarketPrice(
                    ticker_symbol=sym,
                    current_price=Decimal('0.01'),
                    last_updated=checked_at
                )
                self.db.add(mp)
        
        await self.db.commit()

        # Fetch quotes from TwelveData
        print(f"📡 Calling TwelveData API for {len(to_check)} symbols...")
        
        # Quick mode: fetch all at once (uses more API credits but no waiting)
        # Rate-limited mode: wait between batches to respect 8 credits/minute
        delay = 0 if quick_mode else 60
        quotes = self.adapter.fetch_quotes(to_check, delay_between_batches=delay)
        print(f"📡 TwelveData returned {len(quotes)} quotes: {list(quotes.keys())[:5]}...")

        # Update database with fetched quotes
        updated = 0
        now = datetime.utcnow()  # Timezone-naive for PostgreSQL
        
        for sym, price in quotes.items():
            result = await self.db.execute(
                select(MarketPrice).where(MarketPrice.ticker_symbol == sym)
            )
            mp = result.scalar_one_or_none()
            
            if mp:
                mp.current_price = Decimal(str(price))
                mp.last_updated = now
            else:
                mp = MarketPrice(
                    ticker_symbol=sym,
                    current_price=Decimal(str(price)),
                    last_updated=now
                )
                self.db.add(mp)
            updated += 1
        
        await self.db.commit()
        return updated, sorted(list(quotes.keys()))
    
    async def get_symbols_to_refresh(self, force: bool = False) -> Tuple[List[str], List[List[str]]]:
        """
        Get list of symbols that need refreshing and their batches
        
        Returns:
            Tuple of (all_symbols, list_of_batches)
        """
        if not self.api_key:
            raise ValueError("Market data API key not configured")

        symbols = await self._get_symbols()
        symbols = list(dict.fromkeys(symbols))  # Remove duplicates
        to_check = await self._get_stale_symbols(symbols, force=force)
        
        if not to_check:
            return [], []
        
        batches = self.adapter.chunk_symbols(to_check)
        return to_check, batches
    
    async def update_price_in_db(self, symbol: str, price: float) -> bool:
        """
        Update a single price in the database
        
        Returns:
            True if successful
        """
        try:
            now = datetime.utcnow()
            result = await self.db.execute(
                select(MarketPrice).where(MarketPrice.ticker_symbol == symbol)
            )
            mp = result.scalar_one_or_none()
            
            if mp:
                mp.current_price = Decimal(str(price))
                mp.last_updated = now
            else:
                mp = MarketPrice(
                    ticker_symbol=symbol,
                    current_price=Decimal(str(price)),
                    last_updated=now
                )
                self.db.add(mp)
            
            await self.db.commit()
            return True
        except Exception as e:
            print(f"Error updating price for {symbol}: {e}")
            await self.db.rollback()
            return False
    
    async def should_run_automatic(self, run_type: str) -> bool:
        """
        Check if automatic run should happen today
        
        Args:
            run_type: 'startup' or 'close'
            
        Returns:
            True if run hasn't happened today yet
        """
        if run_type not in ('startup', 'close'):
            return False
        
        try:
            result = await self.db.execute(
                text("""
                    SELECT 1 FROM market_data_runs 
                    WHERE run_type = :rt AND run_date = CURRENT_DATE
                """),
                {'rt': run_type}
            )
            row = result.first()
            return row is None
        except Exception:
            return True
    
    async def mark_run(self, run_type: str) -> None:
        """Mark that a run has happened today"""
        try:
            await self.db.execute(
                text("""
                    INSERT INTO market_data_runs (run_type, run_date) 
                    VALUES (:rt, CURRENT_DATE)
                    ON CONFLICT (run_type, run_date) DO NOTHING
                """),
                {'rt': run_type}
            )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
    
    def is_market_hours(self) -> bool:
        """
        Check if current time is during market hours (9:30 AM - 4:00 PM EST)
        
        Returns:
            True if currently during market hours on a weekday
        """
        try:
            # Import timezone handling
            try:
                from zoneinfo import ZoneInfo
            except ImportError:
                import pytz
                ZoneInfo = lambda tz: pytz.timezone(tz)
            
            # Get current time in market timezone
            market_tz = ZoneInfo(self.cfg.get('TIMEZONE', 'America/New_York'))
            now = datetime.now(market_tz)
            
            # Check if it's a weekday (Monday=0, Sunday=6)
            if now.weekday() > 4:  # Saturday or Sunday
                return False
            
            # Parse market start and end times
            start_str = self.cfg.get('MARKET_START', '09:30')
            end_str = self.cfg.get('MARKET_END', '16:00')
            
            start_hour, start_min = map(int, start_str.split(':'))
            end_hour, end_min = map(int, end_str.split(':'))
            
            market_start = time(start_hour, start_min)
            market_end = time(end_hour, end_min)
            
            current_time = now.time()
            return market_start <= current_time <= market_end
            
        except Exception as e:
            print(f"Warning: Could not determine market hours: {e}")
            return False
    
    def should_auto_refresh(self) -> bool:
        """
        Check if automatic refresh should run based on configuration
        
        Returns:
            True if auto-refresh is enabled and conditions are met
        """
        refresh_mode = self.cfg.get('REFRESH_MODE', 'on_tab_click')
        
        if refresh_mode == 'market_hours_auto':
            return self.is_market_hours()
        elif refresh_mode == 'always':
            return True
        else:  # on_tab_click or other modes
            return False
    
    def get_config_status(self) -> Dict[str, any]:
        """Get current configuration status"""
        return {
            'provider': self.provider,
            'has_api_key': bool(self.api_key),
            'ttl_seconds': self.ttl_seconds,
            'max_batch': self.max_batch,
            'refresh_mode': self.cfg.get('REFRESH_MODE'),
            'market_start': self.cfg.get('MARKET_START'),
            'market_end': self.cfg.get('MARKET_END'),
            'is_market_hours': self.is_market_hours(),
            'timezone': self.cfg.get('TIMEZONE')
        }

