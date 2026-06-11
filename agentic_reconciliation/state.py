from typing import Dict, Any, List, TypedDict, Annotated
import operator
from langchain_core.messages import BaseMessage

class AgenticState(TypedDict):
    """
    State representing the context of a financial reconciliation discrepancy analysis.
    """
    # Input discrepancy data (from reconciliation report JSON or direct structure)
    discrepancy: Dict[str, Any]
    
    # Categorisation Agent outputs
    category: str  # Class: "Timing Difference", "Missing Ledger Entry", "Amount Discrepancy", "Duplicate Ledger Entry", "Unrecognized Card Charge (Potential Fraud)", "Other"
    categorisation_reasoning: str
    
    # RCA Agent outputs
    rca_analysis: str
    db_queries: List[Dict[str, Any]]  # Record of database queries executed: [{"query": str, "result": List[Dict[str, Any]]}]
    
    # Decision Agent outputs
    decision_status: str  # "AUTO_RESOLVED" | "REQUIRES_HUMAN_INTERVENTION"
    recommended_action: str
    suggested_fix: str    # Recommended ledger/process corrections
    
    # Message log for debugging / trace
    messages: Annotated[List[BaseMessage], operator.add]
