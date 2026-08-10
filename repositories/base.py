"""The storage interface.

Every repository implementation must provide exactly these methods. The API layer
(main.py) is written against this class and never against a specific database, which
is what makes swapping SQLite for Postgres a one-line configuration change.

Note what is NOT here: no HTTP, no status codes, no HTTPException. A repository
reports facts ("no such row" -> None, "nothing deleted" -> False) and lets the
API layer decide what those facts mean in HTTP terms.
"""

from abc import ABC, abstractmethod


class TaskRepository(ABC):
    @abstractmethod
    def init_schema(self) -> None:
        """Create the table if missing and seed example rows if it is empty."""

    @abstractmethod
    def list_tasks(self, done: bool | None = None, search: str | None = None) -> list[dict]:
        """Return all tasks, optionally filtered by completion and/or title search."""

    @abstractmethod
    def get_task(self, task_id: int) -> dict | None:
        """Return one task, or None if no task has that id."""

    @abstractmethod
    def create_task(self, title: str) -> dict:
        """Insert a task and return it, including the id assigned by the database."""

    @abstractmethod
    def update_task(self, task_id: int, title: str | None, done: bool | None) -> dict | None:
        """Update the given fields and return the task, or None if the id is unknown."""

    @abstractmethod
    def delete_task(self, task_id: int) -> bool:
        """Delete the task. Return True if a row was removed, False if the id is unknown."""

    @abstractmethod
    def stats(self) -> dict:
        """Return {"total": int, "done": int, "open": int}."""
