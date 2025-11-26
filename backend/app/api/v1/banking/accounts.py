"""
Finance Manager - Accounts API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse, AccountSummary

router = APIRouter()


@router.post("/", response_model=AccountResponse)
async def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new account for the current user."""
    db_account = Account(
        user_id=current_user.id,
        name=account.name,
        account_type=account.account_type,
        account_number=account.account_number,
        bank_name=account.bank_name,
        balance=account.balance,
        credit_limit=account.credit_limit
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    # Convert UUID to string for JSON response
    response_data = AccountResponse(
        id=str(db_account.id),
        user_id=str(db_account.user_id),
        name=db_account.name,
        account_type=db_account.account_type,
        account_number=db_account.account_number,
        bank_name=db_account.bank_name,
        balance=db_account.balance,
        credit_limit=db_account.credit_limit,
        is_active=db_account.is_active,
        created_at=db_account.created_at,
        updated_at=db_account.updated_at
    )
    return response_data


@router.get("/", response_model=List[AccountSummary])
async def get_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all accounts for the current user."""
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    
    # Convert UUID to string for JSON response
    response_data = []
    for account in accounts:
        response_data.append(AccountSummary(
            id=str(account.id),
            name=account.name,
            account_type=account.account_type,
            balance=account.balance,
            is_active=account.is_active
        ))
    return response_data


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific account by ID."""
    try:
        account_uuid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account ID format"
        )
    
    account = db.query(Account).filter(
        Account.id == account_uuid,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Convert UUID to string for JSON response
    response_data = AccountResponse(
        id=str(account.id),
        user_id=str(account.user_id),
        name=account.name,
        account_type=account.account_type,
        account_number=account.account_number,
        bank_name=account.bank_name,
        balance=account.balance,
        credit_limit=account.credit_limit,
        is_active=account.is_active,
        created_at=account.created_at,
        updated_at=account.updated_at
    )
    return response_data


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    account_update: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing account."""
    try:
        account_uuid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account ID format"
        )
    
    account = db.query(Account).filter(
        Account.id == account_uuid,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Update fields if provided
    update_data = account_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    
    # Convert UUID to string for JSON response
    response_data = AccountResponse(
        id=str(account.id),
        user_id=str(account.user_id),
        name=account.name,
        account_type=account.account_type,
        account_number=account.account_number,
        bank_name=account.bank_name,
        balance=account.balance,
        credit_limit=account.credit_limit,
        is_active=account.is_active,
        created_at=account.created_at,
        updated_at=account.updated_at
    )
    return response_data


@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an account (soft delete by setting is_active to False)."""
    try:
        account_uuid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account ID format"
        )
    
    account = db.query(Account).filter(
        Account.id == account_uuid,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Soft delete by setting is_active to False
    account.is_active = False
    db.commit()
    
    return {"message": "Account deleted successfully"}


@router.get("/status")
async def accounts_status():
    """Account service status check."""
    return {"status": "available"}
