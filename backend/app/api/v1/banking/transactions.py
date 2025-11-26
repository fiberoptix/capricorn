"""
Transactions API Endpoints - Single User System
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, Any
from datetime import datetime

from app.core.database import get_async_db
from app.models.transaction import Transaction
from app.models.category import Category
from app.core.constants import SINGLE_USER_ID

router = APIRouter(tags=["Transactions"])


@router.put("/{transaction_id}/category")
async def update_transaction_category(
    transaction_id: str,
    category_id: str = Query(..., description="Category ID to assign"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update the category of a specific transaction.
    """
    try:
        # Find the transaction
        transaction_query = select(Transaction).filter(
            and_(
                Transaction.id == transaction_id,
                Transaction.user_id == SINGLE_USER_ID
            )
        )
        transaction_result = await db.execute(transaction_query)
        transaction = transaction_result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found"
            )
        
        # Verify the category exists
        category_query = select(Category).filter(Category.id == category_id)
        category_result = await db.execute(category_query)
        category = category_result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(
                status_code=404,
                detail="Category not found"
            )
        
        # Update the transaction category
        transaction.category_id = category_id
        await db.commit()
        
        return {
            "success": True,
            "message": f"Transaction category updated to '{category.name}' successfully",
            "data": {
                "transaction_id": transaction_id,
                "category_id": category_id,
                "category_name": category.name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update transaction category: {str(e)}"
        )


@router.get("/double-charges")
async def get_double_charges(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Find potential double charges - debit transactions with same description and amount on the same day
    Excludes MTA charges and credit transactions (refunds are legitimate)
    """
    try:
        # Get all transactions for the user
        transactions_query = select(Transaction).where(
            Transaction.user_id == SINGLE_USER_ID
        ).order_by(Transaction.transaction_date.desc())
        
        result = await db.execute(transactions_query)
        transactions = result.scalars().all()
        
        # Find potential double charges
        double_charges = []
        
        # Convert to list for easier iteration
        transaction_list = list(transactions)
        
        for i, transaction in enumerate(transaction_list):
            # Skip MTA charges (legitimate round trips)
            if "MTA" in transaction.description.upper():
                continue
            
            # Skip non-debit transactions (we only care about double charges, not refunds)
            if transaction.transaction_type != 'debit':
                continue
            
            # Look for matching transactions on the same day
            matches = []
            for j, other_transaction in enumerate(transaction_list):
                if i != j:  # Don't compare with itself
                    # Check if description and amount match AND both are debit transactions
                    if (transaction.description.lower() == other_transaction.description.lower() and 
                        abs(float(transaction.amount) - float(other_transaction.amount)) < 0.01 and
                        transaction.transaction_type == 'debit' and
                        other_transaction.transaction_type == 'debit'):
                        
                        # Check if dates are exactly the same
                        if transaction.transaction_date == other_transaction.transaction_date:
                            matches.append({
                                "id": str(other_transaction.id),
                                "transaction_date": other_transaction.transaction_date.isoformat(),
                                "description": other_transaction.description,
                                "amount": float(other_transaction.amount),
                                "transaction_type": other_transaction.transaction_type,
                                "created_at": other_transaction.created_at.isoformat(),
                                "days_apart": 0  # Same day
                            })
            
            if matches:
                # Sort matches by date
                matches.sort(key=lambda x: x["transaction_date"])
                
                double_charges.append({
                    "primary_transaction": {
                        "id": str(transaction.id),
                        "transaction_date": transaction.transaction_date.isoformat(),
                        "description": transaction.description,
                        "amount": float(transaction.amount),
                        "transaction_type": transaction.transaction_type,
                        "created_at": transaction.created_at.isoformat()
                    },
                    "matching_transactions": matches,
                    "total_matches": len(matches)
                })
        
        # Remove duplicates (if transaction A matches B, don't also show B matches A)
        unique_groups = []
        processed_ids = set()
        
        for group in double_charges:
            primary_id = group["primary_transaction"]["id"]
            if primary_id not in processed_ids:
                # Mark all IDs in this group as processed
                processed_ids.add(primary_id)
                for match in group["matching_transactions"]:
                    processed_ids.add(match["id"])
                unique_groups.append(group)
        
        return {
            "success": True,
            "data": {
                "double_charge_groups": unique_groups,
                "total_groups": len(unique_groups),
                "total_suspicious_transactions": sum(1 + len(group["matching_transactions"]) for group in unique_groups)
            },
            "message": f"Found {len(unique_groups)} potential double charge groups"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find double charges: {str(e)}"
        )


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Delete a transaction by ID
    """
    try:
        # Find the transaction
        transaction_query = select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == SINGLE_USER_ID
        )
        
        result = await db.execute(transaction_query)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found"
            )
        
        # Delete the transaction
        await db.delete(transaction)
        await db.commit()
        
        return {
            "success": True,
            "message": "Transaction deleted successfully",
            "deleted_transaction": {
                "id": str(transaction.id),
                "description": transaction.description,
                "amount": float(transaction.amount),
                "transaction_date": transaction.transaction_date.isoformat()
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete transaction: {str(e)}"
        )
