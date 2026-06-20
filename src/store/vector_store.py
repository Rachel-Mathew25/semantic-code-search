import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="code_chunks")


def reset_collection():
    """Delete and recreate the collection (used before a fresh re-index)."""
    global collection
    client.delete_collection(name="code_chunks")
    collection = client.get_or_create_collection(name="code_chunks")


def add_chunks(chunks, embed_fn):
    """Embed and upsert a list of chunk dicts into the collection.

    Each chunk must have: id, name, type, file_path, start_line,
    end_line, code. embed_fn converts code text -> vector.
    """
    for chunk in chunks:
        # Upsert semantics: remove any existing chunk with the same id
        # first, so re-indexing a changed file doesn't leave stale
        # duplicates behind.
        try:
            collection.delete(ids=[chunk["id"]])
        except Exception:
            pass

        collection.add(
            ids=[chunk["id"]],
            embeddings=[embed_fn(chunk["code"])],
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


def search(query: str, embed_fn, n_results: int = 5):
    """Embed a query and return the top-n most similar chunks."""
    results = collection.query(
        query_embeddings=[embed_fn(query)],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for metadata, document, distance in zip(
        results["metadatas"][0],
        results["documents"][0],
        results["distances"][0],
    ):
        output.append(
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
    return output
