"""
Unit tests for the semantic code search pipeline.

Run with:
    pytest tests/ -v

Each test verifies one layer of the pipeline in isolation. The goal
is to catch regressions early - if you change chunking logic, embedding
dimensions, or storage behavior, the relevant test will fail immediately
instead of you discovering the breakage via a bad search result.

We use a fake embedder (deterministic hash-based, no network/model needed)
for tests that touch the vector store and retriever - this makes tests
fast, offline, and reproducible. The real embedding model is only tested
in test_embed_text_* which explicitly load it.
"""

import hashlib
import pytest
from pathlib import Path

# --- Fixtures ---

FIXTURE_REPO = Path(__file__).parent.parent / "examples" / "sample_repo"
FIXTURE_FILE = FIXTURE_REPO / "auth.py"


def fake_embed(text: str):
    """Deterministic fake embedder - no model download, no network."""
    h = hashlib.sha256(text.encode()).digest()
    vec = [b / 255.0 for b in h[:16]]
    return vec


# --- Chunker tests ---

def test_chunk_python_file_returns_chunks():
    """Chunker should extract at least one chunk from auth.py."""
    from src.indexer.chunker import chunk_python_file
    chunks = chunk_python_file(str(FIXTURE_FILE))
    assert len(chunks) > 0, "Expected at least one chunk from auth.py"


def test_chunk_has_required_fields():
    """Every chunk must have the fields the vector store and UI depend on."""
    from src.indexer.chunker import chunk_python_file
    chunks = chunk_python_file(str(FIXTURE_FILE))
    required = {"id", "name", "type", "file_path", "start_line", "end_line", "code"}
    for chunk in chunks:
        missing = required - set(chunk.keys())
        assert not missing, f"Chunk '{chunk.get('name')}' missing fields: {missing}"


def test_chunk_type_is_function_or_class():
    """Chunker should only produce 'function' or 'class' type chunks."""
    from src.indexer.chunker import chunk_python_file
    chunks = chunk_python_file(str(FIXTURE_FILE))
    for chunk in chunks:
        assert chunk["type"] in ("function", "class"), \
            f"Unexpected chunk type: {chunk['type']}"


def test_chunk_repository_finds_multiple_files():
    """Walking the fixture repo should find chunks from multiple files."""
    from src.indexer.chunker import chunk_repository
    chunks = chunk_repository(str(FIXTURE_REPO))
    files = {c["file_path"] for c in chunks}
    assert len(files) > 1, "Expected chunks from more than one file"


def test_test_files_excluded_by_default():
    """Files in tests/ directories should not appear in chunk_repository output."""
    from src.indexer.chunker import chunk_repository
    chunks = chunk_repository(str(FIXTURE_REPO))
    for chunk in chunks:
        assert "test_" not in Path(chunk["file_path"]).name, \
            f"Test file leaked into index: {chunk['file_path']}"


def test_chunk_line_numbers_are_valid():
    """start_line should be >= 1 and end_line should be >= start_line."""
    from src.indexer.chunker import chunk_python_file
    chunks = chunk_python_file(str(FIXTURE_FILE))
    for chunk in chunks:
        assert chunk["start_line"] >= 1
        assert chunk["end_line"] >= chunk["start_line"]


# --- Embedder tests ---

def test_embed_text_returns_list():
    """embed_text should return a list (not a numpy array or tensor)."""
    from src.indexer.embedder import embed_text
    result = embed_text("def foo(): pass")
    assert isinstance(result, list), f"Expected list, got {type(result)}"


def test_embed_text_correct_dimension():
    """all-MiniLM-L6-v2 produces 384-dimensional embeddings."""
    from src.indexer.embedder import embed_text
    result = embed_text("def foo(): pass")
    assert len(result) == 384, f"Expected 384 dims, got {len(result)}"


def test_embed_text_returns_floats():
    """Every element of the embedding should be a float."""
    from src.indexer.embedder import embed_text
    result = embed_text("def foo(): pass")
    assert all(isinstance(x, float) for x in result), \
        "Expected all floats in embedding vector"


# --- Vector store tests ---

@pytest.fixture(autouse=False)
def fresh_collection():
    """Reset the ChromaDB collection before and after each store test."""
    from src.store import vector_store
    vector_store.reset_collection()
    yield
    vector_store.reset_collection()


def test_vector_store_add_and_search(fresh_collection):
    """Insert a chunk, search for it, expect to get it back as top result."""
    from src.store import vector_store
    chunk = {
        "id": "test::auth::authenticate_user",
        "name": "authenticate_user",
        "type": "function",
        "file_path": "auth.py",
        "start_line": 1,
        "end_line": 5,
        "code": "def authenticate_user(username, password): return True",
    }
    vector_store.add_chunks([chunk], embed_fn=fake_embed)
    results = vector_store.search(
        "authenticate_user", embed_fn=fake_embed, n_results=1
    )
    assert len(results) == 1
    assert results[0]["name"] == "authenticate_user"


def test_vector_store_no_duplicates(fresh_collection):
    """Re-indexing the same chunk id should not create duplicate entries."""
    from src.store import vector_store
    chunk = {
        "id": "test::auth::authenticate_user",
        "name": "authenticate_user",
        "type": "function",
        "file_path": "auth.py",
        "start_line": 1,
        "end_line": 5,
        "code": "def authenticate_user(username, password): return True",
    }
    vector_store.add_chunks([chunk], embed_fn=fake_embed)
    vector_store.add_chunks([chunk], embed_fn=fake_embed)
    results = vector_store.search(
        "authenticate_user", embed_fn=fake_embed, n_results=5
    )
    names = [r["name"] for r in results]
    assert names.count("authenticate_user") == 1, \
        "Duplicate chunk found after re-indexing same id"


# --- Reranker tests ---

def test_reranker_returns_top_k():
    """Reranker should return exactly top_k results (or fewer if less available)."""
    from src.retriever.reranker import rerank
    candidates = [
        {"name": f"func_{i}", "code": f"def func_{i}(): pass", "distance": float(i)}
        for i in range(10)
    ]
    results = rerank("authentication", candidates, top_k=3)
    assert len(results) == 3


def test_reranker_adds_score_field():
    """Every result returned by reranker should have a rerank_score field."""
    from src.retriever.reranker import rerank
    candidates = [
        {"name": "authenticate_user",
         "code": "def authenticate_user(u, p): return u == 'admin'",
         "distance": 1.0},
        {"name": "validate_card",
         "code": "def validate_card(n): return len(n) == 16",
         "distance": 1.2},
    ]
    results = rerank("authentication", candidates, top_k=2)
    for r in results:
        assert "rerank_score" in r, "Missing rerank_score field in result"


def test_reranker_orders_by_relevance():
    """More relevant candidate should rank above less relevant one."""
    from src.retriever.reranker import rerank
    candidates = [
        {"name": "validate_card",
         "code": "def validate_card(number): return luhn_check(number)",
         "distance": 0.9},
        {"name": "authenticate_user",
         "code": "def authenticate_user(username, password): return check_credentials(username, password)",
         "distance": 1.1},
    ]
    results = rerank("how is user authentication handled", candidates, top_k=2)
    assert results[0]["name"] == "authenticate_user", \
        "Expected authenticate_user to rank above validate_card for auth query"
