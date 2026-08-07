from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
 

app = FastAPI()

tasks = [{"id": 1, "title": "Task 1", "done": False}, {"id": 2, "title": "Task 2", "done": True}, {"id": 3, "title": "Task 3", "done": False}]

@app.get("/")
def read_root():
     return {"name":"Task API","version":"1.0","endpoints":["/tasks"]}


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/tasks")
def list_tasks():
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] ==task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.exception_handler(HTTPException)
def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

class TaskCreate(BaseModel):
    title: str | None = None


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")

    new_id = (max(t["id"] for t in tasks) if tasks else 0) + 1
    new_task = {"id": new_id, "title": payload.title.strip(), "done": False}
    tasks.append(new_task)
    return new_task



