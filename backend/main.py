import os
import uuid
from fastapi import FastAPI
from langgraph.graph import StateGraph, END
from src.sql_validation.sql_validate_query import validate_sql
from src.sql_execution.sql_execute_query import execute_sql_query
from src.sql_generation.sql_generate_query import llm_generate_sql, end_error
from src.data_model.request_models import QueryInput, QueryOutput
from src.data_model.agent_states import AgentState
from src.retriver.retrieve import retrieve_schema_context
from typing import Dict, Any

# Define LangGraph graph wiring
# Define Nodes
graph = StateGraph(AgentState)
graph.add_node(node="retrieve_schema_context", action=retrieve_schema_context)
graph.add_node(node="generate_sql_query", action=llm_generate_sql)
graph.add_node(node="validate_sql_query", action=validate_sql)
graph.add_node(node="execute_sql_query", action=execute_sql_query)
graph.add_node(node="error", action=end_error)

# Define entry point node
graph.set_entry_point(key="retrieve_schema_context")

# Define edges (workflow)
graph.add_edge(start_key="retrieve_schema_context", end_key="generate_sql_query")
graph.add_edge(start_key="generate_sql_query", end_key="validate_sql_query")
graph.add_conditional_edges(
    source="validate_sql_query",
    path=lambda state: "valid" if state.get("is_valid") else "invalid",
    path_map={
        "valid": "execute_sql_query",
        "invalid": "error",
    },
)
graph.add_edge("execute_sql_query", END)
graph.add_edge("error", END)

# Compile LangGraph graph
complied_graph = graph.compile()

app = FastAPI(title="QueryCraft Agent (LangGraph, Postgres, Ollama, FastAPI )")


@app.post("/agent/query", response_model=QueryOutput)
async def agent_query(payload: QueryInput) -> QueryOutput:
    """
    Handles the `/agent/query` endpoint to process a query through the LangGraph.

    Args:
        payload (QueryInput): The input payload containing the query.

    Returns:
        QueryOutput: The output containing the SQL query, rows, error, tables in scope,
        context chunks, and the unique run ID.
    """
    # Run a fresh graph per request (stateless across requests)
    initial: AgentState = {"question": payload.question}
    # Use a unique thread/run id to keep logs distinct
    run_id: str = str(uuid.uuid4())

    # invoke supports async if any nodes are async (our LLM node is async)
    result: AgentState = await complied_graph.ainvoke(
        initial,
        config={"configurable": {"thread_id": run_id}}
    )

    # Normalize response
    return QueryOutput(
        sql=result.get("sql"),
        rows=result.get("rows"),
        error=result.get("error"),
        tables_in_scope=result.get("tables_in_scope"),
        context_chunks=result.get("context_chunks"),
        run_id=run_id,
    )


@app.get("/health")
def health() -> Dict[str, Any]:
    """
    Handles the `/health` endpoint to check the health of the application.

    Returns:
        Dict[str, Any]: A dictionary containing the status, Ollama host, and data model.
    """
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL")

    # lightweight DB/LLM health check
    return {
        "status": "Ok",
        "ollama_host": OLLAMA_HOST,
        "data_model": OLLAMA_MODEL,
    }
