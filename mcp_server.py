import os
import sys
import sqlite3
import json
from typing import List, Dict, Any

# Ensure project root is in python path so imports resolve correctly when run from other directories
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import DB helper functions
from reconciliation_engine.database import get_connection
from agentic_reconciliation.tools.database_tools import query_database, is_query_safe

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("Apex Reconciliation DB Server")

@mcp.tool()
def run_query(sql_query: str) -> str:
    """
    Executes a read-only SQL SELECT query on the financial reconciliation database.
    Only SELECT statements are permitted.
    
    Args:
        sql_query (str): The SELECT query to execute.
    """
    # Enforce read-only SELECT rules
    if not is_query_safe(sql_query):
        return "Error: Unsafe or non-read-only SQL query detected. Only SELECT statements are allowed."
    
    try:
        res = query_database(sql_query)
        return json.dumps(res, indent=2)
    except Exception as e:
        return f"Error executing query: {str(e)}"

@mcp.tool()
def list_tables() -> str:
    """
    Lists all tables in the financial reconciliation database.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return json.dumps({"tables": tables}, indent=2)
    except Exception as e:
        return f"Error listing tables: {str(e)}"

@mcp.tool()
def get_table_schema(table_name: str) -> str:
    """
    Retrieves the schema (column details) for a given table in the database.
    
    Args:
        table_name (str): The name of the table to retrieve schema for.
    """
    # Restrict to known tables to prevent injection
    valid_tables = ["accounts", "ledger_entries", "bank_statement_lines", "card_statement_lines"]
    if table_name not in valid_tables:
        return f"Error: Invalid table name '{table_name}'. Valid tables are: {', '.join(valid_tables)}"
        
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [
            {
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": bool(row[3]),
                "dflt_value": row[4],
                "pk": bool(row[5])
            }
            for row in cursor.fetchall()
        ]
        conn.close()
        return json.dumps({"table": table_name, "schema": columns}, indent=2)
    except Exception as e:
        return f"Error fetching schema: {str(e)}"

@mcp.tool()
def preview_table(table_name: str, limit: int = 50) -> str:
    """
    Retrieves the first N records from a table in the database.
    
    Args:
        table_name (str): The name of the table to preview.
        limit (int): The maximum number of records to return (default is 50, maximum is 200).
    """
    valid_tables = ["accounts", "ledger_entries", "bank_statement_lines", "card_statement_lines"]
    if table_name not in valid_tables:
        return f"Error: Invalid table name '{table_name}'. Valid tables are: {', '.join(valid_tables)}"
        
    # Cap limit to prevent large output responses
    limit = min(max(1, limit), 200)
    
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT ?;", (limit,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return json.dumps(rows, indent=2)
    except Exception as e:
        return f"Error previewing table: {str(e)}"

if __name__ == "__main__":
    # In FastMCP, calling run() starts the server on stdio.
    mcp.run()
