# Credit Card & Bank Reconciliation Sandbox

This repository provides a realistic, modular testing sandbox for developing and benchmarking **Agentic AI systems** in retail payments, banking, and general ledger reconciliation. 

It contains a generated SQLite database populated with 3 months of synthetic financial data, together with a deterministic, rule-based matching engine that achieves high reconciliation accuracy while identifying key business anomalies.

---

## Reconciliation & Agentic Workflow

The diagram below maps the end-to-end transaction generation, rule-based matching, and agent-driven anomaly analysis pipeline:

```mermaid
flowchart TD
    subgraph Data & Matching Engine
        A[data/generate_db.py <br> Seed Database] -->|reconciliation.db| B[reconciliation_engine/main.py <br> Rule-Based Matching Engine]
        B -->|Perfect Matches| C[Reconciled Matches]
        B -->|Flagged Anomalies| D[data/reconciliation_report.json]
    end

    subgraph LangGraph Agentic Pipeline
        D -->|Exceptions| E[Categorisation Agent <br> Classify Variance Type]
        E -->|Category| F[RCA Agent <br> Dynamic SQL Diagnostics SELECT]
        F -->|Root Cause Findings| G[Decision Agent <br> Auto-Resolve vs Human Intervention]
        G -->|Enriched States| H[data/agent_reconciliation_report.json]
    end

    subgraph Review & Metrics
        H --> I[evaluation/evaluate.py <br> Calculate Technical/Business Metrics]
        H --> J[reports/reconciliation_final_report.md <br> Human-Readable Action Plan]
    end
```

### End-to-End Steps:
1. **Database Seeding (`data/generate_db.py`)**: Deterministically seeds the SQLite database (`reconciliation.db`) containing checking, card, and ledger transactions with specific pre-configured discrepancies (lags, tips, currency differences, potential fraud).
2. **Rule-Based Pre-Matching (`reconciliation_engine/main.py`)**: Filters out perfect matches, merchant name DBA resolving, and multi-currency matches, exporting all unresolved variances to `data/reconciliation_report.json`.
3. **Agentic Exception Handling (`agentic_reconciliation/main.py`)**:
   * **Categorisation**: Classifies the exceptions into specific accounting categories.
   * **Root Cause Analysis (RCA)**: Connects to the database safely (read-only) in a ReAct loop to inspect date ranges, currency exchange rates, subtotals (tips), or duplicate listings.
   * **Decision**: Decides if the discrepancy is `AUTO_RESOLVED` (generating adjustments) or `REQUIRES_HUMAN_INTERVENTION` (e.g. employee missing receipt, potential fraud card locks).
4. **Enriched Results Export**: Outputs details to `data/agent_reconciliation_report.json`.
5. **System Evaluation (`evaluation/evaluate.py`)**: Automatically computes technical and business metrics (reduction in manual work, fraud exposure prevented, categorisation accuracy, and tool use counts), writing them to `evaluation/evaluation_report.md`.
6. **Business Reporting (`reports/reconciliation_final_report.md`)**: Synthesizes the exact actions the accounting team must perform to close the month's books.

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
├── reconciliation_engine/
│   ├── README.md                 # Reconciliation matching pipeline stages guide
│   ├── database.py               # Database client mapping SQLite to dictionaries
│   ├── normalizers.py            # DBA resolvers, text cleaners, and fuzzy matchers
│   ├── reconciliation.py         # Multi-stage matching pipelines (card & bank)
│   └── main.py                   # Engine CLI pipeline runner and reporting dashboard
├── agentic_reconciliation/
│   ├── README.md                 # Documentation of agents (Categorisation, RCA, Decision)
│   ├── state.py                  # LangGraph state definition
│   ├── graph.py                  # StateGraph layout and node definitions
│   ├── main.py                   # CLI agent runner and report enricher
│   ├── agents/                   # Agents submodules (categorisation, rca, decision)
│   └── tools/                    # Read-only database querying tool
├── evaluation/
│   ├── README.md                 # Documentation of metrics accounted for
│   ├── evaluate.py               # Performance evaluation script
│   └── evaluation_report.md      # Detailed findings and performance statistics report
└── reports/
    └── reconciliation_final_report.md # Final human-readable report for accounting team
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

Open `.env` and configure your API keys. To run the live agentic workflow on Groq, configure your `GROQ_API_KEY`:
```env
GROQ_API_KEY=gsk_...
```
*Note: If no `GROQ_API_KEY` is present, the pipeline defaults to **Dry-Run Simulation Mode** which plays back pre-cached agent responses but executes the actual database lookup queries in real-time.*

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

### 4. Running the LangGraph Agentic Pipeline

Once the engine flags discrepancies, run the LangGraph-based agentic pipeline to categorize issues, perform database-driven Root Cause Analysis (RCA), and render final decisions on automated resolution or human intervention:

```bash
python3 -m agentic_reconciliation.main
```
This script will print colored execution logs detailing each agent's findings, log diagnostic database queries, and save the enriched report to `data/agent_reconciliation_report.json`.

To process a single discrepancy ID (for debugging):
```bash
python3 -m agentic_reconciliation.main --id <discrepancy_id>
```

### 5. Running the Performance Evaluation

To measure the agent pipeline's accuracy, query efficiency, manual workload reduction, and fraud exposure prevention:

```bash
python3 evaluation/evaluate.py
```
This script displays the performance report directly in the console. The findings are saved locally in [evaluation_report.md](file:///Users/aryankasat/Documents/Aryan/Codes/Financial-Reconcilliation-Agentic-AI/evaluation/evaluation_report.md).

### 6. Reviewing Accounting Action Reports

A human-readable summary detailing each discrepancy, its root cause, and concrete journal entries or security steps for the accounting team can be viewed at [reconciliation_final_report.md](file:///Users/aryankasat/Documents/Aryan/Codes/Financial-Reconcilliation-Agentic-AI/reports/reconciliation_final_report.md).

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