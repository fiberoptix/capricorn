"""
Banking API Module - Single User System
Combines all banking-related endpoints under /api/v1/banking/
"""

from fastapi import APIRouter
from . import (
    accounts,
    categories,
    transactions,
    settings,
    process,
    finance
)

# Create main banking router
router = APIRouter(prefix="/api/v1/banking", tags=["banking"])

# Include all sub-routers (production endpoints only)
router.include_router(finance.router)  # Dashboard, transactions, budget, cumulative-spending
router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
router.include_router(categories.router, prefix="/categories", tags=["categories"])
router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
router.include_router(process.router, prefix="/process", tags=["process"])
router.include_router(settings.router, prefix="/settings", tags=["settings"])

# Health check endpoint for banking module
@router.get("/health")
async def banking_health():
    """Check if banking module is healthy"""
    return {
        "status": "healthy",
        "module": "banking",
        "services": {
            "classifier": "ready",
            "parser": "ready",
            "tagger": "ready",
            "uploader": "ready"
        }
    }
