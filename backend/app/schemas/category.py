"""
Category schemas for API requests/responses
"""

from pydantic import BaseModel
from typing import Optional, List

class CategoryBase(BaseModel):
    name: str
    type: str
    parent_category_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    parent_category_id: Optional[int] = None

class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True

class CategoryTree(CategoryResponse):
    children: List['CategoryTree'] = []
    
CategoryTree.model_rebuild()
