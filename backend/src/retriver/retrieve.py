"""
Module: schema_retriever

This module provides functionality for retrieving schema-related context from
a Qdrant vector database given a natural language question. It is designed to
be part of an agent pipeline where state is passed between different steps
(e.g., question understanding, retrieval, reasoning).

Key Components:
---------------
- QDRANT_URL, QDRANT_API_KEY, COLLECTION: Configuration loaded from environment
  variables to connect to Qdrant.
- retrieve_schema_context: Asynchronous function that takes the current
  AgentState, queries Qdrant with the user's question, and returns relevant
  schema/document chunks as well as the tables likely involved.

Expected AgentState fields:
---------------------------
Input:
    - "question": str — The user's natural language question.

Output (merged into state):
    - "context_chunks": List[str] — Relevant text/document chunks from Qdrant.
    - "tables_in_scope": List[str] — Unique table names mentioned in the results.

This context can be used downstream for SQL generation, validation, or further
reasoning about which parts of the database schema are relevant to the query.
"""

import os
from qdrant_client import QdrantClient
from ..data_model.agent_states import AgentState

QDRANT_URL = os.getenv("QDRANT_URL")  # URL of the Qdrant service
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # API key for Qdrant (if set)
COLLECTION = os.getenv("QDRANT_COLLECTION", "DDL")  # Default collection name
TOP_K = 5  # Number of top results to fetch from Qdrant


async def retrieve_schema_context(state: AgentState) -> AgentState:
    """
    Retrieve schema/document context from Qdrant for a given natural language question.

    Parameters
    ----------
    state : AgentState
        The current agent state, which must include a "question" field containing
        the user's input.

    Returns
    -------
    AgentState
        A dictionary-like state with the following additional fields:
            - "context_chunks": List[str], relevant document chunks retrieved.
            - "tables_in_scope": List[str], deduplicated table names related to the query.

    Notes
    -----
    - Uses Qdrant's semantic query API to find the most relevant schema entries.
    - Deduplicates table names so the agent has a clean list of candidates.
    - Intended to run asynchronously as part of a larger LangGraph/agent pipeline.
    """

    q = state["question"].strip()
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, check_compatibility=False)
    results = client.query(
        collection_name=COLLECTION,
        query_text=q,
        limit=TOP_K
    )
    chunks = [r.document for r in results]
    tables = [r.metadata['table'] for r in results]

    # Deduplicate and keep simple names like orders, customers, products
    tables_in_scope = list(set(tables))
    return {"context_chunks": chunks, "tables_in_scope": tables_in_scope}
