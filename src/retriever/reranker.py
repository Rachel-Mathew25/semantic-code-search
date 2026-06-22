"""Cross-encoder reranking - second stage of retrieval.

Stage 1 (vector_store.search) finds candidates fast but approximately,
by comparing independently-computed embeddings. This module re-scores
those candidates by running the query and each candidate's code
*together* through a cross-encoder model, which is slower but more
accurate - it can actually reason about how well this specific chunk
answers this specific query, not just how close their vectors are.
"""

_model = None


def _get_model():
    # Lazy-loaded for the same reason as embedder.py: importing this
    # module shouldn't trigger a multi-second model download/load if
    # the caller never actually reranks anything.
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder
        _model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _model


def rerank(query: str, candidates: list, top_k: int = 5) -> list:
    """Re-score and re-sort candidates by relevance to the query.

    candidates: list of dicts from vector_store.search(), each with a
    "code" field. Returns the same dicts, re-sorted, with an added
    "rerank_score" field, truncated to top_k.
    """
    if not candidates:
        return candidates

    model = _get_model()
    pairs = [(query, c["code"]) for c in candidates]
    scores = model.predict(pairs)

    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)

    candidates.sort(key=lambda c: c["rerank_score"], reverse=True)
    return candidates[:top_k]
