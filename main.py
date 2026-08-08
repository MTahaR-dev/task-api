from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from db import get_connection, row_to_task, init_db

init_db()

app = FastAPI(
    title="Task API",
    description="A small CRUD API for managing a to-do list, backed by SQLite. "
                "FlyRank Internship-Backend Track-Week 3-Assignment A1.",
    version="1.0",
)

# ---------- Models ----------
class TaskCreate(BaseModel):
    title: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


# ---------- Meta ----------
@app.get("/", summary="API information", tags=["Meta"])
def read_root():
    """Describe this API: its name, version and available resources."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Health check", tags=["Meta"])
def health_check():
    """Return 200 while the server is alive. Used by uptime monitors."""
    return {"status": "ok"}


@app.get("/stats", summary="Task statistics", tags=["Meta"])
def get_stats():
    """Return counts of total, completed and open tasks, computed by SQL."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(done), 0) AS done FROM tasks"
        ).fetchone()
    finally:
        conn.close()

    total, done = row["total"], row["done"]
    return {"total": total, "done": done, "open": total - done}


# ---------- Tasks ----------
@app.get("/tasks", summary="List tasks, optionally filtered", tags=["Tasks"])
def list_tasks(done: bool | None = None, search: str | None = None):
    """List all tasks. Filter with ?done=true, or search titles with ?search=milk."""
    query = "SELECT id, title, done FROM tasks"
    conditions = []
    params = []

    if done is not None:
        conditions.append("done = ?")
        params.append(1 if done else 0)
    if search:
        conditions.append("title LIKE ?")
        params.append(f"%{search}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id"

    conn = get_connection()
    try:
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()

    return [row_to_task(row) for row in rows]


@app.get("/tasks/{task_id}", summary="Get one task", tags=["Tasks"])
def get_task(task_id: int):
    """Return a single task by id. Returns 404 if no task has that id."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return row_to_task(row)


@app.post("/tasks", status_code=201, summary="Create a task", tags=["Tasks"])
def create_task(payload: TaskCreate):
    """Create a task from a non-empty `title`. The database assigns the id."""
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")

    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (payload.title.strip(), 0),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    finally:
        conn.close()

    return row_to_task(row)


@app.put("/tasks/{task_id}", summary="Update a task", tags=["Tasks"])
def update_task(task_id: int, payload: TaskUpdate):
    """Update a task's title and/or done flag. Send at least one field."""
    if payload.title is None and payload.done is None:
        raise HTTPException(status_code=400, detail="Nothing to update: send title and/or done")
    if payload.title is not None and not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    # Column names are built from our own code; values always go through ? placeholders.
    fields = []
    params = []
    if payload.title is not None:
        fields.append("title = ?")
        params.append(payload.title.strip())
    if payload.done is not None:
        fields.append("done = ?")
        params.append(1 if payload.done else 0)
    params.append(task_id)

    conn = get_connection()
    try:
        cursor = conn.execute(
            f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", params
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    finally:
        conn.close()

    return row_to_task(row)


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task", tags=["Tasks"])
def delete_task(task_id: int):
    """Delete a task by id. Returns 204 with an empty body on success."""
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        deleted = cursor.rowcount
    finally:
        conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return None


# ---------- Error formatting ----------
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    """Render every HTTPException as {"error": "..."} instead of FastAPI's default {"detail": ...}."""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

