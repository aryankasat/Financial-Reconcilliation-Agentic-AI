import os
import json
import argparse
from dotenv import load_dotenv

# Load environment variables (like DATABASE_PATH and GROQ_API_KEY)
load_dotenv()

from agentic_reconciliation.graph import reconciliation_graph

# Terminal formatting styles
STYLE_BOLD_CYAN = "\033[1;36m"
STYLE_BOLD_GREEN = "\033[1;32m"
STYLE_BOLD_RED = "\033[1;31m"
STYLE_BOLD_YELLOW = "\033[1;33m"
STYLE_BOLD_WHITE = "\033[1;37m"
STYLE_DIM = "\033[2m"
STYLE_RESET = "\033[0m"

def print_separator(char="=", length=75, color=STYLE_BOLD_CYAN):
    print(f"{color}{char * length}{STYLE_RESET}")

def run_agentic_pipeline(single_id=None):
    # Resolve path to the source reconciliation report
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    report_path = os.path.join(base_dir, "data", "reconciliation_report.json")
    enriched_report_path = os.path.join(base_dir, "data", "agent_reconciliation_report.json")
    
    if not os.path.exists(report_path):
        print(f"{STYLE_BOLD_RED}Error: Reconciliation report not found at {report_path}.{STYLE_RESET}")
        print("Please run reconciliation_engine/main.py first to generate the report.")
        return

    with open(report_path, "r") as f:
        report = json.load(f)
        
    card_recon = report.get("card_reconciliation", {})
    
    # Extract discrepancy lists
    unmatched_ledger = card_recon.get("unmatched_ledger_details", [])
    unmatched_card = card_recon.get("unmatched_card_details", [])
    discrepancies = card_recon.get("discrepancies_details", [])
    
    # Combine everything into a flat list of items to analyze
    items_to_process = []
    
    for item in unmatched_ledger:
        item["_type"] = "unmatched_ledger"
        items_to_process.append(item)
        
    for item in unmatched_card:
        item["_type"] = "unmatched_card"
        items_to_process.append(item)
        
    for item in discrepancies:
        item["_type"] = "amount_discrepancy"
        # Set a common ID field for routing/indexing
        item["id"] = item.get("ledger_id") or item.get("card_id")
        items_to_process.append(item)
        
    # If filtered to a single ID
    if single_id:
        items_to_process = [item for item in items_to_process if item.get("id") == single_id]
        if not items_to_process:
            print(f"{STYLE_BOLD_RED}No discrepancy found matching ID: {single_id}{STYLE_RESET}")
            return
            
    print_separator()
    print(f"               {STYLE_BOLD_WHITE}LANGGRAPH AGENTIC RECONCILIATION PIPELINE{STYLE_RESET}")
    if os.getenv("GROQ_API_KEY"):
        print(f"               {STYLE_BOLD_GREEN}MODE: LIVE (LLM: openai/gpt-oss-120b via Groq){STYLE_RESET}")
    else:
        print(f"               {STYLE_BOLD_YELLOW}MODE: DRY-RUN SIMULATION (Pre-recorded traces & Live DB){STYLE_RESET}")
    print_separator()
    print(f"Found {len(items_to_process)} discrepancy item(s) to analyze.\n")
    
    enriched_items = []
    auto_resolved_count = 0
    human_intervention_count = 0
    
    for idx, item in enumerate(items_to_process, 1):
        item_id = item.get("id")
        item_type = item.get("_type")
        
        print(f"{STYLE_BOLD_WHITE}[{idx}/{len(items_to_process)}] Analyzing {item_type.replace('_', ' ').upper()} ID: {item_id}{STYLE_RESET}")
        
        # Display basic details
        if item_type == "unmatched_ledger":
            print(f"  Details: {item['date']} | {item['amount']} {item['currency']} | '{item['description']}'")
        elif item_type == "unmatched_card":
            print(f"  Details: {item['date']} | {item['amount']} {item['currency']} | '{item['description']}' | Cardholder: {item['cardholder']}")
        elif item_type == "amount_discrepancy":
            print(f"  Details: Ledger: '{item['ledger_desc']}' ({item['ledger_amount']} {item.get('ledger_currency', 'USD')})")
            print(f"           Card:   '{item['card_desc']}' ({item['card_amount']} {item.get('card_currency', 'USD')})")
            print(f"           Variance: {item['variance']} USD")
            
        print(f"  {STYLE_DIM}Invoking LangGraph State Workflow...{STYLE_RESET}")
        
        # Invoke LangGraph
        initial_state = {
            "discrepancy": item,
            "category": "",
            "categorisation_reasoning": "",
            "rca_analysis": "",
            "db_queries": [],
            "decision_status": "",
            "recommended_action": "",
            "suggested_fix": "",
            "messages": []
        }
        
        # Invoke LangGraph wrapped in collect_runs to capture LangSmith trace telemetry
        from langchain_core.tracers.context import collect_runs
        from langsmith import Client
        
        run_url = None
        with collect_runs() as cb:
            result = reconciliation_graph.invoke(initial_state)
            
        if cb.traced_runs:
            try:
                ls_client = Client()
                run_url = ls_client.get_run_url(run=cb.traced_runs[0])
                print(f"  -> {STYLE_BOLD_CYAN}LangSmith Trace URL:{STYLE_RESET} {run_url}")
            except Exception as e:
                # Fallback silently if credentials or internet are not configured
                pass
        
        # Extract outcomes
        category = result.get("category", "Other")
        reasoning = result.get("categorisation_reasoning", "")
        rca_analysis = result.get("rca_analysis", "")
        db_queries = result.get("db_queries", [])
        decision_status = result.get("decision_status", "REQUIRES_HUMAN_INTERVENTION")
        recommended_action = result.get("recommended_action", "")
        suggested_fix = result.get("suggested_fix", "")
        
        # Print Categorisation outcomes
        print(f"  -> {STYLE_BOLD_YELLOW}Classification:{STYLE_RESET} {category}")
        print(f"     Reasoning: {reasoning}")
        
        # Print SQL Queries Executed
        if db_queries:
            print(f"  -> {STYLE_BOLD_CYAN}Database Diagnostics (SQL queries run):{STYLE_RESET}")
            for q_idx, query_log in enumerate(db_queries, 1):
                query_str = query_log.get("query", "").strip()
                res_count = len(query_log.get("result", [])) if isinstance(query_log.get("result"), list) else 0
                print(f"     {q_idx}. {STYLE_DIM}{query_str}{STYLE_RESET} (Returned {res_count} row(s))")
                
        # Print RCA synthesis
        print(f"  -> {STYLE_BOLD_WHITE}Root Cause Analysis:{STYLE_RESET}")
        rca_lines = rca_analysis.strip().split('\n')
        # Clean up double headers
        rca_lines = [l for l in rca_lines if not l.startswith("RCA FINDINGS:")]
        for line in rca_lines:
            if line.strip():
                print(f"     {line.strip()}")
                
        # Print Decision outcomes
        status_color = STYLE_BOLD_GREEN if decision_status == "AUTO_RESOLVED" else STYLE_BOLD_RED
        print(f"  -> {STYLE_BOLD_WHITE}Resolution Status:{STYLE_RESET} {status_color}{decision_status}{STYLE_RESET}")
        print(f"     Recommended Action: {recommended_action}")
        print(f"     Suggested Fix: {suggested_fix}")
        print()
        
        # Keep track of counts
        if decision_status == "AUTO_RESOLVED":
            auto_resolved_count += 1
        else:
            human_intervention_count += 1
            
        # Store enriched item data
        enriched_item = item.copy()
        enriched_item.update({
            "agent_category": category,
            "agent_categorisation_reasoning": reasoning,
            "agent_rca_analysis": rca_analysis,
            "agent_decision_status": decision_status,
            "agent_recommended_action": recommended_action,
            "agent_suggested_fix": suggested_fix,
            "agent_db_queries": db_queries,
            "agent_langsmith_trace_url": run_url
        })
        enriched_items.append(enriched_item)
        print_separator("-", 50, STYLE_DIM)
        
    # Summarize runs and save
    if not single_id:
        print_separator()
        print(f"               {STYLE_BOLD_WHITE}AGENTIC PIPELINE PROCESSING SUMMARY{STYLE_RESET}")
        print_separator()
        print(f"Total Discrepancies Analyzed: {len(enriched_items)}")
        print(f"Auto-Resolved / Matched:       {STYLE_BOLD_GREEN}{auto_resolved_count}{STYLE_RESET}")
        print(f"Requires Human Intervention:   {STYLE_BOLD_RED}{human_intervention_count}{STYLE_RESET}")
        
        # Save enriched report
        report["card_reconciliation"]["enriched_discrepancies"] = enriched_items
        
        with open(enriched_report_path, "w") as f:
            json.dump(report, f, indent=4)
            
        print(f"\nEnriched reconciliation report successfully saved to:")
        print(f"  -> {STYLE_BOLD_GREEN}data/agent_reconciliation_report.json{STYLE_RESET}")
        print_separator()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LangGraph Reconciliation Agent")
    parser.cli_args = parser.add_argument("--id", help="Process only a single discrepancy ID (e.g. led_264a780d)")
    args = parser.parse_args()
    
    run_agentic_pipeline(single_id=args.id)
