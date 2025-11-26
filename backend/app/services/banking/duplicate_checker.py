#!/usr/bin/env python3
"""
Transaction Duplicate Check Script
Compares processed transactions with existing database records to identify duplicates
"""

import csv
import psycopg2
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'finance_manager',
    'user': 'finance_user',
    'password': 'secure_password',
    'port': 5432
}

def connect_to_database():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def get_existing_transactions():
    """Get all existing transactions from the database"""
    conn = connect_to_database()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        # Get all transactions with basic info
        query = """
        SELECT 
            t.transaction_date,
            t.description,
            t.amount,
            t.transaction_type,
            a.name as account_name,
            c.name as category_name
        FROM transactions t
        LEFT JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = '00000000-0000-0000-0000-000000000001'
        ORDER BY t.transaction_date DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        transactions = []
        for row in rows:
            transactions.append({
                'date': row[0].strftime('%m/%d/%Y'),
                'description': row[1],
                'amount': float(row[2]),  # Database stores as positive
                'type': row[3],
                'account': row[4] or 'Unknown',
                'category': row[5] or 'Uncategorized'
            })
        
        cursor.close()
        conn.close()
        
        return transactions
        
    except Exception as e:
        print(f"❌ Error fetching transactions: {e}")
        return []

def load_processed_transactions():
    """Load transactions from Master_Transactions_Tagged.csv"""
    tagged_file = Path('output/Master_Transactions_Tagged.csv')
    
    if not tagged_file.exists():
        print(f"❌ Tagged file not found: {tagged_file}")
        return []
    
    transactions = []
    try:
        with open(tagged_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Convert date format - handle both MM/DD/YYYY and M/D/YY formats
                try:
                    date_obj = datetime.strptime(row['Date'], '%m/%d/%Y')
                except ValueError:
                    try:
                        date_obj = datetime.strptime(row['Date'], '%m/%d/%y')
                    except ValueError:
                        print(f"⚠️  Warning: Could not parse date '{row['Date']}', skipping transaction")
                        continue
                formatted_date = date_obj.strftime('%m/%d/%Y')
                
                # Apply final transformation - all amounts to positive (like uploader does)
                amount = abs(float(row['Amount']))
                
                transactions.append({
                    'date': formatted_date,
                    'description': row['Description'].strip(),
                    'amount': amount,
                    'spender': row['Spender'],
                    'source': row['Source'],
                    'category': row['Tag'] or 'Uncategorized'
                })
        
        return transactions
        
    except Exception as e:
        print(f"❌ Error loading processed transactions: {e}")
        return []

def find_duplicates(existing_transactions, new_transactions):
    """Find potential duplicates between existing and new transactions"""
    duplicates = []
    
    for new_tx in new_transactions:
        matches = []
        
        for existing_tx in existing_transactions:
            # Exact match: same date + same amount + same description
            if (new_tx['date'] == existing_tx['date'] and
                new_tx['amount'] == existing_tx['amount'] and
                new_tx['description'].lower() == existing_tx['description'].lower()):
                matches.append({'type': 'EXACT_MATCH', 'existing': existing_tx, 'confidence': 100})
            
            # Near match: same date + same amount + similar description
            elif (new_tx['date'] == existing_tx['date'] and
                  new_tx['amount'] == existing_tx['amount']):
                new_desc = new_tx['description'].lower()
                existing_desc = existing_tx['description'].lower()
                if new_desc in existing_desc or existing_desc in new_desc:
                    matches.append({'type': 'NEAR_MATCH', 'existing': existing_tx, 'confidence': 90})
            
            # Possible match: same amount within 1 day
            elif new_tx['amount'] == existing_tx['amount']:
                try:
                    new_date = datetime.strptime(new_tx['date'], '%m/%d/%Y')
                    existing_date = datetime.strptime(existing_tx['date'], '%m/%d/%Y')
                    days_diff = abs((new_date - existing_date).days)
                    if days_diff <= 1:
                        matches.append({'type': 'POSSIBLE_MATCH', 'existing': existing_tx, 'confidence': 70})
                except:
                    pass
        
        if matches:
            duplicates.append({'new_transaction': new_tx, 'matches': matches})
    
    return duplicates

def analyze_duplicates():
    """Main function to analyze duplicates"""
    print("🔍 DUPLICATE ANALYSIS - Final Check Before Upload")
    print("=" * 70)
    
    print("📊 Fetching existing transactions from database...")
    existing_transactions = get_existing_transactions()
    print(f"✅ Found {len(existing_transactions)} existing transactions")
    
    print("\n📄 Loading processed transactions from Master_Transactions_Tagged.csv...")
    new_transactions = load_processed_transactions()
    print(f"✅ Found {len(new_transactions)} new transactions")
    
    if not new_transactions:
        print("❌ No new transactions to check")
        return
    
    print("\n🔍 Analyzing for potential duplicates...")
    duplicates = find_duplicates(existing_transactions, new_transactions)
    
    if not duplicates:
        print("✅ No duplicates found! All transactions are safe to upload.")
        return
    
    print(f"\n⚠️  Found {len(duplicates)} potential duplicate transactions:")
    print("=" * 70)
    
    exact_count = 0
    near_count = 0
    possible_count = 0
    
    for i, duplicate in enumerate(duplicates, 1):
        new_tx = duplicate['new_transaction']
        matches = duplicate['matches']
        
        print(f"\n🔍 New Transaction #{i}:")
        print(f"   Date: {new_tx['date']}")
        print(f"   Description: {new_tx['description']}")
        print(f"   Amount: ${new_tx['amount']}")
        print(f"   Source: {new_tx['source']} ({new_tx['spender']})")
        
        for match in matches:
            existing_tx = match['existing']
            match_type = match['type']
            confidence = match['confidence']
            
            if match_type == 'EXACT_MATCH':
                exact_count += 1
                print(f"   🎯 EXACT MATCH ({confidence}% confidence):")
            elif match_type == 'NEAR_MATCH':
                near_count += 1
                print(f"   ⚠️  NEAR MATCH ({confidence}% confidence):")
            else:
                possible_count += 1
                print(f"   ❓ POSSIBLE MATCH ({confidence}% confidence):")
            
            print(f"      Existing: {existing_tx['date']} | ${existing_tx['amount']} | {existing_tx['description']}")
            print(f"      Account: {existing_tx['account']} | Category: {existing_tx['category']}")
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY:")
    print(f"   Total new transactions: {len(new_transactions)}")
    print(f"   Potential duplicates: {len(duplicates)}")
    print(f"   Exact matches: {exact_count}")
    print(f"   Near matches: {near_count}")
    print(f"   Possible matches: {possible_count}")
    print(f"   Safe to upload: {len(new_transactions) - len(duplicates)}")
    
    print("\n💡 RECOMMENDATION:")
    if exact_count > 0:
        print("   ❌ DO NOT UPLOAD - Exact matches found!")
    elif near_count > 0:
        print("   ⚠️  REVIEW CAREFULLY - Near matches found")
    else:
        print("   ✅ SAFE TO UPLOAD - Only possible matches (likely false positives)")

if __name__ == "__main__":
    analyze_duplicates() 