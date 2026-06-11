import os
import json
import re
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from agentic_reconciliation.state import AgenticState
from agentic_reconciliation.prompts import CATEGORISATION_SYSTEM_PROMPT
from agentic_reconciliation.mock_responses import MOCK_RESPONSES

def get_groq_llm(model="openai/gpt-oss-120b"):
    """
    Returns a ChatGroq LLM instance if GROQ_API_KEY is available, else returns None.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return None
    return ChatGroq(
        model_name=model,
        groq_api_key=groq_api_key,
        temperature=0.0
    )

def parse_llm_json(text: str) -> dict:
    """
    Safely extracts and parses a JSON object from LLM response text.
    """
    text = text.strip()
    # Strip markdown block wraps
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    try:
        return json.loads(text)
    except Exception:
        # Fallback to regex extraction of the first curly brace pair
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        raise ValueError(f"Could not parse valid JSON from LLM output: {text}")

import time

def invoke_llm_with_retry(llm, messages, max_retries=4, initial_delay=3.0):
    """
    Invokes the LLM with simple retry backoff on 429 Rate Limit errors.
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "rate_limit" in err_str.lower() or "rate limit" in err_str.lower():
                print(f"       [Rate Limit (429) hit. Retrying in {delay}s... (Attempt {attempt+1}/{max_retries})]")
                time.sleep(delay)
                delay *= 2
            else:
                raise e
    return llm.invoke(messages)

def categorise_node(state: AgenticState) -> dict:
    """
    LangGraph node for the Categorisation Agent.
    """
    discrepancy = state["discrepancy"]
    
    # Identify unique identifier key
    disc_id = (
        discrepancy.get("ledger_id") or 
        discrepancy.get("id") or 
        discrepancy.get("card_id")
    )
    
    llm = get_groq_llm()
    
    if llm is None:
        # Dry-run fallback mode
        mock = MOCK_RESPONSES.get(disc_id)
        if mock:
            category = mock["categorise"]["category"]
            reasoning = mock["categorise"]["reasoning"]
        else:
            category = "Other"
            reasoning = f"No simulation mock response found for discrepancy ID '{disc_id}' and GROQ_API_KEY is not set."
            
        print(f"[{disc_id}] [Categorisation Agent (SIMULATED)]: Classifying as '{category}'")
        return {
            "category": category,
            "categorisation_reasoning": reasoning
        }
        
    # Live execution mode using Groq
    print(f"[{disc_id}] [Categorisation Agent (LIVE)]: Invoking openai/gpt-oss-120b...")
    
    # Format user message
    discrepancy_str = json.dumps(discrepancy, indent=2)
    messages = [
        SystemMessage(content=CATEGORISATION_SYSTEM_PROMPT),
        HumanMessage(content=f"Please categorise the following discrepancy:\n\n{discrepancy_str}")
    ]
    
    try:
        response = invoke_llm_with_retry(llm, messages)
        res_data = parse_llm_json(response.content)
        category = res_data.get("category", "Other")
        reasoning = res_data.get("reasoning", "No reasoning provided.")
    except Exception as e:
        print(f"[{disc_id}] [Categorisation Agent (LIVE ERROR)]: Fallback triggered due to: {e}")
        # Graceful fallback on LLM failure
        category = "Other"
        reasoning = f"Error during live classification: {str(e)}"
        
    print(f"[{disc_id}] [Categorisation Agent (LIVE)]: Classified as '{category}'")
    return {
        "category": category,
        "categorisation_reasoning": reasoning
    }
