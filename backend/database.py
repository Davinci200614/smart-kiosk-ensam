"""Compatibility layer for the JSON-backed application.

The project is intentionally configured to use JSON persistence. This module keeps
legacy code working when older UI entry points still call SessionLocal() and
configure_database().
"""

from __future__ import annotations

DEFAULT_DATABASE_URL = "json://local"


class JSONSession:
    """Minimal no-op context manager used by the legacy UI layer."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def close(self) -> None:
        return None


SessionLocal = JSONSession


def configure_database(database_url: str = DEFAULT_DATABASE_URL) -> None:
    """Legacy compatibility shim for the JSON-only backend."""
    return None


def init_db() -> None:
    """Legacy compatibility shim for the JSON-only backend."""
    return None


if __name__ == "__main__":
    init_db()