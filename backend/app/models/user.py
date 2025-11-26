"""
User model - stub for Finance Manager compatibility
Actual user model is user_profile.py, this is for endpoint compatibility
"""

# For DEV mode, just import UserProfile as User
from .user_profile import UserProfile as User

__all__ = ['User']
