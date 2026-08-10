"""Repository factory.

main.py calls get_repository() and receives *something* that satisfies TaskRepository.
It never imports sqlite3 or psycopg, and never learns which one it got.

Which implementation is returned is decided entirely by the TASK_REPOSITORY
environment variable, read from .env.
"""

import os

from dotenv import load_dotenv

from .base import TaskRepository

load_dotenv()  # read .env into the environment, if the file exists

_BACKEND = os.getenv("TASK_REPOSITORY", "sqlite").strip().lower()


def get_repository() -> TaskRepository:
    if _BACKEND == "postgres":
        from .postgres_repo import PostgresTaskRepository

        return PostgresTaskRepository()

    if _BACKEND == "sqlite":
        from .sqlite_repo import SQLiteTaskRepository

        return SQLiteTaskRepository()

    raise ValueError(
        f"Unknown TASK_REPOSITORY={_BACKEND!r}. Expected 'sqlite' or 'postgres'."
    )


def backend_name() -> str:
    """Which backend is active. Exposed on GET / so it is visible without reading code."""
    return _BACKEND


__all__ = ["TaskRepository", "get_repository", "backend_name"]
