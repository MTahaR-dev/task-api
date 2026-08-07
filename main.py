from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(
    title="Task API",
    description="A small in-memory CRUD API for managing a to-do list. "
                "FlyRank Internship-Backend Track-Week 2-Assignment A1.",
    version="1.0",
)

# ---------- In-memory store (no database — data resets on restart) ----------
tasks = [
    {"id": 1, "title": "Task 1", "done": False},
    {"id": 2, "title": "Task 2", "done": True},
    {"id": 3, "title": "Task 3", "done": False},
]


# ---------- Models ----------
class TaskCreate(BaseModel):
    title: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


# ---------- Helper ----------
def find_task(task_id: int) -> dict:
    """Return the task with this id, or raise a 404."""
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


# ---------- Meta ----------
@app.get("/", summary="API information", tags=["Meta"])
def read_root():
    """Describe this API: its name, version and available resources."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Health check", tags=["Meta"])
def health_check():
    """Return 200 while the server is alive. Used by uptime monitors."""
    return {"status": "ok"}


# ---------- Tasks ----------
@app.get("/tasks", summary="List all tasks", tags=["Tasks"])
def list_tasks():
    """Return every task currently held in memory."""
    return tasks


@app.get("/tasks/{task_id}", summary="Get one task", tags=["Tasks"])
def get_task(task_id: int):
    """Return a single task by id. Returns 404 if no task has that id."""
    return find_task(task_id)


@app.post("/tasks", status_code=201, summary="Create a task", tags=["Tasks"])
def create_task(payload: TaskCreate):
    """Create a task from a non-empty `title`. The server assigns the id and sets done to false."""
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")

    new_id = (max(t["id"] for t in tasks) if tasks else 0) + 1
    new_task = {"id": new_id, "title": payload.title.strip(), "done": False}
    tasks.append(new_task)
    return new_task


@app.put("/tasks/{task_id}", summary="Update a task", tags=["Tasks"])
def update_task(task_id: int, payload: TaskUpdate):
    """Update a task's title and/or done flag. Send at least one field."""
    task = find_task(task_id)

    if payload.title is None and payload.done is None:
        raise HTTPException(status_code=400, detail="Nothing to update: send title and/or done")
    if payload.title is not None and not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    if payload.title is not None:
        task["title"] = payload.title.strip()
    if payload.done is not None:
        task["done"] = payload.done
    return task


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task", tags=["Tasks"])
def delete_task(task_id: int):
    """Delete a task by id. Returns 204 with an empty body on success."""
    task = find_task(task_id)
    tasks.remove(task)
    return None


# ---------- Error formatting ----------
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    """Render every HTTPException as {"error": "..."} instead of FastAPI's default {"detail": ...}."""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})