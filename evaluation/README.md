# Agentic Reconciliation Evaluation Module

This folder contains the evaluation scripts and findings reports for testing the performance of the LangGraph-based reconciliation agents.

---

## 📂 Folder Contents
1.  **`evaluate.py`**: A standalone Python script that parses the agent-enriched reconciliation report and calculates key operational and technical performance metrics.
2.  **`evaluation_report.md`**: A detailed document summarizing the findings, statistics, and business values of the agent workflow.

---

## 📈 Accounted Metrics

### Business Metrics (Operational Value)
*   **Auto-Reconciliation Rate**: The percentage of discrepancy items that the agent resolved autonomously (e.g. creating adjustive ledger entries or marking timing differences).
*   **Manual Workload Reduction**: Direct reduction in manual review ticket volume, saving operational accounting hours.
*   **Total Discrepancy Value**: Total dollar amount of variances, analyzed by resolved vs. flagged distributions.
*   **Risk Mitigation**: Captures unrecognized or potentially fraudulent card charges.

### Technical Metrics (Model Robustness)
*   **Categorisation Accuracy**: Ratio of agent classifications matching ground truth expert classifications.
*   **Average SQL Queries per RCA Run**: Tracks the tool use efficiency of the RCA agent.
*   **RCA SQL Success Rate**: Ratio of successfully executed SQL SELECT queries to check for syntax bugs or database lookup errors.
*   **Decision Explainability**: Ensures 100% of final agent actions have clear, human-auditable text explanations.

---

## ⚡ How to Run

To execute the evaluation script and print the metrics report to the terminal:

```bash
# Ensure you are at the project root folder
python3 evaluation/evaluate.py
```

*Note: The script requires `data/agent_reconciliation_report.json` to be generated first. If you haven't run the agent workflow yet, do so by running `python3 -m agentic_reconciliation.main`.*
