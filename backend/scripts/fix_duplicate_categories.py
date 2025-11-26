"""
Fix Duplicate Categories Script

This script:
1. Finds duplicate category names in the database
2. Consolidates them into single categories
3. Updates all transactions to point to the consolidated categories
4. Deletes the duplicate categories
5. Re-tags transactions that have NULL category_id
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, delete, and_
from app.core.config import settings
from app.models.category import Category
from app.models.transaction import Transaction
from app.core.constants import SINGLE_USER_ID
from app.services.banking.tagger import IntelligentTagger


async def fix_duplicate_categories():
    """Main function to fix duplicate categories"""
    print("=" * 70)
    print("🔧 FIXING DUPLICATE CATEGORIES")
    print("=" * 70)
    
    # Create engine and session
    database_url = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Step 1: Find all duplicate category names
            print("\n📊 Step 1: Finding duplicate categories...")
            
            # Get all categories grouped by lowercase name
            result = await db.execute(
                select(
                    func.lower(Category.name).label('lower_name'),
                    func.count(Category.id).label('count'),
                    func.array_agg(Category.id).label('ids'),
                    func.array_agg(Category.name).label('names')
                ).group_by(func.lower(Category.name)).having(func.count(Category.id) > 1)
            )
            
            duplicates = result.all()
            
            if not duplicates:
                print("✅ No duplicate categories found!")
            else:
                print(f"⚠️  Found {len(duplicates)} sets of duplicate categories:")
                
                for dup in duplicates:
                    print(f"\n   Category: '{dup.lower_name}'")
                    print(f"   - {dup.count} duplicates with IDs: {dup.ids}")
                    print(f"   - Names: {dup.names}")
                    
                    # Step 2: Consolidate duplicates
                    # Keep the first one, migrate transactions from others
                    primary_id = dup.ids[0]
                    duplicate_ids = dup.ids[1:]
                    
                    print(f"   - Keeping category ID {primary_id} as primary")
                    print(f"   - Migrating transactions from IDs: {duplicate_ids}")
                    
                    # Update all transactions pointing to duplicate categories
                    for dup_id in duplicate_ids:
                        # Count transactions to migrate
                        count_result = await db.execute(
                            select(func.count(Transaction.id)).where(
                                Transaction.category_id == dup_id
                            )
                        )
                        trans_count = count_result.scalar()
                        
                        if trans_count > 0:
                            # Update transactions to point to primary category
                            await db.execute(
                                Transaction.__table__.update().where(
                                    Transaction.category_id == dup_id
                                ).values(category_id=primary_id)
                            )
                            print(f"   - Migrated {trans_count} transactions from ID {dup_id} to {primary_id}")
                        
                        # Delete the duplicate category
                        await db.execute(
                            delete(Category).where(Category.id == dup_id)
                        )
                        print(f"   - Deleted duplicate category ID {dup_id}")
                
                # Commit all changes
                await db.commit()
                print("\n✅ All duplicate categories consolidated and deleted")
            
            # Step 3: Re-tag transactions with NULL category_id
            print("\n📊 Step 2: Re-tagging transactions with NULL category_id...")
            
            # Get count of transactions with NULL category
            result = await db.execute(
                select(func.count(Transaction.id)).where(
                    and_(
                        Transaction.user_id == SINGLE_USER_ID,
                        Transaction.category_id.is_(None)
                    )
                )
            )
            null_count = result.scalar()
            
            if null_count == 0:
                print("✅ All transactions have categories!")
            else:
                print(f"⚠️  Found {null_count} transactions without categories")
                print("🏷️  Re-tagging with ML model...")
                
                # Initialize tagger
                tagger = IntelligentTagger()
                
                # Get transactions without categories
                result = await db.execute(
                    select(Transaction).where(
                        and_(
                            Transaction.user_id == SINGLE_USER_ID,
                            Transaction.category_id.is_(None)
                        )
                    )
                )
                transactions = result.scalars().all()
                
                tagged_count = 0
                for trans in transactions:
                    # Get ML prediction
                    category_name = tagger.tag_transaction(
                        trans.description,
                        float(trans.amount)
                    )
                    
                    # Default to Uncategorized if no match
                    if not category_name or not category_name.strip():
                        category_name = 'Uncategorized'
                    
                    # Find or create category (case-insensitive)
                    cat_result = await db.execute(
                        select(Category).where(
                            func.lower(Category.name) == func.lower(category_name.strip())
                        )
                    )
                    category = cat_result.scalar_one_or_none()
                    
                    if not category:
                        # Create category
                        category = Category(
                            name=category_name.strip(),
                            category_type='expense',
                            is_active=True
                        )
                        db.add(category)
                        await db.flush()
                    
                    # Update transaction
                    trans.category_id = category.id
                    tagged_count += 1
                    
                    if tagged_count % 50 == 0:
                        print(f"   - Tagged {tagged_count}/{null_count} transactions...")
                        await db.commit()
                
                # Final commit
                await db.commit()
                print(f"✅ Re-tagged {tagged_count} transactions")
            
            # Step 4: Show final statistics
            print("\n" + "=" * 70)
            print("📊 FINAL STATISTICS")
            print("=" * 70)
            
            # Count unique categories
            result = await db.execute(
                select(func.count(Category.id)).where(Category.is_active == True)
            )
            category_count = result.scalar()
            
            # Count transactions by category status
            result = await db.execute(
                select(
                    func.count(Transaction.id).filter(Transaction.category_id.is_not(None)).label('tagged'),
                    func.count(Transaction.id).filter(Transaction.category_id.is_(None)).label('untagged'),
                    func.count(Transaction.id).label('total')
                ).where(Transaction.user_id == SINGLE_USER_ID)
            )
            stats = result.first()
            
            print(f"\n✅ Categories: {category_count} unique categories")
            print(f"✅ Transactions: {stats.tagged} tagged, {stats.untagged} untagged, {stats.total} total")
            
            if stats.untagged == 0:
                print("\n🎉 SUCCESS! All transactions are properly categorized!")
            else:
                print(f"\n⚠️  Still have {stats.untagged} untagged transactions")
            
            print("\n" + "=" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()


if __name__ == "__main__":
    print("\n🚀 Starting category fix script...")
    asyncio.run(fix_duplicate_categories())
    print("\n✅ Script complete!\n")

