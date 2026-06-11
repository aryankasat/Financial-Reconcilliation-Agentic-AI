from langgraph.graph import StateGraph, END
from agentic_reconciliation.state import AgenticState
from agentic_reconciliation.agents.categorisation import categorise_node
from agentic_reconciliation.agents.rca import rca_node
from agentic_reconciliation.agents.decision import decide_node

def create_reconciliation_graph():
    """
    Constructs, wires up, and compiles the reconciliation analysis state graph.
    """
    workflow = StateGraph(AgenticState)
    
    # Define nodes in our pipeline
    workflow.add_node("categorise", categorise_node)
    workflow.add_node("rca", rca_node)
    workflow.add_node("decide", decide_node)
    
    # Wire the execution path sequentially
    workflow.set_entry_point("categorise")
    workflow.add_edge("categorise", "rca")
    workflow.add_edge("rca", "decide")
    workflow.add_edge("decide", END)
    
    # Compile and return the executable graph application
    return workflow.compile()

# Main compiled graph instance ready for import and execution
reconciliation_graph = create_reconciliation_graph()
