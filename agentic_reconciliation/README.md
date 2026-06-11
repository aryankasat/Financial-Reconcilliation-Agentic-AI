# Agentic Financial Reconciliation (LangGraph Workflow)

This folder contains a LangGraph-based agentic system designed to analyze and resolve financial reconciliation discrepancies between general ledgers and bank/credit card statements.

The workflow is built with modular Python modules utilizing LangGraph, LangChain, and Groq's high-performance `openai/gpt-oss-120b` model.

---

## 📂 Folder Structure

```
agentic_reconciliation/
├── README.md               # This documentation file
├── state.py                # Defines the LangGraph pipeline execution state
├── prompts.py              # System prompts for all three agents
├── graph.py                # LangGraph StateGraph configuration and node wireup
├── mock_responses.py       # Pre-recorded LLM outputs for dry-run simulation mode
├── main.py                 # CLI tool to run the pipeline on discrepancy reports
├── evaluate.py             # Evaluation script to compute business & technical metrics
├── agents/                 # Pipeline agent nodes
│   ├── __init__.py
│   ├── categorisation.py   # Classifies discrepancies into appropriate groups
│   ├── rca.py              # Queries the DB to compile Root Cause Analysis logs
│   └── decision.py         # Concludes resolution actions and suggested corrections
├── tools/                  # Executable tools for agents
│   ├── __init__.py
│   └── database_tools.py   # Safe, read-only SQLite database query execution
└── tests/                  # Automated verification suite
    ├── __init__.py
    └── test_pipeline.py    # Pytest cases checking safe SQL and state graph runs
```

---

## 🤖 The Three Agents

Our reconciliation pipeline consists of three specialized agents that execute sequentially inside the LangGraph state machine:

1.  **Categorisation Agent** ([categorisation.py](file:///Users/aryankasat/Documents/Aryan/Codes/Financial-Reconcilliation-Agentic-AI/agentic_reconciliation/agents/categorisation.py)):
    Classifies a discrepancy (e.g. amount variance or unmatched entry) into one of the core transaction types:
    *   *Timing Difference*
    *   *Amount Discrepancy*
    *   *Missing Ledger Entry*
    *   *Duplicate Ledger Entry*
    *   *Unrecognized Card Charge (Potential Fraud)*
2.  **Root Cause Analysis (RCA) Agent** ([rca.py](file:///Users/aryankasat/Documents/Aryan/Codes/Financial-Reconcilliation-Agentic-AI/agentic_reconciliation/agents/rca.py)):
    Investigates why the discrepancy occurred by utilizing a tool-calling ReAct loop. It runs SQL commands against `data/reconciliation.db` (via [database_tools.py](file:///Users/aryankasat/Documents/Aryan/Codes/Financial-Reconcilliation-Agentic-AI/agentic_reconciliation/tools/database_tools.py)) to look for corresponding transactions, timing gaps, or conversion rates, generating a detailed technical report.
3.  **Decision Agent** ([decision.py](file:///Users/aryankasat/Documents/Aryan/Codes/Financial-Reconcilliation-Agentic-AI/agentic_reconciliation/agents/decision.py)):
    Determines if the discrepancy can be cleared automatically (`AUTO_RESOLVED`) or requires human review (`REQUIRES_HUMAN_INTERVENTION`). It outputs a recommended action and a suggested accounting fix (e.g., correcting journal entry or dispute instruction).

---

## ⚡ How to Run

### 1. Prerequisites
Ensure you have the virtual environment activated and dependencies installed:
```bash
source venv/bin/activate
pip install langgraph langchain-groq
```

### 2. Configure Environment (Optional for Live Run)
Add your Groq API key to your `.env` file in the project root:
```env
GROQ_API_KEY=gsk_...
```
> [!NOTE]
> If `GROQ_API_KEY` is not present, the system automatically runs in **Dry-Run Simulation Mode**. It loads pre-recorded reasoning outputs for the seeded dataset but still queries the local database in real-time, allowing you to test the pipeline flow and inspect tool query logs immediately.

### 3. Run Pipeline on Reconciliation Report
Generate the discrepancy report from the reconciliation engine, then run the agentic pipeline:
```bash
# 1. Generate the source report
python3 -m reconciliation_engine.main

# 2. Run the agentic enrichment
python3 -m agentic_reconciliation.main
```
This prints a colored terminal log of agent thinking processes, diagnostic SQL queries run, and final decisions, and exports the enriched report to [agent_reconciliation_report.json](file:///Users/aryankasat/Documents/Aryan/Codes/Financial-Reconcilliation-Agentic-AI/data/agent_reconciliation_report.json).

To process a single discrepancy ID (for fast debugging), use the `--id` flag:
```bash
python3 -m agentic_reconciliation.main --id led_264a780d
```

### 4. Evaluate Metrics
Compute business performance metrics (Manual workload reduction, Auto-reconciliation value) and technical metrics (Accuracy, SQL query success rates):
```bash
python3 -m agentic_reconciliation.evaluate
```

### 5. Run Unit Tests
Execute the automated test suite to verify graph transitions and SQL safety checks:
```bash
pytest agentic_reconciliation/tests/
```

---

## 🛡️ Database Safety
The RCA agent is equipped with a `query_database` tool. To protect company data:
*   Only read-only SQL queries (`SELECT`) are permitted.
*   Modification keywords (e.g. `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `PRAGMA`) are strictly validated and blocked at the tool interface level, returning a warning to the agent.
