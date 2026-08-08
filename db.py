import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tasks.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_task(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute()

        count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                [("Task 1", 0), ("Task 2", 1), ("Task 3", 0)],
            )

        conn.commit()
    finally:
        conn.close()