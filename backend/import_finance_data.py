#!/usr/bin/env python3
"""
Import Finance Manager data into Capricorn database
Run inside Docker container: docker exec capricorn-backend python import_finance_data.py
"""
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models import UserProfile, Category, Account, Transaction

def load_export_file():
    """Load Finance Manager export file"""
    print("📂 Loading export file...")
    with open('/app/finance_export.json', 'r') as f:
        data = json.load(f)
    
    stats = data['statistics']
    print(f"   Users: {stats['total_users']}")
    print(f"   Accounts: {stats['total_accounts']}")
    print(f"   Categories: {stats['total_categories']}")
    print(f"   Transactions: {stats['total_transactions']}")
    
    return data['data']

def import_users(db: Session, users_data):
    """Import users from Finance Manager"""
    print("\n👤 Importing users...")
    uuid_map = {}
    
    for user in users_data:
        new_user = UserProfile(
            email=user['email'],
            first_name=user['first_name'],
            last_name=user['last_name']
        )
        db.add(new_user)
        db.flush()  # Get the ID
        uuid_map[user['id']] = new_user.id
        print(f"   ✅ {user['email']} → ID {new_user.id}")
    
    return uuid_map

def import_categories(db: Session, categories_data):
    """Import categories with hierarchy"""
    print("\n📁 Importing categories...")
    uuid_map = {}
    
    # Sort categories: parents first (parent_id = null)
    parents = [c for c in categories_data if c['parent_id'] is None]
    children = [c for c in categories_data if c['parent_id'] is not None]
    
    # Import parents first
    print(f"   Importing {len(parents)} parent categories...")
    for cat in parents:
        new_cat = Category(
            name=cat['name'],
            description=cat.get('description'),
            category_type=cat['category_type'],
            parent_id=None,
            is_active=cat['is_active']
        )
        db.add(new_cat)
        db.flush()
        uuid_map[cat['id']] = new_cat.id
        print(f"   ✅ {cat['name']} ({cat['category_type']}) → ID {new_cat.id}")
    
    # Then import children
    print(f"\n   Importing {len(children)} child categories...")
    for cat in children:
        parent_new_id = uuid_map.get(cat['parent_id'])
        new_cat = Category(
            name=cat['name'],
            description=cat.get('description'),
            category_type=cat['category_type'],
            parent_id=parent_new_id,
            is_active=cat['is_active']
        )
        db.add(new_cat)
        db.flush()
        uuid_map[cat['id']] = new_cat.id
        if parent_new_id:
            print(f"   ✅ {cat['name']} (parent: {parent_new_id}) → ID {new_cat.id}")
    
    return uuid_map

def import_accounts(db: Session, accounts_data, user_map):
    """Import accounts"""
    print("\n💳 Importing accounts...")
    uuid_map = {}
    
    # Get the single user ID (demo app has only one user)
    user_new_id = list(user_map.values())[0]
    
    for acc in accounts_data:
        new_acc = Account(
            user_id=user_new_id,
            name=acc['name'],
            account_type=acc['account_type'],
            account_number=acc.get('account_number'),
            bank_name=acc.get('bank_name'),
            balance=acc['balance'],
            credit_limit=acc.get('credit_limit'),
            is_active=acc['is_active']
        )
        db.add(new_acc)
        db.flush()
        uuid_map[acc['id']] = new_acc.id
        print(f"   ✅ {acc['name']} ({acc['account_type']}) → ID {new_acc.id}")
    
    return uuid_map

def import_transactions(db: Session, transactions_data, user_map, account_map, category_map):
    """Import transactions in batches"""
    print("\n💰 Importing transactions...")
    total = len(transactions_data)
    batch_size = 500
    imported = 0
    
    # Get the single user ID
    user_new_id = list(user_map.values())[0]
    
    # Create category name → ID lookup (for denormalized data)
    category_name_map = {}
    for cat in db.query(Category).all():
        category_name_map[cat.name.lower()] = cat.id
    
    # Create account name → ID lookup (for denormalized data)
    account_name_map = {}
    for acc in db.query(Account).all():
        account_name_map[acc.name.lower()] = acc.id
    
    for i in range(0, total, batch_size):
        batch = transactions_data[i:i + batch_size]
        
        for txn in batch:
            
            # Look up account by name (from denormalized data)
            account_new_id = None
            if txn.get('account_name'):
                account_new_id = account_name_map.get(txn['account_name'].lower())
            
            # Look up category by name (from denormalized data)
            category_id = None
            if txn.get('category_name'):
                category_id = category_name_map.get(txn['category_name'].lower())
            
            new_txn = Transaction(
                user_id=user_new_id,
                account_id=account_new_id,
                category_id=category_id,
                description=txn['description'],
                amount=txn['amount'],
                transaction_date=datetime.strptime(txn['transaction_date'], '%Y-%m-%d').date(),
                transaction_type=txn['transaction_type'],
                is_processed=txn['is_processed']
            )
            db.add(new_txn)
        
        db.flush()
        imported += len(batch)
        progress = (imported / total) * 100
        print(f"   Progress: {imported}/{total} ({progress:.1f}%)")
    
    return imported

def main():
    print("🚀 Starting Finance Manager data import...\n")
    
    try:
        # Load export file
        data = load_export_file()
        
        # Create database session
        db = SessionLocal()
        
        # Import in order (respecting foreign keys)
        user_map = import_users(db, data['users'])
        category_map = import_categories(db, data['categories'])
        account_map = import_accounts(db, data['accounts'], user_map)
        txn_count = import_transactions(db, data['transactions'], user_map, account_map, category_map)
        
        # Commit all changes
        print("\n💾 Committing to database...")
        db.commit()
        
        print("\n✅ Import complete!")
        print(f"\n📊 Summary:")
        print(f"   Users: {len(user_map)}")
        print(f"   Categories: {len(category_map)}")
        print(f"   Accounts: {len(account_map)}")
        print(f"   Transactions: {txn_count}")
        
        db.close()
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
            db.close()

if __name__ == "__main__":
    main()

