import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "reconciliation.db"))

def get_connection():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Please run generate_db.py first.")
    return sqlite3.connect(DB_PATH)

def fetch_accounts():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, type, currency FROM accounts;")
    accounts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return accounts

def fetch_ledger_entries(account_id=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if account_id:
        cursor.execute("""
            SELECT id, transaction_date, cleared_date, amount, currency, description, account_id, reference_number, status, category, created_at
            FROM ledger_entries
            WHERE account_id = ?
            ORDER BY transaction_date ASC;
        """, (account_id,))
    else:
        cursor.execute("""
            SELECT id, transaction_date, cleared_date, amount, currency, description, account_id, reference_number, status, category, created_at
            FROM ledger_entries
            ORDER BY transaction_date ASC;
        """)
    entries = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return entries

def fetch_card_statement_lines(statement_id=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if statement_id:
        cursor.execute("""
            SELECT id, account_id, statement_id, transaction_date, posting_date, description, amount, currency, foreign_amount, foreign_currency, cardholder_name, card_last_four, mcc, merchant_name, auth_code
            FROM card_statement_lines
            WHERE statement_id = ?
            ORDER BY transaction_date ASC;
        """, (statement_id,))
    else:
        cursor.execute("""
            SELECT id, account_id, statement_id, transaction_date, posting_date, description, amount, currency, foreign_amount, foreign_currency, cardholder_name, card_last_four, mcc, merchant_name, auth_code
            FROM card_statement_lines
            ORDER BY transaction_date ASC;
        """)
    lines = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return lines

def fetch_bank_statement_lines(statement_id=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if statement_id:
        cursor.execute("""
            SELECT id, account_id, statement_id, transaction_date, value_date, description, amount, currency, reference_number, running_balance
            FROM bank_statement_lines
            WHERE statement_id = ?
            ORDER BY value_date ASC;
        """, (statement_id,))
    else:
        cursor.execute("""
            SELECT id, account_id, statement_id, transaction_date, value_date, description, amount, currency, reference_number, running_balance
            FROM bank_statement_lines
            ORDER BY value_date ASC;
        """)
    lines = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return lines
