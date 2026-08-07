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
| `GET` | `/stats` | Counts of total / done / open tasks | `200` | — |
| `GET` | `/tasks` | List all tasks | `200` | — |
| `GET` | `/tasks?done=true` | List only finished (or unfinished) tasks | `200` | — |
| `GET` | `/tasks?search=milk` | List tasks whose title contains the term | `200` | — |
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

Create a task, mark it done, list everything, delete it, then trigger both error paths.
Full session below — status line, headers and body for every step.

```
$ curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Buy milk"}'
HTTP/1.1 201 Created
date: Fri, 07 Aug 2026 18:00:15 GMT
server: uvicorn
content-length: 40
content-type: application/json

{"id":4,"title":"Buy milk","done":false}


$ curl -i -X PUT http://localhost:8000/tasks/4 -H "Content-Type: application/json" -d '{"done":true}'
HTTP/1.1 200 OK
date: Fri, 07 Aug 2026 18:00:15 GMT
server: uvicorn
content-length: 39
content-type: application/json

{"id":4,"title":"Buy milk","done":true}


$ curl -i http://localhost:8000/tasks
HTTP/1.1 200 OK
date: Fri, 07 Aug 2026 18:00:15 GMT
server: uvicorn
content-length: 157
content-type: application/json

[{"id":1,"title":"Task 1","done":false},{"id":2,"title":"Task 2","done":true},{"id":3,"title":"Task 3","done":false},{"id":4,"title":"Buy milk","done":true}]


$ curl -i -X DELETE http://localhost:8000/tasks/4
HTTP/1.1 204 No Content
date: Fri, 07 Aug 2026 18:00:15 GMT
server: uvicorn


$ curl -i http://localhost:8000/tasks/99
HTTP/1.1 404 Not Found
date: Fri, 07 Aug 2026 18:00:15 GMT
server: uvicorn
content-length: 29
content-type: application/json

{"error":"Task 99 not found"}


$ curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{}'
HTTP/1.1 400 Bad Request
date: Fri, 07 Aug 2026 18:00:15 GMT
server: uvicorn
content-length: 29
content-type: application/json

{"error":"Title is required"}


$ curl -i "http://localhost:8000/tasks?done=true"
HTTP/1.1 200 OK
date: Fri, 07 Aug 2026 18:00:15 GMT
server: uvicorn
content-length: 39
content-type: application/json

[{"id":2,"title":"Task 2","done":true}]


$ curl -i http://localhost:8000/stats
HTTP/1.1 200 OK
date: Fri, 07 Aug 2026 18:00:15 GMT
server: uvicorn
content-length: 29
content-type: application/json

{"total":3,"done":1,"open":2}
```

Note the `204 No Content` response: no `content-length`, no body at all. The status code *is*
the answer — that is what "No Content" means.

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
- **Query parameters for filtering, path parameters for identity.** `/tasks/3` addresses one
  specific resource; `/tasks?done=true` describes a view of the collection. Mixing the two up
  (`/tasks/done`) is a common REST design mistake.

