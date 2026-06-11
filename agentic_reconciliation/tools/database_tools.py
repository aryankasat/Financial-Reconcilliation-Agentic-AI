import os
import sqlite3
from typing import List, Dict, Any
from reconciliation_engine.database import get_connection

def is_query_safe(sql_query: str) -> bool:
    """
    Validates that a SQL query is read-only.
    """
    clean_query = sql_query.strip().lower()
    
    # We only permit SELECT queries. 
    # Reject modifications: INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, REPLACE, PRAGMA.
    # Check if the query starts with select or with a common table expression (WITH ... SELECT)
    if not (clean_query.startswith("select") or clean_query.startswith("with")):
        return False
        
    unsafe_keywords = ["insert", "update", "delete", "drop", "create", "alter", "replace", "pragma", "vacuum", "exec"]
    for keyword in unsafe_keywords:
        # Check if the word is present as a standalone token
        words = clean_query.split()
        if keyword in words or any(f"{keyword}_" in w for w in words):
            return False
            
    return True

def query_database(sql_query: str) -> List[Dict[str, Any]]:
    """
    Executes a read-only SQL SELECT query on the financial reconciliation database and returns rows as dictionaries.
    
    Args:
        sql_query (str): The SQL query to run. Must be read-only (SELECT).
        
    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing the query results.
    """
    if not is_query_safe(sql_query):
        raise ValueError("Unsafe or non-read-only SQL query detected. Only SELECT statements are allowed.")
        
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        return [{"error": str(e)}]
