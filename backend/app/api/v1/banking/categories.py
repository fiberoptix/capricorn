"""
Finance Manager - Categories API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
import uuid

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter()


@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    category_type: Optional[str] = Query(None, description="Filter by category type (income/expense)"),
    search: Optional[str] = Query(None, description="Search categories by name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all categories for the current user with optional filtering."""
    query = db.query(Category).filter(Category.is_active == True)
    
    # Apply filters
    if category_type:
        query = query.filter(Category.category_type == category_type.lower())
    
    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))
    
    # Order by name
    categories = query.order_by(Category.name).all()
    
    return [
        CategoryResponse(
            id=str(category.id),
            name=category.name,
            description=category.description,
            category_type=category.category_type,
            parent_id=str(category.parent_id) if category.parent_id else None,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at
        )
        for category in categories
    ]


@router.post("/", response_model=CategoryResponse)
async def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new category."""
    # Check if category name already exists
    existing_category = db.query(Category).filter(
        Category.name == category.name,
        Category.is_active == True
    ).first()
    
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )
    
    # Create new category
    db_category = Category(
        name=category.name,
        description=category.description,
        category_type=category.category_type.lower(),
        is_active=True
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return CategoryResponse(
        id=str(db_category.id),
        name=db_category.name,
        description=db_category.description,
        category_type=db_category.category_type,
        parent_id=str(db_category.parent_id) if db_category.parent_id else None,
        is_active=db_category.is_active,
        created_at=db_category.created_at,
        updated_at=db_category.updated_at
    )


@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_category_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get category statistics and transaction counts."""
    
    # Get categories with transaction counts
    category_stats = db.query(
        Category.id,
        Category.name,
        Category.category_type,
        func.count(Transaction.id).label('transaction_count'),
        func.sum(Transaction.amount).label('total_amount')
    ).outerjoin(Transaction, Category.id == Transaction.category_id)\
     .filter(Category.is_active == True)\
     .group_by(Category.id, Category.name, Category.category_type)\
     .order_by(desc('transaction_count'))\
     .all()
    
    # Calculate totals
    total_categories = db.query(Category).filter(Category.is_active == True).count()
    income_categories = db.query(Category).filter(
        Category.is_active == True,
        Category.category_type == 'income'
    ).count()
    expense_categories = db.query(Category).filter(
        Category.is_active == True,
        Category.category_type == 'expense'
    ).count()
    
    # Format category stats
    categories_with_stats = []
    for stat in category_stats:
        categories_with_stats.append({
            "id": str(stat.id),
            "name": stat.name,
            "category_type": stat.category_type,
            "transaction_count": stat.transaction_count or 0,
            "total_amount": float(stat.total_amount) if stat.total_amount else 0.0
        })
    
    return {
        "total_categories": total_categories,
        "income_categories": income_categories,
        "expense_categories": expense_categories,
        "categories_with_stats": categories_with_stats
    }


@router.get("/status")
async def categories_status():
    return {"status": "available"}
