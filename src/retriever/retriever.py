from src.indexer.embedder import embed_text
from src.store import vector_store
from src.retriever.reranker import rerank


def retrieve(query: str, n_results: int = 5, use_reranker: bool = True):
    """Retrieve the top-n most relevant code chunks for a query.

    This is the single entrypoint the API/CLI/UI should call for
    search - they should never talk to vector_store directly.

    Two-stage retrieval when use_reranker=True:
      1. Vector search pulls a wider candidate pool (fast, approximate)
      2. Cross-encoder reranks those candidates (slower, more accurate)
         and we keep only the final top n_results

    If use_reranker=False, falls back to plain vector search - useful
    for comparing the two, or if you want lower latency at the cost
    of some precision.
    """
    if use_reranker:
        candidate_pool_size = max(n_results * 3, 10)
        candidates = vector_store.search(
            query, embed_fn=embed_text, n_results=candidate_pool_size
        )
        return rerank(query, candidates, top_k=n_results)
    else:
        return vector_store.search(query, embed_fn=embed_text, n_results=n_results)
