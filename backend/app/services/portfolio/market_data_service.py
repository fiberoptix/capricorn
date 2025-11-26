"""
Market Data Fetch Service (Provider-agnostic)

Currently supports Twelve Data for:
- Multi-symbol live quotes
- Daily close (1-day time_series)

Reads configuration from backend/market_data/TwelveData_Config.txt if present.
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple
from datetime import datetime, timedelta, timezone, time
import requests

from sqlalchemy.orm import Session
from decimal import Decimal as D

from app.models.portfolio_models import MarketPrice
from .transaction_service import TransactionService


class ConfigLoader:
    @staticmethod
    def load_config() -> Dict[str, str]:
        # Default values
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

        # File overrides
        cfg_path = os.path.join(os.path.dirname(__file__), '..', 'market_data', 'TwelveData_Config.txt')
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
    BASE_URL = 'https://api.twelvedata.com'

    def __init__(self, api_key: str, max_batch: int = 8):
        self.api_key = api_key
        self.max_batch = max_batch

    def chunk_symbols(self, symbols: List[str]) -> List[List[str]]:
        batch = max(1, int(self.max_batch))
        return [symbols[i:i + batch] for i in range(0, len(symbols), batch)]

    def fetch_quotes(self, symbols: List[str]) -> Dict[str, float]:
        """Fetch latest quotes for multiple symbols."""
        results: Dict[str, float] = {}
        for chunk in self.chunk_symbols(symbols):
            params = {
                'symbol': ','.join(chunk),
                'apikey': self.api_key,
            }
            url = f'{self.BASE_URL}/quote'
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            # Normalize possible response shapes:
            # 1) Single object: { symbol: 'AAPL', price: '123.45', close: '122.00', is_market_open: false, ... }
            # 2) Map of symbols: { 'AAPL': { price/close/... }, 'MSFT': { ... } }
            # 3) Wrapped array: { data: [ { symbol: 'AAPL', price/close/... }, ... ] }
            # 4) Wrapped dict: { data: { 'AAPL': { price/close/... }, ... } }
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
            try:
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
                    # Attempt symbol-keyed map fallback
                    for sym in chunk:
                        obj = data.get(sym) or data.get(sym.upper())
                        pr = extract_price(obj or {})
                        if pr is not None:
                            results[sym.upper()] = float(pr)
            except Exception:
                # Ignore parse errors for this chunk; continue
                pass
        return results


class MarketDataService:
    def __init__(self, db: Session):
        self.db = db
        self.cfg = ConfigLoader.load_config()
        self.provider = self.cfg.get('PROVIDER', 'twelve_data').lower()
        self.api_key = self.cfg.get('API_KEY', '')
        self.ttl_seconds = int(self.cfg.get('TTL_SECONDS', '120') or '120')
        self.max_batch = int(self.cfg.get('MAX_BATCH', '8') or '8')

        if self.provider == 'twelve_data':
            self.adapter = TwelveDataAdapter(self.api_key, self.max_batch)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _get_symbols(self) -> List[str]:
        src = self.cfg.get('SYMBOLS_SOURCE', 'holdings')
        custom = self.cfg.get('CUSTOM_SYMBOLS', '')
        from services.transaction_service import TransactionService
        ts = TransactionService(self.db)
        if src == 'custom' and custom:
            return [s.strip().upper() for s in custom.split(',') if s.strip()]
        # default: only currently held tickers (positive net quantity)
        tickers = ts.get_currently_held_tickers()
        return [t.upper() for t in tickers]

    def _get_stale_symbols(self, symbols: List[str], force: bool = False) -> List[str]:
        if not symbols:
            return []
        if force:
            return [s.upper() for s in symbols]
        stale: List[str] = []
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.ttl_seconds)
        existing: Dict[str, datetime] = {}
        rows = self.db.query(MarketPrice.ticker_symbol, MarketPrice.last_updated).all()
        for sym, ts in rows:
            # assume stored in UTC if tz-naive
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            existing[sym.upper()] = ts
        for sym in symbols:
            ts = existing.get(sym.upper())
            if ts is None or ts < cutoff:
                stale.append(sym.upper())
        return stale

    def refresh_quotes(self, force: bool = False) -> Tuple[int, List[str]]:
        if not self.api_key:
            raise ValueError("Market data API key not configured")

        symbols = self._get_symbols()
        symbols = list(dict.fromkeys(symbols))  # dedupe, keep order
        to_check = self._get_stale_symbols(symbols, force=force)
        if not to_check:
            # Nothing to check; but if forced with empty symbols, nothing to do
            return 0, []

        # 1) Immediately mark the symbols we're checking as "checked now" in DB, regardless of outcome
        checked_at = datetime.now(timezone.utc)
        for sym in to_check:
            mp = self.db.query(MarketPrice).filter(MarketPrice.ticker_symbol == sym).first()
            if mp:
                mp.last_updated = checked_at
            else:
                # create placeholder with price=0; better to keep previous price if exists; since it doesn't, use small positive
                # We'll overwrite price below if provider returns data
                mp = MarketPrice(ticker_symbol=sym, current_price=D('0.0001'), last_updated=checked_at)
                self.db.add(mp)
        self.db.commit()

        # 2) Fetch quotes from provider for the same set
        quotes = self.adapter.fetch_quotes(to_check)

        updated = 0
        now = datetime.now(timezone.utc)
        for sym, price in quotes.items():
            mp = self.db.query(MarketPrice).filter(MarketPrice.ticker_symbol == sym).first()
            if mp:
                mp.current_price = D(str(price))
                mp.last_updated = now
            else:
                mp = MarketPrice(ticker_symbol=sym, current_price=D(str(price)), last_updated=now)
                self.db.add(mp)
            updated += 1
        self.db.commit()
        return updated, sorted(list(quotes.keys()))

    def should_run_automatic(self, run_type: str) -> bool:
        """Check market_data_runs for today's run of the given type."""
        if run_type not in ('startup','close'):
            return False
        try:
            rs = self.db.execute(
                """
                SELECT 1 FROM market_data_runs WHERE run_type=:rt AND run_date= CURRENT_DATE
                """,
                { 'rt': run_type }
            ).fetchone()
            return rs is None
        except Exception:
            return True

    def mark_run(self, run_type: str) -> None:
        try:
            self.db.execute(
                """
                INSERT INTO market_data_runs (run_type, run_date) VALUES (:rt, CURRENT_DATE)
                ON CONFLICT (run_type, run_date) DO NOTHING
                """,
                { 'rt': run_type }
            )
            self.db.commit()
        except Exception:
            self.db.rollback()

    def after_close_refresh_needed(self) -> bool:
        """Return True if it's a weekday and there has not been a 'close' run yet today.
        Used by callers that want to conditionally refresh after 4:05pm local time.
        """
        weekday = datetime.utcnow().weekday()
        if weekday > 4:
            return False
        return self.should_run_automatic('close')

    def is_market_hours(self) -> bool:
        """Check if current time is during market hours (9:30 AM - 4:00 PM EST)"""
        try:
            # Import zoneinfo for timezone handling
            try:
                from zoneinfo import ZoneInfo
            except ImportError:
                # Fallback for older Python versions
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
            # Fallback: assume market hours if we can't determine
            print(f"Warning: Could not determine market hours, defaulting to True: {e}")
            return True

    def should_auto_refresh(self) -> bool:
        """Check if automatic refresh should run based on configuration"""
        refresh_mode = self.cfg.get('REFRESH_MODE', 'on_tab_click')
        
        if refresh_mode == 'market_hours_auto':
            return self.is_market_hours()
        elif refresh_mode == 'always':
            return True
        else:  # on_tab_click or other modes
            return False


