"""Postgres implementation of TaskRepository.

Differences from the SQLite version, all of them dialect details rather than logic:

  placeholder        ?              ->  %s
  auto id            AUTOINCREMENT  ->  SERIAL / IDENTITY
  boolean            INTEGER 1/0    ->  native BOOLEAN
  id of new row      cursor.lastrowid -> RETURNING id, title, done

The method signatures and return values are identical, which is the point.
"""

import os

import psycopg
from psycopg.rows import dict_row

from .base import TaskRepository

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://taskuser:taskpass@localhost:5432/taskdb"
)


class PostgresTaskRepository(TaskRepository):
    def _connect(self) -> psycopg.Connection:
        # row_factory=dict_row makes every fetch return a plain dict.
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)

    def init_schema(self) -> None:
        """Safety net for running outside Docker. In compose, init.sql already did this."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id    SERIAL PRIMARY KEY,
                    title TEXT    NOT NULL,
                    done  BOOLEAN NOT NULL DEFAULT FALSE
                )
                """
            )
            count = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
            if count == 0:
                conn.execute(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s), (%s, %s), (%s, %s)",
                    ("Task 1", False, "Task 2", True, "Task 3", False),
                )
            conn.commit()

    def list_tasks(self, done: bool | None = None, search: str | None = None) -> list[dict]:
        query = "SELECT id, title, done FROM tasks"
        conditions, params = [], []

        if done is not None:
            conditions.append("done = %s")
            params.append(done)
        if search:
            conditions.append("title ILIKE %s")  # ILIKE = case-insensitive LIKE
            params.append(f"%{search}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id"

        with self._connect() as conn:
            return conn.execute(query, params).fetchall()

    def get_task(self, task_id: int) -> dict | None:
        with self._connect() as conn:
            return conn.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s", (task_id,)
            ).fetchone()

    def create_task(self, title: str) -> dict:
        with self._connect() as conn:
            row = conn.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done",
                (title, False),
            ).fetchone()
            conn.commit()
        return row

    def update_task(self, task_id: int, title: str | None, done: bool | None) -> dict | None:
        # Column names come from this file only; values always travel as parameters.
        fields, params = [], []
        if title is not None:
            fields.append("title = %s")
            params.append(title)
        if done is not None:
            fields.append("done = %s")
            params.append(done)
        params.append(task_id)

        with self._connect() as conn:
            row = conn.execute(
                f"UPDATE tasks SET {', '.join(fields)} WHERE id = %s "
                "RETURNING id, title, done",
                params,
            ).fetchone()
            conn.commit()
        return row

    def delete_task(self, task_id: int) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,)
            ).fetchone()
            conn.commit()
        return row is not None

    def stats(self) -> dict:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS total, "
                "COUNT(*) FILTER (WHERE done) AS done "
                "FROM tasks"
            ).fetchone()
        total, done = row["total"], row["done"]
        return {"total": total, "done": done, "open": total - done}
