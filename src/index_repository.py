from pathlib import Path

from src.indexer.chunker import chunk_python_file
from src.indexer.embedder import embed_text
from src.store.vector_store import collection

repo = Path("fixtures/sample_repo")

for py_file in repo.rglob("*.py"):
    chunks = chunk_python_file(str(py_file))

    for chunk in chunks:
        collection.add(
            ids=[chunk["id"]],
            embeddings=[embed_text(chunk["code"])],
            documents=[chunk["code"]],
            metadatas=[{
                "name": chunk["name"],
                "type": chunk["type"],
                "file_path": chunk["file_path"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
            }],
        )

print("Repository indexed successfully!")