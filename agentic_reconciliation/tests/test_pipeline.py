import pytest
from agentic_reconciliation.tools.database_tools import is_query_safe, query_database
from agentic_reconciliation.graph import reconciliation_graph

def test_sql_safety():
    """
    Verifies that unsafe modification queries are blocked and SELECT queries are permitted.
    """
    assert is_query_safe("SELECT * FROM accounts;") is True
    assert is_query_safe("WITH temp AS (SELECT * FROM accounts) SELECT * FROM temp;") is True
    assert is_query_safe("   SELECT name FROM accounts   ") is True
    
    # Unsafe commands should return False
    assert is_query_safe("INSERT INTO accounts VALUES ('acc_test', 'Test', 'BANK', 'USD');") is False
    assert is_query_safe("UPDATE accounts SET currency = 'EUR';") is False
    assert is_query_safe("DELETE FROM accounts;") is False
    assert is_query_safe("DROP TABLE accounts;") is False
    assert is_query_safe("PRAGMA integrity_check;") is False

def test_query_database():
    """
    Verifies query execution against the SQLite database.
    """
    res = query_database("SELECT count(*) as count FROM accounts;")
    assert len(res) == 1
    assert "count" in res[0]
    assert res[0]["count"] > 0

def test_graph_dry_run():
    """
    Verifies that the state graph executes fully and yields expected classifications and decisions.
    """
    discrepancy = {
        "id": "led_264a780d",
        "date": "2026-06-29",
        "amount": 124.8,
        "currency": "USD",
        "description": "Amazon - Office Equipment"
    }
    initial_state = {
        "discrepancy": discrepancy,
        "category": "",
        "categorisation_reasoning": "",
        "rca_analysis": "",
        "db_queries": [],
        "decision_status": "",
        "recommended_action": "",
        "suggested_fix": "",
        "messages": []
    }
    
    result = reconciliation_graph.invoke(initial_state)
    assert result["category"] == "Timing Difference"
    assert "Amazon" in result["rca_analysis"] or "led_264a780d" in result["rca_analysis"]
    assert result["decision_status"] == "AUTO_RESOLVED"
    assert len(result["db_queries"]) > 0
