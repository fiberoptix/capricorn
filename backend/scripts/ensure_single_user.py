#!/usr/bin/env python3
"""
Ensure Single User Setup

This script ensures the database is configured for single-user operation:
1. Creates the single user if it doesn't exist
2. Migrates all existing data to user_id=1
3. Removes any other users
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import async_engine
from app.core.constants import SINGLE_USER_ID, SINGLE_USER_EMAIL, SINGLE_USER_NAME

async def ensure_single_user():
    """Ensure database is configured for single-user operation"""
    
    async with async_engine.begin() as conn:
        print("🔧 Ensuring single-user database setup...")
        
        # Step 1: Check if single user exists
        result = await conn.execute(
            text("SELECT id FROM user_profile WHERE id = :user_id"),
            {"user_id": SINGLE_USER_ID}
        )
        user_exists = result.fetchone() is not None
        
        if not user_exists:
            print(f"✅ Creating single user (ID={SINGLE_USER_ID})...")
            await conn.execute(
                text("""
                    INSERT INTO user_profile (id, email, first_name, last_name, created_at, updated_at)
                    VALUES (:id, :email, :first_name, :last_name, NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": SINGLE_USER_ID,
                    "email": SINGLE_USER_EMAIL,
                    "first_name": SINGLE_USER_NAME.split()[0],
                    "last_name": SINGLE_USER_NAME.split()[-1] if len(SINGLE_USER_NAME.split()) > 1 else ""
                }
            )
        else:
            print(f"✓ Single user already exists (ID={SINGLE_USER_ID})")
        
        # Step 2: Migrate all data to single user
        tables_with_user_id = [
            'transactions',
            'accounts',
            'budgets',
            'portfolios',
            'holdings',
            'portfolio_transactions',
            'retirement_accounts',
            'retirement_projections'
        ]
        
        for table in tables_with_user_id:
            # Check if table exists
            result = await conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = :table_name
                    )
                """),
                {"table_name": table}
            )
            
            if result.scalar():
                # Check if column exists
                result = await conn.execute(
                    text("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name = :table_name AND column_name = 'user_id'
                        )
                    """),
                    {"table_name": table}
                )
                
                if result.scalar():
                    # Migrate data
                    result = await conn.execute(
                        text(f"UPDATE {table} SET user_id = :new_id WHERE user_id != :new_id"),
                        {"new_id": SINGLE_USER_ID}
                    )
                    if result.rowcount > 0:
                        print(f"  📦 Migrated {result.rowcount} records in {table}")
        
        # Step 3: Remove other users (but keep the single user)
        result = await conn.execute(
            text("DELETE FROM user_profile WHERE id != :user_id"),
            {"user_id": SINGLE_USER_ID}
        )
        if result.rowcount > 0:
            print(f"🗑️ Removed {result.rowcount} other user(s)")
        
        print("✅ Database configured for single-user operation!")
        print(f"   User ID: {SINGLE_USER_ID}")
        print(f"   Email: {SINGLE_USER_EMAIL}")

if __name__ == "__main__":
    asyncio.run(ensure_single_user())
