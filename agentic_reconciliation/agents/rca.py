import os
import json
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from agentic_reconciliation.state import AgenticState
from agentic_reconciliation.prompts import RCA_SYSTEM_PROMPT
from agentic_reconciliation.agents.categorisation import get_groq_llm, invoke_llm_with_retry
from agentic_reconciliation.mock_responses import MOCK_RESPONSES

@tool
def query_database_tool(sql_query: str) -> str:
    """
    Executes a read-only SQL SELECT query on the financial reconciliation SQLite database and returns the results.
    Only SELECT queries are allowed.
    """
    try:
        from agentic_reconciliation.tools.database_tools import query_database
        res = query_database(sql_query)
        return json.dumps(res, indent=2)
    except Exception as e:
        return f"Error executing query: {str(e)}"

def rca_node(state: AgenticState) -> dict:
    """
    LangGraph node for the RCA (Root Cause Analysis) Agent.
    """
    discrepancy = state["discrepancy"]
    category = state["category"]
    
    disc_id = (
        discrepancy.get("ledger_id") or 
        discrepancy.get("id") or 
        discrepancy.get("card_id")
    )
    
    llm = get_groq_llm()
    executed_queries = []
    
    if llm is None:
        # Fallback to simulation/mock mode
        mock = MOCK_RESPONSES.get(disc_id)
        if mock:
            # We run the suggested queries against the SQLite database in real-time
            # to verify DB status and record actual query outputs in the state.
            from agentic_reconciliation.tools.database_tools import query_database
            for query in mock["rca"].get("suggested_queries", []):
                try:
                    res = query_database(query)
                    executed_queries.append({"query": query, "result": res})
                except Exception as e:
                    executed_queries.append({"query": query, "result": f"Error: {e}"})
            
            print(f"[{disc_id}] [RCA Agent (SIMULATED)]: Ran {len(executed_queries)} SQL query checks.")
            return {
                "rca_analysis": mock["rca"]["analysis"],
                "db_queries": executed_queries
            }
        else:
            return {
                "rca_analysis": "No RCA simulation data available for this discrepancy.",
                "db_queries": []
            }
            
    # Live execution using Groq with Tools
    print(f"[{disc_id}] [RCA Agent (LIVE)]: Beginning investigation using openai/gpt-oss-120b and SQL query tools...")
    
    llm_with_tools = llm.bind_tools([query_database_tool])
    
    messages = [
        SystemMessage(content=RCA_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Discrepancy Details:\n{json.dumps(discrepancy, indent=2)}\n\n"
            f"Categorised As: {category}"
        ))
    ]
    
    max_steps = 6
    final_response_content = ""
    
    for step in range(max_steps):
        try:
            response = invoke_llm_with_retry(llm_with_tools, messages)
            messages.append(response)
            
            # Check if tool calls were requested
            if not response.tool_calls:
                final_response_content = response.content
                break
                
            for tool_call in response.tool_calls:
                if tool_call["name"] == "query_database_tool":
                    sql_query = tool_call["args"].get("sql_query")
                    print(f"[{disc_id}] [RCA Agent (LIVE SQL)]: Executing: {sql_query}")
                    
                    try:
                        from agentic_reconciliation.tools.database_tools import query_database
                        res = query_database(sql_query)
                        executed_queries.append({"query": sql_query, "result": res})
                        tool_output = json.dumps(res, indent=2)
                    except Exception as e:
                        tool_output = f"Error during query execution: {e}"
                        executed_queries.append({"query": sql_query, "result": tool_output})
                        
                    messages.append(ToolMessage(
                        content=tool_output,
                        tool_call_id=tool_call["id"],
                        name=tool_call["name"]
                    ))
        except Exception as e:
            print(f"[{disc_id}] [RCA Agent (LIVE ERROR)]: Error on step {step}: {e}")
            final_response_content = f"RCA failed due to error: {str(e)}"
            break
    else:
        # Reached max steps
        # Try to ask LLM for final response without tool capability
        try:
            messages.append(HumanMessage(content="Please synthesize your final findings now based on the queries executed."))
            response = invoke_llm_with_retry(llm, messages)
            final_response_content = response.content
        except Exception as e:
            final_response_content = f"RCA hit maximum steps and synthesis failed: {e}"
            
    print(f"[{disc_id}] [RCA Agent (LIVE)]: Investigation complete. Analysis compiled.")
    return {
        "rca_analysis": final_response_content,
        "db_queries": executed_queries
    }
