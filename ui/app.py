import streamlit as st
import requests

st.title("🔍 Semantic Code Search")

# Repository indexing
repo_path = st.text_input(
    "Local repository path",
    help="A path on this machine, e.g. fixtures/sample_repo. "
         "GitHub URL support (clone-then-index) isn't built yet.",
)

if st.button("Index Repository"):
    if repo_path:
        response = requests.post(
            "http://127.0.0.1:8000/index",
            json={"repo_path": repo_path},
        )

        if response.status_code == 200:
            st.success(response.json()["message"])
        else:
            st.error("Failed to index repository.")

# Search section
st.divider()

query = st.text_input("Search your repository")

if st.button("Search"):
    response = requests.get(
        "http://127.0.0.1:8000/search",
        params={"q": query},
    )

    results = response.json()

    if len(results) == 0:
        st.warning("No results found.")

    for result in results:
        st.subheader(result["name"])

        st.write(f"📄 File: {result['file']}")

        st.write(
            f"📍 Lines {result['start_line']} - {result['end_line']}"
        )

        st.write(
            f"🎯 Similarity Score: {result['distance']:.4f}"
        )

        st.code(
            result["code"],
            language="python"
        )

        st.divider()