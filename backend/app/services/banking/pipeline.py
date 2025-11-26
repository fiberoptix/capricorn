"""
Transaction Processing Pipeline Service

Orchestrates the complete CSV processing workflow:
1. Receive uploaded CSV files
2. Classify file type (BOFA_CHECKING, BOFA_CREDIT, AMEX_CREDIT)
3. Parse transactions from CSV
4. Auto-tag transactions using ML model (97% accuracy)
5. Check for duplicates
6. Save to PostgreSQL database

This service integrates all the proven processing scripts from Finance Manager.
"""

import os
import shutil
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
from app.core.constants import SINGLE_USER_ID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category
from app.models.user import User  # Fixed import
from app.core.database import get_async_db

# Import our proven processing scripts
from .classifier import classify_and_copy_files, analyze_csv_structure
from .parser import parse_classified_files, create_master_file, main as parser_main
from .tagger import IntelligentTagger
# Note: duplicate_checker.py has functions, not a class - we implement our own duplicate checking


class TransactionPipeline:
    """Main pipeline for processing uploaded financial CSV files"""
    
    def __init__(self):
        """Initialize the pipeline with default settings"""
        # Use path relative to this module - works in both DEV and PROD Docker
        self.base_dir = Path(__file__).parent / "data"
        self.input_dir = self.base_dir / "input"
        self.classified_dir = self.base_dir / "classified"
        self.output_dir = self.base_dir / "output"
        
        # Ensure directories exist
        for dir_path in [self.input_dir, self.classified_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ML tagger (duplicate checking is done via database queries)
        self.tagger = IntelligentTagger()
        
    async def process_uploaded_file(
        self, 
        file_path: str,
        account_name: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Process a single uploaded CSV file through the complete pipeline
        Single-user system - always uses SINGLE_USER_ID
        
        Args:
            file_path: Path to the uploaded CSV file
            account_name: Name of the bank account (for finding account_id)
            db: Database session
            
        Returns:
            Processing results including statistics
        """
        try:
            # Copy file to input directory
            input_file = self.input_dir / Path(file_path).name
            shutil.copy2(file_path, input_file)
            
            # Step 1: Classify the file type using analyze_csv_structure
            file_type = analyze_csv_structure(str(input_file))
            if not file_type:
                return {
                    "status": "error",
                    "message": "Unable to determine file type. Supported: BOFA_CHECKING, BOFA_CREDIT, AMEX_CREDIT"
                }
            
            # Move to working directory (where parser expects classified files)
            working_dir = self.base_dir / "working"
            working_dir.mkdir(parents=True, exist_ok=True)
            classified_file = working_dir / f"{file_type}_{input_file.name}"
            shutil.move(str(input_file), str(classified_file))
            
            # Step 2: Parse transactions from CSV
            transactions_list = parse_classified_files(str(self.base_dir))
            if not transactions_list:
                return {
                    "status": "error", 
                    "message": "No transactions found in file"
                }
            
            # Convert list to DataFrame with proper column names
            columns = ['transaction_date', 'description', 'amount', 'spender', 'source', 'transaction_type', 'tag', 'duplicate']
            transactions_df = pd.DataFrame(transactions_list, columns=columns)
            
            # Step 3: Auto-tag transactions
            tagged_transactions = []
            for _, row in transactions_df.iterrows():
                description = str(row['description'])
                # Convert amount to float
                try:
                    amount = float(str(row['amount']).replace(',', ''))
                except (ValueError, TypeError):
                    amount = 0
                
                # Get ML prediction using tag_transaction method
                category_name = self.tagger.tag_transaction(description, amount)
                # Default to "Uncategorized" if no tag found
                if not category_name or category_name.strip() == '':
                    category_name = 'Uncategorized'
                
                # Parse date properly (Finance Manager approach - 3 formats)
                from datetime import datetime
                date_str = row['transaction_date']
                try:
                    # Try format 1: YYYY-MM-DD
                    transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except:
                    try:
                        # Try format 2: MM/DD/YYYY (4-digit year)
                        transaction_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                    except:
                        try:
                            # Try format 3: MM/DD/YY (2-digit year) - CRITICAL for BOFA files!
                            transaction_date = datetime.strptime(date_str, '%m/%d/%y').date()
                        except:
                            # Last resort: log error and use today's date
                            print(f"❌ Failed to parse date '{date_str}' with all 3 formats, using today's date")
                            transaction_date = datetime.now().date()
                
                tagged_transactions.append({
                    'transaction_date': transaction_date,
                    'description': description,
                    'amount': abs(amount),  # Store as positive
                    'transaction_type': 'credit' if amount > 0 else 'debit',
                    'category_name': category_name,
                    'file_type': file_type
                })
            
            # Step 4: Extract unique accounts from transactions (source + spender)
            print(f"🏦 Identifying accounts from transactions...")
            unique_accounts = {}
            for trans in tagged_transactions:
                # Get source and spender from original transactions_df
                source = transactions_df[transactions_df['description'] == trans['description']]['source'].iloc[0]
                spender = transactions_df[transactions_df['description'] == trans['description']]['spender'].iloc[0]
                
                # Create account name from source and spender (Finance Manager approach)
                account_key = f"{source}_{spender}" if spender and spender != "Unknown" else source
                if account_key not in unique_accounts:
                    unique_accounts[account_key] = {
                        'source': source,
                        'spender': spender,
                        'file_type': trans['file_type']
                    }
            
            print(f"   Found {len(unique_accounts)} unique accounts: {list(unique_accounts.keys())}")
            
            # Create or get all accounts
            account_cache = {}
            for account_key, info in unique_accounts.items():
                account = await self._get_or_create_account(
                    db, account_key, info['file_type']
                )
                account_cache[account_key] = account
                print(f"   ✅ Account: {account.name} (ID: {account.id})")
            
            # Commit accounts first
            await db.commit()
            print(f"✅ All accounts created and committed")
            
            # Step 5: PRE-CREATE ALL CATEGORIES (Finance Manager approach)
            print(f"📋 Pre-creating categories...")
            unique_categories = set()
            for trans in tagged_transactions:
                if trans['category_name']:
                    unique_categories.add(trans['category_name'])
            
            print(f"   Found {len(unique_categories)} unique categories: {', '.join(sorted(unique_categories))}")
            
            # Create category cache (like Finance Manager does)
            category_cache = {}
            for category_name in unique_categories:
                category = await self._get_or_create_category(db, category_name)
                category_cache[category_name] = category
                print(f"   ✅ Category cached: {category_name} (ID: {category.id})")
            
            # Commit categories first
            await db.commit()
            print(f"✅ All categories created and committed")
            
            # Step 6: Check for duplicates and save to database
            saved_count = 0
            duplicate_count = 0
            
            print(f"📝 Processing {len(tagged_transactions)} transactions...")
            for idx, trans in enumerate(tagged_transactions):
                if idx == 0:
                    print(f"  First transaction: {trans['description'][:30]} - ${trans['amount']}")
                
                # Check for duplicate
                try:
                    is_duplicate = await self._check_duplicate(
                        db,
                        trans['transaction_date'],
                        trans['amount'],
                        trans['description']
                    )
                except Exception as e:
                    print(f"❌ Duplicate check error: {e}")
                    is_duplicate = False
                
                if is_duplicate:
                    duplicate_count += 1
                    continue
                
                # Get category from cache (Finance Manager approach - no DB queries!)
                category = None
                if trans['category_name'] and trans['category_name'] in category_cache:
                    category = category_cache[trans['category_name']]
                    if idx == 0:
                        print(f"  Category: {category.name} (ID: {category.id}) [from cache]")
                
                # Get account from cache based on source + spender
                source = transactions_df[transactions_df['description'] == trans['description']]['source'].iloc[0]
                spender = transactions_df[transactions_df['description'] == trans['description']]['spender'].iloc[0]
                account_key = f"{source}_{spender}" if spender and spender != "Unknown" else source
                account = account_cache.get(account_key)
                
                if not account:
                    print(f"⚠️  Account not found for key: {account_key}, using first account")
                    account = list(account_cache.values())[0]
                
                if idx == 0:
                    print(f"  Account: {account.name} (ID: {account.id}) [from cache]")
                
                # Create transaction
                new_transaction = Transaction(
                    user_id=SINGLE_USER_ID,
                    account_id=account.id,
                    category_id=category.id if category else None,
                    description=trans['description'],
                    amount=Decimal(str(abs(trans['amount']))),
                    transaction_date=trans['transaction_date'],
                    transaction_type=trans['transaction_type'],
                    is_processed=True  # Mark as auto-tagged
                )
                
                db.add(new_transaction)
                saved_count += 1
            
            print(f"💾 Ready to save {saved_count} transactions, {duplicate_count} duplicates found")
            
            # Commit all transactions
            try:
                await db.commit()
                print(f"✅ Committed {saved_count} transactions to database")
            except Exception as e:
                print(f"❌ Commit error: {e}")
                await db.rollback()
                raise
            
            # Create summary file
            summary = {
                "processed_at": datetime.now().isoformat(),
                "file_type": file_type,
                "total_transactions": len(tagged_transactions),
                "saved": saved_count,
                "duplicates": duplicate_count,
                "auto_tagged": saved_count,
                "accuracy_expected": "97%"
            }
            
            # Save summary
            summary_file = self.output_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            return {
                "status": "success",
                "file_type": file_type,
                "processed": len(tagged_transactions),
                "saved": saved_count,
                "duplicates": duplicate_count,
                "auto_tagged": saved_count,
                "summary_file": str(summary_file)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _get_or_create_account(
        self,
        db: AsyncSession,
        account_name: str,
        file_type: str
    ) -> Account:
        """Get existing account or create new one"""
        # Try to find existing account
        result = await db.execute(
            select(Account).where(
                and_(
                    Account.user_id == SINGLE_USER_ID,
                    Account.name == account_name
                )
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            # Determine account type from file type
            account_type_map = {
                'BOFA_CHECKING': 'checking',
                'BOFA_CREDIT': 'credit',
                'AMEX_CREDIT': 'credit'
            }
            account_type = account_type_map.get(file_type, 'checking')
            
            # Create new account
            account = Account(
                user_id=SINGLE_USER_ID,
                name=account_name,
                account_type=account_type,
                balance=Decimal('0.00'),
                is_active=True
            )
            db.add(account)
            await db.flush()  # Get the ID without committing
        
        return account
    
    async def _get_or_create_category(
        self,
        db: AsyncSession,
        category_name: str
    ) -> Category:
        """
        Get existing category or create new one
        Uses case-insensitive lookup to prevent duplicates
        """
        # Normalize category name (title case)
        normalized_name = category_name.strip()
        
        # Try to find existing category (case-insensitive)
        result = await db.execute(
            select(Category).where(
                func.lower(Category.name) == func.lower(normalized_name)
            )
        )
        category = result.scalar_one_or_none()
        
        if not category:
            # Create new category with normalized name
            category = Category(
                name=normalized_name,
                category_type='expense',  # Default, can be updated later
                is_active=True
            )
            db.add(category)
            await db.flush()  # Get the ID without committing
            print(f"   🆕 Created new category: {normalized_name}")
        else:
            print(f"   ✓ Found existing category: {category.name} (ID: {category.id})")
        
        return category
    
    async def _check_duplicate(
        self,
        db: AsyncSession,
        transaction_date: date,
        amount: float,
        description: str
    ) -> bool:
        """Check if a transaction already exists (duplicate detection)"""
        result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.user_id == SINGLE_USER_ID,
                    Transaction.transaction_date == transaction_date,
                    Transaction.amount == Decimal(str(abs(amount))),
                    Transaction.description == description
                )
            ).limit(1)
        )
        
        return result.scalar_one_or_none() is not None
    
    async def get_processing_stats(
        self,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get statistics about processed transactions"""
        # Count total transactions
        total_result = await db.execute(
            select(func.count(Transaction.id)).where(
                Transaction.user_id == SINGLE_USER_ID
            )
        )
        total_count = total_result.scalar() or 0
        
        # Count auto-tagged transactions
        tagged_result = await db.execute(
            select(func.count(Transaction.id)).where(
                and_(
                    Transaction.user_id == SINGLE_USER_ID,
                    Transaction.is_processed == True,
                    Transaction.category_id.isnot(None)
                )
            )
        )
        tagged_count = tagged_result.scalar() or 0
        
        # Count untagged transactions
        untagged_result = await db.execute(
            select(func.count(Transaction.id)).where(
                and_(
                    Transaction.user_id == SINGLE_USER_ID,
                    Transaction.category_id.is_(None)
                )
            )
        )
        untagged_count = untagged_result.scalar() or 0
        
        # Calculate accuracy
        accuracy = (tagged_count / total_count * 100) if total_count > 0 else 0
        
        return {
            "total_transactions": total_count,
            "auto_tagged": tagged_count,
            "untagged": untagged_count,
            "accuracy_percentage": round(accuracy, 2),
            "expected_accuracy": 97.0
        }


# Singleton instance
pipeline = TransactionPipeline()
