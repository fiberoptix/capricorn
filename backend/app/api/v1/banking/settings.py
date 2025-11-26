"""
Settings API Endpoints for Capricorn Finance Module

Handles:
- Data summary statistics
- Transaction date ranges
- Tag/category management

Note: Export/Import/Clear functionality moved to DATA module (Phase 10)
Uses /api/v1/data/* endpoints instead
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, update
from sqlalchemy.orm import selectinload
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_async_db
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category

class TagUpdateRequest(BaseModel):
    new_tag_name: str

class TagMigrateRequest(BaseModel):
    target_tag_name: str

router = APIRouter()

# Import single user constant
from app.core.constants import SINGLE_USER_ID


@router.get("/data-summary/", response_model=Dict[str, Any])
async def get_data_summary(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a summary of all user data in the system.
    
    Args:
        db: Database session
        
    Returns:
        Dict containing data summary
    """
    try:
        user_id = SINGLE_USER_ID  # For DEV mode
        
        # Count transactions
        result = await db.execute(
            text("SELECT COUNT(*) FROM transactions WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        transaction_count = result.scalar() or 0
        
        # Count accounts
        result = await db.execute(
            text("SELECT COUNT(*) FROM accounts WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        account_count = result.scalar() or 0
        
        # Count categories used by this user's transactions
        result = await db.execute(
            text("""
                SELECT COUNT(DISTINCT c.id) 
                FROM categories c
                JOIN transactions t ON t.category_id = c.id
                WHERE t.user_id = :user_id
            """),
            {"user_id": user_id}
        )
        category_count = result.scalar() or 0
        
        # Count files
        file_count = 0
        file_details = {}
        # Use path relative to banking services module - works in both DEV and PROD Docker
        base_dir = Path(__file__).parent.parent.parent.parent / "services" / "banking" / "data"
        
        for dir_name in ["input", "working", "output", "classified"]:
            dir_path = base_dir / dir_name
            if dir_path.exists():
                files = list(dir_path.glob("*"))
                file_details[dir_name] = len(files)
                if dir_name == "working":  # Count working directory for main count
                    file_count = len(files)
        
        # Check uploads directory
        uploads_dir = Path("/tmp/capricorn_uploads")
        if uploads_dir.exists():
            upload_files = list(uploads_dir.glob("*"))
            file_details["uploads"] = len(upload_files)
        
        return {
            "success": True,
            "data": {
                "transactions": transaction_count,
                "accounts": account_count,
                "categories": category_count,
                "files": file_count,
                "file_details": file_details,
                "user_id": user_id
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get data summary: {str(e)}"
        )


@router.get("/transaction-date-ranges/", response_model=Dict[str, Any])
async def get_transaction_date_ranges(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get earliest and latest transaction dates by account.
    
    Args:
        db: Database session
        
    Returns:
        Dict containing earliest and latest transaction dates by account
    """
    try:
        user_id = SINGLE_USER_ID  # For DEV mode
        
        # Get transaction date ranges by account
        query = text("""
            SELECT 
                a.name as account_name,
                MIN(t.transaction_date) as earliest_date,
                MAX(t.transaction_date) as latest_date,
                COUNT(t.id) as transaction_count
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            WHERE t.user_id = :user_id
            GROUP BY a.name
            ORDER BY a.name
        """)
        
        result = await db.execute(query, {"user_id": user_id})
        ranges_data = result.fetchall()
        
        # Format the results
        account_ranges = []
        for row in ranges_data:
            account_ranges.append({
                "account_name": row[0],
                "earliest_date": row[1].strftime("%Y-%m-%d") if row[1] else None,
                "latest_date": row[2].strftime("%Y-%m-%d") if row[2] else None,
                "transaction_count": row[3]
            })
        
        return {
            "success": True,
            "data": {
                "account_ranges": account_ranges
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get transaction date ranges: {str(e)}"
        )


@router.get("/tags-summary/", response_model=Dict[str, Any])
async def get_tags_summary(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a summary of all tags and their usage counts.
    
    Args:
        db: Database session
        
    Returns:
        Dict containing tags summary
    """
    try:
        user_id = SINGLE_USER_ID  # For DEV mode
        
        # Get all tags with their counts
        query = text("""
            SELECT 
                COALESCE(c.name, 'Uncategorized') as tag_name,
                COUNT(t.id) as record_count
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = :user_id
            GROUP BY c.name
            ORDER BY tag_name
        """)
        
        result = await db.execute(query, {"user_id": user_id})
        tags_data = result.fetchall()
        
        # Format the results
        tags_summary = []
        for row in tags_data:
            tags_summary.append({
                "tag_name": row[0],
                "record_count": row[1]
            })
        
        return {
            "success": True,
            "data": {
                "tags": tags_summary,
                "total_tags": len(tags_summary)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tags summary: {str(e)}"
        )


@router.put("/tags/{tag_name}/edit", response_model=Dict[str, Any])
async def edit_tag(
    tag_name: str,
    request: TagUpdateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Edit a tag name and update all records with that tag.
    
    Args:
        tag_name: Current tag name to edit
        request: New tag name
        db: Database session
        
    Returns:
        Dict containing operation result
    """
    try:
        user_id = SINGLE_USER_ID  # For DEV mode
        
        # First, find or create the new category
        category_query = select(Category).where(
            Category.name == request.new_tag_name
        )
        category_result = await db.execute(category_query)
        new_category = category_result.scalar_one_or_none()
        
        if not new_category:
            # Create new category
            new_category = Category(
                name=request.new_tag_name,
                category_type='expense'  # Default to expense
            )
            db.add(new_category)
            await db.flush()
        
        # Find the old category
        old_category_query = select(Category).where(
            Category.name == tag_name
        )
        old_category_result = await db.execute(old_category_query)
        old_category = old_category_result.scalar_one_or_none()
        
        records_updated = 0
        
        if not old_category:
            # Handle "Uncategorized" case
            if tag_name == "Uncategorized":
                # Update all uncategorized transactions
                update_query = update(Transaction).where(
                    Transaction.user_id == user_id,
                    Transaction.category_id.is_(None)
                ).values(category_id=new_category.id)
                result = await db.execute(update_query)
                records_updated = result.rowcount
            else:
                raise HTTPException(status_code=404, detail="Tag not found")
        else:
            # Update all transactions with this category
            update_query = update(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.category_id == old_category.id
            ).values(category_id=new_category.id)
            result = await db.execute(update_query)
            records_updated = result.rowcount
            
            # Delete the old category if it's different from the new one
            if old_category.id != new_category.id:
                await db.delete(old_category)
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Tag '{tag_name}' updated to '{request.new_tag_name}'",
            "data": {
                "old_tag_name": tag_name,
                "new_tag_name": request.new_tag_name,
                "records_updated": records_updated
            }
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to edit tag: {str(e)}"
        )


@router.delete("/tags/{tag_name}/remove", response_model=Dict[str, Any])
async def remove_tag(
    tag_name: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Remove a tag and set all records with that tag to Uncategorized.
    
    Args:
        tag_name: Tag name to remove
        db: Database session
        
    Returns:
        Dict containing operation result
    """
    try:
        user_id = SINGLE_USER_ID  # For DEV mode
        
        # Can't remove "Uncategorized"
        if tag_name == "Uncategorized":
            raise HTTPException(status_code=400, detail="Cannot remove 'Uncategorized' tag")
        
        # Find the category to remove
        category_query = select(Category).where(
            Category.name == tag_name
        )
        category_result = await db.execute(category_query)
        category = category_result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(status_code=404, detail="Tag not found")
        
        # Update all transactions with this category to uncategorized (NULL)
        update_query = update(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.category_id == category.id
        ).values(category_id=None)
        result = await db.execute(update_query)
        records_updated = result.rowcount
        
        # Delete the category
        await db.delete(category)
        await db.commit()
        
        return {
            "success": True,
            "message": f"Tag '{tag_name}' removed and {records_updated} records set to Uncategorized",
            "data": {
                "removed_tag_name": tag_name,
                "records_updated": records_updated
            }
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove tag: {str(e)}"
        )


@router.put("/tags/{tag_name}/migrate", response_model=Dict[str, Any])
async def migrate_tag(
    tag_name: str,
    request: TagMigrateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Migrate all records from one tag to another tag.
    
    Args:
        tag_name: Source tag name to migrate from
        request: Target tag name to migrate to
        db: Database session
        
    Returns:
        Dict containing operation result
    """
    try:
        user_id = SINGLE_USER_ID  # For DEV mode
        
        # Find the target category
        target_category_query = select(Category).where(
            Category.name == request.target_tag_name
        )
        target_category_result = await db.execute(target_category_query)
        target_category = target_category_result.scalar_one_or_none()
        
        if not target_category:
            raise HTTPException(status_code=404, detail="Target tag not found")
        
        # Find the source category
        source_category_query = select(Category).where(
            Category.name == tag_name
        )
        source_category_result = await db.execute(source_category_query)
        source_category = source_category_result.scalar_one_or_none()
        
        records_updated = 0
        
        if not source_category:
            # Handle "Uncategorized" case
            if tag_name == "Uncategorized":
                # Update all uncategorized transactions
                update_query = update(Transaction).where(
                    Transaction.user_id == user_id,
                    Transaction.category_id.is_(None)
                ).values(category_id=target_category.id)
                result = await db.execute(update_query)
                records_updated = result.rowcount
            else:
                raise HTTPException(status_code=404, detail="Source tag not found")
        else:
            # Update all transactions with this category
            update_query = update(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.category_id == source_category.id
            ).values(category_id=target_category.id)
            result = await db.execute(update_query)
            records_updated = result.rowcount
            
            # Delete the source category
            await db.delete(source_category)
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Tag '{tag_name}' migrated to '{request.target_tag_name}'",
            "data": {
                "source_tag_name": tag_name,
                "target_tag_name": request.target_tag_name,
                "records_updated": records_updated
            }
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to migrate tag: {str(e)}"
        )


@router.post("/tags/create", response_model=Dict[str, Any])
async def create_tag(
    request: TagUpdateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new tag for future use.
    
    Args:
        request: New tag name
        db: Database session
        
    Returns:
        Dict containing operation result
    """
    try:
        # Check if tag already exists
        category_query = select(Category).where(
            Category.name == request.new_tag_name
        )
        category_result = await db.execute(category_query)
        existing_category = category_result.scalar_one_or_none()
        
        if existing_category:
            raise HTTPException(status_code=400, detail="Tag already exists")
        
        # Create new category
        new_category = Category(
            name=request.new_tag_name,
            category_type='expense'  # Default to expense
        )
        db.add(new_category)
        await db.commit()
        
        return {
            "success": True,
            "message": f"Tag '{request.new_tag_name}' created successfully",
            "data": {
                "tag_name": request.new_tag_name,
                "category_id": str(new_category.id)
            }
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create tag: {str(e)}"
        )
