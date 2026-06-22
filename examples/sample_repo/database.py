"""Simple in-memory database layer."""

class Database:
    def __init__(self):
        self._store = {}

    def insert(self, key, value):
        self._store[key] = value

    def get(self, key):
        return self._store.get(key)

    def delete(self, key):
        self._store.pop(key, None)

def connect(config: dict):
    """Initialize a Database from config."""
    return Database()
