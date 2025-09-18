import requests
import streamlit as st


def request_natural_language_question(question: str, api_base: str) -> requests.Response | Exception:
    """
    Sends a natural-language question to the backend agent and returns the response object.

    Args:
        question (str): The user's question in natural language.
        api_base (str): The base URL of the backend API.

    Returns:
        requests.Response: The HTTP response from the backend agent.
        Exception: If a request error occurs.
    """
    try:
        resp = requests.post(
            f"{api_base}/agent/query",
            json={"question": question},
            timeout=6000,
        )
        return resp
    except Exception as e:
        return e


def request_health_check(api_base: str, health_col: st.delta_generator.DeltaGenerator) -> None:
    """
    Checks the health of the backend agent and updates the provided Streamlit column.

    Args:
        api_base (str): The base URL of the backend API.
        health_col (st.delta_generator.DeltaGenerator): Streamlit column to display health status.

    Returns:
        None
    """
    try:
        r = requests.get(f"{api_base}/health", timeout=5)
        if r.ok:
            h = r.json()
            health_col.success(
                f"✅ {h.get('status')} • Model: {h.get('data_model', '?')} • Ollama Host: {h.get('ollama_host', '?')}"
            )
        else:
            health_col.warning(f"⚠️ {r.status_code}")
    except Exception as e:
        health_col.error(f"❌ {e}")
