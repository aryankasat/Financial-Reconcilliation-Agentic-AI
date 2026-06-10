# Rule-Based Reconciliation Engine

This directory contains the rule-based matching engine designed to automatically reconcile ledger entries against bank and card statements from the SQLite database.

## Engine Structure

The code is organized into a modular design:
- **`database.py`**: Handles connection to `reconciliation.db` and maps table rows to dictionary lists.
- **`normalizers.py`**: Text cleaners and normalization rules, including:
  - Suffix cleaners (stripping employee cardholder suffixes like `- John Smith`).
  - Standard text normalizers (stripping standalone numbers, state/location descriptors, extra spacing, and converting to lowercase).
  - Contextual DBA mapping (resolving legal names on card statements, such as `Formagrid Inc` or `Agilebits Inc`, to their brand names `Airtable` or `1Password`).
  - A Levenshtein distance string similarity engine.
- **`reconciliation.py`**: Implements the matching pipeline stages for credit card and checking account records.
- **`main.py`**: Runs the engine pipeline across all ledger entries and statement lines, logs details of matches, flags discrepancies/anomalies in the terminal, and exports a JSON report.

---

## Reconciliation Matching Pipelines

### Credit Card Reconciliation
Matches ledger entries against credit card statement lines using a multi-stage process:

1. **Stage 1: Exact Matches**: Same amount, same currency (USD), date within 3 days, and exact matching normalized descriptions.
2. **Stage 2: Merchant Substring/Token Match**: Same amount, same currency (USD), date within 3 days, and matching merchant prefixes or substrings (e.g. matching `"uber"` or `"marriott"`).
3. **Stage 3: Contextual DBA Match**: Same amount, same currency (USD), date within 3 days, and DBA mappings resolving to the same entity (e.g., mapping `"WW Operating LLC"` to `"WeWork"`).
4. **Stage 4: Multi-Currency Match**: Date within 3 days, ledger currency matching statement `foreign_currency` (e.g. EUR, GBP), and ledger amount matching statement `foreign_amount` exactly.
5. **Stage 5: Fuzzy Matches**: Same amount, same currency (USD), date within 4 days, and Levenshtein similarity score `>= 0.70`.
6. **Stage 6: Amount Discrepancies**: Date within 3 days, matching merchant descriptions, but different amounts (flags tip/fee differences for review).
7. **Stage 7: Duplicate Ledger Entries**: Flags remaining unmatched ledger entries that share the same date, amount, and reference number (or description) as an already-matched transaction.

### Bank Reconciliation (Checking Account)
Matches checking ledger entries against bank statement lines:
1. **Amount & Date Match**: Matches exact amount and clears bank within 4 days of transaction date.
2. **Associative Keyword Match**: Checks if ledger and bank descriptions share associated business keywords (e.g. `rent` / `landlord`, `payroll`, `wire` / `customer`, or `stripe`).

---

## Execution Instructions

To execute the reconciliation pipeline and print the console dashboard report, run from the repository root:

```bash
PYTHONPATH=. python3 reconciliation_engine/main.py
```

This will run the pipeline and export a detailed JSON file at `data/reconciliation_report.json`.
