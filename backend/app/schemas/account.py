"""
Account schemas for API requests/responses
"""

from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class AccountBase(BaseModel):
    name: str
    account_type: str
    bank_name: Optional[str] = None
    account_number: Optional[str] = None

class AccountCreate(AccountBase):
    balance: Optional[Decimal] = 0

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    balance: Optional[Decimal] = None
    is_active: Optional[bool] = None

class AccountResponse(AccountBase):
    id: int
    balance: Decimal
    is_active: bool
    
    class Config:
        from_attributes = True

class AccountSummary(BaseModel):
    total_accounts: int
    total_balance: Decimal
    active_accounts: int
