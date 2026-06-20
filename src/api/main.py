from fastapi import FastAPI
from pydantic import BaseModel

from src.indexer.chunker import chunk_repository
from src.store import vector_store
from src.retriever.retriever import retrieve

app = FastAPI()


class IndexRequest(BaseModel):
    repo_path: str


@app.get("/search")
def search(q: str, n_results: int = 5):
    return retrieve(q, n_results=n_results)


@app.post("/index")
def index_repo(request: IndexRequest):
    from src.indexer.embedder import embed_text

    chunks = chunk_repository(request.repo_path)
    vector_store.add_chunks(chunks, embed_fn=embed_text)
    return {"message": f"Indexed {len(chunks)} chunks from {request.repo_path}"}
