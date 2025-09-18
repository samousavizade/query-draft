"""
Module: sql_validate_query.py

This module is responsible for validating SQL queries to ensure they adhere to security and business rules.
It checks for forbidden keywords, ensures only allowed tables are referenced, and enforces a maximum row limit.

Environment Variables:
- SQL_MAX_LIMIT: The maximum number of rows to return in the SQL query (default: 100).

Dependencies:
- os: For accessing environment variables.
- sqlparse: For parsing and analyzing SQL statements.
- ..data_model.agent_states: Contains the `AgentState` type definition.
- .utils: Contains helper functions `_extract_tables`, `_contains_forbidden`, and `_inject_safe_limit`.

Constants:
- ALLOWED_TABLES: A set of table names that are allowed to be queried.
- FORBIDDEN_KEYWORDS: A set of SQL keywords that are forbidden for security reasons.
- MAX_LIMIT: The maximum number of rows to return in the SQL query, retrieved from the environment variable.

Functions:
- validate_sql(state: AgentState) -> AgentState: Validates the SQL query in the agent state.
"""

import os
from ..data_model.agent_states import AgentState
from .utils import _extract_tables, _contains_forbidden, _inject_safe_limit
import sqlparse

# A set of table names that are allowed to be queried
ALLOWED_TABLES = {
    "customers",
    "products",
    "orders",
    "CURRENT_DATE",
}

# A set of SQL keywords that are forbidden for security reasons
FORBIDDEN_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "truncate",
    "alter",
    "create",
    "grant",
    "revoke",
    "call",
    "execute"
}

# The maximum number of rows to return in the SQL query, retrieved from the environment variable
MAX_LIMIT = int(os.getenv("SQL_MAX_LIMIT", "100"))


def validate_sql(state: AgentState) -> AgentState:
    """
    Validates the SQL query in the agent state to ensure it adheres to security and business rules.

    This function performs the following checks:
    - Ensures the SQL query is not empty.
    - Checks for forbidden keywords in the SQL query.
    - Ensures only one SQL statement is present.
    - Verifies that only allowed tables are referenced in the query.
    - Enforces a maximum row limit on the query.

    Args:
        state (AgentState): The current agent state, which includes the SQL query to validate.

    Returns:
        AgentState: The updated agent state with validation results. If the query is valid,
                    the `is_valid` field is set to True, and the `sql` field contains the
                    safe SQL query. If invalid, the `is_valid` field is set to False, and
                    the `error` field contains the error message.
    """
    sql = state.get("sql", "")
    if not sql:
        return {"is_valid": False, "error": "No SQL to validate."}

    # Check for forbidden keywords in the SQL query
    bad = _contains_forbidden(sql, FORBIDDEN_KEYWORDS)
    if bad:
        return {"is_valid": False, "error": f"Forbidden or invalid SQL detected: {bad}"}

    # Ensure only one SQL statement is present
    if len(sqlparse.split(sql)) != 1:
        return {"is_valid": False, "error": "Multiple SQL statements detected; only one SELECT is allowed."}

    # Extract tables referenced in the query
    tables = _extract_tables(sql)
    if not tables:
        return {"is_valid": False, "error": "No table referenced (missing FROM?)."}

    # Check if any referenced tables are not allowed
    illegal = [t for t in tables if t not in ALLOWED_TABLES]
    if illegal:
        return {"is_valid": False, "error": f"Illegal table(s): {', '.join(illegal)}"}

    # Inject a safe row limit into the query
    safe_sql = _inject_safe_limit(sql, MAX_LIMIT)
    state["sql"] = safe_sql
    return {"is_valid": True}