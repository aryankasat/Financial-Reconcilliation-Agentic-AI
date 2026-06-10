import sqlite3
import random
import uuid
import os
from datetime import datetime, timedelta

def get_uuid(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def generate_database():
    db_path = os.path.join(os.path.dirname(__file__), "reconciliation.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        currency TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ledger_entries (
        id TEXT PRIMARY KEY,
        transaction_date TEXT NOT NULL,
        cleared_date TEXT,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        description TEXT NOT NULL,
        account_id TEXT NOT NULL,
        reference_number TEXT,
        status TEXT NOT NULL,
        category TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (account_id) REFERENCES accounts(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bank_statement_lines (
        id TEXT PRIMARY KEY,
        account_id TEXT NOT NULL,
        statement_id TEXT NOT NULL,
        transaction_date TEXT NOT NULL,
        value_date TEXT NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        reference_number TEXT,
        running_balance REAL NOT NULL,
        FOREIGN KEY (account_id) REFERENCES accounts(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS card_statement_lines (
        id TEXT PRIMARY KEY,
        account_id TEXT NOT NULL,
        statement_id TEXT NOT NULL,
        transaction_date TEXT NOT NULL,
        posting_date TEXT NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        foreign_amount REAL,
        foreign_currency TEXT,
        cardholder_name TEXT NOT NULL,
        card_last_four TEXT NOT NULL,
        mcc TEXT NOT NULL,
        merchant_name TEXT NOT NULL,
        auth_code TEXT NOT NULL,
        FOREIGN KEY (account_id) REFERENCES accounts(id)
    );
    """)

    # Clear existing data
    cursor.execute("DELETE FROM ledger_entries;")
    cursor.execute("DELETE FROM bank_statement_lines;")
    cursor.execute("DELETE FROM card_statement_lines;")
    cursor.execute("DELETE FROM accounts;")

    # Insert accounts
    cursor.execute("INSERT INTO accounts VALUES ('acc_checking', 'SVB Checking Account', 'BANK', 'USD');")
    cursor.execute("INSERT INTO accounts VALUES ('acc_card_corp', 'Stripe Corporate Card', 'CREDIT_CARD', 'USD');")

    # Seed random for repeatability
    random.seed(12345)

    # Date range: April 1, 2026 to June 30, 2026
    start_date = datetime(2026, 4, 1)
    end_date = datetime(2026, 6, 30)

    # Let's track lists of records to insert
    ledger_records = []
    bank_records = []
    card_records = []

    # Cardholders and their card info
    cardholders = [
        {"name": "Jane Doe", "card": "1111", "role": "CEO"},
        {"name": "John Smith", "card": "2222", "role": "CTO"},
        {"name": "Alice Johnson", "card": "3333", "role": "Marketing"},
        {"name": "Bob Brown", "card": "4444", "role": "Sales"}
    ]

    # Standard Merchants
    # Format: (merchant_name, clean_ledger_desc, statement_desc, mcc, min_amt, max_amt, category)
    merchants = [
        ("Uber", "Uber Ride", "UBER *TRIP RIDE", "4121", 10.0, 55.0, "Travel"),
        ("Lyft", "Lyft Ride", "LYFT *RIDE MON", "4121", 12.0, 48.0, "Travel"),
        ("Starbucks", "Starbucks Coffee", "STARBUCKS COFFEE SEATTLE WA", "5814", 5.0, 22.0, "Meals & Entertainment"),
        ("Chipotle", "Chipotle Lunch", "CHIPOTLE 1234 DENVER CO", "5814", 12.0, 38.0, "Meals & Entertainment"),
        ("Sweetgreen", "Sweetgreen Dinner", "SWEETGREEN SF CENTER SF", "5814", 15.0, 28.0, "Meals & Entertainment"),
        ("Amazon", "Amazon Office Supplies", "AMZN Mktp US*AMZN.COM/BILL", "5943", 20.0, 180.0, "Office Supplies"),
        ("Staples", "Staples Office Supplies", "STAPLES 01249 SEATTLE WA", "5943", 40.0, 120.0, "Office Supplies"),
    ]

    # Pre-generated dates list
    current_date = start_date
    all_dates = []
    while current_date <= end_date:
        all_dates.append(current_date)
        current_date += timedelta(days=1)

    # 1. Generate SaaS Subscriptions (Perfect Matches & Merchant name variations)
    # AWS (3rd of month)
    aws_prices = {4: 1254.80, 5: 1412.50, 6: 1650.00}
    for m in [4, 5, 6]:
        d = datetime(2026, m, 3)
        post_d = d + timedelta(days=1)
        amt = aws_prices[m]
        ref = f"AWS-{m:02d}-2026"
        crd_id = get_uuid("crd")
        led_id = get_uuid("led")
        # Card record
        card_records.append({
            "id": crd_id, "account_id": "acc_card_corp", "statement_id": f"stmt_card_2026_{m:02d}",
            "transaction_date": d.strftime("%Y-%m-%d"), "posting_date": post_d.strftime("%Y-%m-%d"),
            "description": "AMAZON WEB SERVICES AWS.AMAZON.CO", "amount": amt,
            "cardholder_name": "John Smith", "card_last_four": "2222", "mcc": "7372",
            "merchant_name": "Amazon Web Services", "auth_code": f"{random.randint(100000, 999999)}"
        })
        # Ledger record
        ledger_records.append({
            "id": led_id, "transaction_date": d.strftime("%Y-%m-%d"), "cleared_date": post_d.strftime("%Y-%m-%d"),
            "amount": amt, "currency": "USD", "description": f"AWS Cloud Hosting - May Statement" if m==5 else f"AWS Cloud Hosting",
            "account_id": "acc_card_corp", "reference_number": ref, "status": "POSTED",
            "category": "Software & Subscriptions", "created_at": d.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Slack (5th of month)
    for m in [4, 5, 6]:
        d = datetime(2026, m, 5)
        post_d = d + timedelta(days=2)
        amt = 200.00
        ref = f"SLK-{m:02d}-982"
        crd_id = get_uuid("crd")
        led_id = get_uuid("led")
        card_records.append({
            "id": crd_id, "account_id": "acc_card_corp", "statement_id": f"stmt_card_2026_{m:02d}",
            "transaction_date": d.strftime("%Y-%m-%d"), "posting_date": post_d.strftime("%Y-%m-%d"),
            "description": "SLACK *T0123456789 WWW.SLACK.COM", "amount": amt,
            "cardholder_name": "John Smith", "card_last_four": "2222", "mcc": "7372",
            "merchant_name": "Slack Technologies", "auth_code": f"{random.randint(100000, 999999)}"
        })
        ledger_records.append({
            "id": led_id, "transaction_date": d.strftime("%Y-%m-%d"), "cleared_date": post_d.strftime("%Y-%m-%d"),
            "amount": amt, "currency": "USD", "description": "Slack Subscription",
            "account_id": "acc_card_corp", "reference_number": ref, "status": "POSTED",
            "category": "Software & Subscriptions", "created_at": d.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Github Copilot (10th of month)
    for m in [4, 5, 6]:
        d = datetime(2026, m, 10)
        post_d = d + timedelta(days=1)
        amt = 200.00
        ref = f"GH-{m:02d}-551"
        crd_id = get_uuid("crd")
        led_id = get_uuid("led")
        card_records.append({
            "id": crd_id, "account_id": "acc_card_corp", "statement_id": f"stmt_card_2026_{m:02d}",
            "transaction_date": d.strftime("%Y-%m-%d"), "posting_date": post_d.strftime("%Y-%m-%d"),
            "description": "GITHUB *COPILOT SEATTLE WA", "amount": amt,
            "cardholder_name": "John Smith", "card_last_four": "2222", "mcc": "7372",
            "merchant_name": "Github", "auth_code": f"{random.randint(100000, 999999)}"
        })
        ledger_records.append({
            "id": led_id, "transaction_date": d.strftime("%Y-%m-%d"), "cleared_date": post_d.strftime("%Y-%m-%d"),
            "amount": amt, "currency": "USD", "description": "Github Copilot Subscription",
            "account_id": "acc_card_corp", "reference_number": ref, "status": "POSTED",
            "category": "Software & Subscriptions", "created_at": d.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Google Workspace (18th of month)
    for m in [4, 5, 6]:
        d = datetime(2026, m, 18)
        post_d = d + timedelta(days=1)
        amt = 450.00
        ref = f"GGL-{m:02d}-009"
        crd_id = get_uuid("crd")
        led_id = get_uuid("led")
        card_records.append({
            "id": crd_id, "account_id": "acc_card_corp", "statement_id": f"stmt_card_2026_{m:02d}",
            "transaction_date": d.strftime("%Y-%m-%d"), "posting_date": post_d.strftime("%Y-%m-%d"),
            "description": "GOOGLE *WORKSPACE G.CO/HELPPAY CA", "amount": amt,
            "cardholder_name": "John Smith", "card_last_four": "2222", "mcc": "7372",
            "merchant_name": "Google", "auth_code": f"{random.randint(100000, 999999)}"
        })
        ledger_records.append({
            "id": led_id, "transaction_date": d.strftime("%Y-%m-%d"), "cleared_date": post_d.strftime("%Y-%m-%d"),
            "amount": amt, "currency": "USD", "description": "Google Workspace Subscription",
            "account_id": "acc_card_corp", "reference_number": ref, "status": "POSTED",
            "category": "Software & Subscriptions", "created_at": d.strftime("%Y-%m-%d %H:%M:%S")
        })

    # 2. Generate Random Standard Transactions (Travel, Meals, Office Supplies)
    # We will generate ~15-20 transactions per month.
    # To keep things clean, we generate them on random dates.
    for m in [4, 5, 6]:
        # Generate 18 transactions for each month
        num_transactions = 18
        # Ensure dates are unique-ish or just random days in the month
        available_days = list(range(1, 28))
        random.shuffle(available_days)
        
        for idx in range(num_transactions):
            day = available_days[idx % len(available_days)]
            d = datetime(2026, m, day)
            
            # Select random merchant
            merch = random.choice(merchants)
            name, clean_desc, stmt_desc, mcc, min_a, max_a, cat = merch
            
            # Select random cardholder
            holder = random.choice(cardholders)
            
            # Decide amount
            amt = round(random.uniform(min_a, max_a), 2)
            
            # Let's skip generating card statement lines for dates that would collide with our special cases
            # Or if it matches our special case days, just skip or shift the day
            if m == 4 and d.day == 29 and name == "Marriott Hotels":
                continue # Skip because we manually insert this special timing case
            if m == 5 and d.day == 30 and name == "Uber":
                continue # Skip manual timing case
            if m == 6 and d.day == 29 and name == "Amazon":
                continue # Skip manual timing case
            if m == 5 and d.day == 14 and name == "Uber":
                continue # Skip missing ledger case
            if m == 6 and d.day == 12 and name == "Uber": # Wait, steakhouse is the special missing case
                continue
            if m == 5 and d.day == 20 and name == "Chipotle":
                continue # Skip amount discrepancy case
            if m == 6 and d.day == 15 and name == "Staples":
                continue # Skip Jetbrains discrepancy case
            if m == 5 and d.day == 10 and name == "Staples":
                continue # Skip duplicate case
            
            # Standard perfect match
            post_d = d + timedelta(days=random.choice([1, 2]))
            crd_id = get_uuid("crd")
            led_id = get_uuid("led")
            ref = f"REF-{m:02d}-{idx:02d}"
            
            card_records.append({
                "id": crd_id, "account_id": "acc_card_corp", "statement_id": f"stmt_card_2026_{m:02d}",
                "transaction_date": d.strftime("%Y-%m-%d"), "posting_date": post_d.strftime("%Y-%m-%d"),
                "description": f"{stmt_desc}", "amount": amt,
                "cardholder_name": holder["name"], "card_last_four": holder["card"], "mcc": mcc,
                "merchant_name": name, "auth_code": f"{random.randint(100000, 999999)}"
            })
            
            ledger_records.append({
                "id": led_id, "transaction_date": d.strftime("%Y-%m-%d"), "cleared_date": post_d.strftime("%Y-%m-%d"),
                "amount": amt, "currency": "USD", "description": f"{clean_desc} - {holder['name']}",
                "account_id": "acc_card_corp", "reference_number": ref, "status": "POSTED",
                "category": cat, "created_at": d.strftime("%Y-%m-%d %H:%M:%S")
            })

    # 3. Manually Insert Special Reconciliation Cases

    # CASE 3: Timing Differences
    # A: John Smith stays at Marriott on Apr 29, posts May 2.
    crd_id_t1 = get_uuid("crd")
    led_id_t1 = get_uuid("led")
    card_records.append({
        "id": crd_id_t1, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_05",  # Appears in MAY card statement because it posted May 2!
        "transaction_date": "2026-04-29", "posting_date": "2026-05-02",
        "description": "MARRIOTT HOTELS BOSTON", "amount": 342.15,
        "cardholder_name": "John Smith", "card_last_four": "2222", "mcc": "7011",
        "merchant_name": "Marriott Hotels", "auth_code": "481023"
    })
    ledger_records.append({
        "id": led_id_t1, "transaction_date": "2026-04-29", "cleared_date": "2026-05-02",
        "amount": 342.15, "currency": "USD", "description": "Marriott Lodging - CTO Travel",
        "account_id": "acc_card_corp", "reference_number": "TXN-2026-0429", "status": "POSTED",
        "category": "Travel", "created_at": "2026-04-29 18:24:00"
    })

    # B: Alice Johnson Uber on May 30, posts June 2.
    crd_id_t2 = get_uuid("crd")
    led_id_t2 = get_uuid("led")
    card_records.append({
        "id": crd_id_t2, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_06",  # Appears in JUNE card statement because it posted June 2!
        "transaction_date": "2026-05-30", "posting_date": "2026-06-02",
        "description": "UBER *TRIP RIDE", "amount": 89.50,
        "cardholder_name": "Alice Johnson", "card_last_four": "3333", "mcc": "4121",
        "merchant_name": "Uber", "auth_code": "912384"
    })
    ledger_records.append({
        "id": led_id_t2, "transaction_date": "2026-05-30", "cleared_date": "2026-06-02",
        "amount": 89.50, "currency": "USD", "description": "Uber - Marketing Event",
        "account_id": "acc_card_corp", "reference_number": "TXN-2026-0530", "status": "POSTED",
        "category": "Travel", "created_at": "2026-05-30 22:10:00"
    })

    # C: Bob Brown Amazon on June 29, posts July 2. (Will NOT be in the June card statement, outstanding card charge!)
    led_id_t3 = get_uuid("led")
    ledger_records.append({
        "id": led_id_t3, "transaction_date": "2026-06-29", "cleared_date": None,
        "amount": 124.80, "currency": "USD", "description": "Amazon - Office Equipment",
        "account_id": "acc_card_corp", "reference_number": "TXN-2026-0629", "status": "PENDING",
        "category": "Office Supplies", "created_at": "2026-06-29 11:45:00"
    })
    # Note: No card record in the April/May/June database statements. It would be in July statement.

    # CASE 4: Missing Ledger Entries
    # A: Alice Johnson Uber on May 14.
    crd_id_m1 = get_uuid("crd")
    card_records.append({
        "id": crd_id_m1, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_05",
        "transaction_date": "2026-05-14", "posting_date": "2026-05-15",
        "description": "UBER *TRIP RIDE", "amount": 42.50,
        "cardholder_name": "Alice Johnson", "card_last_four": "3333", "mcc": "4121",
        "merchant_name": "Uber", "auth_code": "772184"
    })
    # NO LEDGER RECORD

    # B: Jane Doe dinner on June 12.
    crd_id_m2 = get_uuid("crd")
    card_records.append({
        "id": crd_id_m2, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_06",
        "transaction_date": "2026-06-12", "posting_date": "2026-06-14",
        "description": "THE STEAKHOUSE CHICAGO", "amount": 185.50,
        "cardholder_name": "Jane Doe", "card_last_four": "1111", "mcc": "5812",
        "merchant_name": "The Steakhouse", "auth_code": "882103"
    })
    # NO LEDGER RECORD

    # CASE 5: Amount Discrepancies
    # A: Bob Brown Chipotle lunch on May 20. Ledger: 15.00, Card: 18.50.
    crd_id_d1 = get_uuid("crd")
    led_id_d1 = get_uuid("led")
    card_records.append({
        "id": crd_id_d1, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_05",
        "transaction_date": "2026-05-20", "posting_date": "2026-05-21",
        "description": "CHIPOTLE 1234 DENVER CO", "amount": 18.50,
        "cardholder_name": "Bob Brown", "card_last_four": "4444", "mcc": "5814",
        "merchant_name": "Chipotle", "auth_code": "551299"
    })
    ledger_records.append({
        "id": led_id_d1, "transaction_date": "2026-05-20", "cleared_date": "2026-05-21",
        "amount": 15.00, "currency": "USD", "description": "Bob Brown Chipotle lunch",
        "account_id": "acc_card_corp", "reference_number": "TXN-2026-0520-CHP", "status": "POSTED",
        "category": "Meals & Entertainment", "created_at": "2026-05-20 12:30:00"
    })

    # B: John Smith JetBrains subscription on June 15. Ledger: 100.00, Card: 102.45 (due to Forex fee).
    crd_id_d2 = get_uuid("crd")
    led_id_d2 = get_uuid("led")
    card_records.append({
        "id": crd_id_d2, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_06",
        "transaction_date": "2026-06-15", "posting_date": "2026-06-16",
        "description": "JETBRAINS S.R.O. PRAGUE", "amount": 102.45,
        "cardholder_name": "John Smith", "card_last_four": "2222", "mcc": "7372",
        "merchant_name": "JetBrains", "auth_code": "291034"
    })
    ledger_records.append({
        "id": led_id_d2, "transaction_date": "2026-06-15", "cleared_date": "2026-06-16",
        "amount": 100.00, "currency": "USD", "description": "JetBrains Subscription",
        "account_id": "acc_card_corp", "reference_number": "TXN-2026-0615-JB", "status": "POSTED",
        "category": "Software & Subscriptions", "created_at": "2026-06-15 09:15:00"
    })

    # CASE 6: Duplicate Ledger Entries
    # Staples supplies on May 10. Card: 84.20 once. Ledger: 84.20 twice.
    crd_id_dp = get_uuid("crd")
    led_id_dp1 = get_uuid("led")
    led_id_dp2 = get_uuid("led")
    card_records.append({
        "id": crd_id_dp, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_05",
        "transaction_date": "2026-05-10", "posting_date": "2026-05-11",
        "description": "STAPLES 01249 SEATTLE WA", "amount": 84.20,
        "cardholder_name": "Bob Brown", "card_last_four": "4444", "mcc": "5943",
        "merchant_name": "Staples", "auth_code": "848201"
    })
    ledger_records.append({
        "id": led_id_dp1, "transaction_date": "2026-05-10", "cleared_date": "2026-05-11",
        "amount": 84.20, "currency": "USD", "description": "Office Printer Paper",
        "account_id": "acc_card_corp", "reference_number": "STAPLES-9921", "status": "POSTED",
        "category": "Office Supplies", "created_at": "2026-05-10 14:15:00"
    })
    ledger_records.append({
        "id": led_id_dp2, "transaction_date": "2026-05-11", "cleared_date": None,
        "amount": 84.20, "currency": "USD", "description": "Staples Office Supplies",
        "account_id": "acc_card_corp", "reference_number": "STAPLES-9921", "status": "POSTED",
        "category": "Office Supplies", "created_at": "2026-05-11 09:30:00"
    })

    # CASE 7: Unrecognized/Fraudulent Card Charge
    # Bob Brown card shows ELECTRONICS DIRECT $450.00 on June 22.
    crd_id_f = get_uuid("crd")
    card_records.append({
        "id": crd_id_f, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_06",
        "transaction_date": "2026-06-22", "posting_date": "2026-06-23",
        "description": "ELECTRONICS DIRECT ONLINE", "amount": 450.00,
        "cardholder_name": "Bob Brown", "card_last_four": "4444", "mcc": "5732",
        "merchant_name": "ELECTRONICS DIRECT", "auth_code": "661023"
    })
    # NO LEDGER RECORD

    # CASE 9: Contextual Normalization Required (DBA/Legal names vs. Product names)
    # A: Airtable vs Formagrid (Apr 15)
    crd_id_c1 = get_uuid("crd")
    led_id_c1 = get_uuid("led")
    card_records.append({
        "id": crd_id_c1, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_04",
        "transaction_date": "2026-04-15", "posting_date": "2026-04-16",
        "description": "FORMAGRID INC SF CA", "amount": 320.00,
        "cardholder_name": "John Smith", "card_last_four": "2222", "mcc": "7372",
        "merchant_name": "Formagrid Inc", "auth_code": "392019"
    })
    ledger_records.append({
        "id": led_id_c1, "transaction_date": "2026-04-15", "cleared_date": "2026-04-16",
        "amount": 320.00, "currency": "USD", "description": "Airtable CRM Subscription",
        "account_id": "acc_card_corp", "reference_number": "AIR-2026-APR", "status": "POSTED",
        "category": "Software & Subscriptions", "created_at": "2026-04-15 10:00:00"
    })

    # B: 1Password vs AgileBits (May 12)
    crd_id_c2 = get_uuid("crd")
    led_id_c2 = get_uuid("led")
    card_records.append({
        "id": crd_id_c2, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_05",
        "transaction_date": "2026-05-12", "posting_date": "2026-05-13",
        "description": "AGILEBITS INC TORONTO ON", "amount": 72.00,
        "cardholder_name": "John Smith", "card_last_four": "2222", "mcc": "7372",
        "merchant_name": "Agilebits Inc", "auth_code": "190283"
    })
    ledger_records.append({
        "id": led_id_c2, "transaction_date": "2026-05-12", "cleared_date": "2026-05-13",
        "amount": 72.00, "currency": "USD", "description": "1Password Team License",
        "account_id": "acc_card_corp", "reference_number": "1PW-2026-MAY", "status": "POSTED",
        "category": "Software & Subscriptions", "created_at": "2026-05-12 11:30:00"
    })

    # C: Instagram Ads vs Meta (May 25)
    crd_id_c3 = get_uuid("crd")
    led_id_c3 = get_uuid("led")
    card_records.append({
        "id": crd_id_c3, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_05",
        "transaction_date": "2026-05-25", "posting_date": "2026-05-26",
        "description": "META ADS *10283748 SF", "amount": 1250.00,
        "cardholder_name": "Alice Johnson", "card_last_four": "3333", "mcc": "7311",
        "merchant_name": "Meta Ads", "auth_code": "581902"
    })
    ledger_records.append({
        "id": led_id_c3, "transaction_date": "2026-05-25", "cleared_date": "2026-05-26",
        "amount": 1250.00, "currency": "USD", "description": "Instagram Ads Run",
        "account_id": "acc_card_corp", "reference_number": "MET-2026-0525", "status": "POSTED",
        "category": "Advertising & Marketing", "created_at": "2026-05-25 15:45:00"
    })

    # D: Twitter Blue vs X.com (June 08)
    crd_id_c4 = get_uuid("crd")
    led_id_c4 = get_uuid("led")
    card_records.append({
        "id": crd_id_c4, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_06",
        "transaction_date": "2026-06-08", "posting_date": "2026-06-09",
        "description": "X.COM CORP BILLING CA", "amount": 84.00,
        "cardholder_name": "Jane Doe", "card_last_four": "1111", "mcc": "4899",
        "merchant_name": "X.com", "auth_code": "291083"
    })
    ledger_records.append({
        "id": led_id_c4, "transaction_date": "2026-06-08", "cleared_date": "2026-06-09",
        "amount": 84.00, "currency": "USD", "description": "Twitter Premium Verification",
        "account_id": "acc_card_corp", "reference_number": "TW-BLUE-2026", "status": "POSTED",
        "category": "Software & Subscriptions", "created_at": "2026-06-08 09:00:00"
    })

    # E: WeWork vs WW Operating (June 01)
    crd_id_c5 = get_uuid("crd")
    led_id_c5 = get_uuid("led")
    card_records.append({
        "id": crd_id_c5, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_06",
        "transaction_date": "2026-06-01", "posting_date": "2026-06-02",
        "description": "WW *OPERATING LLC NY", "amount": 450.00,
        "cardholder_name": "Bob Brown", "card_last_four": "4444", "mcc": "6513",
        "merchant_name": "WW Operating LLC", "auth_code": "771890"
    })
    ledger_records.append({
        "id": led_id_c5, "transaction_date": "2026-06-01", "cleared_date": "2026-06-02",
        "amount": 450.00, "currency": "USD", "description": "WeWork Hot Desks",
        "account_id": "acc_card_corp", "reference_number": "WEWORK-2026-JUN", "status": "POSTED",
        "category": "Rent & Facilities", "created_at": "2026-06-01 08:30:00"
    })

    # CASE 10: Multi-Currency Transactions (Currency Normalization)
    # A: Exact Foreign Match (EUR)
    crd_id_curr1 = get_uuid("crd")
    led_id_curr1 = get_uuid("led")
    card_records.append({
        "id": crd_id_curr1, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_05",
        "transaction_date": "2026-05-18", "posting_date": "2026-05-19",
        "description": "JETBRAINS DEUTSCHLAND GMBH MUNICH", "amount": 163.50, "currency": "USD",
        "foreign_amount": 150.00, "foreign_currency": "EUR",
        "cardholder_name": "John Smith", "card_last_four": "2222", "mcc": "7372",
        "merchant_name": "JetBrains", "auth_code": "492019"
    })
    ledger_records.append({
        "id": led_id_curr1, "transaction_date": "2026-05-18", "cleared_date": "2026-05-19",
        "amount": 150.00, "currency": "EUR", "description": "SaaS Subscription EUR",
        "account_id": "acc_card_corp", "reference_number": "EUR-JB-990", "status": "POSTED",
        "category": "Software & Subscriptions", "created_at": "2026-05-18 10:30:00"
    })

    # B: Foreign Exchange Fee discrepancy (GBP)
    crd_id_curr2 = get_uuid("crd")
    led_id_curr2 = get_uuid("led")
    card_records.append({
        "id": crd_id_curr2, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_06",
        "transaction_date": "2026-06-05", "posting_date": "2026-06-06",
        "description": "THE SCRUM HALF LONDON", "amount": 104.20, "currency": "USD",
        "foreign_amount": 80.00, "foreign_currency": "GBP",
        "cardholder_name": "John Smith", "card_last_four": "2222", "mcc": "5812",
        "merchant_name": "The Scrum Half Pub", "auth_code": "881920"
    })
    ledger_records.append({
        "id": led_id_curr2, "transaction_date": "2026-06-05", "cleared_date": "2026-06-06",
        "amount": 80.00, "currency": "GBP", "description": "Team Dinner in London",
        "account_id": "acc_card_corp", "reference_number": "GBP-DN-002", "status": "POSTED",
        "category": "Meals & Entertainment", "created_at": "2026-06-05 20:00:00"
    })

    # C: Multi-currency amount mismatch (Double Conversion / drift) (CAD)
    crd_id_curr3 = get_uuid("crd")
    led_id_curr3 = get_uuid("led")
    card_records.append({
        "id": crd_id_curr3, "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_04",
        "transaction_date": "2026-04-10", "posting_date": "2026-04-11",
        "description": "SHOPIFY SUBSCRIPTION OTTAWA ON", "amount": 148.50, "currency": "USD",
        "foreign_amount": 202.00, "foreign_currency": "CAD",
        "cardholder_name": "Jane Doe", "card_last_four": "1111", "mcc": "7372",
        "merchant_name": "Shopify", "auth_code": "991028"
    })
    ledger_records.append({
        "id": led_id_curr3, "transaction_date": "2026-04-10", "cleared_date": "2026-04-11",
        "amount": 200.00, "currency": "CAD", "description": "Shopify CAD Storefront",
        "account_id": "acc_card_corp", "reference_number": "CAD-SH-091", "status": "POSTED",
        "category": "Software & Subscriptions", "created_at": "2026-04-10 14:00:00"
    })

    # 4. Generate Checking Account Activity (Payroll, Rent, Wire Inflows, Card Payments)
    # Start checking balance at $150,000.00
    checking_balance = 150000.00

    # Let's define checking transactions in a timeline
    checking_events = []

    # Office Rent: April 1, May 1, June 1 (-$3,500.00)
    for m in [4, 5, 6]:
        d = datetime(2026, m, 1)
        checking_events.append({
            "date": d, "amount": -3500.00, "desc_ledger": "Office Rent - Monthly",
            "desc_bank": "ACH OUT - LANDLORD CORP", "ref": f"RNT-{m:02d}-2026", "cat": "Rent & Facilities"
        })

    # Payroll: 15th and 30th (or 28th/29th/30th if weekend - for simplicity we do exactly 15th and 30th)
    # Amount: -$22,500.00
    for m in [4, 5, 6]:
        for day in [15, 30]:
            d = datetime(2026, m, day)
            checking_events.append({
                "date": d, "amount": -22500.00, "desc_ledger": f"Semi-monthly Payroll - {d.strftime('%b %d')}",
                "desc_bank": "ACH OUT - PAYROLL SERVICES", "ref": f"PAY-{m:02d}-{day}", "cat": "Compensation"
            })

    # Weekly Customer Inflows (every Friday)
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() == 4: # Friday
            amt = round(random.uniform(9000.0, 24000.0), 2)
            checking_events.append({
                "date": current_date, "amount": amt, "desc_ledger": "Customer Wire Transfer - Inbound",
                "desc_bank": f"WIRE TRANS *CUSTOMER-{random.randint(100, 999)}", "ref": f"WIR-{current_date.strftime('%m%d')}", "cat": "Revenue"
            })
        current_date += timedelta(days=1)

    # Now calculate the Credit Card Payment Amounts.
    # To do this, we need to know what posted on the card statement in April and May.
    # April Statement Balance: sum of all card_records where posting_date is in April
    april_card_statement_bal = sum(r["amount"] for r in card_records if r["posting_date"].startswith("2026-04"))
    # May Statement Balance: sum of all card_records where posting_date is in May (this statement will include the payment of April balance too!)
    # Let's pay April balance on May 20.
    # April Card statement balance is paid in full on May 20:
    d_pay_apr = datetime(2026, 5, 20)
    checking_events.append({
        "date": d_pay_apr, "amount": -april_card_statement_bal,
        "desc_ledger": "Stripe Corporate Card Autopay",
        "desc_bank": "ACH AUTO-PAY STRIPE CARD", "ref": "PMT-APR-STRP", "cat": "Credit Card Payment",
        "is_cc_payment": True, "cc_stmt_id": "stmt_card_2026_05", "cleared_offset": 1 # Clears bank May 21
    })

    # Now we insert the credit card payment credit record in card statement:
    card_records.append({
        "id": get_uuid("crd"), "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_05",
        "transaction_date": "2026-05-20", "posting_date": "2026-05-20",
        "description": "PAYMENT RECEIVED - THANK YOU", "amount": -april_card_statement_bal,
        "cardholder_name": "System", "card_last_four": "0000", "mcc": "0000",
        "merchant_name": "Stripe Card Payment", "auth_code": "000000"
    })
    # And matching ledger entries on the credit card account side!
    # Remember: a credit card payment decreases the credit card payable balance. In our sign convention:
    # Charges are positive (increasing what we owe), payments are negative (decreasing what we owe).
    # Checking account ledger entry: amount is negative (outflow).
    # Credit Card ledger entry: amount is negative (reducing card balance).
    ledger_records.append({
        "id": get_uuid("led"), "transaction_date": "2026-05-20", "cleared_date": "2026-05-20",
        "amount": -april_card_statement_bal, "currency": "USD", "description": "Stripe Corporate Card Payment",
        "account_id": "acc_card_corp", "reference_number": "PMT-APR-STRP", "status": "POSTED",
        "category": "Credit Card Payment", "created_at": "2026-05-20 08:00:00"
    })

    # Now we can compute May card transactions posted in May (excluding the payment) to determine the May closing balance.
    may_charges_only = sum(r["amount"] for r in card_records if r["posting_date"].startswith("2026-05") and r["cardholder_name"] != "System")
    # In real card statements: New Balance = Previous Balance ($april_card_statement_bal) - Payment ($april_card_statement_bal) + New Charges ($may_charges_only) = $may_charges_only.
    # This balance is paid in full on June 20.
    # Since June 20 is a Saturday, the bank statement clears on Monday June 22.
    d_pay_may = datetime(2026, 6, 20)
    checking_events.append({
        "date": d_pay_may, "amount": -may_charges_only,
        "desc_ledger": "Stripe Corporate Card Autopay",
        "desc_bank": "ACH AUTO-PAY STRIPE CARD", "ref": "PMT-MAY-STRP", "cat": "Credit Card Payment",
        "is_cc_payment": True, "cc_stmt_id": "stmt_card_2026_06", "cleared_offset": 2 # Clears bank Monday June 22
    })
    # Card statement credit record:
    card_records.append({
        "id": get_uuid("crd"), "account_id": "acc_card_corp", "statement_id": "stmt_card_2026_06",
        "transaction_date": "2026-06-20", "posting_date": "2026-06-20",
        "description": "PAYMENT RECEIVED - THANK YOU", "amount": -may_charges_only,
        "cardholder_name": "System", "card_last_four": "0000", "mcc": "0000",
        "merchant_name": "Stripe Card Payment", "auth_code": "000000"
    })
    # Credit Card ledger entry:
    ledger_records.append({
        "id": get_uuid("led"), "transaction_date": "2026-06-20", "cleared_date": "2026-06-20",
        "amount": -may_charges_only, "currency": "USD", "description": "Stripe Corporate Card Payment",
        "account_id": "acc_card_corp", "reference_number": "PMT-MAY-STRP", "status": "POSTED",
        "category": "Credit Card Payment", "created_at": "2026-06-20 08:00:00"
    })

    # Sort checking events by date
    checking_events.sort(key=lambda x: x["date"])

    # Now generate the ledger and bank statement entries for checking account.
    # We will simulate the running balance.
    # Note that bank statement lines clear 1-2 days after ledger entries.
    bank_lines_to_generate = []
    
    # We first generate all ledger entries for checking account
    for ev in checking_events:
        d = ev["date"]
        amt = ev["amount"]
        desc_led = ev["desc_ledger"]
        ref = ev["ref"]
        cat = ev["cat"]
        
        led_id = get_uuid("led")
        
        # Insert ledger entry
        ledger_records.append({
            "id": led_id, "transaction_date": d.strftime("%Y-%m-%d"), 
            "cleared_date": (d + timedelta(days=ev.get("cleared_offset", 1))).strftime("%Y-%m-%d"),
            "amount": amt, "currency": "USD", "description": desc_led,
            "account_id": "acc_checking", "reference_number": ref, "status": "POSTED",
            "category": cat, "created_at": d.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Prepare bank statement line (which occurs value_date days later)
        clear_days = ev.get("cleared_offset", 1)
        clear_d = d + timedelta(days=clear_days)
        
        bank_lines_to_generate.append({
            "date": d.strftime("%Y-%m-%d"),
            "value_date": clear_d.strftime("%Y-%m-%d"),
            "description": ev["desc_bank"],
            "amount": amt,
            "reference_number": ref
        })

    # Sort bank lines by value_date to compute running balance correctly
    bank_lines_to_generate.sort(key=lambda x: x["value_date"])
    
    running_bal = checking_balance
    # Insert initial bank line representing starting balance on April 1
    # Bank statement for checking will be split by month: stmt_bank_2026_04, stmt_bank_2026_05, stmt_bank_2026_06
    for line in bank_lines_to_generate:
        running_bal = round(running_bal + line["amount"], 2)
        v_date = datetime.strptime(line["value_date"], "%Y-%m-%d")
        stmt_id = f"stmt_bank_2026_{v_date.month:02d}"
        
        bank_records.append({
            "id": get_uuid("bnk"), "account_id": "acc_checking", "statement_id": stmt_id,
            "transaction_date": line["date"], "value_date": line["value_date"],
            "description": line["description"], "amount": line["amount"],
            "reference_number": line["reference_number"], "running_balance": running_bal
        })

    # 5. Insert everything into the database
    # Ledger entries
    for r in ledger_records:
        cursor.execute("""
        INSERT INTO ledger_entries (id, transaction_date, cleared_date, amount, currency, description, account_id, reference_number, status, category, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (r["id"], r["transaction_date"], r["cleared_date"], r["amount"], r["currency"], r["description"], r["account_id"], r["reference_number"], r["status"], r["category"], r["created_at"]))

    # Card statement lines
    for r in card_records:
        currency = r.get("currency", "USD")
        foreign_amount = r.get("foreign_amount", None)
        foreign_currency = r.get("foreign_currency", None)
        cursor.execute("""
        INSERT INTO card_statement_lines (id, account_id, statement_id, transaction_date, posting_date, description, amount, currency, foreign_amount, foreign_currency, cardholder_name, card_last_four, mcc, merchant_name, auth_code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (r["id"], r["account_id"], r["statement_id"], r["transaction_date"], r["posting_date"], r["description"], r["amount"], currency, foreign_amount, foreign_currency, r["cardholder_name"], r["card_last_four"], r["mcc"], r["merchant_name"], r["auth_code"]))

    # Bank statement lines
    for r in bank_records:
        currency = r.get("currency", "USD")
        cursor.execute("""
        INSERT INTO bank_statement_lines (id, account_id, statement_id, transaction_date, value_date, description, amount, currency, reference_number, running_balance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (r["id"], r["account_id"], r["statement_id"], r["transaction_date"], r["value_date"], r["description"], r["amount"], currency, r["reference_number"], r["running_balance"]))

    conn.commit()

    # Print summary statistics
    cursor.execute("SELECT COUNT(*) FROM ledger_entries;")
    ledger_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM card_statement_lines;")
    card_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM bank_statement_lines;")
    bank_count = cursor.fetchone()[0]

    print("Database generation completed successfully!")
    print(f"Ledger entries inserted: {ledger_count}")
    print(f"Card statement lines inserted: {card_count}")
    print(f"Bank statement lines inserted: {bank_count}")

    conn.close()

if __name__ == "__main__":
    generate_database()
