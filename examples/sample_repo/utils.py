"""Generic utility helpers."""
import re

def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    return re.sub(r'[\s_]+', '-', text)

def chunk_list(items: list, size: int) -> list:
    """Split a list into chunks of given size."""
    return [items[i:i+size] for i in range(0, len(items), size)]

def retry(func, attempts: int = 3):
    """Retry a function up to attempts times on exception."""
    for _ in range(attempts - 1):
        try:
            return func()
        except Exception:
            pass
    return func()
