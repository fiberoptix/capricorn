"""
Budget schemas for API requests/responses
"""

from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import date

class BudgetBase(BaseModel):
    category_id: int
    amount: Decimal
    start_date: date
    end_date: date

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    amount: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class BudgetResponse(BudgetBase):
    id: int
    user_id: int
    spent: Optional[Decimal] = 0
    remaining: Optional[Decimal] = 0
    
    class Config:
        from_attributes = True
