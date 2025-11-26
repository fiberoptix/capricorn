#!/usr/bin/env python3
"""
Transaction Parser Script - Enhanced Version
Parses classified BOFA Checking, BOFA Credit, and AMEX Credit transaction files
from the working directory and creates a Master_Transactions.csv file.
"""

import csv
import os
import glob
import shutil
from pathlib import Path
from collections import defaultdict

def create_master_file(base_dir=None):
    """Create the Master_Transactions.csv file with headers, starting fresh"""
    if base_dir is None:
        # Use path relative to this module - works in both DEV and PROD Docker
        base_dir = Path(__file__).parent / "data"
    else:
        base_dir = Path(base_dir)
    
    master_file = str(base_dir / "output" / "Master_Transactions.csv")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(master_file), exist_ok=True)
    
    # Always delete existing file to start fresh
    if os.path.exists(master_file):
        os.remove(master_file)
        print(f"🗑️  Deleted existing {master_file}")
    
    # Create new file with headers
    with open(master_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Description", "Amount", "Spender", "Source", "Type", "Tag", "Duplicate"])
    print(f"✅ Created fresh {master_file} with headers")
    return master_file

def read_file_with_encoding(file_path):
    """Read file with multiple encoding attempts"""
    encodings = ['utf-8', 'iso-8859-1', 'cp1252', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', newline='', encoding=encoding) as f:
                return f.readlines(), encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"  ⚠️  Error reading {file_path} with {encoding}: {e}")
            continue
    
    raise Exception(f"Unable to read {file_path} with any supported encoding")

def get_file_type_from_prefix(filename):
    """Extract file type from classification prefix"""
    if filename.startswith("BOFA_CHECKING_"):
        return "BOFA_CHECKING"
    elif filename.startswith("BOFA_CREDIT_"):
        return "BOFA_CREDIT"
    elif filename.startswith("AMEX_CREDIT_"):
        return "AMEX_CREDIT"
    else:
        return "UNKNOWN"

def extract_spender_from_filename(filename, file_type):
    """Extract spender name from filename"""
    filename_upper = filename.upper()
    
    if "ANDREW" in filename_upper:
        return "Andrew"
    elif "JACKIE" in filename_upper or "JACQUELINE" in filename_upper:
        return "Jackie"
    elif file_type == "BOFA_CREDIT":
        return "Andrew"  # Default for BOFA Credit files
    else:
        return "Unknown"

def determine_transaction_type(amount_str):
    """Determine if transaction is Credit (positive) or Debit (negative)"""
    try:
        amount_clean = amount_str.replace(',', '').strip()
        if amount_clean == '' or amount_clean == '0' or amount_clean == '0.00':
            return "Credit"
        
        amount_float = float(amount_clean)
        return "Credit" if amount_float >= 0 else "Debit"
    except (ValueError, TypeError):
        return "Credit"

def is_valid_amount(amount_str):
    """Check if amount is valid (not empty or blank)"""
    if not amount_str or amount_str.strip() == '':
        return False
    return True

def parse_bofa_checking_file(file_path, filename):
    """Parse a single BOFA Checking file"""
    print(f"📊 Processing BOFA Checking: {filename}")
    
    transactions = []
    skipped_count = 0
    spender = extract_spender_from_filename(filename, "BOFA_CHECKING")
    
    try:
        lines, encoding = read_file_with_encoding(file_path)
        print(f"  📝 Reading with {encoding} encoding")
        
        # Headers on row 7 (index 6), data starts on row 8 (index 7)
        if len(lines) > 7:
            for line_idx in range(7, len(lines)):
                line = lines[line_idx].strip()
                if line:
                    try:
                        # Parse CSV line
                        reader = csv.reader([line])
                        row = next(reader)
                        
                        # Handle BOM in first field if present
                        if row and row[0].startswith('\ufeff'):
                            row[0] = row[0].lstrip('\ufeff')
                        
                        if len(row) >= 3:
                            date = row[0].strip()
                            description = row[1].strip()
                            amount = row[2].strip()
                            
                            # Skip empty dates or header-like rows
                            if date and date != "Date" and description:
                                if not is_valid_amount(amount):
                                    skipped_count += 1
                                    continue
                                
                                transaction_type = determine_transaction_type(amount)
                                transactions.append([date, description, amount, spender, "BOFA Checking", transaction_type, "", ""])
                    except Exception as e:
                        print(f"  ⚠️  Error parsing line {line_idx + 1}: {e}")
        
        print(f"  ✅ Parsed {len(transactions)} transactions")
        if skipped_count > 0:
            print(f"  ⏭️  Skipped {skipped_count} transactions with empty amounts")
            
    except Exception as e:
        print(f"  ❌ Error processing {filename}: {e}")
    
    return transactions

def parse_bofa_credit_file(file_path, filename):
    """Parse a single BOFA Credit file"""
    print(f"📊 Processing BOFA Credit: {filename}")
    
    transactions = []
    skipped_count = 0
    spender = extract_spender_from_filename(filename, "BOFA_CREDIT")
    
    try:
        lines, encoding = read_file_with_encoding(file_path)
        print(f"  📝 Reading with {encoding} encoding")
        
        # Convert lines to CSV reader
        reader = csv.reader(lines)
        
        # Skip header row
        header = next(reader, None)
        if header and header[0].startswith('\ufeff'):
            header[0] = header[0].lstrip('\ufeff')
        
        for row_idx, row in enumerate(reader, start=2):
            if len(row) >= 5:
                try:
                    # Handle BOM in first field if present
                    if row and row[0].startswith('\ufeff'):
                        row[0] = row[0].lstrip('\ufeff')
                    
                    posted_date = row[0].strip()  # Posted Date -> Date
                    payee = row[2].strip()        # Payee -> Description
                    amount = row[4].strip()       # Amount -> Amount
                    
                    if posted_date and payee:
                        if not is_valid_amount(amount):
                            skipped_count += 1
                            continue
                        
                        transaction_type = determine_transaction_type(amount)
                        transactions.append([posted_date, payee, amount, spender, "BOFA Credit", transaction_type, "", ""])
                except Exception as e:
                    print(f"  ⚠️  Error parsing row {row_idx}: {e}")
        
        print(f"  ✅ Parsed {len(transactions)} transactions")
        if skipped_count > 0:
            print(f"  ⏭️  Skipped {skipped_count} transactions with empty amounts")
            
    except Exception as e:
        print(f"  ❌ Error processing {filename}: {e}")
    
    return transactions

def parse_amex_credit_file(file_path, filename):
    """Parse a single AMEX Credit file"""
    print(f"📊 Processing AMEX Credit: {filename}")
    
    transactions = []
    skipped_count = 0
    
    try:
        lines, encoding = read_file_with_encoding(file_path)
        print(f"  📝 Reading with {encoding} encoding")
        
        # Convert lines to CSV reader
        reader = csv.reader(lines)
        
        # Skip header row
        header = next(reader, None)
        if header and header[0].startswith('\ufeff'):
            header[0] = header[0].lstrip('\ufeff')
        
        for row_idx, row in enumerate(reader, start=2):
            if len(row) >= 4:  # Be flexible with column count
                try:
                    # Handle BOM in first field if present
                    if row and row[0].startswith('\ufeff'):
                        row[0] = row[0].lstrip('\ufeff')
                    
                    date = row[0].strip()           # Date
                    description = row[1].strip()   # Description
                    card_member = row[2].strip()   # Card Member -> Spender
                    amount = row[4].strip() if len(row) > 4 else ""  # Amount
                    
                    # Map card member names
                    if card_member == "ANDREW GAMACHE":
                        spender = "Andrew"
                    elif card_member == "JACQUELINE KARWACKI":
                        spender = "Jackie"
                    else:
                        spender = card_member
                    
                    if date and description:
                        if not is_valid_amount(amount):
                            skipped_count += 1
                            continue
                        
                        # Flip AMEX amount signs to match BOFA format
                        try:
                            flipped_amount = str(float(amount) * -1)
                        except ValueError:
                            print(f"  ⚠️  Could not flip amount sign for: {amount}")
                            flipped_amount = amount
                        
                        transaction_type = determine_transaction_type(flipped_amount)
                        transactions.append([date, description, flipped_amount, spender, "AMEX Credit", transaction_type, "", ""])
                except Exception as e:
                    print(f"  ⚠️  Error parsing row {row_idx}: {e}")
        
        print(f"  ✅ Parsed {len(transactions)} transactions")
        if skipped_count > 0:
            print(f"  ⏭️  Skipped {skipped_count} transactions with empty amounts")
            
    except Exception as e:
        print(f"  ❌ Error processing {filename}: {e}")
    
    return transactions

def parse_classified_files(base_dir=None):
    """Parse all classified files from the working directory"""
    if base_dir is None:
        # Use path relative to this module - works in both DEV and PROD Docker
        base_dir = Path(__file__).parent / "data"
    else:
        base_dir = Path(base_dir)
    
    working_dir = base_dir / "working"
    
    if not working_dir.exists():
        print(f"❌ Working directory does not exist: {working_dir}")
        return []
    
    # Get all CSV files from working directory
    csv_files = list(working_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"❌ No CSV files found in {working_dir}")
        return []
    
    print(f"📂 Found {len(csv_files)} classified files in working directory")
    
    all_transactions = []
    stats = {"BOFA_CHECKING": 0, "BOFA_CREDIT": 0, "AMEX_CREDIT": 0, "UNKNOWN": 0}
    
    for file_path in csv_files:
        filename = file_path.name
        file_type = get_file_type_from_prefix(filename)
        
        if file_type == "BOFA_CHECKING":
            transactions = parse_bofa_checking_file(file_path, filename)
            stats["BOFA_CHECKING"] += len(transactions)
        elif file_type == "BOFA_CREDIT":
            transactions = parse_bofa_credit_file(file_path, filename)
            stats["BOFA_CREDIT"] += len(transactions)
        elif file_type == "AMEX_CREDIT":
            transactions = parse_amex_credit_file(file_path, filename)
            stats["AMEX_CREDIT"] += len(transactions)
        else:
            print(f"❌ Unknown file type for: {filename}")
            stats["UNKNOWN"] += 1
            continue
        
        all_transactions.extend(transactions)
    
    print(f"\n📊 Parsing Summary:")
    print(f"   - BOFA Checking: {stats['BOFA_CHECKING']} transactions")
    print(f"   - BOFA Credit: {stats['BOFA_CREDIT']} transactions")
    print(f"   - AMEX Credit: {stats['AMEX_CREDIT']} transactions")
    print(f"   - Total: {len(all_transactions)} transactions")
    
    return all_transactions

def append_to_master_file(master_file, transactions):
    """Append transactions to the master file"""
    if transactions:
        with open(master_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(transactions)
        print(f"✅ Appended {len(transactions)} transactions to {master_file}")
    else:
        print("⚠️  No transactions to append")

def filter_internal_transfers(master_file):
    """Filter out internal transfers from the master file"""
    print("🗑️  Starting internal transfer filtering...")
    
    # Read all transactions
    transactions = []
    with open(master_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            print("❌ Error: Could not read fieldnames from master file")
            return 0, 0, 0
        for row in reader:
            transactions.append(row)
    
    original_count = len(transactions)
    print(f"📊 Original transaction count: {original_count}")
    
    # Filter out internal transfers
    filtered_transactions = []
    removed_count = 0
    
    for transaction in transactions:
        description = transaction['Description'].upper()
        
        # Check for internal transfer patterns
        is_internal_transfer = (
            'TRANSFER TO SAV' in description or
            'TRANSFER TO CHK' in description or
            'TRANSFER FROM SAV' in description or
            'TRANSFER FROM CHK' in description or
            ('ONLINE BANKING TRANSFER' in description and ('SAV' in description or 'CHK' in description)) or
            'ONLINE PAYMENT FROM CHK 2148' in description or
            'ONLINE PAYMENT FROM SAV 2180' in description
        )
        
        if is_internal_transfer:
            removed_count += 1
            print(f"🗑️  Removed internal transfer: {transaction['Date']} | {transaction['Description'][:50]}... | ${transaction['Amount']}")
        else:
            filtered_transactions.append(transaction)
    
    print(f"📊 Internal transfer filtering results:")
    print(f"   - Original transactions: {original_count}")
    print(f"   - Internal transfers removed: {removed_count}")
    print(f"   - Remaining transactions: {len(filtered_transactions)}")
    
    # Write filtered transactions back to file
    with open(master_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_transactions)
    
    print(f"✅ Internal transfer filtering complete: {master_file}")
    return original_count, removed_count, len(filtered_transactions)

def flag_duplicates_in_master_file(master_file):
    """Flag duplicate transactions in master file without removing them"""
    print("🔄 Starting duplicate flagging process...")
    
    # Read all transactions
    transactions = []
    with open(master_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            print("❌ Error: Could not read fieldnames from master file")
            return 0, 0, 0
        for row in reader:
            transactions.append(row)
    
    print(f"📊 Total transactions to analyze: {len(transactions)}")
    
    # Group by Spender + Source first, then find duplicates within each group
    spender_source_groups = defaultdict(list)
    
    # First, separate transactions by Spender + Source
    for transaction in transactions:
        spender_source_key = f"{transaction['Spender']}|{transaction['Source']}"
        spender_source_groups[spender_source_key].append(transaction)
    
    print(f"📊 Analyzing duplicates by Spender + Source:")
    for key, trans_list in spender_source_groups.items():
        spender, source = key.split('|')
        print(f"   {spender} - {source}: {len(trans_list)} transactions")
    
    # Now find duplicates within each Spender + Source group
    all_groups = defaultdict(list)
    
    for spender_source_key, spender_source_transactions in spender_source_groups.items():
        # Within this Spender + Source, group by transaction details
        for transaction in spender_source_transactions:
            # Create key from transaction fields (excluding Spender/Source since they're already grouped)
            detail_key = f"{spender_source_key}|{transaction['Date']}|{transaction['Description']}|{transaction['Amount']}|{transaction['Type']}|{transaction['Tag']}"
            all_groups[detail_key].append(transaction)
    
    # Flag duplicates but keep all transactions
    flagged_transactions = []
    duplicate_groups = 0
    flagged_count = 0
    
    for key, group in all_groups.items():
        if len(group) > 1:
            # Special handling for MTA transactions
            is_mta = "MTA" in group[0]['Description'].upper()
            
            if is_mta and len(group) == 2:
                # MTA with only 2 transactions = legitimate round trip, don't flag
                print(f"🚇 MTA Round Trip (not flagged): {group[0]['Date']} | {group[0]['Description'][:40]}... | ${group[0]['Amount']} (x{len(group)})")
                for transaction in group:
                    transaction['Duplicate'] = "No"
                    flagged_transactions.append(transaction)
            elif is_mta and len(group) >= 3:
                # MTA with 3+ transactions = unusual, flag for review
                duplicate_groups += 1
                print(f"🚇 MTA Multiple Rides (flagged): {group[0]['Date']} | {group[0]['Description'][:40]}... | ${group[0]['Amount']} (x{len(group)})")
                for i, transaction in enumerate(group):
                    transaction['Duplicate'] = f"Yes ({i+1} of {len(group)})"
                    flagged_transactions.append(transaction)
                    flagged_count += 1
            else:
                # Non-MTA duplicates - flag normally
                duplicate_groups += 1
                print(f"🔄 Found {len(group)} copies of: {group[0]['Date']} | {group[0]['Description'][:40]}... | ${group[0]['Amount']}")
                for i, transaction in enumerate(group):
                    transaction['Duplicate'] = f"Yes ({i+1} of {len(group)})"
                    flagged_transactions.append(transaction)
                    flagged_count += 1
        else:
            # Single transaction - not a duplicate
            group[0]['Duplicate'] = "No"
            flagged_transactions.append(group[0])
    
    print(f"📊 Duplicate flagging results:")
    print(f"   - Total transactions: {len(transactions)}")
    print(f"   - Duplicate groups found: {duplicate_groups}")
    print(f"   - Transactions flagged as duplicates: {flagged_count}")
    print(f"   - Unique transactions: {len(transactions) - flagged_count}")
    
    # Write flagged transactions back to file with updated fieldnames
    updated_fieldnames = ['Date', 'Description', 'Amount', 'Spender', 'Source', 'Type', 'Tag', 'Duplicate']
    with open(master_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=updated_fieldnames)
        writer.writeheader()
        writer.writerows(flagged_transactions)
    
    print(f"✅ Duplicate flagging complete: {master_file}")
    return len(transactions), duplicate_groups, flagged_count

def main(base_dir=None):
    """Main processing function"""
    print("🏦 Starting Enhanced Transaction File Parser")
    print("=" * 50)
    
    if base_dir is None:
        # Use path relative to this module - works in both DEV and PROD Docker
        base_dir = Path(__file__).parent / "data"
    else:
        base_dir = Path(base_dir)
    
    # Clean output directory first (ensure fresh start)
    output_dir = base_dir / "output"
    if output_dir.exists():
        print("🗑️  Cleaning output directory for fresh start...")
        shutil.rmtree(output_dir)
    
    # Create master file
    master_file = create_master_file(base_dir)
    
    # Parse all classified files
    print("\n📂 Processing classified files from working directory...")
    all_transactions = parse_classified_files(base_dir)
    
    if not all_transactions:
        print("❌ No transactions found. Please check that files are properly classified.")
        return
    
    append_to_master_file(master_file, all_transactions)
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🎉 PARSING COMPLETE!")
    print(f"📊 Total transactions processed: {len(all_transactions)}")
    print(f"📄 Master file: {master_file}")
    
    # Filter out internal transfers
    print("\n" + "🗑️ INTERNAL TRANSFER FILTERING")
    print("=" * 50)
    original_count, removed_count, remaining_count = filter_internal_transfers(master_file)
    
    # Flag duplicates in the master file
    print("\n" + "🔄 DUPLICATE FLAGGING PROCESS")
    print("=" * 50)
    total_transactions, duplicate_groups, flagged_count = flag_duplicates_in_master_file(master_file)
    
    print("\n" + "=" * 50)
    print(f"🎉 PROCESSING COMPLETE!")
    print(f"📊 Final Results:")
    print(f"   - Original transactions parsed: {original_count}")
    print(f"   - Internal transfers removed: {removed_count}")
    print(f"   - Final transactions: {total_transactions}")
    print(f"   - Duplicate groups found: {duplicate_groups}")
    print(f"   - Transactions flagged as duplicates: {flagged_count}")
    print(f"   - Clean transactions ready for analysis: {total_transactions - flagged_count}")
    print(f"📄 Master file with duplicate flags: {master_file}")
    
    # Show first few transactions as verification
    if os.path.exists(master_file):
        print(f"\n🔍 First 5 transactions in {master_file}:")
        with open(master_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            print(f"   {', '.join(header)}")
            for i, row in enumerate(reader):
                if i < 5:
                    print(f"   {', '.join(row)}")
                else:
                    break

if __name__ == "__main__":
    main() 