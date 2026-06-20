from sentence_transformers import SentenceTransformer

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text: str):
    return model.encode(text).tolist()


if __name__ == "__main__":
    sample_code = """
def authenticate_user(username, password):
    return username == "admin" and password == "secret"
"""

    vector = embed_text(sample_code)

    print("Embedding dimension:", len(vector))
    print("First 10 values:", vector[:10])