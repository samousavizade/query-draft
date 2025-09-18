import os
import json
from pathlib import Path
from qdrant_client import QdrantClient

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:16333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = os.getenv("QDRANT_COLLECTION", "DDL")
SCHEMA_JSON_PATH = "../document_ingestion/documents.json"


def load_documents(path: str):
    # Load schema documents from .json file
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Schema JSON not found: {p.resolve()}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Basic validation
    if not isinstance(data, list):
        raise ValueError("Top-level JSON must be a list of {document, metadata} objects.")
    for i, item in enumerate(data):
        if "document" not in item or "metadata" not in item:
            raise ValueError(f"Item {i} missing 'document' or 'metadata' keys.")
        if not isinstance(item["document"], str):
            raise ValueError(f"Item {i} 'document' must be a string.")
        if not isinstance(item["metadata"], dict):
            raise ValueError(f"Item {i} 'metadata' must be an object.")
    return data


def main():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # If the collection exists, drop it for a clean reindex
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)

    # Load docs from JSON
    documents = load_documents(SCHEMA_JSON_PATH)

    # The 'add' method will (a) create the collection automatically and
    # (b) embed the documents via FastEmbed under the hood.
    client.add(
        collection_name=COLLECTION,
        documents=[d["document"] for d in documents],
        metadata=[d["metadata"] for d in documents],
    )

    print(f"Indexed {len(documents)} schema docs into '{COLLECTION}' from '{SCHEMA_JSON_PATH}'")


if __name__ == "__main__":
    main()
