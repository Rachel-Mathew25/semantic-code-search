from src.indexer.embedder import embed_text
from src.store.vector_store import collection

query = input("Search: ")

results = collection.query(
    query_embeddings=[embed_text(query)],
    n_results=3,
)

for i in range(len(results["ids"][0])):
    print("=" * 50)
    print(results["metadatas"][0][i])
    print()
    print(results["documents"][0][i])