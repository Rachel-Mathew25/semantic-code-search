import argparse

from src.indexer.chunker import chunk_repository
from src.indexer.embedder import embed_text
from src.store import vector_store

parser = argparse.ArgumentParser(
    description="Index a Python repository into ChromaDB"
)
parser.add_argument("repo_path", help="Path to the repository to index")
parser.add_argument(
    "--reset",
    action="store_true",
    help="Wipe the existing collection before indexing (fresh start)",
)
args = parser.parse_args()

if args.reset:
    vector_store.reset_collection()

chunks = chunk_repository(args.repo_path)
vector_store.add_chunks(chunks, embed_fn=embed_text)

print(f"Indexed {len(chunks)} chunks from {args.repo_path}")
