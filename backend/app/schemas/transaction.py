"""
Transaction schemas for API requests/responses
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

class TransactionBase(BaseModel):
    description: str
    amount: Decimal
    transaction_date: date
    transaction_type: str
    account_id: int
    category_id: Optional[int] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    transaction_date: Optional[date] = None
    transaction_type: Optional[str] = None
    account_id: Optional[int] = None
    category_id: Optional[int] = None

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True

class TransactionSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    transaction_count: int
    start_date: Optional[date]
    end_date: Optional[date]
