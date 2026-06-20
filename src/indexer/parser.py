import ast
def parse_python_file(file_path):
    with open(file_path,"r",encoding="utf-8") as f:
              source_code = f.read()

    tree = ast.parse(source_code)
    return tree

def print_structure(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            print(f"Function: {node.name}")
        elif isinstance(node, ast.ClassDef):
            print(f"Class: {node.name}")

if __name__ == "__main__":
    tree = parse_python_file("fixtures/sample_repo/auth.py")
    print_structure(tree)

