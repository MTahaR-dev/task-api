"""SQLite implementation of TaskRepository (the Week 3 storage, kept for comparison).

SQLite has no boolean type, so `done` is stored as 1/0 and converted back on the way
out. Placeholders are `?`.
"""

import sqlite3
from pathlib import Path

from .base import TaskRepository

DB_PATH = Path(__file__).resolve().parent.parent / "tasks.db"


def _row_to_task(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


class SQLiteTaskRepository(TaskRepository):
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT    NOT NULL,
                    done  INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            if conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0:
                conn.executemany(
                    "INSERT INTO tasks (title, done) VALUES (?, ?)",
                    [("Task 1", 0), ("Task 2", 1), ("Task 3", 0)],
                )
            conn.commit()
        finally:
            conn.close()

    def list_tasks(self, done: bool | None = None, search: str | None = None) -> list[dict]:
        query = "SELECT id, title, done FROM tasks"
        conditions, params = [], []

        if done is not None:
            conditions.append("done = ?")
            params.append(1 if done else 0)
        if search:
            conditions.append("title LIKE ?")
            params.append(f"%{search}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id"

        conn = self._connect()
        try:
            rows = conn.execute(query, params).fetchall()
        finally:
            conn.close()
        return [_row_to_task(row) for row in rows]

    def get_task(self, task_id: int) -> dict | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        finally:
            conn.close()
        return _row_to_task(row) if row else None

    def create_task(self, title: str) -> dict:
        conn = self._connect()
        try:
            cursor = conn.execute(
                "INSERT INTO tasks (title, done) VALUES (?, ?)", (title, 0)
            )
            conn.commit()
            row = conn.execute(
                "SELECT id, title, done FROM tasks WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        finally:
            conn.close()
        return _row_to_task(row)

    def update_task(self, task_id: int, title: str | None, done: bool | None) -> dict | None:
        # Column names come from this file only; values always travel as parameters.
        fields, params = [], []
        if title is not None:
            fields.append("title = ?")
            params.append(title)
        if done is not None:
            fields.append("done = ?")
            params.append(1 if done else 0)
        params.append(task_id)

        conn = self._connect()
        try:
            cursor = conn.execute(
                f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", params
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            row = conn.execute(
                "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        finally:
            conn.close()
        return _row_to_task(row)

    def delete_task(self, task_id: int) -> bool:
        conn = self._connect()
        try:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def stats(self) -> dict:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS total, COALESCE(SUM(done), 0) AS done FROM tasks"
            ).fetchone()
        finally:
            conn.close()
        total, done = row["total"], row["done"]
        return {"total": total, "done": done, "open": total - done}
