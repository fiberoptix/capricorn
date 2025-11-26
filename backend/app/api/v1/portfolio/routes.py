"""
Portfolio Manager Flask Backend

Main application entry point for the Portfolio Manager tax-optimization
portfolio management system using Flask instead of FastAPI.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime, time, timezone
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None
from contextlib import contextmanager
import atexit

# Import APScheduler for market hours refresh
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Import our models and services
from models.database import engine, get_db, Base, SessionLocal
from models import Portfolio, Transaction, MarketPrice, InvestorProfile, TaxRate, StateTaxRate
from services.portfolio_service import PortfolioService
from services.transaction_service import TransactionService
from services.market_price_service import MarketPriceService
from services.investor_profile_service import InvestorProfileService
from services.tax_calculation_service import TaxCalculationService, CapitalGainsType
from services.state_tax_service import StateTaxService
from services.comprehensive_tax_service import ComprehensiveTaxService
from services.break_even_service import BreakEvenService
from services.market_data_service import MarketDataService

# Create Flask application
app = Flask(__name__)

# CORS configuration for Next.js frontend
CORS(app, origins=[
    "http://localhost:3000",  # Next.js dev server
    "http://localhost:3030",  # Next.js production (our container port)
            "http://portfolio-manager-frontend:3000",  # Container internal communication
    "*"  # Allow all origins for development (remove in production)
])

# ----- Startup Functions -----
def ensure_default_profile():
    """
    Ensure exactly ONE investor profile exists (single-profile system).
    - If no profiles exist: creates default profile with ID 1
    - If multiple profiles exist: keeps ID 1, deletes others
    - Profile ID 1 is the single source of truth for investor data
    """
    try:
        db = SessionLocal()
        all_profiles = db.query(InvestorProfile).order_by(InvestorProfile.id).all()
        profile_count = len(all_profiles)
        
        if profile_count == 0:
            print("📋 No investor profiles found - creating default profile (ID 1)...")
            default_profile = InvestorProfile(
                name="Investor",
                annual_household_income=100000,
                filing_status="single",
                state_of_residence="NY",
                local_tax_rate=0.01
            )
            db.add(default_profile)
            db.commit()
            db.refresh(default_profile)
            print(f"✅ Created default investor profile: ID {default_profile.id}, 'Investor' (Single, $100K, NY, 1%)")
        elif profile_count == 1:
            print(f"✅ Single-profile system verified: ID {all_profiles[0].id}, '{all_profiles[0].name}'")
        else:
            # Multiple profiles exist - enforce single profile system
            print(f"⚠️  Found {profile_count} profiles - enforcing single-profile system...")
            primary_profile = all_profiles[0]  # Keep first profile (should be ID 1)
            
            # Delete all other profiles
            deleted_count = 0
            for profile in all_profiles[1:]:
                print(f"   Deleting duplicate profile: ID {profile.id}, '{profile.name}'")
                db.delete(profile)
                deleted_count += 1
            
            db.commit()
            print(f"✅ Single-profile system enforced: Kept ID {primary_profile.id}, deleted {deleted_count} duplicate(s)")
        
        db.close()
    except Exception as e:
        print(f"❌ Error enforcing single-profile system: {e}")

# Call startup functions when module is loaded
ensure_default_profile()

# ----- Real-Time Quotes Toggle State -----
# In-memory toggle for enabling/disabling automatic market price refresh
# Each server instance maintains its own independent state
realtime_quotes_enabled = True  # Default: ON

# ----- Market Hours Scheduler -----
def scheduled_market_refresh():
    """Background task to refresh market prices every 5 minutes during market hours"""
    global realtime_quotes_enabled
    
    # Check if real-time quotes are enabled
    if not realtime_quotes_enabled:
        return  # Skip refresh when disabled
    
    try:
        with get_db_session() as db:
            market_service = MarketDataService(db)
            
            # Only refresh if we're in market hours and auto refresh is enabled
            if market_service.should_auto_refresh():
                print(f"🔄 Scheduled market refresh starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                updated_count, symbols = market_service.refresh_quotes(force=False)
                if updated_count > 0:
                    print(f"✅ Scheduled refresh updated {updated_count} symbols: {', '.join(symbols)}")
                else:
                    print("ℹ️ Scheduled refresh: no symbols needed updating (within TTL)")
            else:
                # Don't log during off-hours to avoid spam
                pass
                
    except ValueError as e:
        # Handle quota exhaustion gracefully
        error_msg = str(e)
        if "run out of API credits" in error_msg or "429" in error_msg:
            print(f"⚠️ Scheduled refresh: API quota exhausted - will retry tomorrow")
            # Optionally disable scheduler until tomorrow
            # scheduler.pause_job('market_refresh_job')
        else:
            print(f"❌ Scheduled market refresh failed (ValueError): {e}")
    except Exception as e:
        print(f"❌ Scheduled market refresh failed: {e}")

# Initialize and start the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=scheduled_market_refresh,
    trigger=IntervalTrigger(minutes=15),  # Every 15 minutes
    id='market_refresh_job',
    name='Market Price Refresh',
    replace_existing=True
)

# Start scheduler
scheduler.start()
print("🕐 Market hours scheduler started - refreshing every 15 minutes during market hours")

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# ----- Utilities -----
def iso_utc(dt: datetime) -> str:
    """Serialize a datetime as ISO-8601 in UTC with a 'Z' suffix.
    Treats tz-naive timestamps as UTC (our DB stores timestamps without TZ).
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace('+00:00', 'Z')

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for container monitoring and QA testing.
    Returns system status and database connectivity.
    """
    try:
        # Test database connection using SQLAlchemy
        from sqlalchemy import text
        with get_db_session() as db:
            # Simple query to verify database is working
            result = db.execute(text("SELECT COUNT(*) FROM portfolios")).scalar()
        
        # Automatic morning refresh at 9:35 AM (5 min after market open, once per day on weekdays)
        try:
            weekday = datetime.now().weekday()  # 0=Mon .. 6=Sun
            if weekday <= 4:  # Mon-Fri
                with get_db_session() as db:
                    mds = MarketDataService(db)
                    # Get timezone and morning open time
                    tz_name = mds.cfg.get('TIMEZONE', 'America/New_York')
                    morning_time = time(hour=9, minute=35)  # 9:35 AM
                    
                    if ZoneInfo is not None:
                        now_tz = datetime.now(ZoneInfo(tz_name))
                    else:
                        now_tz = datetime.now()
                    
                    # Only run if current time is at or after 9:35 AM
                    if now_tz.time() >= morning_time:
                        if mds.should_run_automatic('startup'):
                            try:
                                mds.refresh_quotes()
                            finally:
                                mds.mark_run('startup')
                # Automatic close refresh at or after configured close time (default 16:05)
                with get_db_session() as db:
                    mds2 = MarketDataService(db)
                    # Determine market timezone now
                    tz_name = mds2.cfg.get('TIMEZONE', 'America/New_York')
                    close_str = mds2.cfg.get('DAILY_CLOSE_TIME', '16:05')
                    try:
                        hh, mm = [int(x) for x in close_str.split(':', 1)]
                    except Exception:
                        hh, mm = 16, 5
                    if ZoneInfo is not None:
                        now_tz = datetime.now(ZoneInfo(tz_name))
                    else:
                        now_tz = datetime.now()
                    close_t = time(hour=hh, minute=mm)
                    # If current local time is at or after close time, run once per day
                    if now_tz.time() >= close_t:
                        if mds2.should_run_automatic('close'):
                            try:
                                mds2.refresh_quotes()
                            finally:
                                mds2.mark_run('close')
        except Exception:
            pass

        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Portfolio Manager Flask API",
            "version": "1.0.0",
            "database": "connected",
            "portfolios_count": result
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Portfolio Manager Flask API",
            "version": "1.0.0",
            "database": "disconnected",
            "error": str(e)
        }), 503

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        "message": "Portfolio Manager API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs",
        "health": "/health",
        "description": "Tax-optimization focused stock portfolio management system"
    })

# Portfolio API endpoints
@app.route('/api/portfolios', methods=['GET'])
def get_portfolios():
    """Get all portfolios or filter by type"""
    try:
        portfolio_type = request.args.get('type')
        
        with get_db_session() as db:
            service = PortfolioService(db)
            
            if portfolio_type:
                portfolios = service.get_portfolios_by_type(portfolio_type)
            else:
                portfolios = service.get_all_portfolios()
            
            return jsonify({
                "portfolios": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "type": p.type,
                        "description": p.description,
                        "cash_on_hand": float(p.cash_on_hand) if p.cash_on_hand else 0.00,
                        "created_at": p.created_at.isoformat(),
                        "updated_at": p.updated_at.isoformat()
                    }
                    for p in portfolios
                ],
                "count": len(portfolios)
            })
    except Exception as e:
        return jsonify({
            "error": str(e), 
            "message": "Failed to retrieve portfolios"
        }), 500

@app.route('/api/portfolios', methods=['POST'])
def create_portfolio():
    """Create a new portfolio"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'type' not in data:
            return jsonify({
                "error": "Missing required fields: name, type"
            }), 400
        
        with get_db_session() as db:
            service = PortfolioService(db)
            new_portfolio = service.create_portfolio(
                name=data['name'],
                portfolio_type=data['type'],
                description=data.get('description'),
                cash_on_hand=float(data.get('cash_on_hand', 0.00))
            )
            
            return jsonify({
                "id": new_portfolio.id,
                "name": new_portfolio.name,
                "type": new_portfolio.type,
                "description": new_portfolio.description,
                "cash_on_hand": float(new_portfolio.cash_on_hand) if new_portfolio.cash_on_hand else 0.00,
                "created_at": new_portfolio.created_at.isoformat(),
                "updated_at": new_portfolio.updated_at.isoformat(),
                "message": "Portfolio created successfully"
            }), 201
    except ValueError as e:
        return jsonify({
            "error": str(e), 
            "message": "Invalid portfolio data"
        }), 400
    except Exception as e:
        return jsonify({
            "error": str(e), 
            "message": "Failed to create portfolio"
        }), 500

@app.route('/api/portfolios/<int:portfolio_id>', methods=['GET'])
def get_portfolio(portfolio_id):
    """Get portfolio by ID"""
    try:
        with get_db_session() as db:
            service = PortfolioService(db)
            portfolio = service.get_portfolio(portfolio_id)
            
            if not portfolio:
                return jsonify({
                    "error": "Portfolio not found"
                }), 404
            
            return jsonify({
                "id": portfolio.id,
                "name": portfolio.name,
                "type": portfolio.type,
                "description": portfolio.description,
                "cash_on_hand": float(portfolio.cash_on_hand) if portfolio.cash_on_hand else 0.00,
                "created_at": portfolio.created_at.isoformat(),
                "updated_at": portfolio.updated_at.isoformat()
            })
    except Exception as e:
        return jsonify({
            "error": str(e), 
            "message": "Failed to retrieve portfolio"
        }), 500

@app.route('/api/portfolios/<int:portfolio_id>/summary', methods=['GET'])
def get_portfolio_summary(portfolio_id):
    """Get portfolio summary with statistics"""
    try:
        with get_db_session() as db:
            service = PortfolioService(db)
            summary = service.get_portfolio_summary(portfolio_id)
            
            if not summary:
                return jsonify({
                    "error": "Portfolio not found"
                }), 404
            
            return jsonify(summary)
    except Exception as e:
        return jsonify({
            "error": str(e), 
            "message": "Failed to retrieve portfolio summary"
        }), 500

@app.route('/api/portfolios/<int:portfolio_id>', methods=['PUT'])
def update_portfolio(portfolio_id):
    """Update portfolio"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No data provided"
            }), 400
        
        with get_db_session() as db:
            service = PortfolioService(db)
            updated_portfolio = service.update_portfolio(
                portfolio_id=portfolio_id,
                name=data.get('name'),
                description=data.get('description'),
                portfolio_type=data.get('type'),
                cash_on_hand=float(data['cash_on_hand']) if 'cash_on_hand' in data else None
            )
            
            if not updated_portfolio:
                return jsonify({
                    "error": "Portfolio not found"
                }), 404
            
            return jsonify({
                "id": updated_portfolio.id,
                "name": updated_portfolio.name,
                "type": updated_portfolio.type,
                "description": updated_portfolio.description,
                "cash_on_hand": float(updated_portfolio.cash_on_hand) if updated_portfolio.cash_on_hand else 0.00,
                "created_at": updated_portfolio.created_at.isoformat(),
                "updated_at": updated_portfolio.updated_at.isoformat(),
                "message": "Portfolio updated successfully"
            })
    except Exception as e:
        return jsonify({
            "error": str(e), 
            "message": "Failed to update portfolio"
        }), 500

@app.route('/api/portfolios/<int:portfolio_id>', methods=['DELETE'])
def delete_portfolio(portfolio_id):
    """Delete portfolio"""
    try:
        with get_db_session() as db:
            service = PortfolioService(db)
            success = service.delete_portfolio(portfolio_id)
            
            if not success:
                return jsonify({
                    "error": "Portfolio not found"
                }), 404
            
            return jsonify({
                "message": "Portfolio deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "error": str(e), 
            "message": "Failed to delete portfolio"
        }), 500

# Transaction API endpoints  
@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    """Get transactions with optional filtering"""
    try:
        # Get query parameters
        portfolio_id = request.args.get('portfolio_id', type=int)
        ticker = request.args.get('ticker')
        transaction_type = request.args.get('transaction_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        order_by = request.args.get('order_by', 'date_desc')
        
        with get_db_session() as db:
            service = TransactionService(db)
            
            if portfolio_id:
                # Parse date parameters if provided
                from datetime import datetime
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
                
                transactions = service.get_transactions_by_portfolio(
                    portfolio_id=portfolio_id,
                    ticker=ticker,
                    transaction_type=transaction_type,
                    start_date=start_date_obj,
                    end_date=end_date_obj,
                    order_by=order_by
                )
            elif ticker:
                transactions = service.get_transactions_by_ticker(ticker)
            else:
                return jsonify({"error": "portfolio_id or ticker parameter required"}), 400
            
            return jsonify({
                "count": len(transactions),
                "transactions": [
                    {
                        "id": t.id,
                        "portfolio_id": t.portfolio_id,
                        "ticker": t.ticker_symbol,
                        "stock_name": t.stock_name,
                        "transaction_type": t.transaction_type,
                        "quantity": float(t.quantity),
                        "price_per_share": float(t.price_per_share),
                        "transaction_date": t.transaction_date.isoformat(),
                        "created_at": t.created_at.isoformat(),
                        "updated_at": t.updated_at.isoformat()
                    }
                    for t in transactions
                ]
            })
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to fetch transactions: {str(e)}"}), 500


@app.route("/api/transactions", methods=["POST"])
def create_transaction():
    """Create a new transaction"""
    try:
        data = request.json
        
        # Parse transaction date
        from datetime import datetime
        from decimal import Decimal
        transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
        
        with get_db_session() as db:
            service = TransactionService(db)
            
            transaction = service.create_transaction(
                portfolio_id=data['portfolio_id'],
                ticker=data['ticker'],
                transaction_type=data['transaction_type'],
                quantity=Decimal(str(data['quantity'])),
                price_per_share=Decimal(str(data['price_per_share'])),
                transaction_date=transaction_date,
                stock_name=data.get('stock_name')
            )
            
            return jsonify({
                "id": transaction.id,
                "portfolio_id": transaction.portfolio_id,
                "ticker": transaction.ticker_symbol,
                "stock_name": transaction.stock_name,
                "transaction_type": transaction.transaction_type,
                "quantity": float(transaction.quantity),
                "price_per_share": float(transaction.price_per_share),
                "transaction_date": transaction.transaction_date.isoformat(),
                "created_at": transaction.created_at.isoformat(),
                "updated_at": transaction.updated_at.isoformat()
            }), 201
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create transaction: {str(e)}"}), 500


@app.route("/api/transactions/<int:transaction_id>", methods=["GET"])
def get_transaction(transaction_id):
    """Get a specific transaction by ID"""
    try:
        with get_db_session() as db:
            service = TransactionService(db)
            transaction = service.get_transaction_by_id(transaction_id)
            
            if not transaction:
                return jsonify({"error": "Transaction not found"}), 404
            
            return jsonify({
                "id": transaction.id,
                "portfolio_id": transaction.portfolio_id,
                "ticker": transaction.ticker_symbol,
                "stock_name": transaction.stock_name,
                "transaction_type": transaction.transaction_type,
                "quantity": float(transaction.quantity),
                "price_per_share": float(transaction.price_per_share),
                "transaction_date": transaction.transaction_date.isoformat(),
                "created_at": transaction.created_at.isoformat(),
                "updated_at": transaction.updated_at.isoformat()
            })
    
    except Exception as e:
        return jsonify({"error": f"Failed to fetch transaction: {str(e)}"}), 500


@app.route("/api/transactions/<int:transaction_id>", methods=["PUT"])
def update_transaction(transaction_id):
    """Update a specific transaction by ID"""
    try:
        data = request.get_json()
        
        with get_db_session() as db:
            transaction_service = TransactionService(db)
            
            # Validate transaction exists
            existing = transaction_service.get_transaction_by_id(transaction_id)
            if not existing:
                return jsonify({"error": "Transaction not found"}), 404
            
            # Build updates dict with only provided fields
            updates = {}
            if 'quantity' in data:
                updates['quantity'] = data['quantity']
            if 'price_per_share' in data:
                updates['price_per_share'] = data['price_per_share']
            if 'transaction_date' in data:
                updates['transaction_date'] = data['transaction_date']
            if 'ticker' in data:
                updates['ticker_symbol'] = data['ticker']
            if 'transaction_type' in data:
                updates['transaction_type'] = data['transaction_type']
            
            # Call service method
            updated = transaction_service.update_transaction(transaction_id, **updates)
            
            if not updated:
                return jsonify({"error": "Update failed"}), 500
            
            return jsonify({
                "id": updated.id,
                "portfolio_id": updated.portfolio_id,
                "ticker": updated.ticker_symbol,
                "transaction_type": updated.transaction_type,
                "quantity": float(updated.quantity),
                "price_per_share": float(updated.price_per_share),
                "transaction_date": updated.transaction_date.isoformat(),
                "created_at": updated.created_at.isoformat(),
                "updated_at": updated.updated_at.isoformat()
            })
    
    except Exception as e:
        return jsonify({"error": f"Failed to update transaction: {str(e)}"}), 500


@app.route("/api/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    """Delete a specific transaction by ID"""
    try:
        with get_db_session() as db:
            service = TransactionService(db)
            success = service.delete_transaction(transaction_id)
            if not success:
                return jsonify({"error": "Transaction not found"}), 404
            return jsonify({"message": f"Transaction {transaction_id} deleted successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to delete transaction: {str(e)}"}), 500


@app.route("/api/portfolios/<int:portfolio_id>/holdings", methods=["GET"])
def get_portfolio_holdings(portfolio_id):
    """Get current holdings for a portfolio"""
    try:
        with get_db_session() as db:
            service = TransactionService(db)
            holdings = service.get_portfolio_holdings(portfolio_id)
            
            # Convert Decimal to float for JSON serialization
            holdings_json = {}
            for ticker, holding in holdings.items():
                holdings_json[ticker] = {
                    "quantity": float(holding['quantity']),
                    "avg_cost_basis": float(holding['avg_cost_basis']),
                    "total_invested": float(holding['total_invested']),
                    "transaction_count": len(holding['transactions'])
                }
            
            return jsonify({
                "portfolio_id": portfolio_id,
                "holdings": holdings_json
            })
    
    except Exception as e:
        return jsonify({"error": f"Failed to fetch holdings: {str(e)}"}), 500


# MarketPrice API endpoints
@app.route("/api/market-prices", methods=["GET"])
def get_market_prices():
    """Get all market prices or filter by tickers"""
    try:
        tickers = request.args.get('tickers')  # Comma-separated list
        order_by = request.args.get('order_by', 'ticker')
        
        with get_db_session() as db:
            service = MarketPriceService(db)
            
            if tickers:
                # Get specific tickers
                ticker_list = [t.strip().upper() for t in tickers.split(',')]
                prices_dict = service.get_prices_for_tickers(ticker_list)
                prices = list(prices_dict.values())
            else:
                # Get all prices
                prices = service.get_all_prices(order_by=order_by)
            
            return jsonify({
                "count": len(prices),
                "prices": [
                    {
                        "id": p.id,
                        "ticker": p.ticker_symbol,
                        "current_price": float(p.current_price),
                "last_updated": iso_utc(p.last_updated)
                    }
                    for p in prices
                ]
            })
    
    except Exception as e:
        return jsonify({"error": f"Failed to fetch market prices: {str(e)}"}), 500


@app.route("/api/market-prices/<ticker>", methods=["GET"])
def get_market_price(ticker):
    """Get market price for a specific ticker"""
    try:
        with get_db_session() as db:
            service = MarketPriceService(db)
            price = service.get_price(ticker)
            
            if not price:
                return jsonify({"error": f"Price not found for ticker {ticker.upper()}"}), 404
            
            return jsonify({
                "id": price.id,
                "ticker": price.ticker_symbol,
                "current_price": float(price.current_price),
                "last_updated": iso_utc(price.last_updated)
            })
    
    except Exception as e:
        return jsonify({"error": f"Failed to fetch price for {ticker}: {str(e)}"}), 500


@app.route("/api/market-prices/<ticker>", methods=["PUT"])
def update_market_price(ticker):
    """Update market price for a ticker"""
    try:
        data = request.json
        
        if 'current_price' not in data:
            return jsonify({"error": "current_price is required"}), 400
        
        from decimal import Decimal
        current_price = Decimal(str(data['current_price']))
        
        with get_db_session() as db:
            service = MarketPriceService(db)
            price = service.update_price(ticker, current_price)
            
            return jsonify({
                "id": price.id,
                "ticker": price.ticker_symbol,
                "current_price": float(price.current_price),
                "last_updated": price.last_updated.isoformat() + 'Z',
                "message": "Price updated successfully"
            })
    
    except ValueError as e:
        return jsonify({"error": f"Invalid price value: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update price for {ticker}: {str(e)}"}), 500


@app.route("/api/market-prices/bulk-update", methods=["POST"])
def bulk_update_market_prices():
    """Bulk update multiple market prices"""
    try:
        data = request.json
        
        if not isinstance(data, dict) or 'prices' not in data:
            return jsonify({"error": "Expected format: {'prices': {'AAPL': 150.25, 'TSLA': 225.50}}"}), 400
        
        price_data = data['prices']
        if not isinstance(price_data, dict):
            return jsonify({"error": "prices must be a dictionary mapping ticker to price"}), 400
        
        # Convert to Decimal
        from decimal import Decimal
        decimal_prices = {}
        for ticker, price in price_data.items():
            try:
                decimal_prices[ticker] = Decimal(str(price))
            except (ValueError, TypeError):
                return jsonify({"error": f"Invalid price for {ticker}: {price}"}), 400
        
        with get_db_session() as db:
            service = MarketPriceService(db)
            updated_prices = service.bulk_update_prices(decimal_prices)
            
            return jsonify({
                "count": len(updated_prices),
                "updated_prices": [
                    {
                        "id": p.id,
                        "ticker": p.ticker_symbol,
                        "current_price": float(p.current_price),
                        "last_updated": p.last_updated.isoformat() + 'Z'
                    }
                    for p in updated_prices
                ],
                "message": f"Successfully updated {len(updated_prices)} prices"
            })
    
    except Exception as e:
        return jsonify({"error": f"Failed to bulk update prices: {str(e)}"}), 500


@app.route("/api/market-prices/refresh", methods=["POST"])
def refresh_market_prices():
    """Fetch fresh quotes from external provider for stale/missing symbols.

    Reads config from backend/market_data/TwelveData_Config.txt or environment.
    On success, returns updated_count and list of updated symbols.
    """
    try:
        force = False
        try:
            data = request.get_json(silent=True) or {}
            force = bool(data.get('force', False))
        except Exception:
            force = False
        with get_db_session() as db:
            service = MarketDataService(db)
            updated_count, symbols = service.refresh_quotes(force=force)
            return jsonify({
                "updated_count": updated_count,
                "updated_symbols": symbols,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "market_hours": service.is_market_hours()
            })
    except ValueError as e:
        # Handle quota exhaustion gracefully
        error_msg = str(e)
        if "run out of API credits" in error_msg or "429" in error_msg:
            return jsonify({
                "error": "API quota exhausted - automatic refresh disabled until tomorrow",
                "quota_exhausted": True,
                "updated_count": 0,
                "updated_symbols": [],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 429
        return jsonify({"error": error_msg}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to refresh market prices: {str(e)}"}), 500

@app.route("/api/market-prices/scheduler/status", methods=["GET"])
def get_scheduler_status():
    """Get status of the market hours scheduler"""
    global realtime_quotes_enabled
    
    try:
        with get_db_session() as db:
            service = MarketDataService(db)
            
            return jsonify({
                "scheduler_running": scheduler.running,
                "realtime_quotes_enabled": realtime_quotes_enabled,
                "market_hours": service.is_market_hours(),
                "auto_refresh_enabled": service.should_auto_refresh(),
                "refresh_mode": service.cfg.get('REFRESH_MODE', 'unknown'),
                "market_start": service.cfg.get('MARKET_START', '09:30'),
                "market_end": service.cfg.get('MARKET_END', '16:00'),
                "timezone": service.cfg.get('TIMEZONE', 'America/New_York'),
                "ttl_seconds": service.cfg.get('TTL_SECONDS', '300'),
                "max_batch": service.cfg.get('MAX_BATCH', '20'),
                "next_run": scheduler.get_job('market_refresh_job').next_run_time.isoformat() if scheduler.get_job('market_refresh_job') else None
            })
    except Exception as e:
        return jsonify({"error": f"Failed to get scheduler status: {str(e)}"}), 500

@app.route("/api/market-prices/scheduler/toggle", methods=["POST"])
def toggle_realtime_quotes():
    """Toggle real-time quotes on/off for this server instance"""
    global realtime_quotes_enabled
    
    try:
        # Toggle the state
        realtime_quotes_enabled = not realtime_quotes_enabled
        
        status = "enabled" if realtime_quotes_enabled else "disabled"
        print(f"🔄 Real-time quotes {status} via API toggle")
        
        return jsonify({
            "realtime_quotes_enabled": realtime_quotes_enabled,
            "status": status,
            "message": f"Real-time quotes {status} successfully"
        })
    except Exception as e:
        return jsonify({"error": f"Failed to toggle real-time quotes: {str(e)}"}), 500

@app.route("/api/market-prices/<ticker>", methods=["DELETE"])
def delete_market_price(ticker):
    """Delete market price for a ticker"""
    try:
        with get_db_session() as db:
            service = MarketPriceService(db)
            success = service.delete_price(ticker)
            
            if not success:
                return jsonify({"error": f"Price not found for ticker {ticker.upper()}"}), 404
            
            return jsonify({"message": f"Price for {ticker.upper()} deleted successfully"})
    
    except Exception as e:
        return jsonify({"error": f"Failed to delete price for {ticker}: {str(e)}"}), 500


@app.route("/api/portfolios/<int:portfolio_id>/market-value", methods=["GET"])
def get_portfolio_market_value(portfolio_id):
    """Get current market value and gains/losses for a portfolio"""
    try:
        with get_db_session() as db:
            # Get portfolio for cash on hand
            portfolio_service = PortfolioService(db)
            portfolio = portfolio_service.get_portfolio(portfolio_id)
            
            if not portfolio:
                return jsonify({"error": "Portfolio not found"}), 404
            
            # Get portfolio holdings
            transaction_service = TransactionService(db)
            holdings = transaction_service.get_portfolio_holdings(portfolio_id)
            
            # Calculate market values (investments only)
            market_price_service = MarketPriceService(db)
            market_analysis = market_price_service.calculate_portfolio_value(holdings)
            
            # Add cash on hand to total value
            investment_value = float(market_analysis['total_market_value'])
            cash_on_hand = float(portfolio.cash_on_hand) if portfolio.cash_on_hand else 0.00
            total_value = investment_value + cash_on_hand
            
            return jsonify({
                "portfolio_id": portfolio_id,
                "investment_value": investment_value,
                "cash_on_hand": cash_on_hand,
                "total_market_value": total_value,
                "total_cost_basis": float(market_analysis['total_cost_basis']),
                "total_gain_loss": float(market_analysis['total_gain_loss']),
                "total_gain_loss_percent": market_analysis['total_gain_loss_percent'],
                "holdings": market_analysis['holdings_with_prices']
            })
    
    except Exception as e:
        return jsonify({"error": f"Failed to calculate portfolio market value: {str(e)}"}), 500


@app.route("/api/market-prices/stale", methods=["GET"])
def get_stale_prices():
    """Get market prices that need updating"""
    try:
        hours_old = request.args.get('hours_old', default=24, type=int)
        
        with get_db_session() as db:
            service = MarketPriceService(db)
            stale_prices = service.get_stale_prices(hours_old=hours_old)
            
            return jsonify({
                "count": len(stale_prices),
                "hours_old_threshold": hours_old,
                "stale_prices": [
                    {
                        "id": p.id,
                        "ticker": p.ticker_symbol,
                        "current_price": float(p.current_price),
                        "last_updated": p.last_updated.isoformat() + 'Z',
                        "hours_since_update": int((datetime.utcnow() - p.last_updated).total_seconds() / 3600)
                    }
                    for p in stale_prices
                ]
            })
    
    except Exception as e:
        return jsonify({"error": f"Failed to fetch stale prices: {str(e)}"}), 500


# Maintenance endpoint: Clear all quotes and repopulate only tickers currently held
@app.route("/api/market-prices/reset-to-portfolio", methods=["POST"])
def reset_market_prices_to_portfolio():
    """Delete all quotes then recreate entries only for tickers with positive net holdings."""
    try:
        from services.transaction_service import TransactionService
        from decimal import Decimal
        with get_db_session() as db:
            tx_service = TransactionService(db)
            mp_service = MarketPriceService(db)

            # Determine currently held tickers
            tickers = tx_service.get_currently_held_tickers()

            # Clear all existing market prices
            cleared = 0
            existing = mp_service.get_all_prices()
            for p in existing:
                db.delete(p)
                cleared += 1
            db.commit()

            # Recreate placeholder entries for held tickers with $0.01 (will be updated by refresh call)
            created = 0
            for t in tickers:
                mp_service.update_price(t, Decimal('0.01'))
                created += 1

            return jsonify({
                "cleared": cleared,
                "created": created,
                "tickers": tickers
            })
    except Exception as e:
        return jsonify({"error": f"Failed to reset market prices: {str(e)}"}), 500

# InvestorProfile API endpoints
@app.route("/api/investor-profiles", methods=["GET"])
def get_investor_profiles():
    """Get all investor profiles or filter by name/state"""
    try:
        name = request.args.get('name')
        state = request.args.get('state')
        order_by = request.args.get('order_by', 'name')
        
        with get_db_session() as db:
            service = InvestorProfileService(db)
            
            if name:
                # Search by name
                profile = service.get_profile_by_name(name)
                profiles = [profile] if profile else []
            elif state:
                # Filter by state
                profiles = service.get_profiles_by_state(state)
            else:
                # Get all profiles
                profiles = service.get_all_profiles(order_by=order_by)
            
            return jsonify({
                "count": len(profiles),
                "profiles": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "household_income": float(p.annual_household_income),
                        "filing_status": p.filing_status,
                        "state_of_residence": p.state_of_residence,
                        "local_tax_rate": float(p.local_tax_rate),
                        "created_at": p.created_at.isoformat(),
                        "updated_at": p.updated_at.isoformat()
                    }
                    for p in profiles
                ]
            })
    
    except Exception as e:
        return jsonify({"error": f"Failed to fetch investor profiles: {str(e)}"}), 500


@app.route("/api/investor-profiles", methods=["POST"])
def create_investor_profile():
    """Create a new investor profile"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['name', 'household_income', 'filing_status', 'state_of_residence']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        from decimal import Decimal
        household_income = Decimal(str(data['household_income']))
        local_tax_rate = Decimal(str(data.get('local_tax_rate', 0.0)))
        
        with get_db_session() as db:
            service = InvestorProfileService(db)
            profile = service.create_profile(
                name=data['name'],
                household_income=household_income,
                filing_status=data['filing_status'],
                state_of_residence=data['state_of_residence'],
                local_tax_rate=local_tax_rate
            )
            
            return jsonify({
                "id": profile.id,
                "name": profile.name,
                "household_income": float(profile.annual_household_income),
                "filing_status": profile.filing_status,
                "state_of_residence": profile.state_of_residence,
                "local_tax_rate": float(profile.local_tax_rate),
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat(),
                "message": "Investor profile created successfully"
            }), 201
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create investor profile: {str(e)}"}), 500


@app.route("/api/investor-profiles/<int:profile_id>", methods=["GET"])
def get_investor_profile(profile_id):
    """Get a specific investor profile by ID"""
    try:
        with get_db_session() as db:
            service = InvestorProfileService(db)
            profile = service.get_profile(profile_id)
            
            if not profile:
                return jsonify({"error": f"Investor profile with ID {profile_id} not found"}), 404
            
            return jsonify({
                "id": profile.id,
                "name": profile.name,
                "household_income": float(profile.annual_household_income),
                "filing_status": profile.filing_status,
                "state_of_residence": profile.state_of_residence,
                "local_tax_rate": float(profile.local_tax_rate),
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat()
            })
    
    except Exception as e:
        return jsonify({"error": f"Failed to fetch investor profile: {str(e)}"}), 500


@app.route("/api/investor-profiles/<int:profile_id>", methods=["PUT"])
def update_investor_profile(profile_id):
    """Update an investor profile"""
    try:
        data = request.json
        
        # Convert numeric fields to Decimal if provided
        kwargs = {}
        if 'household_income' in data:
            from decimal import Decimal
            kwargs['household_income'] = Decimal(str(data['household_income']))
        if 'local_tax_rate' in data:
            from decimal import Decimal
            kwargs['local_tax_rate'] = Decimal(str(data['local_tax_rate']))
        
        # Add other fields
        for field in ['name', 'filing_status', 'state_of_residence']:
            if field in data:
                kwargs[field] = data[field]
        
        with get_db_session() as db:
            service = InvestorProfileService(db)
            profile = service.update_profile(profile_id, **kwargs)
            
            if not profile:
                return jsonify({"error": f"Investor profile with ID {profile_id} not found"}), 404
            
            return jsonify({
                "id": profile.id,
                "name": profile.name,
                "household_income": float(profile.annual_household_income),
                "filing_status": profile.filing_status,
                "state_of_residence": profile.state_of_residence,
                "local_tax_rate": float(profile.local_tax_rate),
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat(),
                "message": "Profile updated successfully"
            })
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to update investor profile: {str(e)}"}), 500


@app.route("/api/investor-profiles/<int:profile_id>", methods=["DELETE"])
def delete_investor_profile(profile_id):
    """Delete an investor profile"""
    try:
        with get_db_session() as db:
            service = InvestorProfileService(db)
            success = service.delete_profile(profile_id)
            
            if not success:
                return jsonify({"error": f"Investor profile with ID {profile_id} not found"}), 404
            
            return jsonify({"message": f"Investor profile {profile_id} deleted successfully"})
    
    except Exception as e:
        return jsonify({"error": f"Failed to delete investor profile: {str(e)}"}), 500


@app.route("/api/investor-profiles/<int:profile_id>/tax-settings", methods=["GET"])
def get_tax_settings(profile_id):
    """Get tax settings for a specific investor profile"""
    try:
        with get_db_session() as db:
            service = InvestorProfileService(db)
            tax_settings = service.get_tax_settings(profile_id)
            
            if not tax_settings:
                return jsonify({"error": f"Investor profile with ID {profile_id} not found"}), 404
            
            return jsonify(tax_settings)
    
    except Exception as e:
        return jsonify({"error": f"Failed to fetch tax settings: {str(e)}"}), 500


@app.route("/api/investor-profiles/<int:profile_id>/tax-brackets", methods=["GET"])
def get_tax_brackets(profile_id):
    """Get applicable tax brackets for a specific investor profile"""
    try:
        with get_db_session() as db:
            service = InvestorProfileService(db)
            tax_brackets = service.calculate_tax_brackets(profile_id)
            
            if not tax_brackets:
                return jsonify({"error": f"Investor profile with ID {profile_id} not found"}), 404
            
            return jsonify(tax_brackets)
    
    except Exception as e:
        return jsonify({"error": f"Failed to calculate tax brackets: {str(e)}"}), 500


@app.route("/api/investor-profiles/<int:profile_id>/progressive-tax", methods=["POST"])
def calculate_progressive_tax_endpoint(profile_id):
    """Calculate progressive tax on additional income (like capital gains)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
            
        additional_income = data.get('additional_income', 0)
        is_capital_gains = data.get('is_capital_gains', False)
        is_long_term = data.get('is_long_term', False)
        
        with get_db_session() as db:
            service = InvestorProfileService(db)
            
            result = service.calculate_progressive_tax(
                profile_id,
                additional_income,
                is_capital_gains=is_capital_gains,
                is_long_term=is_long_term
            )
            
            return jsonify(result)
            
    except Exception as e:
        return jsonify({"error": f"Failed to calculate progressive tax: {str(e)}"}), 500


# Tax Calculation API endpoints
@app.route("/api/tax-calculation/capital-gains", methods=["POST"])
def calculate_capital_gains_tax():
    """Calculate capital gains tax for a specific transaction"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['portfolio_id', 'ticker', 'quantity', 'sale_price', 'purchase_date', 'sale_date']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        from datetime import datetime
        from decimal import Decimal
        
        portfolio_id = data['portfolio_id']
        ticker = data['ticker'].upper()
        quantity = Decimal(str(data['quantity']))
        sale_price = Decimal(str(data['sale_price']))
        purchase_date = datetime.fromisoformat(data['purchase_date']).date()
        sale_date = datetime.fromisoformat(data['sale_date']).date()
        purchase_price = Decimal(str(data.get('purchase_price', 0)))
        
        with get_db_session() as db:
            service = TaxCalculationService(db)
            
            # Calculate holding period
            holding_days, gains_type = service.calculate_holding_period(purchase_date, sale_date)
            
            # Calculate capital gains
            capital_gains = service.calculate_capital_gains(purchase_price, sale_price, quantity)
            
            # Get portfolio to find investor profile
            portfolio = service.transaction_service.portfolio_service.get_portfolio(portfolio_id)
            if not portfolio or not portfolio.investor_profile_id:
                return jsonify({"error": f"No investor profile associated with portfolio {portfolio_id}"}), 400
            
            # Calculate tax owed
            tax_calculation = service.calculate_federal_tax_owed(
                portfolio.investor_profile_id,
                capital_gains,
                gains_type
            )
            
            return jsonify({
                "portfolio_id": portfolio_id,
                "ticker": ticker,
                "quantity": float(quantity),
                "purchase_price": float(purchase_price),
                "sale_price": float(sale_price),
                "purchase_date": purchase_date.isoformat(),
                "sale_date": sale_date.isoformat(),
                "holding_days": holding_days,
                "capital_gains": float(capital_gains),
                "tax_calculation": tax_calculation
            })
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to calculate capital gains tax: {str(e)}"}), 500


@app.route("/api/tax-calculation/stock-sale-analysis", methods=["POST"])
def analyze_stock_sale():
    """Analyze tax impact of selling stocks using FIFO method"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['portfolio_id', 'ticker', 'quantity', 'sale_price']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        from datetime import datetime
        from decimal import Decimal
        
        portfolio_id = data['portfolio_id']
        ticker = data['ticker'].upper()
        quantity = Decimal(str(data['quantity']))
        sale_price = Decimal(str(data['sale_price']))
        
        # Optional sale date (defaults to today)
        sale_date = None
        if 'sale_date' in data:
            sale_date = datetime.fromisoformat(data['sale_date']).date()
        
        with get_db_session() as db:
            service = TaxCalculationService(db)
            
            analysis = service.analyze_stock_sale_tax_impact(
                portfolio_id=portfolio_id,
                ticker=ticker,
                quantity_to_sell=quantity,
                sale_price=sale_price,
                sale_date=sale_date
            )
            
            return jsonify(analysis)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to analyze stock sale: {str(e)}"}), 500


@app.route("/api/tax-calculation/break-even-price", methods=["POST"])
def calculate_break_even_price():
    """Calculate break-even price for target after-tax proceeds"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['portfolio_id', 'ticker', 'quantity', 'target_after_tax_amount']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        from datetime import datetime
        from decimal import Decimal
        
        portfolio_id = data['portfolio_id']
        ticker = data['ticker'].upper()
        quantity = Decimal(str(data['quantity']))
        target_amount = Decimal(str(data['target_after_tax_amount']))
        
        # Optional sale date (defaults to today)
        sale_date = None
        if 'sale_date' in data:
            sale_date = datetime.fromisoformat(data['sale_date']).date()
        
        with get_db_session() as db:
            service = TaxCalculationService(db)
            
            break_even_analysis = service.calculate_break_even_price(
                portfolio_id=portfolio_id,
                ticker=ticker,
                quantity_to_sell=quantity,
                target_after_tax_amount=target_amount,
                sale_date=sale_date
            )
            
            return jsonify(break_even_analysis)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to calculate break-even price: {str(e)}"}), 500


@app.route("/api/tax-calculation/holding-period", methods=["POST"])
def calculate_holding_period():
    """Calculate holding period and capital gains type"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['purchase_date', 'sale_date']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        from datetime import datetime
        
        purchase_date = datetime.fromisoformat(data['purchase_date']).date()
        sale_date = datetime.fromisoformat(data['sale_date']).date()
        
        with get_db_session() as db:
            service = TaxCalculationService(db)
            
            holding_days, gains_type = service.calculate_holding_period(purchase_date, sale_date)
            
            return jsonify({
                "purchase_date": purchase_date.isoformat(),
                "sale_date": sale_date.isoformat(),
                "holding_days": holding_days,
                "holding_years": round(holding_days / 365.25, 2),
                "capital_gains_type": gains_type.value,
                "is_long_term": gains_type == CapitalGainsType.LONG_TERM,
                "explanation": f"Holding period of {holding_days} days qualifies as {gains_type.value.replace('_', '-')} capital gains"
            })
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to calculate holding period: {str(e)}"}), 500


@app.route("/api/tax-calculation/rates/<int:investor_profile_id>", methods=["GET"])
def get_tax_rates_for_profile(investor_profile_id):
    """Get applicable tax rates for an investor profile"""
    try:
        gains_type_param = request.args.get('gains_type', 'long_term').lower()
        capital_gains_amount = request.args.get('capital_gains_amount', '10000')
        
        # Validate gains type
        if gains_type_param == 'short_term':
            gains_type = CapitalGainsType.SHORT_TERM
        elif gains_type_param == 'long_term':
            gains_type = CapitalGainsType.LONG_TERM
        else:
            return jsonify({"error": "gains_type must be 'short_term' or 'long_term'"}), 400
        
        from decimal import Decimal
        amount = Decimal(str(capital_gains_amount))
        
        with get_db_session() as db:
            service = TaxCalculationService(db)
            
            tax_rates = service.get_federal_tax_rate(
                investor_profile_id=investor_profile_id,
                gains_type=gains_type,
                capital_gains_amount=amount
            )
            
            return jsonify(tax_rates)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to get tax rates: {str(e)}"}), 500


# State Tax API endpoints
@app.route("/api/state-tax/rates/<state_code>", methods=["GET"])
def get_state_tax_rates(state_code):
    """Get state tax rates and information for a specific state"""
    try:
        with get_db_session() as db:
            service = StateTaxService(db)
            
            state_info = service.get_state_info(state_code)
            if not state_info:
                return jsonify({"error": f"State tax data not available for {state_code}"}), 404
            
            return jsonify(state_info)
    
    except Exception as e:
        return jsonify({"error": f"Failed to get state tax rates: {str(e)}"}), 500


@app.route("/api/state-tax/calculate", methods=["POST"])
def calculate_state_tax():
    """Calculate state capital gains tax for an investor profile"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['investor_profile_id', 'capital_gains_amount']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        from decimal import Decimal
        
        investor_profile_id = data['investor_profile_id']
        capital_gains_amount = Decimal(str(data['capital_gains_amount']))
        gains_type = data.get('gains_type', 'long_term')
        
        if gains_type not in ['short_term', 'long_term']:
            return jsonify({"error": "gains_type must be 'short_term' or 'long_term'"}), 400
        
        with get_db_session() as db:
            service = StateTaxService(db)
            
            state_tax_calculation = service.calculate_state_capital_gains_tax(
                investor_profile_id=investor_profile_id,
                capital_gains_amount=capital_gains_amount,
                gains_type=gains_type
            )
            
            return jsonify(state_tax_calculation)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to calculate state tax: {str(e)}"}), 500


@app.route("/api/state-tax/combined-tax", methods=["POST"])
def calculate_combined_tax():
    """Calculate combined federal + state + local tax burden"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['investor_profile_id', 'capital_gains_amount']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        from decimal import Decimal
        
        investor_profile_id = data['investor_profile_id']
        capital_gains_amount = Decimal(str(data['capital_gains_amount']))
        gains_type = data.get('gains_type', 'long_term')
        
        if gains_type not in ['short_term', 'long_term']:
            return jsonify({"error": "gains_type must be 'short_term' or 'long_term'"}), 400
        
        with get_db_session() as db:
            service = StateTaxService(db)
            
            combined_tax_calculation = service.calculate_combined_tax_burden(
                investor_profile_id=investor_profile_id,
                capital_gains_amount=capital_gains_amount,
                gains_type=gains_type
            )
            
            return jsonify(combined_tax_calculation)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to calculate combined tax: {str(e)}"}), 500


@app.route("/api/state-tax/compare-states", methods=["GET"])
def compare_state_tax_rates():
    """Compare capital gains tax rates across all states"""
    try:
        capital_gains_amount = request.args.get('capital_gains_amount', '10000')
        
        from decimal import Decimal
        amount = Decimal(str(capital_gains_amount))
        
        with get_db_session() as db:
            service = StateTaxService(db)
            
            state_comparisons = service.compare_state_tax_rates(amount)
            
            return jsonify({
                "comparison_amount": float(amount),
                "total_states": len(state_comparisons),
                "states": state_comparisons
            })
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to compare state tax rates: {str(e)}"}), 500


@app.route("/api/state-tax/tax-friendly-states", methods=["GET"])
def get_tax_friendly_states():
    """Get the most tax-friendly states for capital gains"""
    try:
        limit = int(request.args.get('limit', '10'))
        
        with get_db_session() as db:
            service = StateTaxService(db)
            
            tax_friendly_states = service.get_tax_friendly_states(limit)
            
            return jsonify({
                "limit": limit,
                "tax_friendly_states": tax_friendly_states
            })
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to get tax-friendly states: {str(e)}"}), 500


@app.route("/api/state-tax/high-tax-states", methods=["GET"])
def get_high_tax_states():
    """Get the highest tax burden states for capital gains"""
    try:
        limit = int(request.args.get('limit', '10'))
        
        with get_db_session() as db:
            service = StateTaxService(db)
            
            high_tax_states = service.get_high_tax_states(limit)
            
            return jsonify({
                "limit": limit,
                "high_tax_states": high_tax_states
            })
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to get high tax states: {str(e)}"}), 500


@app.route("/api/state-tax/relocation-analysis", methods=["POST"])
def analyze_relocation_tax_savings():
    """Analyze potential tax savings from relocating to a different state"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['investor_profile_id', 'target_state', 'annual_capital_gains']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        from decimal import Decimal
        
        investor_profile_id = data['investor_profile_id']
        target_state = data['target_state'].upper()
        annual_capital_gains = Decimal(str(data['annual_capital_gains']))
        
        with get_db_session() as db:
            service = StateTaxService(db)
            
            relocation_analysis = service.analyze_relocation_tax_savings(
                investor_profile_id=investor_profile_id,
                target_state=target_state,
                annual_capital_gains=annual_capital_gains
            )
            
            return jsonify(relocation_analysis)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to analyze relocation tax savings: {str(e)}"}), 500


# Comprehensive Tax Optimization API endpoints
@app.route("/api/comprehensive-tax/complete-analysis", methods=["POST"])
def comprehensive_tax_analysis():
    """Complete federal + state + local tax impact analysis for a stock sale"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['portfolio_id', 'ticker', 'quantity', 'sale_price']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        from datetime import datetime
        from decimal import Decimal
        
        portfolio_id = data['portfolio_id']
        ticker = data['ticker'].upper()
        quantity = Decimal(str(data['quantity']))
        sale_price = Decimal(str(data['sale_price']))
        
        # Optional sale date (defaults to today)
        sale_date = None
        if 'sale_date' in data:
            sale_date = datetime.fromisoformat(data['sale_date']).date()
        
        with get_db_session() as db:
            service = ComprehensiveTaxService(db)
            
            analysis = service.analyze_complete_tax_impact(
                portfolio_id=portfolio_id,
                ticker=ticker,
                quantity_to_sell=quantity,
                sale_price=sale_price,
                sale_date=sale_date
            )
            
            return jsonify(analysis)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to perform comprehensive tax analysis: {str(e)}"}), 500


@app.route("/api/comprehensive-tax/timing-scenarios", methods=["POST"])
def timing_scenarios_analysis():
    """Compare tax impact of selling at different dates"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['portfolio_id', 'ticker', 'quantity', 'sale_price']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        from datetime import datetime
        from decimal import Decimal
        
        portfolio_id = data['portfolio_id']
        ticker = data['ticker'].upper()
        quantity = Decimal(str(data['quantity']))
        sale_price = Decimal(str(data['sale_price']))
        
        # Optional scenario dates
        scenarios = None
        if 'scenarios' in data:
            scenarios = [datetime.fromisoformat(date_str).date() for date_str in data['scenarios']]
        
        with get_db_session() as db:
            service = ComprehensiveTaxService(db)
            
            analysis = service.compare_sale_timing_scenarios(
                portfolio_id=portfolio_id,
                ticker=ticker,
                quantity_to_sell=quantity,
                sale_price=sale_price,
                scenarios=scenarios
            )
            
            return jsonify(analysis)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to analyze timing scenarios: {str(e)}"}), 500


@app.route("/api/comprehensive-tax/loss-harvesting", methods=["POST"])
def tax_loss_harvesting_analysis():
    """Analyze tax-loss harvesting opportunities in a portfolio"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['portfolio_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        from decimal import Decimal
        
        portfolio_id = data['portfolio_id']
        target_loss_amount = None
        if 'target_loss_amount' in data:
            target_loss_amount = Decimal(str(data['target_loss_amount']))
        
        min_position_value = Decimal(str(data.get('min_position_value', '1000')))
        
        with get_db_session() as db:
            service = ComprehensiveTaxService(db)
            
            analysis = service.analyze_tax_loss_harvesting_opportunities(
                portfolio_id=portfolio_id,
                target_loss_amount=target_loss_amount,
                min_position_value=min_position_value
            )
            
            return jsonify(analysis)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to analyze tax-loss harvesting: {str(e)}"}), 500


@app.route("/api/comprehensive-tax/year-end-strategy", methods=["POST"])
def year_end_tax_strategy():
    """Generate comprehensive year-end tax planning strategy"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['portfolio_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        from decimal import Decimal
        
        portfolio_id = data['portfolio_id']
        target_tax_bracket = data.get('target_tax_bracket')
        target_loss_harvest = None
        if 'target_loss_harvest' in data:
            target_loss_harvest = Decimal(str(data['target_loss_harvest']))
        
        with get_db_session() as db:
            service = ComprehensiveTaxService(db)
            
            strategy = service.calculate_year_end_tax_strategy(
                portfolio_id=portfolio_id,
                target_tax_bracket=target_tax_bracket,
                target_loss_harvest=target_loss_harvest
            )
            
            return jsonify(strategy)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to generate year-end tax strategy: {str(e)}"}), 500


@app.route("/api/comprehensive-tax/multi-state-analysis", methods=["POST"])
def multi_state_tax_analysis():
    """Analyze tax impact across multiple states for relocation planning"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['investor_profile_id', 'annual_capital_gains']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        from decimal import Decimal
        
        investor_profile_id = data['investor_profile_id']
        annual_capital_gains = Decimal(str(data['annual_capital_gains']))
        target_states = data.get('target_states')  # Optional list of state codes
        
        with get_db_session() as db:
            service = ComprehensiveTaxService(db)
            
            analysis = service.analyze_multi_state_tax_impact(
                investor_profile_id=investor_profile_id,
                annual_capital_gains=annual_capital_gains,
                target_states=target_states
            )
            
            return jsonify(analysis)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to analyze multi-state tax impact: {str(e)}"}), 500


# Break-Even Analysis API endpoints
@app.route("/api/break-even/transaction/<int:transaction_id>", methods=["POST"])
def calculate_break_even_transaction(transaction_id):
    """Calculate break-even analysis for a single transaction"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
            
        investor_profile_id = data.get('investor_profile_id')
        current_price = data.get('current_price')  # Optional
        
        if not investor_profile_id:
            return jsonify({"error": "investor_profile_id is required"}), 400
        
        with get_db_session() as db:
            service = BreakEvenService(db)
            
            analysis = service.calculate_break_even_single_transaction(
                transaction_id=transaction_id,
                investor_profile_id=investor_profile_id,
                current_price=Decimal(str(current_price)) if current_price else None
            )
            
            return jsonify(analysis)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to calculate break-even analysis: {str(e)}"}), 500


@app.route("/api/break-even/portfolio/<int:portfolio_id>", methods=["POST"])
def calculate_break_even_portfolio(portfolio_id):
    """Calculate break-even analysis for all positions in a portfolio"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
            
        investor_profile_id = data.get('investor_profile_id')
        
        if not investor_profile_id:
            return jsonify({"error": "investor_profile_id is required"}), 400
        
        with get_db_session() as db:
            service = BreakEvenService(db)
            
            analysis = service.calculate_break_even_portfolio(
                portfolio_id=portfolio_id,
                investor_profile_id=investor_profile_id
            )
            
            return jsonify(analysis)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to calculate portfolio break-even analysis: {str(e)}"}), 500


@app.route("/api/break-even/ticker/<string:ticker>", methods=["POST"])
def calculate_break_even_ticker(ticker):
    """Calculate break-even analysis for all positions of a specific ticker"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
            
        investor_profile_id = data.get('investor_profile_id')
        portfolio_id = data.get('portfolio_id')  # Optional
        
        if not investor_profile_id:
            return jsonify({"error": "investor_profile_id is required"}), 400
        
        with get_db_session() as db:
            service = BreakEvenService(db)
            
            analysis = service.calculate_break_even_by_ticker(
                ticker=ticker.upper(),
                investor_profile_id=investor_profile_id,
                portfolio_id=portfolio_id
            )
            
            return jsonify(analysis)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to calculate ticker break-even analysis: {str(e)}"}), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "message": "The requested URL was not found on the server"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

if __name__ == "__main__":
    print("🚀 Portfolio Manager Flask API starting up...")
    print(f"📅 Started at: {datetime.now()}")
    
    # Test database connection on startup
    try:
        # Test database connection using SQLAlchemy
        from sqlalchemy import text
        db = SessionLocal()
        result = db.execute(text("SELECT COUNT(*) FROM portfolios")).scalar()
        db.close()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=8000, debug=False)