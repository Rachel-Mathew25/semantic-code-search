from src.indexer.embedder import embed_text
from src.store.vector_store import collection

query = input("Search: ")

results = collection.query(
    query_embeddings=[embed_text(query)],
    n_results=3,
    include=["documents", "metadatas", "distances"],
)

for metadata, document, distance in zip(
    results["metadatas"][0],
    results["documents"][0],
    results["distances"][0],
):
    print("=" * 60)
    print(f"📄 File : {metadata['file_path']}")
    print(f"🏷️  Name : {metadata['name']}")
    print(f"📌 Type : {metadata['type']}")
    print(f"📍 Lines: {metadata['start_line']} - {metadata['end_line']}")
    print(f"📊 Distance : {distance:.4f}")
    print()
    print(document)
    print()