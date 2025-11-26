#!/usr/bin/env python3
"""
Intelligent Transaction Tagger
Uses existing database mappings + pattern matching + rules to auto-tag transactions
"""

import csv
import os
import re
from collections import defaultdict
from difflib import SequenceMatcher

class IntelligentTagger:
    def __init__(self):
        # Exact mappings from manual tagging work
        self.exact_mappings = get_exact_mappings()
        
        # Pattern-based mappings (regex patterns -> tag)
        self.pattern_mappings = get_pattern_mappings()
        
        # Tag statistics
        self.exact_matches = 0
        self.pattern_matches = 0  
        self.untagged = 0
        self.filtered_out = 0
        
    def similarity(self, a, b):
        """Calculate similarity between two strings"""
        return SequenceMatcher(None, a, b).ratio()
    
    def find_similar_mapping(self, description, threshold=0.8):
        """Find similar description in exact mappings"""
        for mapped_desc, tag in self.exact_mappings.items():
            if self.similarity(description, mapped_desc) >= threshold:
                return tag
        return None
    
    def should_filter_transaction(self, description):
        """Check if transaction should be filtered out completely"""
        # Rule: Remove all Bank of America Credit Card Bill Payment transactions
        if "Bank of America Credit Card Bill Payment" in description:
            return True
        return False
        
    def tag_transaction(self, description, amount=None):
        """Tag a single transaction description with amount-based rules"""
        # 1. Try exact match first
        if description in self.exact_mappings:
            self.exact_matches += 1
            return self.exact_mappings[description]
        
        # 2. Try similarity matching
        similar_tag = self.find_similar_mapping(description)
        if similar_tag:
            self.exact_matches += 1
            return similar_tag
        
        # 3. Amount-based rules
        if amount is not None:
            try:
                amount_float = float(amount)
                # Rule: Apple.com over $100 is IT Equipment
                if "APPLE.COM" in description.upper() and abs(amount_float) > 100:
                    self.pattern_matches += 1
                    return "IT Equipment"
            except (ValueError, TypeError):
                pass
            
        # 4. Try pattern matching
        for pattern, tag in self.pattern_mappings:
            if re.search(pattern, description, re.IGNORECASE):
                self.pattern_matches += 1
                return tag
                
        # 5. No match found
        self.untagged += 1
        return ''
    
    def process_master_file(self, input_file='output/Master_Transactions.csv', output_file='output/Master_Transactions_Tagged.csv'):
        """Process the master file and add tags"""
        # Delete existing Tagged file to ensure fresh rebuild
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"🗑️  Deleted existing {output_file} for fresh rebuild")
        
        tagged_transactions = []
        
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                description = row['Description']
                amount = row.get('Amount', '')
                
                # Check if transaction should be filtered out
                if self.should_filter_transaction(description):
                    self.filtered_out += 1
                    continue  # Skip this transaction entirely
                
                # Only retag if currently empty
                if not row['Tag'] or len(row['Tag'].strip()) == 0:
                    tag = self.tag_transaction(description, amount)
                    row['Tag'] = tag
                else:
                    # Keep existing tag, but count as exact match
                    self.exact_matches += 1
                tagged_transactions.append(row)
        
        # Write tagged results
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Date', 'Description', 'Amount', 'Spender', 'Source', 'Type', 'Tag', 'Duplicate']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(tagged_transactions)
            
        return len(tagged_transactions)
        
    def print_statistics(self):
        """Print tagging statistics"""
        total = self.exact_matches + self.pattern_matches + self.untagged
        print(f"\n📊 TAGGING RESULTS:")
        print(f"🚫 Filtered Out: {self.filtered_out}")
        print(f"✅ Exact/Similar/Existing: {self.exact_matches}")
        print(f"🎯 New Pattern Matches: {self.pattern_matches}")  
        print(f"❓ Still Untagged: {self.untagged}")
        print(f"📈 Total Processed: {total}")
        
        newly_tagged = self.pattern_matches
        previously_untagged = self.pattern_matches + self.untagged
        if previously_untagged > 0:
            improvement_rate = (newly_tagged / previously_untagged) * 100
            print(f"🚀 New Tagging Success Rate: {improvement_rate:.1f}% of previously untagged")

def get_exact_mappings():
    """Exact description-to-tag mappings from manual tagging work."""
    return {
        # Vape
        "NEW CITY SMOKE SHOP CORP NEW YORK NY": "Vape",
        "JOMASHOP.COM 877-834-1434 NY": "Vape",
        "JOMASHOP.COM 0558   BROOKLYN            NY": "Vape",
        
        # Travel
        "DELTA AIR LINES     ATLANTA": "Travel",
        "DELTA AIR LINES": "Travel",
        "CLEAR *clearme.com clearme.com NY": "Travel",
        "AMTRAK INT          WASHINGTON          DC": "Travel",
        
        # Train
        "MNR ETIX TICKET     877-690-5116        NY": "Train",
        
        # Stereo
        "DENON.COM DENON.COM CARLSBAD            CA": "Stereo",
        
        # Shooting
        "NATIONAL SKEET SHOOT210-688-3371        TX": "Shooting",
        "ELK COUNTY AMMO AND ARMS 866-4350666 PA": "Shooting",
        "NIC*NYSFIREARMSAMMO EGOV.COM NJ": "Shooting",
        "FIELDANDSUPPLY      NEW YORK            NY": "Shooting",
        "THE ORVIS CO #073 MILLBROOK NY": "Shooting",
        "ORVIS SANDANONA 73  MILLBROOK           NY": "Shooting",
        "THE ORVIS COMPANY INSUNDERLAND          VT": "Shooting",
        "ORVIS SANDANONA 73  MILLBROOK           NY": "Shooting",
        "SKB SHOTGUNS ECOMM 402-3304492 NE": "Shooting",
        
        # Restaurants
        "LOMBARDOS           DOBBS FERRY         NY": "Restaurant",
        "CHIPOTLE 1879 NEW YORK NY": "Restaurant",
        "Muji - Fifth Ave 000NEW YORK            NY": "Restaurant",
        "BT*FOOD AT*BUDDHA ASKANSAS CITY         KS": "Restaurant",
        "HOMESTYLE SPRAIN LAKYONKERS             NY": "Restaurant",
        "HOMESTYLE SPRAIN LAKE YONKERS NY": "Restaurant",
        "CS *STARBUCKS GC    877-850-1977        ME": "Restaurant",
        "MCDONALD'S F7588 MOHEGAN LAKE NY": "Restaurant",
        "LOI ESTIATORIO 65000NEW YORK            NY": "Restaurant",
        "EL VEZ NY           NEW YORK            NY": "Restaurant",
        "F&B 16273246005     Hopewell Junction   NY": "Restaurant",
        "DAILYPROVISIONS     NEW YORK            NY": "Restaurant",
        "FOOD ATBUDDHA ASIAN B MENUFY.COM KS": "Restaurant",
        "FOOD AT*BUDDHA ASIAN B MENUFY.COM KS": "Restaurant",
        "BABETTE'S KITCHEN 00MILLBROOK           NY": "Restaurant",
        "Muji - SOHO 00000006NEW YORK            NY": "Restaurant",
        "BENVENUTOS II MOHEGAN LAKE NY": "Restaurant",
        "MILLBROOKDELI MILLBROOK NY": "Restaurant",
        "LEFTERIS GYRO TARRYTOWN NY": "Restaurant",
        "BURGER KING #2106 NEW CASTLE DE": "Restaurant",
        "CHICK-FIL-A #05288 NEW CASTLE DE": "Restaurant",
        "BLT PRIME MIAMI     DORAL               FL": "Restaurant",
        "CIPRIANI MIAMI DOWNTMIAMI               FL": "Restaurant",
        "LE GAMIN            SHARON              CT": "Restaurant",
        "MCDONALD'S F4332 FRANKLIN NJ": "Restaurant",
        "TST* SERAFINA TRATTOFORT LAUDERDALE     FL": "Restaurant",
        "TST* CASA SENSEI 300FORT LAUDERDA       FL": "Restaurant",
        "TST* THE 19TH HOLE 0PLANTATION          FL": "Restaurant",
        "TST* KYMA - FLATIRONNEW YORK            NY": "Restaurant",
        "TST*AKAI LOUNGE - SCARSD Scarsdale NY": "Restaurant",
        "OWENS PUB HAMBURG NJ": "Restaurant",
        "TST* CENTENNIAL GRILLE ROCARMEL NY": "Restaurant",
        "WOODS TAVERN OSSINING NY": "Restaurant",
        
        # Rent
        "AGI*RENTERS/CONDO INS 800-370-1990 FL": "Rent",
        
        # Office Supplies
        "CONTAINERSTOREYONKERYONKERS             NY": "Office Supplies",
        "CONTAINERSTOREYONKERS YONKERS NY": "Office Supplies",
        "LOWES #03305* YONKERS NY": "Office Supplies",
        "E-COWHIDES HTTPSECOWHIDEFL": "Office Supplies",
        "MAXGOGO MAXYOYOHOME.CDE": "Office Supplies",
        
        # Museums
        "MMA ADMISSIONS      NEW YORK            NY": "Museums",
        "FH* LILYMOORE FARM HTTPSWWW.LILYNY": "Museums",
        "HISTORIC HUDSON VALLTARRYTOWN           NY": "Museums",
        "HUDSON RIVER MUSEUM YONKERS             NY": "Museums",
        "VIZCAYA MUSEUM AND GMIAMI               FL": "Museums",
        
        # Mail/FedEx/UPS
        "FEDEX OFFICE        NEW YORK            NY": "Mail/FedEx/UPS",
        "FEDEX Office 5696 15NEW YORK            NY": "Mail/FedEx/UPS",
        "THE UPS STORE 1363 0BRONXVILLE          NY": "Mail/FedEx/UPS",
        "THE UPS STORE       ARDSLEY             NY": "Mail/FedEx/UPS",
        "THE UPS STORE 5446 0YONKERS             NY": "Mail/FedEx/UPS",
        
        # Magazines
        "FABER NEWS # 1378 00WILMINGTON          DE": "Magazines",
        "GOOP, INC           SANTA MONICA        CA": "Magazines",
        "CASA ICONIC MAGAZINENEW YORK            NY": "Magazines",
        "HARPERS BAZAAR MAGAZCHARLOTTE           NC": "Magazines",
        "TOWN & COUNTRY MAGAZCHARLOTTE           NC": "Magazines",
        
        # IT Subscription
        "JOHNDIGWEED-MIXCLOUD LONDON": "IT Subscription",
        "DNH*GODADDY.COM 480-505-8855 AZ": "IT Subscription",
        "EVERNOTE            REDWOOD CITY        CA": "IT Subscription",
        "CURSOR, AI POWERED INEW YORK            NY": "IT Subscription",
        "ZEROHEDGE.COM WWW.ZEROHEDGETX": "IT Subscription",
        "THE DAILY WIRE 818-699-9948 TN": "IT Subscription",
        "ZAPIER.COM/CHARGE   SAN FRANCISCO       CA": "IT Subscription",
        
        # IT Equipment
        "APPLE.COM/US 800-676-2775 CA": "IT Equipment",
        "ALMATECHNOLOGY.NET  EMERYVILLE          CA": "IT Equipment",
        "DRI*Logi Store MINNETONKA MN": "IT Equipment",
        "NICOLA MEYER* O #332GROSSETO            IT": "IT Equipment",
        "PC SERVER AND PARTS NEW HUDSON          MI": "IT Equipment",
        "PC SERVER AND PARTS PCSERVERANDPAMI": "IT Equipment",
        "SOHNNE INC          4159157177          DE": "IT Equipment",
        "WPY*Sohnne Inc 833-900-0017 DE": "IT Equipment",
        
        # Insurance
        "JEWELERS-MUTUAL-PMNT 800-558-6411 WI": "Insurance",
        
        # Hotels & AirBNB
        "JEFAST PELICAN GRAND I PELICANBEACH.FL": "Hotels & AirBNB",
        "PELICAN GRAND BEACH FORT LAUDERDALE     FL": "Hotels & AirBNB",
        "W Miami             Miami               FL": "Hotels & AirBNB",
        
        # Healthcare
        "APOSTROPHE          OAKLAND             CA": "Healthcare",
        "APOSTROPHE          SAN FRANCISCO       CA": "Healthcare",
        "LINE OF SIGHT       New York            NY": "Healthcare",
        "BT*NATURAL SKINCARE WHEAT RIDGE         CO": "Healthcare",
        "EYECONIC            (916)851-5000       CA": "Healthcare",
        "HASTINGS NAILS & FOOT HASTINGS ON HNY": "Healthcare",
        "HASTINGS NAILS & FOOHASTINGS ON H       NY": "Healthcare",
        "BEAUTIFUL SMILE DENTNEW YORK            NY": "Healthcare",
        "HARRYS 888-212-6855 HTTPSWWW.HARRNY": "Healthcare",
        "DUANE READE #21350 0NEW YORK            NY": "Healthcare",
        "NATURALCYCLES NORDICSTOCKHOLM           SE": "Healthcare",
        "CLEARSTEM SKINCAR   LA JOLLA            CA": "Healthcare",
        "GRAMERCY GYNECOLOGY NEW YORK            NY": "Healthcare",
        "FASHION NAIL SPA 4 0NEW YORK            NY": "Healthcare",
        "NORTHWELL PHYS. PARTNERS NEW HYDE PARKNY": "Healthcare",
        "TRUE DERMATOLOGY    NEW YORK            NY": "Healthcare",
        "www.cvs.com 800-746-7287 RI": "Healthcare",
        "www.cvs.com 800-7467287 RI": "Healthcare",
        "SP CLEARSTEM SKINCARLA JOLLA            CA": "Healthcare",
        "SP OMNILUX          NAPA                CA": "Healthcare",
        "SP OLIVE AND JUNE   LOS ANGELES         CA": "Healthcare",
        "TRANQUILITY SPA 6892SCARSDALE           NY": "Healthcare",
        "ZENOTIUSA_POS*EUROPEYONKERS             NY": "Healthcare",
        "PLAZA M SPA HUDSON YNew York            NY": "Healthcare",
        "Q SMILES FAMILY DENTISTRYSLEEPY HOLLOWNY": "Healthcare",
        
        # Golf
        "DICK'S SPORTING GOODCORAOPOLIS          PA": "Golf",
        "Callaway Preowned 800-8266174 TX": "Golf",
        "HERITAGE CLUB AT BETHP 516-9278380 NY": "Golf",
        "HERITAGE CLUB AT BETHP FARMINGDALE NY": "Golf",
        "TST* HERITAGE CLUB AT BETFARMINGDALE NY": "Golf",
        "THE LINKS AT UNION VAL LAGRANGEVILLENY": "Golf",
        "TRUMP NATIONAL HUDSON VA HOPEWELL JUNCNY": "Golf",
        "TRUMP DORAL GAME ROOMIAMI               FL": "Golf",
        
        # Gifts
        "BT*SHUTTERFLY, INC. REDWOOD CITY        CA": "Gifts",
        "BETHANYFLORIST.COM  FRANKFORD           DE": "Gifts",
        "CRUTCHFIELD         CHARLOTTESVILLE     VA": "Gifts",
        "TST* DIFEBOS BETHANYBETHANY BEACH       DE": "Gifts",
        "ODE A LA ROSE LLC 51NEW YORK            NY": "Gifts",
        
        # Gas
        "BP#6640908COUNTRY CLUB S YONKERS NY": "Gas",
        "HASTINGS TIRE HASTINGS ON HNY": "Gas",
        "GULF OIL 92062818 VERBANK NY": "Gas",
        "DAK ENTERPRISES HASTINGS-ON-HNY": "Gas",
        "GULF OIL 92060746 STAMFORD CT": "Gas",
        "ROYAL FARMS #176 OCEAN VIEW DE": "Gas",
        "SHELL SERVICE STATIOYONKERS             NY": "Gas",
        "SHELL SERVICE STATIOCORTLANDT MANOR     NY": "Gas",
        
        # Food
        "D'ARTAGNAN - ECOMM 800-327-8426 NJ": "Food",
        "LUKE'S LOBSTER - GCT NEW YORK NY": "Food",
        "KEYFOOD #1888 000001YONKERS             NY": "Food",
        "HEAT HOT SAUCE HTTPSHEATHOTSCA": "Food",
        "SP HEAT HOT SAUCE HEATHOTSAUCE.CA": "Food",
        "NESPRESSO": "Food",
        
        # Fashion Design
        "BT*SPOONFLOWER      DURHAM              NC": "Fashion Design",
        "MOOD DESIGNER FABRICNEW YORK            NY": "Fashion Design",
        "MEGAN NIELSEN       WEMBLEY             AU": "Fashion Design",
        "M&S SCHMALBERG INC 0NEW YORK            NY": "Fashion Design",
        "JP                  New York            NY": "Fashion Design",
        "C & C BUTTON        NEW YORK            NY": "Fashion Design",
        "BT*SIMPLICITY.COM COMIDWAY              GA": "Fashion Design",
        "EAST COAST TRIMMING New York            NY": "Fashion Design",
        "MENDEL GOLDBERG FABRNewYork            NY": "Fashion Design",
        "DECORATORSB         2127226449          NY": "Fashion Design",
        "CURIO* THYMES       MINNEAPOLIS         MN": "Fashion Design",
        "MATHILDE KIEN       SOUTH YARRA         AU": "Fashion Design",
        "AMZ*Leprestore, AIAJ buysafe@lepreFL": "Fashion Design",
        "PY *FABER - 1378 WILWILMINGTON          DE": "Fashion Design",
        "PURL SOHO 4616820015NEW YORK            NY": "Fashion Design",
        "SIL THREAD 145000000NEW YORK            NY": "Fashion Design",
        "PREVIEW TEXTILES    NEW YORK            NY": "Fashion Design",
        "SP LYCETTE DESIGNS  HYPOLUXO            FL": "Fashion Design",
        "SP CRISWOODSEWS.COM BURIEN              WA": "Fashion Design",
        "SP HELENSCLOSETPATTECOURTENAY           CA": "Fashion Design",
        "SP WAKUSA           CORAL GABLES        FL": "Fashion Design",
        "WUNDERLABEL*WUNDERLAW√úRZBURG            DE": "Fashion Design",
        "SP KC NEEDLEPOINT LLKANSAS CITY         MO": "Fashion Design",
        "SP TWININGS UK      ANDOVER             HA": "Fashion Design",
        "SP VIOLETTEFR-STORE BROOKLYN            NY": "Fashion Design",
        "VIOLETTEFR-STORE    BROOKLYN            NY": "Fashion Design",
        "SP DUCKADILLY       ANN ARBOR           MI": "Fashion Design",
        "REBECCADEVANEY.IE   SAINT MALO": "Fashion Design",
        "SP SKIMS            CULVER CITY         CA": "Fashion Design",
        "SP CLOSETCOREPATTERNMONTREAL": "Fashion Design",
        "SP REMI             SAN FRANCISCO       CA": "Fashion Design",
        "PP *CRAFTSY         855-706-3535        MN": "Fashion Design",
        "VIKISEWS            HALLANDALE BEACH    FL": "Fashion Design",
        "SEWAHOLIC           VANCOUVER           CA": "Fashion Design",
        "SP STIL CLASSICS INCVANCOUVER           CA": "Fashion Design",
        "SUSAN KHALJE COUT   COCKEYSVILLE        MD": "Fashion Design",
        "SP SUSAN KHALJE COUTCOCKEYSVILLE        MD": "Fashion Design",
        "SHAKESPEARE AND     PARIS": "Fashion Design",
        "THREADS             866-288-4241        IA": "Fashion Design",
        "ROWDY POPPY         Denver              CO": "Fashion Design",
        "SP BRITEX FABRICS   SAN FRANCISCO       CA": "Fashion Design",
        "SP ALEXIS SMART FLOWTWENTYNINE PALMS    CA": "Fashion Design",
        "UTRECHTART8004471892NEW YORK            NY": "Fashion Design",
        "PDF Plotting        Richmond            VA": "Fashion Design",
        "WWW.MILANOTE.COM    MELBOURNE           AU": "Fashion Design",
        
        # Education
        "AT *THE JEWISH MUSEUNEW YORK            NY": "Education",
        "AB* ABEBOOKS.CO KCKZSEATTLE             WA": "Education",
        "AB* ABEBOOKS.CO KCZLVICTORIA            CA": "Education",
        "BARD GRADUATE CENTERNewYork            NY": "Education",
        "B&J FABRICS         New York            NY": "Education",
        "LAKESHORE LEARNING MCARSON              CA": "Education",
        "CODECADEMY HTTPSWWW.CODENY": "Education",
        "AT * FRICK COLLECTIONEW YORK            NY": "Education",
        
        # EBay patterns
        "EBAY O*20-10999-8945SAN JOSE            CA": "EBay",
        
        # Clothes
        "DECKERS*UGG         888-432-8530        CA": "Clothes",
        "FOOTWEAR-DECKERSCORP800-367-8382        CA": "Clothes",
        "ETSY, INC.          BROOKLYN            NY": "Clothes",
        "BROOKS ANN BESPOKE LCEDAR GROVE         NC": "Clothes",
        "10670 FIFTH AVENUE NNEW YORK            NY": "Clothes",
        "MACYS .COM 800-289-6229 OH": "Clothes",
        "LLBEAN-DIRECT 084870207-8654761         ME": "Clothes",
        "GAP ONLINE 084870005GROVEPORT           OH": "Clothes",
        "KAT THE LABEL USA   BRIGHTON            AU": "Clothes",
        "Brooks Brothers LYNDHURST NJ": "Clothes",
        "Charles Tyrwhitt, Inc. New York NY": "Clothes",
        "Charles Tyrwhitt, Inc. 208-7351034 NY": "Clothes",
        "J CREW.COM          https://www.jcrew.coNY": "Clothes",
        "ANTHROPOLOGIE INC. 0WHITE PLAINS        NY": "Clothes",
        "NORDSTROM           WHITE PLAINS        NY": "Clothes",
        "LZEDONIA ONLINE     855-564-2351        NY": "Clothes",
        "ADIDAS US ONLINE STORE 800-9829337 OR": "Clothes",
        "BT*ARTIFACTUPRISING.DENVER              CO": "Clothes",
        "LANDSEND.COM        800-332-4700        WI": "Clothes",
        "GAP US 780          SCARSDALE           NY": "Clothes",
        "BANANAREPUBLIC US 8115 SCARSDALE NY": "Clothes",
        "GDP=Dressed History Brooklyn            NY": "Clothes",
        "MANGOUS             NEW YORK            NY": "Clothes",
        "BANANA REPUBLIC ON-LINE 888-2778959 OH": "Clothes",
        "REFORMATION         VERNON              CA": "Clothes",
        "SP PRINTFRESH       PHILADELPHIA        PA": "Clothes",
        "SP VB BEAUTY        NEW YORK            NY": "Clothes",
        "SP BABYLIST         OAKLAND             CA": "Clothes",
        "SP THE LINE         VANCOUVER           CA": "Clothes",
        "SP FOR WELLNESS FORWELLNESS.CNJ": "Clothes",
        "ZARA USA            NEW YORK            NY": "Clothes",
        "ZARA USA INC.       NEW YORK            NY": "Clothes",
        "ZARA USA INC Zara USNEW YORK            NY": "Clothes",
        "UNIQLO USA LLC      NEW YORK            NY": "Clothes",
        "WARBY PARKER        NEW YORK CITY       NY": "Clothes",
        
        # Car Tickets
        "CITYOFYONKERSPARKI 914-377-6631 NY": "Car Tickets",
        "ALLPAID*Village of Hastin888-6047888 NY": "Car Tickets",
        "KENT TN CT DOUCHKOFF KENT LAKES NY": "Car Tickets",
        "VILLAGE OF TARRYTOWN 914-631-7873 NY": "Car Tickets",
        
        # CAR Repair
        "BMW OF WESTCHESTER WHITE PLAINS NY": "CAR Repair",
        "VALENTINO SHOE REPAIR IN DOBBS FERRY NY": "CAR Repair",
        "RAY CATENA BMW OF WEWHITE PLAINS        NY": "CAR Repair",
        "RUBICON RA TARRYTOWN LLC TARRYTOWN NY": "CAR Repair",
        "ROCKWOOD AND PERRY HASTINGS HDSNNY": "CAR Repair",
        
        # BofA Deposit
        "BKOFAMERICA MOBILE 01/25 XXXXX51013 DEPOSIT *MOBILE NY": "BofA Deposit",
        "BKOFAMERICA MOBILE 12/08 XXXXX62410 DEPOSIT *MOBILE NY": "BofA Deposit",
        
        # Activities
        "NEW YORK CITY BALLETNEW YORK            NY": "Activities",
        
        # TAX Preparation
        "REID TAX & ADVISORY 516-802-0100 NY": "TAX Preparation",
        "REID TAX ADVISORY SERVICE317-5025147 NY": "TAX Preparation",
        "NYS DTF PIT DES:Tax Paymnt ID:XXXXXXXXXX26243 INDN:PLXXXXX17478 CO ID:NXXXXX3200 PPD": "TAX Preparation",
        
        # Additional Amazon patterns  
        "HTTPSAMAZON.CWA": "Amazon Prime",
        "WWW.AMAZON.COWA": "Amazon Prime",
        "AMAZON.COM": "Amazon Prime",
        "AMZN MKTP": "Amazon Prime",
        
        # Additional mappings  
        "Trader Joe": "Food",
        "Amzn.com": "Amazon Prime",
        "AUTOPAY PAYMENT - THANK YOU": "CC Payment",
        "Nespresso": "Food",
        "USPS": "Mail/FedEx/UPS"
    }

def get_pattern_mappings():
    """Regex patterns to match transaction descriptions."""
    return [
        # Enhanced Amazon patterns (FIXED to include AMAZON MKTPL*)
        (r'AMAZON\.COM\*.*|AMAZON MKTPL\*.*|AMZN MKTP.*|AMAZON RET.*|AMAZON PRIME.*|AMAZON MAR.*|AMAZON RETA.*|AMAZON MARK.*|WWW\.AMAZON.*|HTTPSAMAZON\.CWA.*|WWW\.AMAZON\.COWA.*|Amazon\.com.*|AMAZON.*|AMZN.*', 'Amazon Prime'),
        
        # Original patterns
        (r'INCOME.*Andrew', 'INCOME Andrew'),
        (r'INCOME.*Jackie', 'INCOME Jackie'),
        (r'BofA Cashback Rewards', 'BofA Cashback Rewards'),
        (r'ATT\*.*BILL PAYMENT', 'Cell Phones ATT'),
        (r'CONED.*', 'ConEd'),
        (r'MTA\*NYCT PAYGO.*', 'Subway'),
        (r'FRESH DIRECT.*', 'Food'),
        (r'GLF\*.*|GOLF.*|PATRIOT HILLS.*', 'Golf'),
        (r'ATM .*|.*ATM.*FEE.*', 'ATM/Cash'),
        (r'GRUBHUB.*|.*CAFE.*|.*RESTAURANT.*', 'Restaurant'),
        (r'.*GAS.*|.*MOBIL.*|.*EXXON.*|.*SHELL.*', 'Gas'),
        (r'CVS.*PHARMACY.*|.*PHARMACY.*', 'Pharmacy'),
        (r'RETURN.*CREDIT.*|.*REFUND.*', 'Returns/Credits'),
        (r'.*FEE.*|.*CHARGE.*', 'Bank Fees'),
        
        # New patterns from manual tagging
        (r'NEW CITY SMOKE SHOP.*|JOMASHOP\.COM.*', 'Vape'),
        (r'DELTA AIR LINES.*|CLEAR \*clearme\.com.*|AMTRAK INT.*', 'Travel'),
        (r'MNR ETIX TICKET.*', 'Train'),
        (r'DENON\.COM.*', 'Stereo'),
        (r'NATIONAL SKEET.*|ELK COUNTY AMMO.*|NIC\*NYSFIREARMSAMMO.*|FIELDANDSUPPLY.*|SKB SHOTGUNS.*', 'Shooting'),
        (r'AGI\*RENTERS/CONDO INS.*', 'Rent'),
        (r'CONTAINERSTOREY.*|LOWES #.*|E-COWHIDES.*|MAXGOGO.*', 'Office Supplies'),
        (r'MMA ADMISSIONS.*|FH\* LILYMOORE FARM.*|HISTORIC HUDSON.*|HUDSON RIVER MUSEUM.*|VIZCAYA MUSEUM.*', 'Museums'),
        (r'FEDEX OFFICE.*|THE UPS STORE.*', 'Mail/FedEx/UPS'),
        (r'FABER NEWS.*|GOOP, INC.*|CASA ICONIC.*|HARPERS BAZAAR.*|TOWN & COUNTRY.*', 'Magazines'),
        (r'JOHNDIGWEED-MIXCLOUD.*|DNH\*GODADDY\.COM.*|EVERNOTE.*|CURSOR.*|ZEROHEDGE\.COM.*|THE DAILY WIRE.*|ZAPIER\.COM.*|.*LINKEDIN.*|.*MOTV.*|.*PLAYSTATION.*', 'IT Subscription'),
        (r'APPLE\.COM/US.*|ALMATECHNOLOGY.*|DRI\*Logi.*|NICOLA MEYER.*|PC SERVER AND PARTS.*|SOHNNE INC.*|WPY\*Sohnne.*', 'IT Equipment'),
        (r'JEWELERS-MUTUAL-PMNT.*', 'Insurance'),
        (r'JEFAST PELICAN.*|PELICAN GRAND BEACH.*|W Miami.*', 'Hotels & AirBNB'),
        (r'APOSTROPHE.*|LINE OF SIGHT.*|EYECONIC.*|BEAUTIFUL SMILE.*|HASTINGS NAILS.*|HARRYS.*|DUANE READE.*|NATURALCYCLES.*|CLEARSTEM.*|GRAMERCY GYNECOLOGY.*|FASHION NAIL SPA.*|NORTHWELL PHYS.*|TRUE DERMATOLOGY.*|www\.cvs\.com.*|SP CLEARSTEM.*|SP OMNILUX.*|SP OLIVE AND JUNE.*|TRANQUILITY SPA.*|ZENOTIUSA_POS.*|PLAZA M SPA.*|Q SMILES FAMILY.*', 'Healthcare'),
        (r'DICK\'S SPORTING.*|Callaway Preowned.*|HERITAGE CLUB.*|THE LINKS AT UNION.*|TRUMP NATIONAL.*|TRUMP DORAL.*', 'Golf'),
        (r'BT\*SHUTTERFLY.*|BETHANYFLORIST.*|CRUTCHFIELD.*|TST\* DIFEBOS.*|ODE A LA ROSE.*', 'Gifts'),
        (r'BP#.*|HASTINGS TIRE.*|GULF OIL.*|DAK ENTERPRISES.*|ROYAL FARMS.*|SHELL SERVICE.*', 'Gas'),
        (r'D\'ARTAGNAN.*|LUKE\'S LOBSTER.*|KEYFOOD.*|HEAT HOT SAUCE.*|SP HEAT HOT SAUCE.*|.*NESPRESSO.*', 'Food'),
        (r'BT\*SPOONFLOWER.*|MOOD DESIGNER.*|MEGAN NIELSEN.*|M&S SCHMALBERG.*|JP.*New York.*|C & C BUTTON.*|BT\*SIMPLICITY.*|EAST COAST TRIMMING.*|MENDEL GOLDBERG.*|DECORATORSB.*|CURIO\* THYMES.*|MATHILDE KIEN.*|AMZ\*Leprestore.*|PY \*FABER.*|PURL SOHO.*|SIL THREAD.*|PREVIEW TEXTILES.*|SP LYCETTE.*|SP CRISWOODSEWS.*|SP HELENSCLOSET.*|SP WAKUSA.*|WUNDERLABEL.*|SP KC NEEDLEPOINT.*|SP TWININGS.*|SP VIOLETTEFR.*|VIOLETTEFR-STORE.*|SP DUCKADILLY.*|REBECCADEVANEY.*|SP SKIMS.*|SP CLOSETCORE.*|SP REMI.*|PP \*CRAFTSY.*|VIKISEWS.*|SEWAHOLIC.*|SP STIL CLASSICS.*|SUSAN KHALJE.*|SP SUSAN KHALJE.*|SHAKESPEARE AND.*|THREADS.*8662.*|ROWDY POPPY.*|SP BRITEX.*|SP ALEXIS SMART.*|UTRECHTART.*|PDF Plotting.*|WWW\.MILANOTE\.COM.*', 'Fashion Design'),
        (r'AT \*THE JEWISH.*|AB\* ABEBOOKS.*|BARD GRADUATE.*|B&J FABRICS.*|LAKESHORE LE.*|CODECADEMY.*|AT \* FRICK.*', 'Education'),
        (r'EBAY O\*.*|eBay O\*.*', 'EBay'),
        (r'DECKERS\*UGG.*|FOOTWEAR-DECKERS.*|ETSY, INC.*|BROOKS ANN.*|10670 FIFTH.*|MACYS \.COM.*|LLBEAN-DIRECT.*|GAP ONLINE.*|KAT THE LABEL.*|Brooks Brothers.*|Charles Tyrwhitt.*|J CREW\.COM.*|ANTHROPOLOGIE.*|NORDSTROM.*|LZEDONIA.*|ADIDAS US.*|BT\*ARTIFACT.*|LANDSEND\.COM.*|GAP US.*|BANANAREPUBLIC.*|GDP=Dressed.*|MANGOUS.*|BANANA REPUBLIC.*|REFORMATION.*|SP PRINTFRESH.*|SP VB BEAUTY.*|SP BABYLIST.*|SP THE LINE.*|SP FOR WELLNESS.*|ZARA USA.*|UNIQLO USA.*|WARBY PARKER.*', 'Clothes'),
        (r'CITYOFYONKERS.*|ALLPAID\*Village.*|KENT TN CT.*|VILLAGE OF TARRYTOWN.*', 'Car Tickets'),
        (r'BMW OF WESTCHESTER.*|VALENTINO SHOE.*|RAY CATENA BMW.*|RUBICON RA.*|ROCKWOOD AND PERRY.*', 'CAR Repair'),
        (r'BKOFAMERICA MOBILE.*DEPOSIT.*', 'BofA Deposit'),
        (r'NEW YORK CITY BALLET.*', 'Activities'),
        (r'REID TAX.*|NYS DTF PIT.*Tax.*', 'TAX Preparation'),
        
        # Restaurant patterns  
        (r'LOMBARDOS.*|CHIPOTLE.*|Muji - Fifth Ave.*|BT\*FOOD AT\*BUDDHA.*|HOMESTYLE SPRAIN.*|CS \*STARBUCKS.*|MCDONALD\'S.*|LOI ESTIATORIO.*|EL VEZ NY.*|F&B.*|DAILYPROVISIONS.*|FOOD.*BUDDHA.*|BABETTE\'S KITCHEN.*|Muji - SOHO.*|BENVENUTOS.*|MILLBROOKDELI.*|LEFTERIS GYRO.*|BURGER KING.*|CHICK-FIL-A.*|BLT PRIME.*|CIPRIANI MIAMI.*|LE GAMIN.*|TST\* SERAFINA.*|TST\* CASA SENSEI.*|TST\* THE 19TH HOLE.*|TST\* KYMA.*|TST\*AKAI LOUNGE.*|OWENS PUB.*|TST\* CENTENNIAL.*|WOODS TAVERN.*', 'Restaurant'),
        
        # Wine patterns
        (r'.*WINE.*|.*SPIRITS.*|.*LIQUOR.*', 'Wine'),
        
        # Verizon patterns  
        (r'VERIZON.*|.*VERIZON.*', 'Cell Phones'),
        
        # === NEW PATTERNS FROM UNTAGGED ANALYSIS ===
        
        # Streaming Services (102 transactions)
        (r'PAYPAL.*HULU.*|PAYPAL.*PEACOCK.*', 'Streaming Services'),
        (r'NETFLIX.*', 'Streaming Services'),
        (r'PRIME VIDEO.*', 'Streaming Services'),
        
        # Grocery Stores (91 transactions)
        (r'DECICCO.*SONS.*', 'Food'),
        (r'STEW LEONARDS.*', 'Food'),
        (r'WHOLEFDS.*|WHOLE FOODS.*', 'Food'),
        (r'TRADER JOE.*', 'Food'),
        
        # Financial Services (57 transactions)
        (r'BANK OF AMERICA.*CASHREWARD.*', 'BofA Cashback Rewards'),
        (r'ONLINE BANKING PAYMENT.*', 'CC Payment'),
        
        # Health/Fitness Tech (38 transactions)
        (r'OURARING.*|BT.*OURARING.*', 'Healthcare'),
        (r'TOBEMAGNETIC.*|WWW\.TOBEMAGNETIC.*', 'Healthcare'),
        
        # Transportation & ATM (27 transactions)
        (r'E-Z.*PASSNY.*', 'EZ Pass'),
        (r'.*WITHDRWL.*', 'Cash'),
        
        # Restaurants (26+ transactions)
        (r'TST\*.*', 'Restaurant'),
        (r'ENBU.*', 'Restaurant'),
        (r'STARBUCKS.*', 'Restaurant'),
        (r'EATALY.*', 'Restaurant'),
        (r'SAINT GEORGE BISTRO.*', 'Restaurant'),
        (r'YORKTOWN COACH DINER.*', 'Restaurant'),
        (r'SAUCE PIZZERIA.*', 'Restaurant'),
        (r'MILLBROOK DINER.*', 'Restaurant'),
        (r'SQ \*.*', 'Restaurant'),  # Square payment restaurants
        
        # Income/Benefits (29 transactions)
        (r'GINSBURGDEV.*', 'Rent'),
        (r'NYS DOL UI DD.*', 'INCOME Jackie'),
        
        # Shopping/Retail (additional)
        (r'BLOOMINGDALES\.COM.*', 'Clothes'),
        (r'PGA TOUR SUPERSTORE.*', 'Golf'),
        (r'PRICE POINT NY.*', 'Clothes'),
        (r'PAPERSOURCE.*', 'Office Supplies'),
        (r'WAL-MART.*', 'Food'),
        
        # Health Services (additional)
        (r'NORTHWELL HEALTH.*', 'Healthcare'),
        (r'ONE VAPOR AVE.*', 'Vape'),
        
        # VENMO transactions
        (r'VENMO.*CASHOUT.*', 'VENMO Received'),
        
        # Additional Amazon variations
        (r'AMZ\*.*', 'Amazon Prime'),
        
        # === DATABASE-LEARNED PATTERNS (65 total) ===
        # Income & Financial
        (r'BNYMELLON.*DES:DIR.*|.*PAYROLL.*Andrew.*', 'INCOME Andrew'),
        (r'CAASTLE.*PAYROLL.*|.*PAYROLL.*Jackie.*', 'INCOME Jackie'),
        (r'BOFA.*CASHBACK.*|BANK.*AMERICA.*REWARDS.*', 'BofA Cashback Rewards'),
        (r'.*FEE REVERSED.*|.*WITHDRAWL FEE REVERSED.*', 'BofA ATM Reimbursement'),
        (r'BKOFAMERICA.*DEPOSIT.*|BOFA.*DEPOSIT.*', 'BofA Deposit'),
        (r'INTEREST.*EARNED.*|DEPOSIT.*INTEREST.*', 'Interest'),
        
        # Shopping & Commerce  
        (r'EBAY.*|eBay.*', 'EBay'),
        (r'GAP.*|ZARA.*|H&M.*|CLOTHING.*|APPAREL.*', 'Clothes'),
        (r'FABRIC.*|SEWING.*|PATTERN.*|DESIGN.*', 'Fashion Design'),
        
        # Food & Dining (enhanced)
        (r'FOOD.*|GROCERY.*|MARKET.*', 'Food'),
        (r'RESTAURANT.*|CAFE.*|KITCHEN.*|GRILL.*', 'Restaurant'),
        (r'GRUBHUB.*|SEAMLESS.*|DELIVERY.*', 'Delivery'),
        (r'BNY.*CAFE.*|OFFICE.*LUNCH.*', 'Work Lunch'),
        
        # Transportation (enhanced)
        (r'MTA.*NYCT.*|SUBWAY.*', 'Subway'),
        (r'^UBER$|UBER .*', 'Uber'),
        (r'DELTA.*|AMERICAN AIRLINES.*|JETBLUE.*|CLEAR.*clearme.*', 'Travel'),
        (r'MNR.*ETIX.*|AMTRAK.*|METRO.*NORTH.*', 'Train'),
        (r'EXXON.*|MOBIL.*|SHELL.*|BP.*|GULF.*', 'Gas'),
        (r'EZ.*PASS.*|EZPASS.*|TOLL.*', 'EZ Pass'),
        
        # Utilities & Bills (enhanced)
        (r'CONED.*|CON ED.*|CONSOLIDATED EDISON.*', 'ConEd'),
        (r'ATT.*BILL.*|AT&T.*', 'Cell Phones ATT'),
        (r'VERIZON.*FIOS.*|SPECTRUM.*|CABLEVISION.*', 'Cable Internet'),
        (r'RENT.*|RENTAL.*|LEASE.*', 'Rent'),
        (r'GEICO.*|STATE FARM.*|.*INSURANCE.*AUTO.*', 'Car Insurance'),
        
        # Technology & Subscriptions (enhanced)
        (r'APPLEBILL.*INTERNET.*|APPLE.*ICLOUD.*', 'iCloud'),
        (r'APPLE.*ICLOUD.*|APPLEBILL.*', 'Apple iCloud'),
        (r'YOUTUBE.*|GOOGLE.*YOUTUBE.*', 'Streaming Services'),
        (r'APPLE.*|COMPUTER.*|ELECTRONICS.*|BESTBUY.*', 'IT Equipment'),
        (r'ADOBE.*|MICROSOFT.*|SOFTWARE.*|SUBSCRIPTION.*', 'IT Subscription'),
        
        # Healthcare & Personal Care
        (r'APOSTROPHE.*|HEALTHCARE.*|MEDICAL.*|PHARMACY.*', 'Healthcare'),
        (r'SALON.*|HAIR.*|BARBER.*', 'Hair Salon'),
        (r'DRY.*CLEAN.*|LAUNDRY.*|CLEANERS.*', 'Dry Cleaning'),
        (r'SMOKE.*SHOP.*|VAPE.*|JUUL.*', 'Vape'),
        
        # Recreation & Hobbies
        (r'GOLF.*', 'Golf'),
        (r'ORVIS.*|AMMO.*|FIREARMS.*|SHOOTING.*', 'Shooting'),
        (r'MUSEUM.*|GALLERY.*|MMA.*ADMISSIONS.*', 'Museums'),
        (r'TICKET.*|EVENT.*|ENTERTAINMENT.*', 'Activities'),
        
        # Home & Services
        (r'HOME DEPOT.*|LOWES.*|BED BATH.*', 'Home Goods'),
        (r'STAPLES.*|OFFICE DEPOT.*|SUPPLIES.*', 'Office Supplies'),
        (r'FEDEX.*|UPS.*|USPS.*|POSTAL.*', 'Mail/FedEx/UPS'),
        (r'FLORIST.*|FLOWERS.*|ROSES.*', 'Flowers'),
        
        # Vehicle Related
        (r'AUTO.*REPAIR.*|MECHANIC.*|GARAGE.*', 'Car Repair'),
        (r'CAR.*WASH.*|AUTO.*WASH.*', 'Car Wash'),
        (r'PARKING.*|GARAGE.*|METER.*', 'Parking'),
        (r'PARKING.*TICKET.*|VIOLATION.*|FINE.*', 'Car Tickets'),
        
        # Financial Services
        (r'^CASH$|CASH EQUIVALENT.*|ATM.*', 'Cash'),
        (r'AUTOPAY.*PAYMENT.*|CREDIT.*CARD.*PAYMENT.*', 'CC Payment'),
        (r'MEMBERSHIP.*FEE.*|ANNUAL.*FEE.*', 'CC Membership'),
        (r'VENMO.*PAYMENT.*|P2P.*VENMO.*', 'VENMO Received'),
        
        # Taxes
        (r'IRS.*|FEDERAL.*TAX.*|1040.*', 'TAX Federal'),
        (r'NYS.*TAX.*|NEW YORK.*STATE.*TAX.*', 'TAX NY State'),
        (r'TAX.*PREP.*|H&R.*BLOCK.*|TURBOTAX.*', 'TAX Preparation'),
        (r'YONKERS.*TAX.*|CITY.*YONKERS.*', 'TAX Yonkers'),
        
        # Specialized Categories
        (r'AMAZON.*AWS.*|AWS.*AMAZON.*', 'Amazon AWS'),
        (r'AMAZON.*BOOK.*|BARNES.*NOBLE.*|BOOK.*', 'Books'),
        (r'UNIVERSITY.*|COLLEGE.*|SCHOOL.*|TUITION.*', 'Education'),
        (r'GIFT.*|PRESENT.*', 'Gifts'),
        (r'HOTEL.*|MARRIOTT.*|HILTON.*|AIRBNB.*', 'Hotels & AirBNB'),
        (r'INSURANCE.*|POLICY.*', 'Insurance'),
        (r'MAGAZINE.*|SUBSCRIPTION.*|NEWS.*', 'Magazines'),
        (r'PURA.*', 'Pura'),
        (r'STEREO.*|AUDIO.*|SOUND.*|SPEAKER.*', 'Sterio'),
        (r'ZELLE.*GOLF.*|P2P.*GOLF.*', 'Zelle Received for Golf')
    ]

if __name__ == "__main__":
    print("🚀 Starting Intelligent Transaction Tagging...")
    
    # Count transactions first
    input_file = 'output/Master_Transactions.csv'
    transaction_count = 0
    if os.path.exists(input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            transaction_count = sum(1 for line in f) - 1  # Subtract 1 for header
    
    print(f"📊 Processing {transaction_count} transactions... Please wait a minute...")
    
    tagger = IntelligentTagger()
    total_processed = tagger.process_master_file()
    
    tagger.print_statistics()
    print(f"\n✅ Tagged file saved as: output/Master_Transactions_Tagged.csv")
    print(f"📄 Processed {total_processed} transactions") 