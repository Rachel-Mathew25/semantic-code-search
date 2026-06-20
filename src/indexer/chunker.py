import ast


def chunk_python_file(file_path):
    # Read the entire file
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    # Split into lines so we can extract portions later
    lines = source_code.splitlines()

    # Parse into an AST
    tree = ast.parse(source_code)

    chunks = []

    # Look only at top-level definitions
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            # Extract the exact lines for this function
            code = "\n".join(lines[node.lineno - 1 : node.end_lineno])

            chunks.append({
                "id": f"{file_path}:{node.name}",
                "name": node.name,
                "type": "function",
                "file_path": file_path,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "code": code,
            })

        elif isinstance(node, ast.ClassDef):
            # Extract the exact lines for this class
            code = "\n".join(lines[node.lineno - 1 : node.end_lineno])

            chunks.append({
                "id": f"{file_path}:{node.name}",
                "name": node.name,
                "type": "class",
                "file_path": file_path,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "code": code,
            })

    return chunks


def _is_test_file(py_file) -> bool:
    """Heuristic for excluding test code from the search index.

    Test functions (test_foo, helper fixtures, etc.) tend to dominate
    semantic search results for queries like "how is X handled" because
    they literally contain the words "test_<feature>" - but a developer
    asking that question almost always wants the implementation, not
    the test. We exclude anything under a tests/ or test/ directory, or
    named test_*.py / *_test.py.
    """
    parts = {p.lower() for p in py_file.parts}
    if "tests" in parts or "test" in parts:
        return True
    name = py_file.name.lower()
    return name.startswith("test_") or name.endswith("_test.py")


def chunk_repository(repo_path, include_tests: bool = False):
    """Walk a repo directory and chunk every .py file found.

    Single home for the "find files, chunk each one" loop - the
    indexing entrypoints (API, CLI) should call this instead of
    re-implementing the walk themselves.

    By default, test files are excluded (see _is_test_file) since they
    tend to crowd out implementation code in search results. Pass
    include_tests=True to index them anyway.
    """
    from pathlib import Path

    all_chunks = []
    for py_file in Path(repo_path).rglob("*.py"):
        if not include_tests and _is_test_file(py_file):
            continue
        all_chunks.extend(chunk_python_file(str(py_file)))
    return all_chunks


if __name__ == "__main__":
    chunks = chunk_python_file("fixtures/sample_repo/auth.py")

    for chunk in chunks:
        print("=" * 40)
        print(f"Name : {chunk['name']}")
        print(f"Type : {chunk['type']}")
        print()
        print(chunk["code"])
        print()