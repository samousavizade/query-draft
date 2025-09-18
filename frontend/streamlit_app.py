"""
Frontend for QueryCraft Service

This Streamlit app provides a user interface for interacting with the QueryCraft backend agent.
Users can submit natural-language questions, which are converted to SQL, executed, and the results displayed.
API health status and configuration are available in the sidebar.
"""

import os
import requests
import pandas as pd
import streamlit as st
from calls import request_natural_language_question, request_health_check

# Streamlit page config
st.set_page_config(page_title="QueryCraft UI", layout="wide")

## Sidebar: API config
default_api = os.getenv("API_BASE_URL")
st.sidebar.header("API Settings")
api_base = st.sidebar.text_input("API Base URL", value=default_api, help="e.g. http://backend:8501")
health_col = st.sidebar.empty()

if st.sidebar.button("Check health", use_container_width=True):
    request_health_check(api_base, health_col)

## Main UI
st.title("🧭 QueryCraft (LangGraph + FastAPI)")

st.write("Enter a natural-language question. The agent will generate SQL, validate it, run it, and return result.")

with st.form(key="qform", clear_on_submit=False):
    question = st.text_area(
        "Type your question in the textbox",
        height=120,
        placeholder="e.g. Show the top 10 customers by number of orders with their email")

    submitted = st.form_submit_button("Run", use_container_width=True)

if submitted:
    if not question.strip():
        st.error("Please enter a question.")
        st.stop()

    with st.spinner("Contacting agent..."):
        resp = request_natural_language_question(question, api_base)

    if isinstance(resp, Exception):
        st.error(f"Request failed: {resp}")
        st.stop()

    if not resp.ok:
        st.error(f"API error {resp.status_code}: {resp.text}")
        st.stop()

    data = resp.json()
    run_id = data.get("run_id", "-")
    sql = data.get("sql")
    rows = data.get("rows")
    err = data.get("error")

    top = st.columns([3, 1])
    with top[0]:
        st.caption("Run ID")
        st.code(run_id, language=None)
    with top[1]:
        st.caption("Status")
        if not err:
            st.success("Ok")
        else:
            st.error("Error")

    st.subheader("Generated SQL")
    st.code(sql or "(no SQL)", language="sql")

    if err:
        st.subheader("Agent Error")
        st.error(err)

    st.subheader("Result")
    if rows:
        df = pd.DataFrame(rows)
        st.write(f"Returned **{len(df):,}** rows.")
        st.dataframe(df, use_container_width=True)
        st.download_button(
            "Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            "result.csv", "text/csv",
            use_container_width=True
        )
    else:
        st.info("No rows returned.")

    with st.expander("Raw response"):
        st.json(data)
