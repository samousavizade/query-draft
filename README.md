# QueryDraft Engine

A lightweight, production-minded stack for **NL-to-SQL** analytics with **RAG over your database schema**.

* **Postgres** — source of truth (data + schema)
* **Ollama** — local LLM host for SQL generation (`hf.co/TheBloke/sqlcoder-7B-GGUF:Q4_K_M`)
* **Qdrant** — vector DB for schema-aware Retrieval Augmented Generation (RAG)
* **FastAPI** — backend API + LangGraph agent
* **Streamlit** — simple frontend for asking questions and viewing results

---

# Quick Start

### (First Time) Generate Sample Records and Ingest Schema Documents

```bash
# 1) generate database records
docker compose exec backend python -m database_data_generation.db_seed
-- Seeded 300 customers, 200 products, 2500 orders in PostgreSQL.

# 2) ingest schema into vector database 
docker compose exec backend python -m document_ingestion.ingest_schema
-- Indexed 3 schema docs into 'DDL' from '../document_ingestion/documents.json'
```

```bash
docker compose up -d --build
```

```
-- Qdrant Dashboard
http://localhost:16333/dashboard#/collections
```

### API Call

```
curl -X POST localhost:8501/agent/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"Top 10 customers by order count in last month"}'
```

### GUI

```
localhost:8502
```

---

## 1) Architecture

```
┌───────────┐      Ask question      ┌────────┐
│ Streamlit │───────────────────────▶ FastAPI  
└───────────┘                        └───┬────┘
                                         │ LangGraph (StateGraph)
                       ┌─────────────────▼─────────────────────┐
                       │ retrieve_schema_context (Qdrant RAG)  │
                       └─────────────────┬─────────────────────┘
                                         │ Schema Chunks (Qdrant Query)
                       ┌─────────────────▼─────────────────────┐
                       │ generate_sql_query (Ollama SQLCoder)  │
                       └─────────────────┬─────────────────────┘
                                         │ SQL
                       ┌─────────────────▼─────────────────────┐
                       │ validate_sql_query (Guardrails)       │
                       └─────────────────┬─────────────────────┘
                                         │ Validation Check? Valid / Error
                       ┌─────────────────▼─────────────────────┐
                       │ execute_sql_query (Postgres Database) │
                       └─────────────────┬─────────────────────┘
                                         │ Result / Error
┌──────────┐                        ┌────▼─────┐
│  Qdrant  │◀────ingest_schema──────  Postgres 
└──────────┘                        └──────────┘
                         ┌─────────────────────────────┐
                         │ Ollama: sqlcoder-7B (GGUF)  │
                         └─────────────────────────────┘
```

---

## 2) Components

### Postgres

Holds your operational or analytics tables. We use it both to run generated SQL and to **inspect schema** during
ingestion.

### Qdrant (RAG Vector DB)

Stores **schema “cards”** (per-table descriptions: columns, PK/FK, tips). At query time we **vector-search** the most
relevant cards to constrain the model.

### Ollama (LLM Host)

Runs `hf.co/TheBloke/sqlcoder-7B-GGUF:Q4_K_M` locally. The model is tuned for SQL generation.

### FastAPI (Backend)

* Exposes `/agent/query`
* Wires a **LangGraph**: `retrieve → generate → validate → (execute|error)`
* Normalizes responses for the UI

### Streamlit (Frontend)

A minimal UI to type questions, see the generated SQL, and preview tabular results.

---

## 3) RAG Flow (at a glance)

1. **Ingest**: A script reads Postgres catalogs, constructs per-table **schema docs**, and pushes them to
   Qdrant (`collection=schema_docs`).
2. **Retrieve**: Given a user question, we query Qdrant `TOP_K` for the most relevant schema docs.
3. **Generate**: The SQL LLM receives only those docs and strict rules (dialect, joins, `LIMIT` policy).
4. **Validate**: Lightweight checks (e.g., referenced tables exist in retrieved scope). Add EXPLAIN or parsers as
   needed.
5. **Execute**: Run on Postgres; return rows or a clear error.

---

## 4) API

### `POST /agent/query`

**Body**

```json
{
  "question": "Total orders per customer in the last 7 days?"
}
```

**Response**

```json
{
  "sql": "SELECT ... LIMIT 100",
  "rows": [
    [
      ...
    ],
    [
      ...
    ]
  ],
  "error": null,
  "run_id": "a3b7-..."
}
```

### `GET /health`

Returns Ollama host/model and a simple “Ok” status.

---

## 5) Running with Docker Compose

---

## 6) Backend LangGraph (nodes)

* `retrieve_schema_context` — query Qdrant with the user question; attach `context_chunks` and `tables_in_scope` to the
  state.
* `generate_sql_query` — assemble strict prompt + context; call Ollama; return `sql`.
* `validate_sql_query` — quick guards (e.g., only retrieved tables referenced); optional EXPLAIN.
    - This module is responsible for validating SQL queries to ensure they adhere to security and business rules.
      It checks for forbidden keywords, ensures only allowed tables are referenced, and enforces a maximum row limit.
* `execute_sql_query` — run on Postgres; return `rows`.

**Error path**: any node can put `error` in state → goes to `error` node and finishes.

---

## 7) Frontend (Streamlit)

* Text input for **question**
* Readonly box for **generated SQL**
* Results table
* Basic error banner (e.g., “Missing schema for X” or DB errors)

