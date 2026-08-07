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

class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            if payload.title is None and payload.done is None:
                raise HTTPException(status_code=400, detail="Nothing to update: send title and/or done")
            if payload.title is not None and not payload.title.strip():
                raise HTTPException(status_code=400, detail="Title cannot be empty")

            if payload.title is not None:
                task["title"] = payload.title.strip()
            if payload.done is not None:
                task["done"] = payload.done
            return task

    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return None

    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

