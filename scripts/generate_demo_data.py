#!/usr/bin/env python3
"""
Generate Demo Data for Capricorn
Creates a sanitized demo dataset based on the real export file structure.

Usage: python generate_demo_data.py
Output: saved_states/Capricorn_DEMO_Data.json
"""

import json
import random
from datetime import datetime, timedelta
from decimal import Decimal
import copy

# Configuration
INPUT_FILE = "/mnt/hgfs/VM_SHARE/Cursor_Projects/unified_ui/saved_states/Capricorn_UserData_2025-11-25_1028.json"
OUTPUT_FILE = "/mnt/hgfs/VM_SHARE/Cursor_Projects/unified_ui/saved_states/Capricorn_DEMO_Data.json"

# Categories to EXCLUDE (by name)
EXCLUDED_CATEGORIES = [
    "TAX Federal",
    "Wine", 
    "Shooting",
    "VENMO Received",
    "EBay",
    "Vape",
    "Car Tickets",
    "Pura"
]

# Category name mappings for income
INCOME_CATEGORY_MAPPINGS = {
    "INCOME Andrew": "INCOME Bob",
    "INCOME Jackie": "INCOME Mary"
}

# Account name mappings
ACCOUNT_MAPPINGS = {
    "AMEX Credit_Jackie": "AMEX Credit_Mary",
    "AMEX Credit_Andrew": "AMEX Credit_Bob",
    "BOFA Checking_Unknown": "BOFA Checking",
    "BOFA Checking_Andrew": "BOFA Checking_Bob",
    "BOFA Checking_Jackie": "BOFA Checking_Mary"
}

# Portfolio name mappings
PORTFOLIO_MAPPINGS = {
    "Schwab Trading": "ETrade Trading",
    "Merrill IRA": "Vanguard IRA",
    "BNY 401k": "Company 401K Plan"
}

# Transaction templates by category (description patterns that ML tagger will recognize)
TRANSACTION_TEMPLATES = {
    "Food": [
        ("FOODTOWN #530 HASTING ON HUNY", 15, 80),
        ("FDH*FRESH DIRECT 866-283-7374 NY", 60, 150),
        ("TRADER JOE'S #567 NEW YORK NY", 40, 120),
        ("WHOLE FOODS MKT NEW YORK NY", 50, 200),
        ("WEGMANS STORE #45 HARRISON NY", 80, 200),
        ("COSTCO WHSE #123 YONKERS NY", 100, 300),
    ],
    "Restaurant": [
        ("GRUBHUB*ORDERAHEA 877-585-7878 IL", 25, 80),
        ("DOORDASH*CHIPOTLE 855-431-0459 CA", 15, 45),
        ("UBER EATS PENDING SAN FRANC CA", 20, 60),
        ("STARBUCKS STORE 12345 NEW YORK NY", 5, 25),
        ("PANERA BREAD #4123 WHITE PLAINS NY", 12, 35),
        ("CHICK-FIL-A #1234 NEW YORK NY", 10, 30),
    ],
    "Amazon Prime": [
        ("Amazon.com*NF35D2WR2 Amzn.com/billWA", 10, 100),
        ("AMAZON MKTPL*NM0TG71S1 Amzn.com/billWA", 15, 150),
        ("AMZN Mktp US*M12K8J0T1 Amzn.com/bill WA", 20, 200),
        ("Amazon.com*N123ABC Amzn.com/billWA", 25, 75),
    ],
    "Gas": [
        ("SHELL OIL 57442162700 YONKERS NY", 40, 70),
        ("EXXONMOBIL 36521478 WHITE PLAINS NY", 35, 65),
        ("BP#1234567 HARRISON NY", 45, 75),
        ("MOBIL GAS STATION BRONXVILLE NY", 40, 80),
    ],
    "Uber": [
        ("UBER *TRIP HELP.UBER.COM CA", 15, 60),
        ("UBER *TRIP 2 HELP.UBER.COM CA", 20, 80),
        ("LYFT *RIDE SAN FRANCISCO CA", 18, 55),
    ],
    "Streaming Services": [
        ("NETFLIX.COM 866-716-0414 CA", 15.99, 22.99),
        ("SPOTIFY USA NEW YORK NY", 10.99, 16.99),
        ("HULU 877-824-4858 CA", 12.99, 17.99),
        ("APPLE.COM/BILL 866-712-7753 CA", 9.99, 14.99),
        ("DISNEY PLUS 888-905-7888 CA", 10.99, 13.99),
    ],
    "Cell Phones": [
        ("VZWRLSS*APOCC VISB 800-922-0204 FL", 80, 150),
        ("AT&T*BILL PAYMENT 800-331-0500 TX", 75, 140),
        ("T-MOBILE*PAYMENT 800-937-8997 WA", 70, 130),
    ],
    "Insurance": [
        ("GEICO *AUTO 800-841-3000 MD", 100, 200),
        ("PROGRESSIVE INS 800-776-4737 OH", 90, 180),
        ("STATE FARM INSURANCE IL", 110, 220),
    ],
    "Healthcare": [
        ("CVS/PHARMACY #1234 NEW YORK NY", 10, 50),
        ("WALGREENS #12345 WHITE PLAINS NY", 15, 60),
        ("NORTHWELL HEALTH 516-321-6789 NY", 25, 150),
        ("QUEST DIAGNOSTICS 800-222-0446 NJ", 50, 200),
    ],
    "Pharmacy": [
        ("CVS/PHARMACY #5678 BRONXVILLE NY", 10, 80),
        ("RITE AID #1234 YONKERS NY", 8, 50),
        ("WALGREENS #9876 HARRISON NY", 12, 75),
    ],
    "Clothes": [
        ("NORDSTROM #123 WHITE PLAINS NY", 50, 300),
        ("MACYS HERALD SQUARE NEW YORK NY", 40, 250),
        ("TARGET 00012345 YONKERS NY", 30, 150),
        ("OLD NAVY #1234 NEW YORK NY", 25, 100),
        ("GAP #5678 WHITE PLAINS NY", 35, 120),
    ],
    "EZ Pass": [
        ("E-ZPASS NY CSC 800-333-8655 NY", 25, 50),
    ],
    "Train": [
        ("MTA*NYCT PAYGO NEW YORK NY", 2.90, 2.90),
        ("METRO-NORTH TVM NEW YORK NY", 10, 25),
        ("LIRR TICKET MACHINE NY", 12, 30),
    ],
    "ConEd": [
        ("CONED ONLINE PMT 800-752-6633 NY", 100, 250),
    ],
    "IT Subscription": [
        ("GITHUB.COM 888-123-4567 CA", 7, 44),
        ("DROPBOX*PLUS 888-345-6789 CA", 11.99, 19.99),
        ("GOOGLE *GSUITE 888-555-1234 CA", 12, 25),
        ("MICROSOFT*OFFICE 800-642-7676 WA", 9.99, 15.99),
        ("ADOBE *CREATIVE 800-833-6687 CA", 54.99, 82.99),
    ],
    "Gifts": [
        ("HALLMARK CARDS #123 NEW YORK NY", 5, 50),
        ("ETSY.COM 718-880-3660 NY", 25, 150),
        ("WILLIAMS-SONOMA WHITE PLAINS NY", 40, 200),
    ],
    "Hotels & AirBNB": [
        ("AIRBNB * HMQK1234 877-555-1234 CA", 150, 400),
        ("MARRIOTT HOTELS 800-228-9290 MD", 150, 350),
        ("HILTON HOTELS 800-445-8667 VA", 140, 320),
    ],
    "Travel": [
        ("UNITED AIRLINES 800-864-8331 IL", 200, 600),
        ("DELTA AIR LINES 800-221-1212 GA", 180, 550),
        ("AMERICAN AIRLINES 800-433-7300 TX", 190, 580),
    ],
    "Activities": [
        ("AMC THEATRES #1234 NEW YORK NY", 15, 50),
        ("BOWLMOR LANES NEW YORK NY", 30, 80),
        ("MSG BOX OFFICE NEW YORK NY", 75, 300),
    ],
    "Golf": [
        ("MAPLE MOOR GOLF COURSE NY", 40, 80),
        ("SAXON WOODS GOLF SCARSDALE NY", 45, 90),
    ],
    "Hair Salon": [
        ("SUPERCUTS #1234 WHITE PLAINS NY", 20, 50),
        ("FANTASTIC SAMS NEW YORK NY", 25, 60),
        ("SALON 123 BRONXVILLE NY", 50, 150),
    ],
    "Dry Cleaning": [
        ("TIDE DRY CLEANERS WHITE PLAINS NY", 15, 50),
        ("ZIPS DRY CLEANERS YONKERS NY", 12, 40),
    ],
    "ATM/Cash": [
        ("ATM WITHDRAWAL BOFA 1234 NY", 40, 200),
        ("CHASE ATM NEW YORK NY", 60, 300),
    ],
    "Office Supplies": [
        ("STAPLES #1234 WHITE PLAINS NY", 20, 100),
        ("OFFICE DEPOT #5678 YONKERS NY", 15, 80),
    ],
    "Interest": [
        ("INTEREST CHARGE ON PURCHASES", 10, 50),
    ],
    "Bank Fees": [
        ("MONTHLY SERVICE FEE", 12, 25),
    ],
    "Car Insurance": [
        ("GEICO *AUTO POLICY 800-841-3000 MD", 120, 180),
    ],
    "CAR Repair": [
        ("JIFFY LUBE #1234 YONKERS NY", 40, 100),
        ("MIDAS AUTO SERVICE WHITE PLAINS NY", 100, 500),
        ("PEPBOYS #5678 NEW YORK NY", 50, 300),
    ],
    "Delivery": [
        ("AMAZON PRIME DELIVERY", 0, 0),  # Usually free
        ("INSTACART DELIVERY FEE", 5, 10),
    ],
    "Magazines": [
        ("NEW YORK TIMES DIGITAL 800-698-4637 NY", 17, 25),
        ("WALL STREET JOURNAL 800-568-7625 NJ", 19.99, 38.99),
    ],
    "Mail/FedEx/UPS": [
        ("USPS PO 1234567890 NEW YORK NY", 5, 25),
        ("UPS STORE #1234 WHITE PLAINS NY", 10, 50),
        ("FEDEX OFFICE #5678 NEW YORK NY", 15, 60),
    ],
    "Museums": [
        ("MET MUSEUM NEW YORK NY", 25, 50),
        ("MOMA NEW YORK NY", 25, 40),
        ("AMNH NEW YORK NY", 23, 46),
    ],
    "TAX Preparation": [
        ("TURBOTAX ONLINE 888-777-3066 CA", 50, 150),
        ("H&R BLOCK #1234 WHITE PLAINS NY", 100, 300),
    ],
    "BofA Cashback Rewards": [
        ("CASHBACK REDEMPTION CREDIT", -25, -100),  # Negative = credit
    ],
    "BofA Deposit": [
        ("MOBILE CHECK DEPOSIT", 100, 500),
    ],
    "Fashion Design": [
        ("JOANN FABRICS #1234 YONKERS NY", 20, 100),
        ("MICHAELS STORES NEW YORK NY", 15, 80),
    ],
    "IT Equipment": [
        ("BEST BUY #1234 WHITE PLAINS NY", 50, 500),
        ("B&H PHOTO NEW YORK NY", 100, 800),
        ("APPLE STORE #123 NEW YORK NY", 100, 1500),
    ],
    "Cash": [
        ("CASH WITHDRAWAL", 20, 100),
    ],
}

# Current market prices (as of Nov 2025)
CURRENT_PRICES = {
    "AAPL": 230.00,
    "MSFT": 420.00,
    "GOOG": 175.00,
    "SPY": 600.00,
}


def load_original_data():
    """Load the original export file."""
    print(f"Loading original data from: {INPUT_FILE}")
    with open(INPUT_FILE, 'r') as f:
        return json.load(f)


def create_demo_profile(original_profile):
    """Create demo user profile for Bob and Mary."""
    profile = copy.deepcopy(original_profile)
    
    # Update names
    profile["email"] = "bob@demo.capricorn.local"
    profile["first_name"] = "Bob"
    profile["last_name"] = "Smith"
    profile["user"] = "Bob"
    profile["partner"] = "Mary"
    
    # Update ages (reasonable demo ages)
    profile["user_age"] = 35
    profile["partner_age"] = 33
    
    # Update salaries
    profile["user_salary"] = "125000.00"
    profile["partner_salary"] = "75000.00"
    
    # Scale down other financial values proportionally
    profile["user_bonus_rate"] = "0.0500"
    profile["user_raise_rate"] = "0.0300"
    profile["partner_bonus_rate"] = "0.0300"
    profile["partner_raise_rate"] = "0.0400"
    
    # Monthly expenses scaled for $200K household
    profile["monthly_living_expenses"] = "8000.00"
    profile["annual_discretionary_spending"] = "15000.00"
    
    # 401K balances scaled down
    profile["user_401k_contribution"] = "20000.00"
    profile["partner_401k_contribution"] = "15000.00"
    profile["user_employer_match"] = "10000.00"
    profile["partner_employer_match"] = "7500.00"
    profile["user_current_401k_balance"] = "100000.00"  # Matches 401K portfolio
    profile["partner_current_401k_balance"] = "25000.00"
    
    # IRA and Trading scaled down
    profile["current_ira_balance"] = "50000.00"  # Matches IRA portfolio
    profile["current_trading_balance"] = "50000.00"  # Matches Trading portfolio
    profile["current_savings_balance"] = "10000.00"
    
    # Inheritance adjusted
    profile["expected_inheritance"] = "100000.00"
    profile["inheritance_year"] = 20
    
    # Retirement adjusted for younger ages
    profile["user_years_to_retirement"] = 30
    profile["partner_years_to_retirement"] = 32
    profile["years_of_retirement"] = 25
    
    # Savings strategy
    profile["fixed_monthly_savings"] = "2000.00"
    profile["percentage_of_leftover"] = "0.5000"
    
    # Keep tax settings the same
    # profile["state"] = "NY" (keep)
    # profile["filing_status"] = "married_filing_jointly" (keep)
    
    # Update timestamps
    now = datetime.now().isoformat()
    profile["created_at"] = now
    profile["updated_at"] = now
    
    return profile


def create_demo_accounts(original_accounts):
    """Create anonymized accounts for demo."""
    accounts = []
    for acc in original_accounts:
        new_acc = copy.deepcopy(acc)
        
        # Apply name mappings
        for old_name, new_name in ACCOUNT_MAPPINGS.items():
            if new_acc["name"] == old_name:
                new_acc["name"] = new_name
                break
        
        # Update bank_name if needed
        if "Andrew" in str(new_acc.get("bank_name", "")):
            new_acc["bank_name"] = new_acc["bank_name"].replace("Andrew", "Bob")
        if "Jackie" in str(new_acc.get("bank_name", "")):
            new_acc["bank_name"] = new_acc["bank_name"].replace("Jackie", "Mary")
            
        accounts.append(new_acc)
    
    return accounts


def create_demo_categories(original_categories):
    """Create categories, excluding unwanted ones and renaming income categories."""
    categories = []
    excluded_ids = set()
    category_id_map = {}  # old_id -> new_id
    
    new_id = 1
    for cat in original_categories:
        # Skip excluded categories
        if cat["name"] in EXCLUDED_CATEGORIES:
            excluded_ids.add(cat["id"])
            continue
        
        new_cat = copy.deepcopy(cat)
        
        # Rename income categories
        if cat["name"] in INCOME_CATEGORY_MAPPINGS:
            new_cat["name"] = INCOME_CATEGORY_MAPPINGS[cat["name"]]
        
        # Map old ID to new ID
        category_id_map[cat["id"]] = new_id
        new_cat["id"] = new_id
        new_id += 1
        
        categories.append(new_cat)
    
    return categories, excluded_ids, category_id_map


def generate_demo_transactions(original_transactions, categories, excluded_category_ids, category_id_map, accounts):
    """Generate 23 months of demo transactions."""
    
    # Build category name lookup
    category_names = {cat["id"]: cat["name"] for cat in categories}
    
    # Get account IDs
    checking_account_id = None
    credit_bob_id = None
    credit_mary_id = None
    
    for acc in accounts:
        if "Checking" in acc["name"]:
            checking_account_id = acc["id"]
        elif "Bob" in acc["name"] and "AMEX" in acc["name"]:
            credit_bob_id = acc["id"]
        elif "Mary" in acc["name"] and "AMEX" in acc["name"]:
            credit_mary_id = acc["id"]
    
    if not checking_account_id:
        checking_account_id = accounts[0]["id"]
    if not credit_bob_id:
        credit_bob_id = accounts[1]["id"] if len(accounts) > 1 else accounts[0]["id"]
    if not credit_mary_id:
        credit_mary_id = accounts[2]["id"] if len(accounts) > 2 else accounts[0]["id"]
    
    # Find category IDs we need
    income_bob_id = None
    income_mary_id = None
    rent_id = None
    
    for cat in categories:
        if cat["name"] == "INCOME Bob":
            income_bob_id = cat["id"]
        elif cat["name"] == "INCOME Mary":
            income_mary_id = cat["id"]
        elif cat["name"] == "Rent":
            rent_id = cat["id"]
    
    # Build list of usable categories (excluding income and rent - we'll add those separately)
    expense_categories = []
    for cat in categories:
        if cat["name"] not in ["INCOME Bob", "INCOME Mary", "Rent", "BofA Deposit", "BofA Cashback Rewards"]:
            if cat["name"] in TRANSACTION_TEMPLATES:
                expense_categories.append(cat)
    
    transactions = []
    tx_id = 1
    
    # Generate transactions for Jan 2024 to Nov 2025 (23 months)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 11, 26)
    
    current_date = start_date
    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        
        # --- INCOME transactions (1st and 15th of each month) ---
        # Bob's income: $2,500 x 2 = $5,000/month
        if income_bob_id:
            for pay_day in [1, 15]:
                pay_date = datetime(year, month, pay_day)
                if pay_date <= end_date:
                    transactions.append({
                        "id": tx_id,
                        "user_id": 1,
                        "account_id": checking_account_id,
                        "category_id": income_bob_id,
                        "description": "PAYROLL ACME CORP BOB SMITH",
                        "amount": "2500.00",
                        "transaction_date": pay_date.strftime("%Y-%m-%d"),
                        "transaction_type": "credit",
                        "is_processed": True,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    })
                    tx_id += 1
        
        # Mary's income: $2,000 x 2 = $4,000/month
        if income_mary_id:
            for pay_day in [1, 15]:
                pay_date = datetime(year, month, pay_day)
                if pay_date <= end_date:
                    transactions.append({
                        "id": tx_id,
                        "user_id": 1,
                        "account_id": checking_account_id,
                        "category_id": income_mary_id,
                        "description": "PAYROLL WIDGET INC MARY SMITH",
                        "amount": "2000.00",
                        "transaction_date": pay_date.strftime("%Y-%m-%d"),
                        "transaction_type": "credit",
                        "is_processed": True,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    })
                    tx_id += 1
        
        # --- RENT transaction (1st of each month) ---
        if rent_id:
            rent_date = datetime(year, month, 1)
            if rent_date <= end_date:
                transactions.append({
                    "id": tx_id,
                    "user_id": 1,
                    "account_id": checking_account_id,
                    "category_id": rent_id,
                    "description": "RENT PAYMENT 123 MAIN ST APT 4B",
                    "amount": "3000.00",
                    "transaction_date": rent_date.strftime("%Y-%m-%d"),
                    "transaction_type": "debit",
                    "is_processed": True,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })
                tx_id += 1
        
        # --- Generate 15-20 expense transactions per month ---
        num_expenses = random.randint(15, 20)
        
        for _ in range(num_expenses):
            # Pick a random category
            cat = random.choice(expense_categories)
            cat_name = cat["name"]
            
            # Get transaction template
            if cat_name in TRANSACTION_TEMPLATES:
                templates = TRANSACTION_TEMPLATES[cat_name]
                template = random.choice(templates)
                description, min_amt, max_amt = template
                
                # Generate random amount in range
                if min_amt == max_amt:
                    amount = min_amt
                else:
                    amount = round(random.uniform(min_amt, max_amt), 2)
                
                # Skip if amount is 0 or negative (except for credits)
                if amount <= 0 and cat_name not in ["BofA Cashback Rewards"]:
                    continue
                
                # Random day in the month
                day = random.randint(1, 28)  # Safe for all months
                tx_date = datetime(year, month, day)
                
                if tx_date <= end_date:
                    # Alternate between Bob and Mary's credit cards
                    account_id = random.choice([credit_bob_id, credit_mary_id, checking_account_id])
                    
                    transactions.append({
                        "id": tx_id,
                        "user_id": 1,
                        "account_id": account_id,
                        "category_id": cat["id"],
                        "description": description,
                        "amount": f"{abs(amount):.2f}",
                        "transaction_date": tx_date.strftime("%Y-%m-%d"),
                        "transaction_type": "credit" if amount < 0 else "debit",
                        "is_processed": True,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    })
                    tx_id += 1
        
        # Move to next month
        if month == 12:
            current_date = datetime(year + 1, 1, 1)
        else:
            current_date = datetime(year, month + 1, 1)
    
    print(f"Generated {len(transactions)} demo transactions")
    return transactions


def create_demo_portfolios():
    """Create scaled-down demo portfolios."""
    now = datetime.now().isoformat()
    
    portfolios = [
        {
            "id": 1,
            "name": "ETrade Trading",
            "type": "real",
            "description": "Personal trading account",
            "cash_on_hand": "5000.00",
            "investor_profile_id": 1,
            "created_at": now,
            "updated_at": now
        },
        {
            "id": 2,
            "name": "Vanguard IRA",
            "type": "retirement",
            "description": "Traditional IRA",
            "cash_on_hand": "2500.00",
            "investor_profile_id": 1,
            "created_at": now,
            "updated_at": now
        },
        {
            "id": 3,
            "name": "Company 401K Plan",
            "type": "retirement",
            "description": "Employer 401(k) plan",
            "cash_on_hand": "0.00",
            "investor_profile_id": 1,
            "created_at": now,
            "updated_at": now
        }
    ]
    
    return portfolios


def create_demo_portfolio_transactions():
    """Create portfolio transactions - all bought in Oct 2024 at 20% below current prices."""
    now = datetime.now().isoformat()
    buy_date = "2024-10-15"  # October 15, 2024
    
    transactions = []
    tx_id = 1
    
    # ETrade Trading ($50K target) - Mix of AAPL, MSFT, GOOG
    # Buy at 20% discount
    trading_stocks = [
        ("AAPL", "Apple Inc", 40, CURRENT_PRICES["AAPL"] * 0.80),  # ~$7,360
        ("MSFT", "Microsoft", 50, CURRENT_PRICES["MSFT"] * 0.80),  # ~$16,800
        ("GOOG", "Alphabet", 100, CURRENT_PRICES["GOOG"] * 0.80), # ~$14,000
    ]
    # Total cost basis: ~$38,160, current value: ~$47,700 + $5K cash = ~$52.7K
    
    for ticker, name, qty, price in trading_stocks:
        transactions.append({
            "id": tx_id,
            "portfolio_id": 1,
            "stock_name": name,
            "ticker_symbol": ticker,
            "transaction_type": "buy",
            "quantity": f"{qty:.4f}",
            "price_per_share": f"{price:.2f}",
            "transaction_date": buy_date,
            "created_at": now,
            "updated_at": now
        })
        tx_id += 1
    
    # Vanguard IRA ($50K target) - Mix of AAPL, MSFT, GOOG
    ira_stocks = [
        ("AAPL", "Apple Inc", 50, CURRENT_PRICES["AAPL"] * 0.80),  # ~$9,200
        ("MSFT", "Microsoft", 40, CURRENT_PRICES["MSFT"] * 0.80),  # ~$13,440
        ("GOOG", "Alphabet", 120, CURRENT_PRICES["GOOG"] * 0.80), # ~$16,800
    ]
    # Total cost basis: ~$39,440, current value: ~$49,300 + $2.5K cash = ~$51.8K
    
    for ticker, name, qty, price in ira_stocks:
        transactions.append({
            "id": tx_id,
            "portfolio_id": 2,
            "stock_name": name,
            "ticker_symbol": ticker,
            "transaction_type": "buy",
            "quantity": f"{qty:.4f}",
            "price_per_share": f"{price:.2f}",
            "transaction_date": buy_date,
            "created_at": now,
            "updated_at": now
        })
        tx_id += 1
    
    # Company 401K ($100K target) - All SPY
    spy_price_at_buy = CURRENT_PRICES["SPY"] * 0.80  # 20% discount = $480
    spy_shares = int(100000 / spy_price_at_buy)  # ~208 shares
    
    transactions.append({
        "id": tx_id,
        "portfolio_id": 3,
        "stock_name": "SPDR S&P 500 ETF",
        "ticker_symbol": "SPY",
        "transaction_type": "buy",
        "quantity": f"{spy_shares:.4f}",
        "price_per_share": f"{spy_price_at_buy:.2f}",
        "transaction_date": buy_date,
        "created_at": now,
        "updated_at": now
    })
    
    print(f"Generated {len(transactions)} portfolio transactions")
    return transactions


def create_demo_market_prices():
    """Create current market prices."""
    now = datetime.now().isoformat()
    
    prices = [
        {"id": 1, "ticker_symbol": "AAPL", "current_price": f"{CURRENT_PRICES['AAPL']:.4f}", "last_updated": now},
        {"id": 2, "ticker_symbol": "MSFT", "current_price": f"{CURRENT_PRICES['MSFT']:.4f}", "last_updated": now},
        {"id": 3, "ticker_symbol": "GOOG", "current_price": f"{CURRENT_PRICES['GOOG']:.4f}", "last_updated": now},
        {"id": 4, "ticker_symbol": "SPY", "current_price": f"{CURRENT_PRICES['SPY']:.4f}", "last_updated": now},
    ]
    
    return prices


def create_demo_investor_profile(original_profile):
    """Create investor profile - keep same tax settings."""
    profile = copy.deepcopy(original_profile)
    
    # Update income to match
    profile["annual_household_income"] = "200000.00"
    
    # Keep tax settings the same
    # profile["filing_status"] = "married_filing_jointly" (keep)
    # profile["state"] = "NY" (keep)
    # profile["local_tax_rate"] = "0.0100" (keep)
    
    now = datetime.now().isoformat()
    profile["created_at"] = now
    profile["updated_at"] = now
    
    return profile


def main():
    """Main function to generate demo data."""
    print("=" * 60)
    print("Capricorn Demo Data Generator")
    print("=" * 60)
    
    # Load original data
    original = load_original_data()
    
    # Create new demo data structure
    demo = {
        "export_info": {
            "exported_at": datetime.now().isoformat() + "Z",
            "version": "1.0",
            "source": "Capricorn Demo Generator"
        },
        "data": {}
    }
    
    # 1. Create demo profile
    print("\n1. Creating demo user profile (Bob & Mary)...")
    demo["data"]["user_profile"] = [create_demo_profile(original["data"]["user_profile"][0])]
    print(f"   - Bob salary: $125,000")
    print(f"   - Mary salary: $75,000")
    
    # 2. Create demo accounts
    print("\n2. Anonymizing accounts...")
    demo["data"]["accounts"] = create_demo_accounts(original["data"]["accounts"])
    print(f"   - Created {len(demo['data']['accounts'])} accounts")
    
    # 3. Create demo categories (excluding unwanted ones)
    print("\n3. Creating categories (excluding personal ones)...")
    categories, excluded_ids, category_id_map = create_demo_categories(original["data"]["categories"])
    demo["data"]["categories"] = categories
    print(f"   - Kept {len(categories)} categories")
    print(f"   - Excluded: {EXCLUDED_CATEGORIES}")
    
    # 4. Generate demo transactions
    print("\n4. Generating 23 months of transactions (Jan 2024 - Nov 2025)...")
    demo["data"]["transactions"] = generate_demo_transactions(
        original["data"]["transactions"],
        categories,
        excluded_ids,
        category_id_map,
        demo["data"]["accounts"]
    )
    
    # 5. Create demo portfolios
    print("\n5. Creating scaled-down portfolios...")
    demo["data"]["portfolios"] = create_demo_portfolios()
    print(f"   - ETrade Trading: ~$50K (AAPL, MSFT, GOOG)")
    print(f"   - Vanguard IRA: ~$50K (AAPL, MSFT, GOOG)")
    print(f"   - Company 401K: ~$100K (SPY)")
    
    # 6. Create portfolio transactions
    print("\n6. Creating portfolio transactions (Oct 2024 @ 20% discount)...")
    demo["data"]["portfolio_transactions"] = create_demo_portfolio_transactions()
    
    # 7. Create market prices
    print("\n7. Setting current market prices...")
    demo["data"]["market_prices"] = create_demo_market_prices()
    
    # 8. Create investor profile
    print("\n8. Creating investor profile...")
    if "investor_profiles" in original["data"] and original["data"]["investor_profiles"]:
        demo["data"]["investor_profiles"] = [create_demo_investor_profile(original["data"]["investor_profiles"][0])]
    else:
        demo["data"]["investor_profiles"] = [{
            "id": 1,
            "annual_household_income": "200000.00",
            "filing_status": "married_filing_jointly",
            "state": "NY",
            "local_tax_rate": "0.0100",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }]
    
    # 9. Add counts
    demo["counts"] = {
        "user_profile": len(demo["data"]["user_profile"]),
        "accounts": len(demo["data"]["accounts"]),
        "categories": len(demo["data"]["categories"]),
        "transactions": len(demo["data"]["transactions"]),
        "portfolios": len(demo["data"]["portfolios"]),
        "portfolio_transactions": len(demo["data"]["portfolio_transactions"]),
        "market_prices": len(demo["data"]["market_prices"]),
        "investor_profiles": len(demo["data"]["investor_profiles"]),
        "total": (
            len(demo["data"]["user_profile"]) +
            len(demo["data"]["accounts"]) +
            len(demo["data"]["categories"]) +
            len(demo["data"]["transactions"]) +
            len(demo["data"]["portfolios"]) +
            len(demo["data"]["portfolio_transactions"]) +
            len(demo["data"]["market_prices"]) +
            len(demo["data"]["investor_profiles"])
        )
    }
    
    # Save demo data
    print(f"\n9. Saving demo data to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(demo, f, indent=2)
    
    print("\n" + "=" * 60)
    print("DEMO DATA GENERATION COMPLETE!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - User Profile: Bob & Mary Smith")
    print(f"  - Accounts: {demo['counts']['accounts']}")
    print(f"  - Categories: {demo['counts']['categories']} (excluded {len(EXCLUDED_CATEGORIES)} personal)")
    print(f"  - Transactions: {demo['counts']['transactions']} (23 months)")
    print(f"  - Portfolios: {demo['counts']['portfolios']}")
    print(f"  - Stock Transactions: {demo['counts']['portfolio_transactions']}")
    print(f"  - Market Prices: {demo['counts']['market_prices']}")
    print(f"\nTotal Records: {demo['counts']['total']}")
    print(f"\nOutput file: {OUTPUT_FILE}")
    print("\nNext step: Import this file via the DATA tab in Capricorn!")


if __name__ == "__main__":
    main()

