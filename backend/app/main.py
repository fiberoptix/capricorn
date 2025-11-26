"""
Capricorn Finance Platform - Main Application
FastAPI backend for unified personal finance management
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db, AsyncSessionLocal
import os
import logging

logger = logging.getLogger(__name__)

# Get build number from environment
BUILD_NUMBER = os.getenv("BUILD_NUMBER", "1")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown lifecycle handler.
    On startup: Check if database has user data, bootstrap if empty.
    """
    # Startup
    logger.info("Capricorn API starting up...")
    
    # Bootstrap user if database is empty
    try:
        from app.api.v1.data.endpoints import ensure_bootstrap_user
        async with AsyncSessionLocal() as db:
            created = await ensure_bootstrap_user(db)
            if created:
                logger.info(f"Bootstrap user created: {created}")
            else:
                logger.info("User data exists, no bootstrap needed")
    except Exception as e:
        logger.warning(f"Bootstrap check failed (may be first run): {e}")
    
    yield  # App runs here
    
    # Shutdown
    logger.info("Capricorn API shutting down...")

app = FastAPI(
    title="Capricorn Finance API",
    description="Unified Personal Finance Platform API",
    version=f"1.0.0-build.{BUILD_NUMBER}",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Capricorn Finance API",
        "version": f"1.0.0-build.{BUILD_NUMBER}",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "capricorn-api",
        "build_number": BUILD_NUMBER
    }

@app.get("/api/docker/status")
async def docker_status():
    """Docker container status - returns running containers count"""
    # In production, this would check actual Docker status
    # For now, return static data indicating all 4 containers are up
    return {"total": 4, "running": 4}

@app.get("/api/dashboard/metrics")
async def dashboard_metrics(db: AsyncSession = Depends(get_async_db)):
    """Dashboard metrics - finance, portfolio, retirement overview"""
    from sqlalchemy import select, func, and_, case
    from app.models.transaction import Transaction
    from app.models.account import Account
    from app.models.category import Category
    from datetime import date
    
    # Get current month date range
    today = date.today()
    month_start = today.replace(day=1)
    
    # Get total balance across accounts
    balance_result = await db.execute(
        select(func.coalesce(func.sum(Account.balance), 0)).where(
            and_(Account.user_id == 1, Account.is_active == True)
        )
    )
    total_balance = float(balance_result.scalar() or 0)
    
    # Get monthly income and expenses
    monthly_result = await db.execute(
        select(
            func.coalesce(func.sum(case((Transaction.transaction_type == 'credit', Transaction.amount), else_=0)), 0).label('income'),
            func.coalesce(func.sum(case((Transaction.transaction_type == 'debit', Transaction.amount), else_=0)), 0).label('expenses')
        ).where(
            and_(
                Transaction.user_id == 1,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date <= today
            )
        )
    )
    monthly_data = monthly_result.first()
    monthly_income = float(monthly_data.income or 0)
    monthly_expenses = float(monthly_data.expenses or 0)
    
    # Get top spending category
    top_category_result = await db.execute(
        select(Category.name)
        .select_from(Transaction)
        .join(Category, Transaction.category_id == Category.id)
        .where(
            and_(
                Transaction.user_id == 1,
                Transaction.transaction_type == 'debit',
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date <= today
            )
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(1)
    )
    top_category = top_category_result.scalar() or "None"
    
    return {
        "finance": {
            "totalBalance": total_balance,
            "monthlyIncome": monthly_income,
            "monthlyExpenses": monthly_expenses,
            "topCategory": top_category
        },
        "portfolio": {
            "totalValue": 0.00,  # Will be implemented in Phase 3
            "ytdReturn": 0.0,
            "realizedGains": 0.00,
            "unrealizedGains": 0.00
        },
        "retirement": {
            "projectedAge": 0,  # Will be implemented in Phase 4
            "monthlyTarget": 0.00,
            "currentSavings": 0.00,
            "monthsToGoal": 0
        }
    }

# Include Banking API router (Phase 2a/2b - Finance Manager Import)
from app.api.v1.banking import router as banking_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.tax.endpoints import router as tax_router
from app.api.v1.profile import router as profile_router  # Phase 3G - Profile API
from app.api.v1.retirement import router as retirement_router  # Phase 3H - Retirement API
from app.api.v1.data.endpoints import router as data_router  # Phase 10 - Data Export/Import
from app.api.v1.settings import router as settings_router  # App-wide settings sync
app.include_router(banking_router)
app.include_router(portfolio_router, prefix="/api/v1")
app.include_router(tax_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")
app.include_router(retirement_router, prefix="/api/v1")
app.include_router(data_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")

