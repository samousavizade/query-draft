from typing import TypedDict, List


class AgentState(TypedDict, total=False):
    """
    Represents the state of an agent during query processing.

    Attributes:
        question (str): The natural language question provided by the user.
        sql (str): The SQL query generated based on the user's question.
        is_valid (bool): Indicates whether the generated SQL query is valid.
        rows (list): The result rows returned after executing the SQL query.
        error (str): Any error message encountered during query generation or execution.
        context_chunks (List[str]): Relevant context or schema information used to generate the SQL query.
        tables_in_scope (List[str]): The list of database tables considered during query generation.
    """
    question: str
    sql: str
    is_valid: bool
    rows: list
    error: str
    context_chunks: List[str]
    tables_in_scope: List[str]