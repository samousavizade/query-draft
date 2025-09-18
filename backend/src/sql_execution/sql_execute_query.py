"""
Module: sql_execute_query.py

This module is responsible for executing SQL queries against a database using SQLAlchemy.
It defines a function that takes the current agent state, executes the SQL query provided
in the state, and returns the updated state with the query results or an error message.

Environment Variables:
- DATABASE_URL: The connection string for the database.

Dependencies:
- os: Access to environment variables.
- sqlalchemy: SQLAlchemy library for database interaction.
- sqlalchemy.engine: Provides the `create_engine` function and `Result` type.
- ..data_model.agent_states: Contains the `AgentState` type definition.

Functions:
- execute_sql_query(state: AgentState) -> AgentState: Executes the SQL query in the agent state.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Result
from ..data_model.agent_states import AgentState

# Retrieve the database connection URL from the environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Create a SQLAlchemy engine for database connections
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


def execute_sql_query(state: AgentState) -> AgentState:
    """
    Executes an SQL query provided in the agent state and returns the updated state.

    This function takes the SQL query from the `sql` field of the `state` dictionary,
    executes it against the database, and returns the query results in the `rows` field.
    If an error occurs during execution, the `error` field is populated with the error message.

    Args:
        state (AgentState): The current agent state, which includes the SQL query to execute.

    Returns:
        AgentState: The updated agent state with the query results or an error message.
    """
    sql_query = state["sql"]
    try:
        # Establish a connection to the database and execute the query
        with engine.connect() as conn:
            result: Result = conn.execute(text(sql_query))
            # Fetch all rows and convert them to a list of dictionaries
            rows = [dict(row._mapping) for row in result.fetchall()]
        # Return the updated state with the query results
        return {"rows": rows}
    except Exception as e:
        # Return the updated state with the error message in case of failure
        return {"error": f"DB error: {e}"}
