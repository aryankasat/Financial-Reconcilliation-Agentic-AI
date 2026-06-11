import os
import json
from langchain_core.messages import SystemMessage, HumanMessage
from agentic_reconciliation.state import AgenticState
from agentic_reconciliation.prompts import DECISION_SYSTEM_PROMPT
from agentic_reconciliation.agents.categorisation import get_groq_llm, parse_llm_json, invoke_llm_with_retry
from agentic_reconciliation.mock_responses import MOCK_RESPONSES

def decide_node(state: AgenticState) -> dict:
    """
    LangGraph node for the Decision Agent.
    """
    discrepancy = state["discrepancy"]
    category = state["category"]
    rca_analysis = state["rca_analysis"]
    
    disc_id = (
        discrepancy.get("ledger_id") or 
        discrepancy.get("id") or 
        discrepancy.get("card_id")
    )
    
    llm = get_groq_llm()
    
    if llm is None:
        # Fallback to simulation/mock mode
        mock = MOCK_RESPONSES.get(disc_id)
        if mock:
            decision_status = mock["decide"]["decision_status"]
            recommended_action = mock["decide"]["recommended_action"]
            suggested_fix = mock["decide"]["suggested_fix"]
        else:
            decision_status = "REQUIRES_HUMAN_INTERVENTION"
            recommended_action = "Manual check required."
            suggested_fix = "No simulation mock data available."
            
        print(f"[{disc_id}] [Decision Agent (SIMULATED)]: Concluded status as '{decision_status}'")
        return {
            "decision_status": decision_status,
            "recommended_action": recommended_action,
            "suggested_fix": suggested_fix
        }
        
    # Live execution using Groq
    print(f"[{disc_id}] [Decision Agent (LIVE)]: Invoking openai/gpt-oss-120b for final resolution decision...")
    
    messages = [
        SystemMessage(content=DECISION_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Discrepancy: {json.dumps(discrepancy, indent=2)}\n\n"
            f"Category: {category}\n\n"
            f"RCA Findings:\n{rca_analysis}"
        ))
    ]
    
    try:
        response = invoke_llm_with_retry(llm, messages)
        res_data = parse_llm_json(response.content)
        decision_status = res_data.get("status", "REQUIRES_HUMAN_INTERVENTION")
        recommended_action = res_data.get("recommended_action", "Review discrepancy details manually.")
        suggested_fix = res_data.get("suggested_fix", "No specific adjustment details supplied.")
    except Exception as e:
        print(f"[{disc_id}] [Decision Agent (LIVE ERROR)]: Fallback triggered due to: {e}")
        decision_status = "REQUIRES_HUMAN_INTERVENTION"
        recommended_action = f"Error occurred during live decision step: {str(e)}"
        suggested_fix = "Review discrepancy logs manually."
        
    print(f"[{disc_id}] [Decision Agent (LIVE)]: Concluded status as '{decision_status}'")
    return {
        "decision_status": decision_status,
        "recommended_action": recommended_action,
        "suggested_fix": suggested_fix
    }
