"""
Self-contained Streamlit app for Hugging Face Spaces deployment.

Unlike the local dev version, this does NOT call out to a separate
FastAPI server - Spaces' free Streamlit SDK runs a single process, so
this imports the pipeline functions directly. Same underlying logic
(chunker, embedder, vector_store, retriever), just no HTTP hop.
"""

import subprocess
import tempfile
import shutil

import streamlit as st

from src.indexer.chunker import chunk_repository
from src.store import vector_store
from src.retriever.retriever import retrieve


st.set_page_config(page_title="Semantic Code Search", page_icon="🔍")
st.title("🔍 Semantic Code Search")
st.caption(
    "Search a Python codebase using natural language. "
    "Ask 'where is authentication handled?' instead of guessing keywords."
)


@st.cache_resource(show_spinner=False)
def _embedder():
    # Imported and loaded lazily, once per Space instance, not per request.
    from src.indexer.embedder import embed_text
    return embed_text


def index_github_repo(github_url: str) -> int:
    """Shallow-clone a public GitHub repo into a temp dir and index it.

    Shallow clone (depth=1) because we only need the current file
    contents, not history - keeps this fast on a free-tier Space.
    """
    tmp_dir = tempfile.mkdtemp()
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", github_url, tmp_dir],
            check=True,
            capture_output=True,
            timeout=120,
        )
        vector_store.reset_collection()
        chunks = chunk_repository(tmp_dir)
        vector_store.add_chunks(chunks, embed_fn=_embedder())
        return len(chunks)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def index_demo_repo() -> int:
    """Index the small bundled fixture repo - no network needed, instant."""
    vector_store.reset_collection()
    chunks = chunk_repository("fixtures/sample_repo")
    vector_store.add_chunks(chunks, embed_fn=_embedder())
    return len(chunks)


# --- Indexing controls ---
st.subheader("1. Index a repository")

col1, col2 = st.columns([3, 1])
with col1:
    github_url = st.text_input(
        "Public GitHub repository URL",
        placeholder="https://github.com/psf/requests",
    )
with col2:
    st.write("")
    st.write("")
    use_demo = st.button("Use demo repo instead")

if st.button("Index Repository", type="primary"):
    if not github_url:
        st.warning("Enter a GitHub URL, or click 'Use demo repo instead'.")
    else:
        with st.spinner(f"Cloning and indexing {github_url} ..."):
            try:
                n = index_github_repo(github_url)
                st.session_state["indexed"] = True
                st.success(f"Indexed {n} chunks from {github_url}")
            except subprocess.CalledProcessError:
                st.error("Couldn't clone that repo. Check the URL is public and correct.")
            except subprocess.TimeoutExpired:
                st.error("Clone timed out - repo may be too large for this demo.")

if use_demo:
    with st.spinner("Indexing demo repo..."):
        n = index_demo_repo()
        st.session_state["indexed"] = True
        st.success(f"Indexed {n} chunks from the bundled demo repo (auth, payments, db, utils)")

# --- Search ---
st.divider()
st.subheader("2. Search")

if not st.session_state.get("indexed"):
    st.info("Index a repository above first.")
else:
    query = st.text_input("Ask a question about the codebase", placeholder="how is authentication handled?")
    if st.button("Search") and query:
        results = retrieve(query, n_results=5)
        if not results:
            st.warning("No results found.")
        for r in results:
            st.markdown(f"**{r['name']}**  ({r['type']})")
            st.caption(f"{r['file']} : lines {r['start_line']}-{r['end_line']}  ·  distance {r['distance']:.3f}")
            st.code(r["code"], language="python")
            st.divider()
