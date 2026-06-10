# Credit Card & Bank Reconciliation Sandbox

This repository provides a realistic, modular testing sandbox for developing and benchmarking **Agentic AI systems** in retail payments, banking, and general ledger reconciliation. 

It contains a generated SQLite database populated with 3 months of synthetic financial data, together with a deterministic, rule-based matching engine that achieves high reconciliation accuracy while identifying key business anomalies.

---

## Directory Structure

```
├── .env                          # Local environment secrets and LLM keys
├── .env.example                  # Template environment variables
├── requirements.txt              # Package dependencies for agents and data processes
├── venv/                         # Python virtual environment (auto-created)
├── data/
│   ├── README.md                 # Database schema details and test case list
│   ├── generate_db.py            # SQLite database generation script
│   └── reconciliation.db         # Synthetic SQLite database (Apr - Jun 2026 data)
└── reconciliation_engine/
    ├── README.md                 # Reconciliation matching pipeline stages guide
    ├── database.py               # Database client mapping SQLite to dictionaries
    ├── normalizers.py            # DBA resolvers, text cleaners, and fuzzy matchers
    ├── reconciliation.py         # Multi-stage matching pipelines (card & bank)
    └── main.py                   # Engine CLI pipeline runner and reporting dashboard
```

---

## Getting Started

### 1. Environment Setup

The workspace is configured with a virtual environment (`venv`) and package dependencies. To activate it and initialize environment files:

```bash
# Activate virtual environment
source venv/bin/activate

# Copy the example environment file
cp .env.example .env
```

Open `.env` and configure your API keys (e.g., `GEMINI_API_KEY`, `OPENAI_API_KEY`) to run downstream agentic AI workflows.

### 2. Regenerating the Data

If you need to reset the sandbox or regenerate the database seed data, run:

```bash
python3 data/generate_db.py
```
*Note: This script dynamically generates all transactions and calculates statement balances to create a closed payment loop between the checking account and the corporate credit card.*

### 3. Running the Reconciliation Engine

Execute the rule-based matching engine runner to reconcile checking and credit card statements:

```bash
PYTHONPATH=. python3 reconciliation_engine/main.py
```

This runner will output a complete CLI reporting dashboard and export a structured JSON report to `data/reconciliation_report.json` with details of all resolved matches and identified anomalies.

---

## Reconciliation Test Cases (Anomalies)

The sandbox database contains specific, pre-configured financial anomalies that must be identified by matching pipelines or AI agents:

1. **Merchant DBA Normalization**: Mapping statement legal/corporate names (e.g., `Formagrid Inc`, `Agilebits Inc`, `WW Operating LLC`) to brand names (`Airtable`, `1Password`, `WeWork`).
2. **Timing Differences**: Outstanding entries booked in the ledger in late June that clear bank/credit statements in early July.
3. **Missing Ledger Entries**: Unrecorded statement lines (e.g., employee did not submit a receipt).
4. **Amount Discrepancies**: Discrepancies resulting from credit card tips, conversion rates, or manual typing errors (e.g., manual Chipotle lunch booking vs. actual card swipe amount).
5. **Duplicate Entries**: Duplicate bookings in the general ledger representing the same physical charge.
6. **Unrecognized Charges (Fraud)**: Unregistered high-value statement transactions (e.g., `$450.00` charge at `Electronics Direct`).
7. **Multi-Currency Alignment**: Transactions billed in USD but processed in foreign currencies (EUR, GBP, CAD) containing foreign amount metadata.