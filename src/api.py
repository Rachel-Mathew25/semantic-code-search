from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path

from src.indexer.embedder import embed_text
from src.indexer.chunker import chunk_python_file
from src.store.vector_store import collection

app = FastAPI()


class IndexRequest(BaseModel):
    repo_path: str


@app.get("/search")
def search(q: str):
    results = collection.query(
        query_embeddings=[embed_text(q)],
        n_results=3,
        include=["documents", "metadatas", "distances"],
    )

    response = []

    for metadata, document, distance in zip(
        results["metadatas"][0],
        results["documents"][0],
        results["distances"][0],
    ):
        response.append(
            {
                "file": metadata["file_path"],
                "name": metadata["name"],
                "type": metadata["type"],
                "start_line": metadata["start_line"],
                "end_line": metadata["end_line"],
                "distance": distance,
                "code": document,
            }
        )

    return response


@app.post("/index")
def index_repo(request: IndexRequest):
    repo = Path(request.repo_path)

    for py_file in repo.rglob("*.py"):
        chunks = chunk_python_file(str(py_file))

        for chunk in chunks:
            # Remove existing chunk with same ID if present
            try:
                collection.delete(ids=[chunk["id"]])
            except Exception:
                pass

            collection.add(
                ids=[chunk["id"]],
                embeddings=[embed_text(chunk["code"])],
                documents=[chunk["code"]],
                metadatas=[
                    {
                        "name": chunk["name"],
                        "type": chunk["type"],
                        "file_path": chunk["file_path"],
                        "start_line": chunk["start_line"],
                        "end_line": chunk["end_line"],
                    }
                ],
            )

    return {"message": "Repository indexed successfully"}