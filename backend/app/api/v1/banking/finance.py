"""
Finance Data API Endpoints

Core endpoints for financial data, dashboard metrics, and budget analysis.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, extract, case
from sqlalchemy.orm import selectinload
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import calendar

from app.core.database import get_async_db
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category
from app.models.budget import Budget
from app.core.constants import SINGLE_USER_ID

router = APIRouter(tags=["Finance Data"])


def get_month_date_range(year: int, month: int) -> Tuple[date, date]:
    """
    Get the exact first and last day of a given month.
    Uses calendar.monthrange() to ensure we always get the correct last day
    (28/29 for Feb, 30 for Apr/Jun/Sep/Nov, 31 for others).
    
    Args:
        year: The year (e.g., 2025)
        month: The month (1-12)
        
    Returns:
        Tuple of (first_day, last_day) as date objects
    """
    first_day = date(year, month, 1)
    _, last_day_num = calendar.monthrange(year, month)
    last_day = date(year, month, last_day_num)
    return first_day, last_day


@router.get("/dashboard")
async def get_dashboard_metrics(
    period: str = Query("this_month", description="Period for metrics"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Get real dashboard metrics from database"""
    
    # Determine date range using bulletproof month boundary calculation
    today = date.today()
    
    if period == "this_month":
        # Get exact first and last day of current month
        start, last_day_of_month = get_month_date_range(today.year, today.month)
        end = today  # Up to today within the current month
    elif period == "last_month":
        # Get the previous month
        if today.month == 1:
            last_month_year = today.year - 1
            last_month = 12
        else:
            last_month_year = today.year
            last_month = today.month - 1
        # Get exact first and last day of last month
        start, end = get_month_date_range(last_month_year, last_month)
    elif period == "last_3_months":
        # Go back 3 months using exact month boundaries
        end = today
        three_months_ago = today.month - 3
        if three_months_ago <= 0:
            start_year = today.year - 1
            start_month = 12 + three_months_ago
        else:
            start_year = today.year
            start_month = three_months_ago
        start, _ = get_month_date_range(start_year, start_month)
    elif period == "this_year":
        # January 1st of current year to today
        start = date(today.year, 1, 1)
        end = today
    elif period == "all_time":
        # No date filtering
        start = None
        end = None
    elif period == "date_range" and start_date and end_date:
        # Custom date range
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        # Default to this month
        start, last_day_of_month = get_month_date_range(today.year, today.month)
        end = today
    
    # Get account balances
    accounts_result = await db.execute(
        select(
            func.sum(Account.balance).label('total_balance'),
            func.count(Account.id).label('account_count')
        ).where(
            and_(
                Account.user_id == SINGLE_USER_ID,
                Account.is_active == True
            )
        )
    )
    accounts_data = accounts_result.first()
    total_balance = float(accounts_data.total_balance or 0)
    
    # Get transaction totals for period
    # Build date filters
    date_filters = [Transaction.user_id == SINGLE_USER_ID]
    if start is not None:
        date_filters.append(Transaction.transaction_date >= start)
    if end is not None:
        date_filters.append(Transaction.transaction_date <= end)
    
    transactions_result = await db.execute(
        select(
            func.sum(case((Transaction.transaction_type == 'credit', Transaction.amount), else_=0)).label('total_income'),
            func.sum(case((Transaction.transaction_type == 'debit', Transaction.amount), else_=0)).label('total_expenses'),
            func.count(Transaction.id).label('transaction_count')
        ).where(and_(*date_filters))
    )
    transactions_data = transactions_result.first()
    
    total_income = float(transactions_data.total_income or 0)
    total_expenses = float(transactions_data.total_expenses or 0)
    net_income = total_income - total_expenses
    
    # Get top spending categories (apply same date filters)
    category_filters = [Transaction.user_id == SINGLE_USER_ID, Transaction.transaction_type == 'debit']
    if start is not None:
        category_filters.append(Transaction.transaction_date >= start)
    if end is not None:
        category_filters.append(Transaction.transaction_date <= end)
    
    categories_result = await db.execute(
        select(
            Category.name,
            func.sum(Transaction.amount).label('total_amount'),
            func.count(Transaction.id).label('transaction_count')
        ).select_from(Transaction).join(
            Category, Transaction.category_id == Category.id
        ).where(and_(*category_filters))
        .group_by(Category.name).order_by(func.sum(Transaction.amount).desc()).limit(10)
    )
    
    categories = []
    for row in categories_result:
        categories.append({
            "name": row.name,
            "amount": float(row.total_amount),
            "count": row.transaction_count
        })
    
    # Get recent transactions with eager loading
    recent_result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(
            Transaction.user_id == SINGLE_USER_ID
        ).order_by(Transaction.transaction_date.desc()).limit(10)
    )
    
    recent_transactions = []
    for trans in recent_result.scalars():
        recent_transactions.append({
            "id": trans.id,
            "date": trans.transaction_date.isoformat(),
            "description": trans.description,
            "amount": float(trans.amount),
            "type": trans.transaction_type,
            "category": trans.category.name if trans.category else "Uncategorized"
        })
    
    # Calculate quick stats
    transaction_count = int(transactions_data.transaction_count or 0)
    if start is not None and end is not None:
        days_in_period = max((end - start).days, 1)
        average_daily_spending = total_expenses / days_in_period if days_in_period > 0 else 0
    else:
        # For all_time, don't calculate daily average
        average_daily_spending = 0
    
    # Get ACTUAL date range from transaction data in DB (not the period filter dates)
    # This tells us how many months of real data we have
    actual_date_range_result = await db.execute(
        select(
            func.min(Transaction.transaction_date).label('first_transaction'),
            func.max(Transaction.transaction_date).label('last_transaction')
        ).where(and_(*date_filters))
    )
    actual_dates = actual_date_range_result.first()
    
    # Calculate average monthly spending based on ACTUAL data range
    average_monthly_spending = 0.0
    months_of_data = 0.0
    data_start_date = None
    data_end_date = None
    
    if actual_dates.first_transaction and actual_dates.last_transaction:
        data_start_date = actual_dates.first_transaction
        data_end_date = actual_dates.last_transaction
        # Calculate months between first and last transaction
        days_of_data = (data_end_date - data_start_date).days + 1  # +1 to include both endpoints
        months_of_data = days_of_data / 30.44  # Average days per month
        if months_of_data > 0:
            average_monthly_spending = total_expenses / months_of_data
    
    # Get account count
    accounts_result = await db.execute(
        select(func.count(func.distinct(Account.id))).where(
            Account.user_id == SINGLE_USER_ID
        )
    )
    account_count = accounts_result.scalar() or 0
    
    # Calculate savings rate
    savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0
    
    # Build response
    return {
        "data": {
            "summary": {
                "balance": net_income,  # Period savings (income - expenses)
                "total_income": total_income,
                "total_expenses": total_expenses,
                "savings_rate": round(savings_rate, 1),
                "period": period
            },
            "quick_stats": {
                "accounts": account_count,
                "transactions_this_period": transaction_count,
                "average_daily_spending": round(average_daily_spending, 2),
                "average_monthly_spending": round(average_monthly_spending, 2),
                "months_of_data": round(months_of_data, 1),
                "data_start_date": data_start_date.isoformat() if data_start_date else None,
                "data_end_date": data_end_date.isoformat() if data_end_date else None
            },
            "categories": categories,
            "recent_transactions": recent_transactions,
            "period": {
                "start": start.isoformat() if start else None,
                "end": end.isoformat() if end else None,
                "label": period
            }
        }
    }


@router.get("/transactions")
async def get_transactions(
    limit: int = Query(100, ge=1, le=10000, description="Number of transactions to return"),
    skip: int = Query(0, ge=0, description="Number of transactions to skip"),
    period: Optional[str] = Query(None, description="Period for summary stats: this_month, last_month, last_3_months, this_year, all_time, date_range"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Get transactions from database with period summary statistics (Finance Manager compatible API)"""
    
    # Determine date range for summary statistics based on period
    # Using bulletproof month boundary calculation with calendar.monthrange()
    summary_start = None
    summary_end = None
    today = date.today()
    
    if period:
        if period == "this_month":
            # Get exact first and last day of current month
            summary_start, last_day_of_month = get_month_date_range(today.year, today.month)
            summary_end = today  # Up to today within the current month
        elif period == "last_month":
            # Get the previous month
            if today.month == 1:
                # If January, go to December of previous year
                last_month_year = today.year - 1
                last_month = 12
            else:
                last_month_year = today.year
                last_month = today.month - 1
            # Get exact first and last day of last month
            summary_start, summary_end = get_month_date_range(last_month_year, last_month)
        elif period == "last_3_months":
            # Go back 3 months (approximately 90 days, but use exact month boundaries)
            summary_end = today
            # Calculate 3 months ago
            three_months_ago = today.month - 3
            if three_months_ago <= 0:
                summary_start_year = today.year - 1
                summary_start_month = 12 + three_months_ago
            else:
                summary_start_year = today.year
                summary_start_month = three_months_ago
            summary_start, _ = get_month_date_range(summary_start_year, summary_start_month)
        elif period == "this_year":
            # January 1st of current year to today
            summary_start = date(today.year, 1, 1)
            summary_end = today
        elif period == "all_time":
            # No date filtering
            summary_start = None
            summary_end = None
        elif period == "date_range" and start_date and end_date:
            # Custom date range from parameters
            summary_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            summary_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    elif start_date and end_date:
        # Use provided date range if no period specified
        summary_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        summary_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    # Build query for transactions list
    query = select(Transaction).where(
        Transaction.user_id == SINGLE_USER_ID
    )
    
    # Apply date filter to transactions query using the calculated period dates
    # This ensures transaction list matches the period summary
    if summary_start is not None:
        query = query.where(Transaction.transaction_date >= summary_start)
    if summary_end is not None:
        query = query.where(Transaction.transaction_date <= summary_end)
    
    # Apply category filter
    if category and category != "all":
        query = query.join(Category).where(Category.name == category)
    
    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total_count = count_result.scalar() or 0
    
    # Apply limit and offset (Finance Manager approach)
    query = query.order_by(Transaction.transaction_date.desc()).limit(limit).offset(skip)
    
    # Execute query
    result = await db.execute(query.options(selectinload(Transaction.category), selectinload(Transaction.account)))
    
    # Format transactions
    transactions = []
    for trans in result.scalars():
        transactions.append({
            "id": trans.id,
            "transaction_date": trans.transaction_date.isoformat(),
            "description": trans.description,
            "amount": float(trans.amount),
            "transaction_type": trans.transaction_type,
            "category_name": trans.category.name if trans.category else "Uncategorized",
            "account_name": trans.account.name if trans.account else "Unknown",
            "is_processed": trans.is_processed
        })
    
    # Calculate summary statistics for the period
    summary_filters = [Transaction.user_id == SINGLE_USER_ID]
    if summary_start is not None:
        summary_filters.append(Transaction.transaction_date >= summary_start)
    if summary_end is not None:
        summary_filters.append(Transaction.transaction_date <= summary_end)
    
    # Get income, expenses, and transaction count for period
    summary_result = await db.execute(
        select(
            func.sum(case((Transaction.transaction_type == 'credit', Transaction.amount), else_=0)).label('total_income'),
            func.sum(case((Transaction.transaction_type == 'debit', Transaction.amount), else_=0)).label('total_expenses'),
            func.count(Transaction.id).label('transaction_count')
        ).where(and_(*summary_filters))
    )
    summary_data = summary_result.first()
    
    total_income = float(summary_data.total_income or 0)
    total_expenses = float(summary_data.total_expenses or 0)
    balance = total_income - total_expenses
    transaction_count = int(summary_data.transaction_count or 0)
    
    # Format period display name
    def get_period_display(period_type, start, end):
        if period_type == "this_month":
            return datetime.now().strftime("%B %Y")
        elif period_type == "last_month":
            today = datetime.now().date()
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            return last_day_last_month.strftime("%B %Y")
        elif period_type == "last_3_months":
            return "Last 3 Months"
        elif period_type == "this_year":
            return str(datetime.now().year)
        elif period_type == "all_time":
            return "All Time"
        elif period_type == "date_range" and start and end:
            return f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
        return "Custom Period"
    
    period_display = get_period_display(period or "custom", summary_start, summary_end)
    
    return {
        "data": {
            "transactions": transactions,
            "total_count": total_count,
            "returned_count": len(transactions),
            # Add summary statistics for the Transactions page
            "total_transactions": transaction_count,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": balance,
            "period": period_display,
            "period_type": period or "all_time",
            "date_range": {
                "start": summary_start.isoformat() if summary_start else None,
                "end": summary_end.isoformat() if summary_end else None
            }
        }
    }


@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Get all categories with spending totals"""
    
    # Get categories with spending totals
    result = await db.execute(
        select(
            Category.id,
            Category.name,
            Category.category_type,
            func.coalesce(func.sum(Transaction.amount), 0).label('total_spent'),
            func.count(Transaction.id).label('transaction_count')
        ).select_from(Category).outerjoin(
            Transaction, 
            and_(
                Transaction.category_id == Category.id,
                Transaction.user_id == SINGLE_USER_ID
            )
        ).where(
            Category.is_active == True
        ).group_by(Category.id, Category.name, Category.category_type)
        .order_by(Category.name)
    )
    
    categories = []
    for row in result:
        categories.append({
            "id": row.id,
            "name": row.name,
            "type": row.category_type,
            "total_spent": float(row.total_spent),
            "transaction_count": row.transaction_count
        })
    
    return {
        "data": categories
    }


@router.get("/accounts")
async def get_accounts(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Get all accounts with balances"""
    
    result = await db.execute(
        select(Account).where(
            and_(
                Account.user_id == SINGLE_USER_ID,
                Account.is_active == True
            )
        ).order_by(Account.name)
    )
    
    accounts = []
    for acc in result.scalars():
        # Calculate actual balance from transactions
        trans_result = await db.execute(
            select(
                func.sum(case(
                    (Transaction.transaction_type == 'credit', Transaction.amount),
                    else_=-Transaction.amount
                )).label('calculated_balance')
            ).where(
                and_(
                    Transaction.account_id == acc.id,
                    Transaction.user_id == SINGLE_USER_ID
                )
            )
        )
        calculated = trans_result.scalar() or 0
        
        accounts.append({
            "id": acc.id,
            "name": acc.name,
            "account_type": acc.account_type,
            "balance": float(acc.balance),
            "calculated_balance": float(calculated),
            "bank_name": acc.bank_name,
            "account_number": acc.account_number[-4:] if acc.account_number else None
        })
    
    return {
        "data": accounts
    }


@router.get("/cumulative-spending")
async def get_cumulative_spending(
    period: str = Query("this_year"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Get cumulative spending data over time by category (Finance Manager compatible format)
    Returns daily cumulative spending for each category over the selected period
    """
    # Determine date range using bulletproof month logic
    today = date.today()
    
    if period == "this_month":
        start, last_day_of_month = get_month_date_range(today.year, today.month)
        end = today
    elif period == "last_month":
        if today.month == 1:
            last_month_year = today.year - 1
            last_month = 12
        else:
            last_month_year = today.year
            last_month = today.month - 1
        start, end = get_month_date_range(last_month_year, last_month)
    elif period == "last_3_months":
        end = today
        three_months_ago = today.month - 3
        if three_months_ago <= 0:
            start_year = today.year - 1
            start_month = 12 + three_months_ago
        else:
            start_year = today.year
            start_month = three_months_ago
        start, _ = get_month_date_range(start_year, start_month)
    elif period == "this_year":
        start = date(today.year, 1, 1)
        end = today
    elif period == "last_year":
        start = date(today.year-1, 1, 1)
        end = date(today.year-1, 12, 31)
    elif period == "all_time":
        start = None
        end = None
    elif period == "date_range" and start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        start = date(today.year, 1, 1)
        end = today
    
    # Build base query filters
    base_filters = [Transaction.user_id == SINGLE_USER_ID]
    if start is not None:
        base_filters.append(Transaction.transaction_date >= start)
    if end is not None:
        base_filters.append(Transaction.transaction_date <= end)
    
    # Get all transactions for the period with categories
    transactions_query = (
        select(Transaction, Category.name.label('category_name'))
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(*base_filters)
        .order_by(Transaction.transaction_date.asc())
    )
    
    result = await db.execute(transactions_query)
    transactions = result.all()
    
    # Group transactions by date and category
    daily_data = {}
    categories = set()
    
    for transaction, category_name in transactions:
        date_str = transaction.transaction_date.isoformat()
        category = category_name or "Uncategorized"
        categories.add(category)
        
        if date_str not in daily_data:
            daily_data[date_str] = {}
        
        if category not in daily_data[date_str]:
            daily_data[date_str][category] = 0
        
        # For expenses (debit), use negative amount; for income (credit), use positive
        amount = float(transaction.amount) if transaction.transaction_type == 'credit' else -float(transaction.amount)
        daily_data[date_str][category] += amount
    
    # Sort dates
    sorted_dates = sorted(daily_data.keys())
    
    # Calculate cumulative totals
    cumulative_data = []
    running_totals = {cat: 0 for cat in categories}
    
    # Add special categories for aggregated data
    categories.add("Income")
    categories.add("Expenses") 
    categories.add("Savings")
    running_totals["Income"] = 0
    running_totals["Expenses"] = 0
    running_totals["Savings"] = 0
    
    for date_str in sorted_dates:
        day_data = daily_data[date_str]
        
        # Update running totals for each category
        daily_income = 0
        daily_expenses = 0
        
        for category, amount in day_data.items():
            running_totals[category] += amount
            
            if amount > 0:
                daily_income += amount
            else:
                daily_expenses += abs(amount)
        
        # Update aggregated totals
        running_totals["Income"] += daily_income
        running_totals["Expenses"] += daily_expenses
        running_totals["Savings"] = running_totals["Income"] - running_totals["Expenses"]
        
        cumulative_data.append({
            "date": date_str,
            "categories": dict(day_data),
            "cumulative": dict(running_totals)
        })
    
    return {
        "data": {
            "chart_data": cumulative_data,
            "categories": sorted(list(categories)),
            "period": period,
            "date_range": {
                "start": start.isoformat() if start else None,
                "end": end.isoformat() if end else None
            }
        }
    }


@router.get("/budget/category-analysis")
async def get_budget_category_analysis(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Get budget analysis data comparing current year vs previous year spending by category.
    
    Returns spending data for each category with:
    - This year total and monthly average
    - Last year total and monthly average  
    - Average monthly change between years
    """
    try:
        # Get current year and previous year dynamically
        current_year = datetime.now().year
        previous_year = current_year - 1
        
        # Find the actual date range of transactions in the current year
        # This gives us the precise months of data, not just the month number
        date_range_query = select(
            func.min(Transaction.transaction_date).label('first_transaction'),
            func.max(Transaction.transaction_date).label('last_transaction')
        ).filter(
            and_(
                Transaction.user_id == SINGLE_USER_ID,
                extract('year', Transaction.transaction_date) == current_year
            )
        )
        
        date_range_result = await db.execute(date_range_query)
        date_range = date_range_result.first()
        
        # Calculate actual fractional months of data based on date range
        # This matches the Dashboard calculation: (last_date - first_date).days / 30.44
        if date_range.first_transaction and date_range.last_transaction:
            days_of_data = (date_range.last_transaction - date_range.first_transaction).days + 1
            current_year_months = days_of_data / 30.44  # Average days per month
            latest_transaction_date = date_range.last_transaction
        else:
            current_year_months = 1.0  # Default to 1 if no data found
            latest_transaction_date = None
        
        # Get all categories that have transactions
        categories_query = select(Category.id, Category.name).join(
            Transaction, Category.id == Transaction.category_id
        ).filter(
            Transaction.user_id == SINGLE_USER_ID
        ).distinct()
        
        result = await db.execute(categories_query)
        categories_with_spending = result.all()
        
        budget_analysis = []
        
        for category_id, category_name in categories_with_spending:
            # Get current year data (only debit/expense transactions)
            current_year_query = select(
                func.sum(func.abs(Transaction.amount))
            ).filter(
                and_(
                    Transaction.user_id == SINGLE_USER_ID,
                    Transaction.category_id == category_id,
                    extract('year', Transaction.transaction_date) == current_year,
                    Transaction.transaction_type == 'debit'  # Only expenses
                )
            )
            
            current_year_result = await db.execute(current_year_query)
            current_year_total = float(current_year_result.scalar() or 0)
            
            # Get previous year data (only debit/expense transactions)
            previous_year_query = select(
                func.sum(func.abs(Transaction.amount))
            ).filter(
                and_(
                    Transaction.user_id == SINGLE_USER_ID,
                    Transaction.category_id == category_id,
                    extract('year', Transaction.transaction_date) == previous_year,
                    Transaction.transaction_type == 'debit'  # Only expenses
                )
            )
            
            previous_year_result = await db.execute(previous_year_query)
            previous_year_total = float(previous_year_result.scalar() or 0)
            
            # Calculate monthly averages
            # Current year: divide by actual months of data available
            current_year_monthly_avg = current_year_total / current_year_months if current_year_months > 0 else 0
            # Previous year: always divide by 12 (full year)
            previous_year_monthly_avg = previous_year_total / 12
            
            # Calculate average monthly change
            avg_monthly_change = current_year_monthly_avg - previous_year_monthly_avg
            
            # Only include categories with spending in either year
            if current_year_total > 0 or previous_year_total > 0:
                budget_analysis.append({
                    "category": category_name,
                    "thisYearTotal": float(current_year_total),
                    "thisYearMonthlyAvg": float(current_year_monthly_avg),
                    "lastYearTotal": float(previous_year_total),
                    "lastYearMonthlyAvg": float(previous_year_monthly_avg),
                    "avgMonthlyChange": float(avg_monthly_change)
                })
        
        # Sort by current year total (descending)
        budget_analysis.sort(key=lambda x: x["thisYearTotal"], reverse=True)
        
        return {
            "success": True,
            "data": budget_analysis,
            "message": f"Budget analysis data retrieved successfully for {current_year} vs {previous_year}",
            "metadata": {
                "current_year": current_year,
                "previous_year": previous_year,
                "current_year_months": round(current_year_months, 1),  # Fractional months (e.g., 9.5)
                "latest_transaction_date": latest_transaction_date.isoformat() if latest_transaction_date else None,
                "total_categories": len(budget_analysis)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve budget analysis: {str(e)}"
        )
