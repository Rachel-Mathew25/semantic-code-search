"""Embedding model wrapper - lazily loaded.

The model is NOT loaded at import time. It loads on the first call to
embed_text(), and is cached after that. This matters because several
modules import from this file just to get the chunking/storage
plumbing - we don't want every one of those imports to trigger a
multi-second model download/load, especially on a cold server start.
"""

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_text(text: str):
    return _get_model().encode(text).tolist()


if __name__ == "__main__":
    sample_code = """
def authenticate_user(username, password):
    return username == "admin" and password == "secret"
"""
    vector = embed_text(sample_code)
    print("Embedding dimension:", len(vector))
    print("First 10 values:", vector[:10])
