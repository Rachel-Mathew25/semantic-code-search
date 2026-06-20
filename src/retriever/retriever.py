from src.indexer.embedder import embed_text
from src.store import vector_store


def retrieve(query: str, n_results: int = 5):
    """Retrieve the top-n most relevant code chunks for a query.

    This is the single entrypoint the API/CLI/UI should call for
    search - they should never talk to vector_store directly. That
    indirection is what lets us slot in reranking (Milestone 6)
    without touching any caller.
    """
    return vector_store.search(query, embed_fn=embed_text, n_results=n_results)
