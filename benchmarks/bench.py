"""
Benchmark script for the semantic code search pipeline.

Usage:
    python -m benchmarks.bench <path-to-cloned-repo>

Example:
    git clone https://github.com/psf/requests
    python -m benchmarks.bench requests

Measures:
    - chunk count
    - index time (seconds)
    - query latency (ms), averaged over a fixed query set
    - prints results for each query so you can manually judge
      precision@3 (how many of the top 3 results are actually relevant)
"""

import sys
import time

from src.indexer.chunker import chunk_repository
from src.indexer.embedder import embed_text
from src.store import vector_store
from src.retriever.retriever import retrieve


# Generic queries that should make sense against most real Python codebases.
# Edit these to be more specific to the repo you're benchmarking if you want
# sharper precision@3 signal (e.g. for `requests`: "how are HTTP headers set").
DEFAULT_QUERIES = [
    "how is authentication handled",
    "how are HTTP requests sent",
    "session management",
    "error handling and exceptions",
    "parsing a URL",
    "setting request headers",
    "handling redirects",
    "connection timeout",
    "reading a response body",
    "retry logic",
]


def benchmark_indexing(repo_path: str):
    vector_store.reset_collection()

    print(f"Indexing repo: {repo_path}")
    start = time.perf_counter()

    chunks = chunk_repository(repo_path)
    vector_store.add_chunks(chunks, embed_fn=embed_text)

    elapsed = time.perf_counter() - start

    print(f"  Chunks indexed : {len(chunks)}")
    print(f"  Index time     : {elapsed:.2f}s")
    print()
    return len(chunks), elapsed


def benchmark_queries(queries=None):
    queries = queries or DEFAULT_QUERIES
    latencies = []

    print(f"Running {len(queries)} queries...\n")
    for q in queries:
        start = time.perf_counter()
        results = retrieve(q, n_results=3)
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies.append(elapsed_ms)

        print("=" * 70)
        print(f"Query: \"{q}\"  ({elapsed_ms:.1f}ms)")
        for i, r in enumerate(results, 1):
            print(f"  [{i}] {r['name']} ({r['type']}) - {r['file']}:{r['start_line']}-{r['end_line']}  dist={r['distance']:.3f}")
        print()

    avg_ms = sum(latencies) / len(latencies)
    print("=" * 70)
    print(f"Average query latency: {avg_ms:.1f}ms over {len(queries)} queries")
    print()
    print("Now manually judge: for each query above, how many of the top 3")
    print("results are actually relevant? Sum across all queries and divide")
    print("by (3 * num_queries) to get precision@3.")
    return avg_ms


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m benchmarks.bench <path-to-repo>")
        sys.exit(1)

    repo_path = sys.argv[1]
    n_chunks, index_time = benchmark_indexing(repo_path)
    avg_latency = benchmark_queries()

    print()
    print("SUMMARY (copy into README)")
    print("-" * 40)
    print(f"Chunks indexed:        {n_chunks}")
    print(f"Index time:            {index_time:.2f}s")
    print(f"Avg query latency:     {avg_latency:.1f}ms")