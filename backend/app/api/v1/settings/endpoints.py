"""
Settings API Endpoints
Manages app-wide settings that sync across all clients
"""
import os
from datetime import datetime, timedelta
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import router
from app.core.database import get_async_db
from app.models.user_profile import UserProfile
from app.core.constants import SINGLE_USER_ID

# GCP Demo Mode: Auto-disable live pricing after 20 minutes
GCP_LIVE_PRICING_TIMEOUT_MINUTES = 20


def is_twelvedata_configured() -> dict:
    """
    Check if TwelveData API key is properly configured.
    Returns dict with is_configured bool and message.
    """
    # Look for config file
    config_paths = [
        '/app/market_data/TwelveData_Config.txt',
        'backend/market_data/TwelveData_Config.txt',
        'market_data/TwelveData_Config.txt',
    ]
    
    api_key = ''
    config_found = False
    
    for path in config_paths:
        if os.path.exists(path):
            config_found = True
            try:
                with open(path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('#') or not line or '=' not in line:
                            continue
                        key, value = line.split('=', 1)
                        if key.strip() == 'API_KEY':
                            api_key = value.strip()
                            break
            except Exception:
                pass
            break
    
    # Check if key is configured and not placeholder
    is_configured = bool(api_key) and api_key not in ['', 'YOUR_API_KEY_HERE']
    
    if not config_found:
        message = "Config file not found"
    elif not api_key:
        message = "API key not set in config"
    elif api_key == 'YOUR_API_KEY_HERE':
        message = "API key is placeholder - needs real key"
    else:
        message = "API key configured"
    
    return {
        "is_configured": is_configured,
        "message": message
    }


@router.get("/twelvedata-status")
async def get_twelvedata_status():
    """
    Check if TwelveData API is properly configured.
    Used by frontend to show helpful messages when API key is missing.
    """
    result = is_twelvedata_configured()
    return {
        "is_configured": result["is_configured"],
        "provider": "twelve_data",
        "message": result["message"]
    }


@router.get("/realtime-pricing")
async def get_realtime_pricing(db: AsyncSession = Depends(get_async_db)):
    """
    Get the current realtime pricing setting.
    Returns the setting from the user profile (single-user system).
    
    GCP Demo Mode: Auto-disables after 20 minutes to preserve API credits.
    """
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == SINGLE_USER_ID)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        return {"enabled": False, "is_gcp": False, "minutes_remaining": None}
    
    enabled = bool(profile.realtime_pricing_enabled)
    enabled_at = profile.live_pricing_enabled_at
    is_gcp = os.getenv("GCP_DEPLOYMENT") == "true"
    minutes_remaining = None
    
    # GCP Demo Mode: Auto-disable after 20 minutes
    if is_gcp and enabled and enabled_at:
        elapsed = datetime.utcnow() - enabled_at
        timeout = timedelta(minutes=GCP_LIVE_PRICING_TIMEOUT_MINUTES)
        
        if elapsed >= timeout:
            # Auto-disable - time's up!
            profile.realtime_pricing_enabled = False
            profile.live_pricing_enabled_at = None
            await db.commit()
            enabled = False
            minutes_remaining = 0
        else:
            # Calculate remaining time
            remaining = timeout - elapsed
            minutes_remaining = max(0, int(remaining.total_seconds() / 60))
    
    return {
        "enabled": enabled,
        "is_gcp": is_gcp,
        "minutes_remaining": minutes_remaining
    }


@router.put("/realtime-pricing")
async def set_realtime_pricing(
    enabled: bool,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Set the realtime pricing setting.
    This persists to the database so all clients see the same state.
    
    GCP Demo Mode: When enabled, starts a 20-minute countdown.
    """
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == SINGLE_USER_ID)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        return {"success": False, "error": "No user profile found"}
    
    is_gcp = os.getenv("GCP_DEPLOYMENT") == "true"
    
    profile.realtime_pricing_enabled = enabled
    
    # Track when it was enabled (for GCP auto-disable feature)
    if enabled:
        profile.live_pricing_enabled_at = datetime.utcnow()
    else:
        profile.live_pricing_enabled_at = None
    
    await db.commit()
    
    return {
        "success": True,
        "enabled": enabled,
        "is_gcp": is_gcp,
        "timeout_minutes": GCP_LIVE_PRICING_TIMEOUT_MINUTES if is_gcp and enabled else None
    }

