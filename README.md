# Task API

A small **CRUD API** for managing a to-do list, built with **FastAPI**.

Tasks are stored **in memory** (a Python list) — there is no database. This is deliberate: the
assignment's point is the request → response loop and correct HTTP semantics, not persistence.

> FlyRank Internship · Backend Development Track · Week 2 · Assignment A1

---

## Requirements

- Python 3.10+
- Git

## Install & run

```bash
git clone https://github.com/MTahaR-dev/task-api.git
cd task-api

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
fastapi dev main.py
```

The server starts at **http://localhost:8000**.

Interactive documentation (Swagger UI): **http://localhost:8000/docs**

---

## Endpoints

| Method | Path | Description | Success | Errors |
|---|---|---|---|---|
| `GET` | `/` | API name, version and available resources | `200` | — |
| `GET` | `/health` | Liveness check | `200` | — |
| `GET` | `/tasks` | List all tasks | `200` | — |
| `GET` | `/tasks/{id}` | Get one task by id | `200` | `404` unknown id |
| `POST` | `/tasks` | Create a task from `{"title": "..."}` | `201` | `400` missing/empty title |
| `PUT` | `/tasks/{id}` | Update `title` and/or `done` | `200` | `400` empty body · `404` unknown id |
| `DELETE` | `/tasks/{id}` | Delete a task | `204` (empty body) | `404` unknown id |

### Task shape

```json
{ "id": 1, "title": "Buy milk", "done": false }
```

| Field | Type | Notes |
|---|---|---|
| `id` | integer | Assigned by the server, never by the client |
| `title` | string | Required on create, must not be blank |
| `done` | boolean | Always `false` on create |

### Error shape

Every error returns a consistent JSON body, produced by a single global exception handler:

```json
{ "error": "Task 99 not found" }
```

---

## Example: full CRUD cycle with curl

> On Windows PowerShell use `curl.exe`, not `curl` — the latter is an alias for `Invoke-WebRequest`.

```bash
curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Buy milk"}'
curl -i -X PUT  http://localhost:8000/tasks/4 -H "Content-Type: application/json" -d '{"done":true}'
curl -i http://localhost:8000/tasks
curl -i -X DELETE http://localhost:8000/tasks/4
curl -i http://localhost:8000/tasks/99
```

### Actual output

<!-- PASTE YOUR REAL `curl -i` OUTPUT BETWEEN THE BACKTICKS BELOW -->

```
HTTP/1.1 200 OK
date: Fri, 07 Aug 2026 17:26:49 GMT
server: uvicorn
content-length: 29
content-type: application/json

{"error":"Task 99 not found"}
```

---

## Swagger UI

Every endpoint is documented and executable at `/docs`. FastAPI generates the OpenAPI spec
directly from the route decorators and type hints — no spec file is written by hand.

![Swagger UI](swagger.png)

---

## The mortality experiment

Create a few tasks, stop the server (`Ctrl+C`), start it again, then call `GET /tasks`.
**The new tasks are gone and the original three are back.**

This happens because `tasks` is an ordinary Python list living in the process's RAM. When the
process ends, its memory is released; when it starts again, the module is re-executed and the
list is rebuilt from its literal definition. Nothing was ever written to disk. This is exactly
the problem a database solves, and the reason Week 3 exists.

---

## Notes on design decisions

- **`title` is declared optional in the Pydantic model**, then validated by hand. Declaring it
  required would make FastAPI return `422 Unprocessable Entity` for a missing field, but the
  assignment specifies `400 Bad Request` — so validation is done explicitly to control the status code.
- **Ids use `max(existing) + 1`, not `len(tasks) + 1`.** After a delete, `len + 1` can produce an
  id that already exists, silently creating two tasks with the same id.
- **`PUT` uses `is not None` checks**, not truthiness. `if payload.done:` would ignore `false`,
  making it impossible to un-tick a completed task.
- **A single `@app.exception_handler`** reshapes FastAPI's default `{"detail": ...}` into
  `{"error": ...}` for every endpoint at once, rather than hand-writing error bodies in five places.

---

## AI vs me

<!-- Stage 7 (bonus). Fill this in after generating an AI version in ai-version/ -->

**My prompt**

```
(paste the prompt you wrote from memory here)
```

**What the AI did better**

-

**What it got wrong or ignored**

-

**What my prompt failed to specify**

-

**After one rematch**

-
