#!/usr/bin/env python3
"""
Intelligent Banking File Classification Script

This script analyzes CSV files in the my_banking_test/input directory and automatically
classifies them as BOFA_CHECKING, BOFA_CREDIT, or AMEX_CREDIT based on their structure.
It then copies the classified files to the working directory with appropriate prefixes.

Based on data_model specifications:
- BOFA Checking: 4 columns, headers on row 7, "Date,Description,Amount,Running Bal."
- BOFA Credit: 5 columns, headers on row 1, "Posted Date,Reference Number,Payee,Address,Amount"
- AMEX Credit: 5 columns, headers on row 1, "Date,Description,Card Member,Account #,Amount"
"""

import os
import csv
import shutil
from pathlib import Path

def read_csv_with_encoding(file_path):
    """
    Read CSV file with multiple encoding attempts.
    
    Returns:
        list: List of rows from the CSV file
    """
    encodings = ['utf-8', 'iso-8859-1', 'cp1252', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', newline='', encoding=encoding) as file:
                reader = csv.reader(file)
                rows = []
                for i, row in enumerate(reader):
                    if i < 10:  # Only read first 10 rows for analysis
                        rows.append(row)
                    else:
                        break
                return rows
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"  ⚠️  Error reading with {encoding}: {str(e)}")
            continue
    
    raise Exception(f"Unable to read file with any supported encoding: {encodings}")

def analyze_csv_structure(file_path):
    """
    Analyze the structure of a CSV file to determine its type.
    
    Returns:
        str: File type classification ('BOFA_CHECKING', 'BOFA_CREDIT', 'AMEX_CREDIT', or 'UNKNOWN')
    """
    try:
        rows = read_csv_with_encoding(file_path)
        
        if not rows:
            return 'UNKNOWN'
        
        # Check for BOFA Checking pattern
        # Look for headers on row 7 (index 6) with 4 columns
        if len(rows) >= 7:
            try:
                row_7_data = rows[6]
                if len(row_7_data) == 4:
                    # Check if it matches BOFA Checking pattern
                    headers = [h.strip().lstrip('\ufeff') for h in row_7_data]  # Handle BOM
                    if ('Date' in headers and 'Description' in headers and 
                        'Amount' in headers and any('Running Bal' in h for h in headers)):
                        return 'BOFA_CHECKING'
            except (IndexError, AttributeError):
                pass
        
        # Check for BOFA Credit or AMEX Credit pattern
        # Both have headers on row 1 with 5 columns
        if len(rows) >= 1:
            try:
                row_1_data = rows[0]
                if len(row_1_data) == 5:
                    headers = [h.strip().lstrip('\ufeff') for h in row_1_data]  # Handle BOM
                    
                    # Check for BOFA Credit pattern
                    if ('Posted Date' in headers and 'Reference Number' in headers and 
                        'Payee' in headers and 'Address' in headers and 'Amount' in headers):
                        return 'BOFA_CREDIT'
                    
                    # Check for AMEX Credit pattern
                    elif ('Date' in headers and 'Description' in headers and 
                          'Card Member' in headers and 'Account #' in headers and 'Amount' in headers):
                        return 'AMEX_CREDIT'
            except (IndexError, AttributeError):
                pass
        
        # Additional check for AMEX files that might have column count issues
        # Look for AMEX-specific patterns in the data
        if len(rows) >= 2:
            try:
                row_1_data = rows[0]
                if len(row_1_data) >= 4:  # Be more lenient with column count
                    headers = [h.strip().lstrip('\ufeff') for h in row_1_data]  # Handle BOM
                    
                    # Check for AMEX Credit pattern with flexible column count
                    if ('Date' in headers and 'Description' in headers and 
                        'Card Member' in headers and any('Account' in h for h in headers)):
                        return 'AMEX_CREDIT'
            except (IndexError, AttributeError):
                pass
        
        return 'UNKNOWN'
        
    except Exception as e:
        print(f"  ❌ Error analyzing file {file_path}: {str(e)}")
        return 'UNKNOWN'

def classify_and_copy_files(base_dir=None):
    """
    Main function to classify all CSV files in input directory and copy to working directory.
    """
    # Set up directories
    if base_dir is None:
        base_dir = Path('/mnt/hgfs/VM_SHARE/Cursor_Projects/unified_ui/capricorn/backend/app/services/banking/data')
    else:
        base_dir = Path(base_dir)
    
    input_dir = base_dir / 'input'
    working_dir = base_dir / 'working'
    
    # Create input directory if it doesn't exist
    input_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean working directory first (ensure fresh start)
    if working_dir.exists():
        print("🗑️  Cleaning working directory for fresh start...")
        shutil.rmtree(working_dir)
    
    # Create working directory
    working_dir.mkdir(parents=True, exist_ok=True)
    
    # Stats tracking
    stats = {
        'BOFA_CHECKING': 0,
        'BOFA_CREDIT': 0,
        'AMEX_CREDIT': 0,
        'UNKNOWN': 0
    }
    
    print("🔍 Starting intelligent file classification (Enhanced Version)...")
    print(f"📁 Input directory: {input_dir}")
    print(f"📁 Working directory: {working_dir}")
    print("-" * 60)
    
    # Process each CSV file
    for file_path in input_dir.glob('*.csv'):
        if file_path.is_file():
            print(f"📄 Analyzing: {file_path.name}")
            
            # Classify the file
            file_type = analyze_csv_structure(file_path)
            stats[file_type] += 1
            
            # Generate new filename with prefix
            if file_type != 'UNKNOWN':
                new_filename = f"{file_type}_{file_path.name}"
                destination = working_dir / new_filename
                
                # Copy file to working directory using basic file operations
                with open(file_path, 'r', encoding='utf-8') as src:
                    with open(destination, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                print(f"✅ Classified as: {file_type}")
                print(f"📋 Copied to: {new_filename}")
            else:
                print(f"❌ Could not classify file type")
            
            print("-" * 40)
    
    # Print summary statistics
    print("\n📊 CLASSIFICATION SUMMARY")
    print("=" * 60)
    total_files = sum(stats.values())
    for file_type, count in stats.items():
        percentage = (count / total_files * 100) if total_files > 0 else 0
        print(f"{file_type:15}: {count:2d} files ({percentage:5.1f}%)")
    
    print(f"\nTotal files processed: {total_files}")
    print(f"Successfully classified: {total_files - stats['UNKNOWN']}")
    
    # List files in working directory
    print("\n📁 FILES IN WORKING DIRECTORY:")
    print("-" * 40)
    working_files = sorted(working_dir.glob('*.csv'))
    for f in working_files:
        print(f"  {f.name}")
    
    return stats

if __name__ == "__main__":
    try:
        stats = classify_and_copy_files()
        print(f"\n🎉 Classification complete! Check the working directory for results.")
    except Exception as e:
        print(f"❌ Error during classification: {str(e)}") 