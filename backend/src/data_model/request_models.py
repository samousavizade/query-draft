from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class QueryInput(BaseModel):
    """
    Represents the input model for a query.

    Attributes:
        question (str): The natural language question provided by the user.
    """
    question: str


class QueryOutput(BaseModel):
    """
    Represents the output model for a query.

    Attributes:
        sql (Optional[str]): The SQL query generated based on the user's question.
        rows (Optional[List[Dict[str, Any]]]): The result rows returned after executing the SQL query.
        error (Optional[str]): Any error message encountered during query generation or execution.
        run_id (str): A unique identifier for the query execution run.
    """
    sql: Optional[str] = None
    rows: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    run_id: str
