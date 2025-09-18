"""
Module: utils.py

This module provides utility functions for SQL query validation and manipulation. 
It includes functions to detect forbidden keywords, extract table names from SQL queries, 
and enforce a maximum row limit in SQL queries.

Dependencies:
- typing: For type annotations.
- re: For regular expression operations.
- sqlparse: For parsing and analyzing SQL statements.

Functions:
- _contains_forbidden(sql: str, forbidden_keywords: Set[str]) -> Optional[str]: 
  Checks if the SQL query contains any forbidden keywords or is not a SELECT statement.

- _extract_tables(sql: str) -> List[str]: 
  Extracts table names referenced in the SQL query.

- _inject_safe_limit(sql: str, max_limit: int) -> str: 
  Ensures the SQL query includes a LIMIT clause and enforces a maximum row limit.
"""

from typing import TypedDict, Dict, Any, Set, List, Optional
import re
import sqlparse


def _contains_forbidden(sql: str, forbidden_keywords: Set[str]) -> Optional[str]:
    """
    Checks if the SQL query contains any forbidden keywords or is not a SELECT statement.

    Args:
        sql (str): The SQL query to check.
        forbidden_keywords (Set[str]): A set of forbidden SQL keywords.

    Returns:
        Optional[str]: The first forbidden keyword found, "non-SELECT statement" if the query 
                       is not a SELECT statement, or None if the query is valid.
    """
    lowered = sql.lower()
    for kw in forbidden_keywords:
        if re.search(rf"\b{kw}\b", lowered):
            return kw
    first = sqlparse.parse(sql)[0]
    tokens = [t for t in first.tokens if not t.is_whitespace]
    if not tokens or tokens[0].ttype is None or tokens[0].value.lower() != "select":
        return "non-SELECT statement"
    return None


def _extract_tables(sql: str) -> List[str]:
    """
    Extracts table names referenced in the SQL query.

    Args:
        sql (str): The SQL query to analyze.

    Returns:
        List[str]: A list of table names referenced in the query.
    """
    tables = []
    for m in re.finditer(r"\b(?:from|join)\s+([a-zA-Z_][\w\.]*)", sql, flags=re.IGNORECASE):
        tbl = m.group(1).split(".")[-1].strip('"')
        tables.append(tbl)
    return tables


def _inject_safe_limit(sql: str, max_limit: int) -> str:
    """
    Ensures the SQL query includes a LIMIT clause and enforces a maximum row limit.

    Args:
        sql (str): The SQL query to modify.
        max_limit (int): The maximum number of rows allowed in the query.

    Returns:
        str: The modified SQL query with the enforced LIMIT clause.
    """
    m = re.search(r"\blimit\b\s+(\d+)", sql, flags=re.IGNORECASE)
    if m:
        current = int(m.group(1))
        if current > max_limit:
            return re.sub(r"\blimit\b\s+\d+", f"LIMIT {max_limit}", sql, flags=re.IGNORECASE)
        return sql
    return f"{sql.rstrip(';')} LIMIT {max_limit}"
