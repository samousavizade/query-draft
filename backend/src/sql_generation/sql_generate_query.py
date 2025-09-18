"""
Module: sql_generate_query.py

This module handles the generation of SQL queries using a Large Language Model
(LLM) via the Ollama API. It builds a prompt with schema context, sends it to
the model, parses the response, and ensures the query is valid and safe to run.

Environment Variables
---------------------
- OLLAMA_HOST: URL of the Ollama API service (default: http://ollama:11434).
- OLLAMA_MODEL: Model identifier to use for SQL generation
  (default: hf.co/TheBloke/sqlcoder-7B-GGUF:Q4_K_M).
- SQL_MAX_LIMIT: Maximum number of rows returned in a query if no LIMIT is provided
  (default: 100).

Key Functions
-------------
- assemble_prompt: Constructs a SQL-generation prompt for the LLM.
- llm_generate_sql: Asynchronously calls the LLM to generate SQL given agent state.
- end_error: Fallback handler that simply returns the state (useful in error branches).

Expected AgentState fields
--------------------------
Input:
    - "question": str — The user’s natural language question.
    - "context_chunks": list[str] — Relevant schema/document context (optional).
    - "tables_in_scope": list[str] — Tables likely relevant to the query (optional).

Output:
    - "sql": str — Generated SQL query, cleaned and with a safe LIMIT enforced.
    - or "error": str — Error message if something went wrong.
"""

import httpx, re, sqlparse, os
from ..data_model.agent_states import AgentState

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "hf.co/TheBloke/sqlcoder-7B-GGUF:Q4_K_M")
MAX_LIMIT = int(os.getenv("SQL_MAX_LIMIT", "100"))


def assemble_prompt(question: str, context_chunks: list[str], tables_in_scope: list[str]) -> str:
    """
    Build a prompt to send to the LLM for SQL generation.

    Parameters
    ----------
    question : str
        The natural language question provided by the user.
    context_chunks : list[str]
        Schema/document context chunks retrieved from a vector DB (can be empty).
    tables_in_scope : list[str]
        Tables inferred to be relevant to the query (logged for debugging).

    Returns
    -------
    str
        A formatted prompt string ready to send to the LLM.
    """

    ctx = "\n".join(context_chunks) if context_chunks else "NO CONTEXT"
    print("Tables:", tables_in_scope)
    prompt = f"""
## Task
Generate a SQL query to answer the following question:
`{question}`

### Database Schema
This query will run on a database whose schema is represented in this string:
{ctx}        
### SQL
Given the database schema, here is the SQL query that answers `{question}`:
```sql
    """.strip()

    print("Prompt: ", prompt)
    return prompt


async def llm_generate_sql(state: AgentState) -> AgentState:
    """
   Generate a SQL query from a natural language question using the LLM.

   Parameters
   ----------
   state : AgentState
       Current agent state. Must contain at least:
           - "question": str
       Optionally:
           - "context_chunks": list[str]
           - "tables_in_scope": list[str]

   Returns
   -------
   AgentState
       A dictionary-like object with one of:
           - {"sql": str} containing the generated SQL query.
           - {"error": str} if generation failed or produced invalid output.

   Notes
   -----
   - Calls Ollama’s `/api/generate` endpoint.
   - Strips markdown code fences (```sql ... ```).
   - Splits into SQL statements and takes the first.
   - Enforces a LIMIT clause if missing, using MAX_LIMIT from env.
   """

    question = state["question"].strip()
    context_chunks = state.get("context_chunks", [])
    tables_in_scope = state.get("tables_in_scope", [])

    prompt = assemble_prompt(question, context_chunks, tables_in_scope)

    url = f"{OLLAMA_HOST.rstrip('/')}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    }
    async with httpx.AsyncClient(timeout=6000) as client:
        r = await client.post(url, json=payload)
        if r.status_code != 200:
            return {"error": f"LLM error {r.status_code}: {r.text}"}
        raw = (r.json().get("response") or "").strip()

    cleaned = re.sub(r"^```(?:sql)?\s*|\s*```$", "", raw, flags=re.IGNORECASE | re.MULTILINE).strip()
    statements = sqlparse.split(cleaned)
    if not statements:
        return {"error": "LLM returned empty SQL."}
    sql = statements[0].strip().rstrip(";")

    # Enforce LIMIT if missing
    if re.search(r"\blimit\b\s+\d+\s*$", sql, flags=re.IGNORECASE) is None:
        sql = f"{sql} LIMIT {MAX_LIMIT}"

    return {"sql": sql}


def end_error(state: AgentState) -> AgentState:
    """
    Identity function used as an error handler.

    Parameters
    ----------
    state : AgentState
        The current state (with an "error" field).

    Returns
    -------
    AgentState
        Unchanged input state.
    """
    return state
