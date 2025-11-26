"""
User schemas for API requests/responses
"""

from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    email: str
    first_name: str
    last_name: str

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool = True
    
    class Config:
        from_attributes = True
