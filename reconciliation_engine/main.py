import json
import os
from reconciliation_engine.database import fetch_ledger_entries, fetch_card_statement_lines, fetch_bank_statement_lines
from reconciliation_engine.reconciliation import reconcile_card_transactions, reconcile_bank_transactions

def get_transaction_month(date_str):
    # Extracts YYYY-MM
    return date_str[:7]

def format_currency(val):
    return f"${val:,.2f}"

def run_pipeline():
    print("==================================================================")
    print("               APEX WIDGETS INC - RECONCILIATION REPORT           ")
    print("==================================================================")
    
    # 1. Fetch data
    ledger_entries = fetch_ledger_entries()
    card_lines = fetch_card_statement_lines()
    bank_lines = fetch_bank_statement_lines()
    
    # Split ledger entries by account type
    card_ledger = [r for r in ledger_entries if r["account_id"] == "acc_card_corp"]
    bank_ledger = [r for r in ledger_entries if r["account_id"] == "acc_checking"]
    
    # 2. Run Reconciliations
    card_results = reconcile_card_transactions(card_ledger, card_lines)
    bank_results = reconcile_bank_transactions(bank_ledger, bank_lines)
    
    # 3. Print Corporate Credit Card Summary
    print("\n--- CORPORATE CARD RECONCILIATION SUMMARY ---")
    print(f"Total Card Statement Lines:  {len(card_lines)}")
    print(f"Total Card Ledger Entries:   {len(card_ledger) - 2} (excluding payment entries)") # subtract the 2 card payment ledger lines
    print(f"Perfect Matches Found:       {len(card_results['matches'])}")
    print(f"Discrepancies Resolved:      {len(card_results['discrepancies'])}")
    print(f"Duplicate Ledger Entries:    {len(card_results['duplicates'])}")
    print(f"Unmatched Ledger Entries:    {len(card_results['unmatched_ledger'])}")
    print(f"Unmatched Card charges:      {len(card_results['unmatched_card'])}")
    
    # Calculate Card Reconciled Ratio
    total_reconciled = len(card_results['matches']) + len(card_results['discrepancies'])
    card_total_to_match = len(card_lines) - 2 # exclude payments
    reconciled_ratio = (total_reconciled / card_total_to_match) * 100 if card_total_to_match > 0 else 0
    print(f"Card Statement Reconciled Ratio: {reconciled_ratio:.1f}%")
    
    # Print Reconciled Details by Rule
    print("\n  [Matching Rule Breakdown]")
    rule_counts = {}
    for m in card_results['matches']:
        rule = m["rule"]
        rule_counts[rule] = rule_counts.get(rule, 0) + 1
    for m in card_results['discrepancies']:
        rule = m["rule"]
        rule_counts[rule] = rule_counts.get(rule, 0) + 1
    for rule, count in rule_counts.items():
        print(f"    - {rule:50} : {count} matches")

    # Details of Discrepancies
    if card_results['discrepancies']:
        print("\n  [Amount Discrepancies Flagged]")
        for d in card_results['discrepancies']:
            led = d["ledger_entry"]
            card = d["card_line"]
            print(f"    * Date: {led['transaction_date']} | Desc: '{led['description']}'")
            print(f"      Ledger Amount: {led['amount']} {led['currency']} | Card Amount: {card['amount']} {card['currency']}")
            print(f"      Variance: {d['variance']} USD (Action: flagged for manual review / adjustment)")
            
    # Details of Duplicates
    if card_results['duplicates']:
        print("\n  [Duplicate Ledger Entries Blocked]")
        for dp in card_results['duplicates']:
            led = dp["duplicate_ledger_entry"]
            orig = dp["original_ledger_entry"]
            card = dp["matched_card_line"]
            print(f"    * Duplicate Ledger ID: {led['id']} | Date: {led['transaction_date']} | Amt: {led['amount']} | Desc: '{led['description']}'")
            print(f"      Matched Original ID:  {orig['id']} | Date: {orig['transaction_date']} | Amt: {orig['amount']} | Desc: '{orig['description']}'")
            print(f"      Card Transaction:     ID: {card['id']} | Date: {card['transaction_date']} | Amt: {card['amount']} | Desc: '{card['description']}'")

    # Details of Unmatched Ledger Entries
    if card_results['unmatched_ledger']:
        print("\n  [Unmatched Ledger Entries (Outstanding or Error)]")
        for led in card_results['unmatched_ledger']:
            print(f"    * Date: {led['transaction_date']} | Amt: {led['amount']} {led['currency']} | Desc: '{led['description']}' (Status: {led['status']})")
            
    # Details of Unmatched Card Lines
    if card_results['unmatched_card']:
        print("\n  [Unmatched Statement Lines (Missing Receipts / Potential Fraud)]")
        for card in card_results['unmatched_card']:
            mcc_note = "Possible Fraud" if card['amount'] >= 400.00 and card['mcc'] == '5732' else "Missing Employee Submission"
            print(f"    * Date: {card['transaction_date']} | Amt: {card['amount']} {card['currency']} | Desc: '{card['description']}' | Cardholder: {card['cardholder_name']} (Type: {mcc_note})")

    # 4. Bank Account Reconciliations
    print("\n==================================================================")
    print("--- BANK RECONCILIATION SUMMARY (acc_checking) ---")
    print(f"Total Bank Statement Lines:  {len(bank_lines)}")
    print(f"Total Bank Ledger Entries:   {len(bank_ledger)}")
    print(f"Reconciled Matches:          {len(bank_results['matches'])}")
    print(f"Unmatched Ledger Items:      {len(bank_results['unmatched_ledger'])}")
    print(f"Unmatched Bank Lines:        {len(bank_results['unmatched_bank'])}")
    
    bank_reconciled_ratio = (len(bank_results['matches']) / len(bank_lines)) * 100 if len(bank_lines) > 0 else 0
    print(f"Bank Statement Reconciled Ratio: {bank_reconciled_ratio:.1f}%")

    if bank_results['unmatched_ledger']:
        print("\n  [Unmatched Bank Ledger Entries (Outstanding Checks / Payments)]")
        for led in bank_results['unmatched_ledger']:
            print(f"    * Date: {led['transaction_date']} | Amt: {led['amount']} | Desc: '{led['description']}'")

    if bank_results['unmatched_bank']:
        print("\n  [Unmatched Bank Statement Lines (Unrecorded Bank Transactions)]")
        for bank in bank_results['unmatched_bank']:
            print(f"    * Date: {bank['transaction_date']} | Amt: {bank['amount']} | Desc: '{bank['description']}'")

    print("\n==================================================================")
    
    # 5. Export Report JSON
    report = {
        "card_reconciliation": {
            "summary": {
                "total_card_lines": len(card_lines),
                "reconciled_matches": len(card_results['matches']),
                "discrepancies": len(card_results['discrepancies']),
                "duplicates": len(card_results['duplicates']),
                "unmatched_ledger": len(card_results['unmatched_ledger']),
                "unmatched_card": len(card_results['unmatched_card']),
                "reconciled_ratio": reconciled_ratio
            },
            "unmatched_ledger_details": [
                {"id": r["id"], "date": r["transaction_date"], "amount": r["amount"], "currency": r["currency"], "description": r["description"]}
                for r in card_results['unmatched_ledger']
            ],
            "unmatched_card_details": [
                {"id": r["id"], "date": r["transaction_date"], "amount": r["amount"], "currency": r["currency"], "description": r["description"], "cardholder": r["cardholder_name"]}
                for r in card_results['unmatched_card']
            ],
            "discrepancies_details": [
                {
                    "ledger_id": d["ledger_entry"]["id"],
                    "ledger_desc": d["ledger_entry"]["description"],
                    "card_id": d["card_line"]["id"],
                    "card_desc": d["card_line"]["description"],
                    "ledger_amount": d["ledger_amount"],
                    "card_amount": d["card_amount"],
                    "variance": d["variance"]
                }
                for d in card_results['discrepancies']
            ]
        },
        "bank_reconciliation": {
            "summary": {
                "total_bank_lines": len(bank_lines),
                "reconciled_matches": len(bank_results['matches']),
                "unmatched_ledger": len(bank_results['unmatched_ledger']),
                "unmatched_bank": len(bank_results['unmatched_bank']),
                "reconciled_ratio": bank_reconciled_ratio
            }
        }
    }
    
    report_path = os.path.join(os.path.dirname(__file__), "..", "data", "reconciliation_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=4)
    print(f"Full report exported to: data/reconciliation_report.json")
    print("==================================================================")

if __name__ == "__main__":
    run_pipeline()
