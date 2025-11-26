"""
Settings API Endpoints
Manages app-wide settings that sync across all clients
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import router
from app.core.database import get_async_db
from app.models.user_profile import UserProfile
from app.core.constants import SINGLE_USER_ID


@router.get("/realtime-pricing")
async def get_realtime_pricing(db: AsyncSession = Depends(get_async_db)):
    """
    Get the current realtime pricing setting.
    Returns the setting from the user profile (single-user system).
    """
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == SINGLE_USER_ID)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        return {"enabled": False}
    
    return {"enabled": bool(profile.realtime_pricing_enabled)}


@router.put("/realtime-pricing")
async def set_realtime_pricing(
    enabled: bool,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Set the realtime pricing setting.
    This persists to the database so all clients see the same state.
    """
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == SINGLE_USER_ID)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        return {"success": False, "error": "No user profile found"}
    
    profile.realtime_pricing_enabled = enabled
    await db.commit()
    
    return {"success": True, "enabled": enabled}

