"""Task API — HTTP layer only.

This file owns routing, request validation and status codes. It does not know whether
data lives in SQLite, Postgres, or anything else: it only talks to a TaskRepository.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from repositories import backend_name, get_repository

app = FastAPI(
    title="Task API",
    description="A CRUD API for managing a to-do list. Storage is pluggable: SQLite or "
                "Postgres, selected by the TASK_REPOSITORY environment variable. "
                "FlyRank Internship-Backend Track.",
    version="2.0",
)

repo = get_repository()
repo.init_schema()


# ---------- Models ----------
class TaskCreate(BaseModel):
    title: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


# ---------- Meta ----------
@app.get("/", summary="API information", tags=["Meta"])
def read_root():
    """Describe this API: its name, version, active storage backend and resources."""
    return {
        "name": "Task API",
        "version": "2.0",
        "storage": backend_name(),
        "endpoints": ["/tasks"],
    }


@app.get("/health", summary="Health check", tags=["Meta"])
def health_check():
    """Return 200 while the server is alive. Used by uptime monitors and Docker."""
    return {"status": "ok"}


@app.get("/stats", summary="Task statistics", tags=["Meta"])
def get_stats():
    """Return counts of total, completed and open tasks, computed by the database."""
    return repo.stats()


# ---------- Tasks ----------
@app.get("/tasks", summary="List tasks, optionally filtered", tags=["Tasks"])
def list_tasks(done: bool | None = None, search: str | None = None):
    """List all tasks. Filter with ?done=true, or search titles with ?search=milk."""
    return repo.list_tasks(done=done, search=search)


@app.get("/tasks/{task_id}", summary="Get one task", tags=["Tasks"])
def get_task(task_id: int):
    """Return a single task by id. Returns 404 if no task has that id."""
    task = repo.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.post("/tasks", status_code=201, summary="Create a task", tags=["Tasks"])
def create_task(payload: TaskCreate):
    """Create a task from a non-empty `title`. The database assigns the id."""
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    return repo.create_task(payload.title.strip())


@app.put("/tasks/{task_id}", summary="Update a task", tags=["Tasks"])
def update_task(task_id: int, payload: TaskUpdate):
    """Update a task's title and/or done flag. Send at least one field."""
    if payload.title is None and payload.done is None:
        raise HTTPException(status_code=400, detail="Nothing to update: send title and/or done")
    if payload.title is not None and not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    title = payload.title.strip() if payload.title is not None else None
    task = repo.update_task(task_id, title, payload.done)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task", tags=["Tasks"])
def delete_task(task_id: int):
    """Delete a task by id. Returns 204 with an empty body on success."""
    if not repo.delete_task(task_id):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return None


# ---------- Error formatting ----------
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    """Render every HTTPException as {"error": "..."} instead of FastAPI's {"detail": ...}."""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
