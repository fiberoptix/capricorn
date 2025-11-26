"""
Authentication module for Capricorn
DEV MODE: No authentication, returns default user
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from app.models.user_profile import UserProfile
from app.core.database import get_db
from sqlalchemy.orm import Session

class DummyUser:
    """Dummy user for DEV mode without authentication"""
    id = "1"  # Default to user_id=1 which we imported
    email = "demo@example.com"
    first_name = "Demo"
    last_name = "User"
    is_active = True
    
def get_current_user(db: Session = Depends(get_db)) -> DummyUser:
    """
    DEV MODE: Returns dummy user without authentication
    In production, this would validate JWT tokens
    """
    return DummyUser()

def get_current_active_user(current_user: DummyUser = Depends(get_current_user)) -> DummyUser:
    """
    DEV MODE: Returns dummy user if active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
