from datetime import datetime
from reconciliation_engine.normalizers import get_normalized_description, string_similarity

def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def date_diff_days(date_str1, date_str2):
    d1 = parse_date(date_str1)
    d2 = parse_date(date_str2)
    return abs((d1 - d2).days)

def check_bank_keywords(led_desc, bank_desc):
    led_desc = led_desc.lower()
    bank_desc = bank_desc.lower()
    
    # Keyword associations for checking account bank reconciliation
    associations = [
        (["rent", "landlord"], ["rent", "landlord"]),
        (["payroll"], ["payroll"]),
        (["wire", "customer", "inbound"], ["wire", "customer"]),
        (["stripe", "autopay", "card"], ["stripe", "autopay", "card"])
    ]
    for led_words, bank_words in associations:
        led_match = any(w in led_desc for w in led_words)
        bank_match = any(w in bank_desc for w in bank_words)
        if led_match and bank_match:
            return True
    return False

def reconcile_card_transactions(ledger_entries, card_lines):
    """
    Reconciles credit card ledger entries with credit card statement lines.
    Returns:
        dict: {
            "matches": [...],
            "discrepancies": [...],  # Matches with amount differences
            "unmatched_ledger": [...],
            "unmatched_card": [...],
            "duplicates": [...]      # Duplicate ledger items
        }
    """
    # Filter out credit card payment entries (reconciled separately or via checking)
    cc_ledger = [r for r in ledger_entries if r["category"] != "Credit Card Payment"]
    cc_lines = [r for r in card_lines if r["cardholder_name"] != "System"] # exclude System payments
    
    # Track matching status
    matched_ledger_ids = set()
    matched_card_ids = set()
    
    matches = []
    discrepancies = []
    duplicates = []

    # STAGE 1: Exact Matches (Same Amount, Same Currency, Close Dates, Exact Normalized Description)
    for led in cc_ledger:
        if led["id"] in matched_ledger_ids:
            continue
        for card in cc_lines:
            if card["id"] in matched_card_ids:
                continue
            
            same_amount = abs(led["amount"] - card["amount"]) < 0.001
            same_currency = led["currency"] == "USD" and card["currency"] == "USD"
            close_date = date_diff_days(led["transaction_date"], card["transaction_date"]) <= 3
            
            if same_amount and same_currency and close_date:
                led_desc = get_normalized_description(led["description"])
                card_desc = get_normalized_description(card["description"])
                if led_desc == card_desc:
                    matches.append({
                        "ledger_entry": led,
                        "card_line": card,
                        "rule": "Exact Match (Amount, Date, Description)"
                    })
                    matched_ledger_ids.add(led["id"])
                    matched_card_ids.add(card["id"])
                    break

    # STAGE 2: Merchant Name / Substring Match (Same Amount, Same Currency, Close Dates, Substring/Merchant/Token match)
    for led in cc_ledger:
        if led["id"] in matched_ledger_ids:
            continue
        for card in cc_lines:
            if card["id"] in matched_card_ids:
                continue
            
            same_amount = abs(led["amount"] - card["amount"]) < 0.001
            same_currency = led["currency"] == "USD" and card["currency"] == "USD"
            close_date = date_diff_days(led["transaction_date"], card["transaction_date"]) <= 3
            
            if same_amount and same_currency and close_date:
                led_norm = get_normalized_description(led["description"])
                card_desc_norm = get_normalized_description(card["description"])
                card_merch_norm = get_normalized_description(card["merchant_name"])
                
                # Extract first word tokens
                card_merch_first = card_merch_norm.split()[0] if card_merch_norm else ""
                card_desc_first = card_desc_norm.split()[0] if card_desc_norm else ""
                
                # Check for direct substrings or first-word token overlaps
                if (card_merch_norm in led_norm or led_norm in card_merch_norm or 
                    card_desc_norm in led_norm or led_norm in card_desc_norm or
                    (card_merch_first and card_merch_first in led_norm) or
                    (card_desc_first and card_desc_first in led_norm)):
                    matches.append({
                        "ledger_entry": led,
                        "card_line": card,
                        "rule": "Merchant Substring/Token Match"
                    })
                    matched_ledger_ids.add(led["id"])
                    matched_card_ids.add(card["id"])
                    break

    # STAGE 3: Contextual DBA Match (Same Amount, Same Currency, Close Dates, Contextual DBA Resolve)
    for led in cc_ledger:
        if led["id"] in matched_ledger_ids:
            continue
        for card in cc_lines:
            if card["id"] in matched_card_ids:
                continue
            
            same_amount = abs(led["amount"] - card["amount"]) < 0.001
            same_currency = led["currency"] == "USD" and card["currency"] == "USD"
            close_date = date_diff_days(led["transaction_date"], card["transaction_date"]) <= 3
            
            if same_amount and same_currency and close_date:
                led_norm = get_normalized_description(led["description"])
                card_desc_norm = get_normalized_description(card["description"])
                card_merch_norm = get_normalized_description(card["merchant_name"])
                
                # Check if DBA mapping resolves them to the same thing
                if led_norm == card_desc_norm or led_norm == card_merch_norm:
                    matches.append({
                        "ledger_entry": led,
                        "card_line": card,
                        "rule": "Contextual DBA Match"
                    })
                    matched_ledger_ids.add(led["id"])
                    matched_card_ids.add(card["id"])
                    break

    # STAGE 4: Multi-Currency Reconciliations (Foreign Currency match)
    for led in cc_ledger:
        if led["id"] in matched_ledger_ids:
            continue
        if led["currency"] == "USD":
            continue # Skip USD ledger items
            
        for card in cc_lines:
            if card["id"] in matched_card_ids:
                continue
            if card["foreign_currency"] != led["currency"]:
                continue # foreign currency must match ledger currency
                
            same_foreign_amount = abs(led["amount"] - card["foreign_amount"]) < 0.001
            close_date = date_diff_days(led["transaction_date"], card["transaction_date"]) <= 3
            
            if same_foreign_amount and close_date:
                matches.append({
                    "ledger_entry": led,
                    "card_line": card,
                    "rule": f"Multi-Currency Match ({led['currency']})"
                })
                matched_ledger_ids.add(led["id"])
                matched_card_ids.add(card["id"])
                break

    # STAGE 5: Fuzzy Matches (Same Amount, Same Currency, Close Dates, similarity >= 0.70)
    for led in cc_ledger:
        if led["id"] in matched_ledger_ids:
            continue
        
        best_match = None
        best_score = 0.0
        
        for card in cc_lines:
            if card["id"] in matched_card_ids:
                continue
                
            same_amount = abs(led["amount"] - card["amount"]) < 0.001
            same_currency = led["currency"] == "USD" and card["currency"] == "USD"
            close_date = date_diff_days(led["transaction_date"], card["transaction_date"]) <= 4
            
            if same_amount and same_currency and close_date:
                score = string_similarity(led["description"], card["description"])
                if score >= 0.70 and score > best_score:
                    best_score = score
                    best_match = card
                    
        if best_match:
            matches.append({
                "ledger_entry": led,
                "card_line": best_match,
                "rule": f"Fuzzy Match (Similarity: {best_score:.2f})"
            })
            matched_ledger_ids.add(led["id"])
            matched_card_ids.add(best_match["id"])

    # STAGE 6: Amount Discrepancies (Close dates, substring/token description overlap, but amounts differ)
    for led in cc_ledger:
        if led["id"] in matched_ledger_ids:
            continue
            
        best_match = None
        best_rule = ""
        
        for card in cc_lines:
            if card["id"] in matched_card_ids:
                continue
                
            close_date = date_diff_days(led["transaction_date"], card["transaction_date"]) <= 3
            
            if close_date:
                led_norm = get_normalized_description(led["description"])
                card_desc_norm = get_normalized_description(card["description"])
                card_merch_norm = get_normalized_description(card["merchant_name"])
                
                # Extract first word tokens
                card_merch_first = card_merch_norm.split()[0] if card_merch_norm else ""
                card_desc_first = card_desc_norm.split()[0] if card_desc_norm else ""
                
                # Check for description overlaps
                desc_match = (card_merch_norm in led_norm or led_norm in card_merch_norm or 
                              card_desc_norm in led_norm or led_norm in card_desc_norm or
                              (card_merch_first and card_merch_first in led_norm) or
                              (card_desc_first and card_desc_first in led_norm))
                
                if desc_match:
                    best_match = card
                    best_rule = "Amount Discrepancy (Merchant Prefix Match)"
                    break
                    
        if best_match:
            discrepancies.append({
                "ledger_entry": led,
                "card_line": best_match,
                "ledger_amount": led["amount"],
                "ledger_currency": led["currency"],
                "card_amount": best_match["amount"],
                "card_currency": best_match["currency"],
                "variance": round(best_match["amount"] - led["amount"], 2),
                "rule": best_rule
            })
            matched_ledger_ids.add(led["id"])
            matched_card_ids.add(best_match["id"])

    # STAGE 7: Duplicate Ledger Entries detection
    for led in cc_ledger:
        if led["id"] in matched_ledger_ids:
            continue
            
        for match in matches:
            card = match["card_line"]
            same_amount = abs(led["amount"] - card["amount"]) < 0.001
            same_currency = led["currency"] == "USD" and card["currency"] == "USD"
            close_date = date_diff_days(led["transaction_date"], card["transaction_date"]) <= 2
            
            if same_amount and same_currency and close_date:
                # Check for same reference number or description matching
                same_ref = led["reference_number"] and led["reference_number"] == match["ledger_entry"].get("reference_number")
                
                led_desc = get_normalized_description(led["description"])
                card_desc = get_normalized_description(card["description"])
                card_merch = get_normalized_description(card["merchant_name"])
                card_merch_first = card_merch.split()[0] if card_merch else ""
                
                desc_match = led_desc == card_desc or (card_merch_first and card_merch_first in led_desc)
                
                if same_ref or desc_match:
                    duplicates.append({
                        "duplicate_ledger_entry": led,
                        "original_ledger_entry": match["ledger_entry"],
                        "matched_card_line": card,
                        "reason": "Duplicate Ledger entry matching already reconciled card transaction."
                    })
                    matched_ledger_ids.add(led["id"]) # mark as resolved duplicate
                    break

    # Unmatched entries
    unmatched_ledger = [led for led in cc_ledger if led["id"] not in matched_ledger_ids]
    unmatched_card = [card for card in cc_lines if card["id"] not in matched_card_ids]

    return {
        "matches": matches,
        "discrepancies": discrepancies,
        "unmatched_ledger": unmatched_ledger,
        "unmatched_card": unmatched_card,
        "duplicates": duplicates
    }

def reconcile_bank_transactions(ledger_entries, bank_lines):
    """
    Reconciles checking account ledger entries with checking statement lines.
    """
    checking_ledger = [r for r in ledger_entries if r["account_id"] == "acc_checking"]
    
    matched_ledger_ids = set()
    matched_bank_ids = set()
    
    matches = []
    
    # Bank matching loop
    for led in checking_ledger:
        if led["id"] in matched_ledger_ids:
            continue
        for bank in bank_lines:
            if bank["id"] in matched_bank_ids:
                continue
                
            same_amount = abs(led["amount"] - bank["amount"]) < 0.001
            led_date = parse_date(led["transaction_date"])
            val_date = parse_date(bank["value_date"])
            # Value date should clear on or after ledger date, within 4 days
            date_ok = led_date <= val_date and (val_date - led_date).days <= 4
            
            if same_amount and date_ok:
                if check_bank_keywords(led["description"], bank["description"]):
                    matches.append({
                        "ledger_entry": led,
                        "bank_line": bank,
                        "rule": "Bank Statement Keyword Match"
                    })
                    matched_ledger_ids.add(led["id"])
                    matched_bank_ids.add(bank["id"])
                    break
                    
    unmatched_ledger = [led for led in checking_ledger if led["id"] not in matched_ledger_ids]
    unmatched_bank = [bank for bank in bank_lines if bank["id"] not in matched_bank_ids]
    
    return {
        "matches": matches,
        "unmatched_ledger": unmatched_ledger,
        "unmatched_bank": unmatched_bank
    }
