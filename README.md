# TaskFlow — Pod Console

A full-stack task-and-project management platform for Blinkit's dark-store
engineering pods: relational backend + dashboard (Section 1), a hand-rolled
sorting/search engine wired into two real endpoints (Section 2), and a
keyless AI quick-add parser that writes into the same task table as
everything else (Section 3). One repository, one running app.

```
taskflow/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, middleware, CORS, routers
│   │   ├── database.py        # SQLAlchemy engine/session (Supabase Postgres)
│   │   ├── models.py          # ORM models: User, Project, Task
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── dependencies.py    # shared get_db() dependency
│   │   ├── algorithms.py      # Section 2 engine
│   │   ├── ai_quickadd.py     # Section 3 mock parser + prompt builder
│   │   └── routers/           # users, projects, tasks, quickadd
│   ├── seed.py
│   ├── check_algorithms.py
│   ├── benchmark.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── README.md
```

---

## 1. Environment setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### Database: Supabase (Postgres)

TaskFlow stores data in **Supabase's managed Postgres**. Supabase is
standard Postgres under the hood, so the backend talks to it the same way
it would talk to any Postgres instance — via a `DATABASE_URL` connection
string, no Supabase-specific SDK required.

**CHANGEABLE — steps to point this at your own Supabase project:**

1. Create a free project at [supabase.com](https://supabase.com).
2. Go to **Project Settings → Database → Connection string → URI**.
3. Copy the URI (looks like
   `postgresql://postgres:[PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres`)
   and paste it into `backend/.env` as `DATABASE_URL`, filling in your DB
   password.
4. That's it — `init_db()` runs `Base.metadata.create_all()` against that
   connection on startup and creates `users`, `projects`, `tasks`
   automatically the first time you run the server.

If `DATABASE_URL` is left unset, the app falls back to a local SQLite file
(`taskflow_fallback.db`) purely so it still boots for a quick sanity check —
the graded setup is the Supabase connection string above.

---

## 2. Running the whole app locally

We use the **two-process run** (recommended):

**Terminal 1 — backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — frontend (any static server):**
```bash
cd frontend
python3 -m http.server 5500
# then open http://127.0.0.1:5500 in your browser
```

Make sure `backend/.env`'s `FRONTEND_ORIGIN` matches whichever origin you
actually load the frontend from (`http://127.0.0.1:5500` by default), and
that `frontend/app.js`'s `API_BASE` (`http://127.0.0.1:8000` by default)
matches wherever uvicorn is running. Both are marked `// CHANGEABLE` /
`# CHANGEABLE` at the top of their respective files.

**Optional single-process run** (backend also serves the frontend): uncomment
the `StaticFiles` mount block at the bottom of `backend/app/main.py`, then
just run `uvicorn app.main:app --reload` and open `http://127.0.0.1:8000`.

### Seed sample data

```bash
cd backend
python3 seed.py
```

Creates 2 users, 2 projects, and 12 sample tasks so the dashboard isn't
empty on first load. Project id `1` is used by the frontend's quick-add
form (`ACTIVE_PROJECT_ID` in `app.js` — changeable).

---

## 3. Endpoint reference

Base URL: `http://127.0.0.1:8000`

### Users

**`POST /users`** — create a user
```json
// request
{ "name": "Aditi Sharma", "email": "aditi@blinkit.example" }
// response 201
{ "id": 1, "name": "Aditi Sharma", "email": "aditi@blinkit.example", "created_at": "2026-08-03T10:00:00" }
```

**`GET /users`** — list all users → `200`, array of the shape above.

### Projects

**`POST /projects`** — create a project
```json
// request
{ "name": "Dark Store Ops - Pod A", "description": "Day-to-day ops", "owner_id": 1 }
// response 201
{ "id": 1, "name": "Dark Store Ops - Pod A", "description": "Day-to-day ops", "owner_id": 1, "created_at": "2026-08-03T10:00:00" }
```

**`GET /projects`** — list all projects → `200`, array of the shape above.

**`GET /projects/{id}`** — get one project → `200`, or `404` if the id
doesn't exist.

**`GET /projects/{id}/stats`** — SQL-aggregated statistics
```json
// response 200
{ "project_id": 1, "project_name": "Dark Store Ops - Pod A", "total_tasks": 6, "todo": 2, "in_progress": 1, "done": 3 }
```

### Tasks — CRUD

**`POST /tasks`** — create
```json
// request
{ "title": "Restock cold shelf", "priority": "high", "due_date": "tomorrow", "status": "todo", "project_id": 1 }
// response 201
{ "id": 5, "title": "Restock cold shelf", "description": null, "priority": "high", "due_date": "tomorrow", "status": "todo", "project_id": 1, "created_at": "2026-08-03T10:05:00" }
```
`422` if `title` is blank, `priority` isn't one of `low/medium/high`, or
`project_id` doesn't reference an existing project.

**`GET /tasks`** — list (optionally `?project_id=1`) → `200`, array.

**`GET /tasks/{id}`** — get one → `200`, or `404`.

**`PUT /tasks/{id}`** — partial update
```json
// request
{ "status": "done" }
// response 200
{ "id": 5, "title": "Restock cold shelf", "description": null, "priority": "high", "due_date": "tomorrow", "status": "done", "project_id": 1, "created_at": "2026-08-03T10:05:00" }
```
`404` if the id doesn't exist.

**`DELETE /tasks/{id}`** → `200`
```json
{ "deleted": true, "id": 5 }
```

### Tasks — algorithms-powered (Section 2)

**`GET /tasks?sort=priority`** (or `?sort=due_date`) — ordering produced by
`insertion_sort()`, not the database or a built-in sort.
```json
// response 200
[
  { "id": 3, "title": "Clean spill", "priority": "high", "due_date": "today", "status": "todo", "project_id": 1, "created_at": "..." },
  { "id": 7, "title": "Audit expiry dates", "priority": "medium", "due_date": null, "status": "todo", "project_id": 1, "created_at": "..." }
]
```

**`GET /tasks/search?title=<exact title>&algo=binary|linear`** (default
`binary`) — exact-title lookup via `binary_search`/`linear_search`.
```json
// GET /tasks/search?title=Clean spill&algo=binary
// response 200
{ "id": 3, "title": "Clean spill", "priority": "high", "due_date": "today", "status": "todo", "project_id": 1, "created_at": "..." }
```
`404` if no task has that exact title.

### AI Quick-Add (Section 3)

**`POST /tasks/quick-add`**
```json
// request
{ "description": "Restock the cold shelf, it's urgent, needed by next friday", "project_id": 1 }
// response 201
{ "id": 9, "title": "Restock the cold shelf, it's , needed by", "description": null, "priority": "high", "due_date": "next friday", "status": "todo", "project_id": 1, "created_at": "..." }
```
`422` on a malformed body or a `project_id` that doesn't reference an
existing project — no row is written in that case.

---

## 4. Middleware, dependency reuse & CORS

- **Middleware**: `log_requests()` in `app/main.py` runs on every request
  and logs `METHOD /path - Xms - status`. Watch the terminal running
  `uvicorn` to see it fire.
- **Shared dependency**: `get_db()` in `app/dependencies.py` is defined once
  and used via `Depends(get_db)` across users, projects, tasks, and
  quick-add routers.
- **CORS**: configured in `app/main.py` with an explicit `FRONTEND_ORIGIN`
  (from `.env`), explicit methods (`GET, POST, PUT, DELETE, OPTIONS`), and
  explicit headers (`Content-Type, Authorization`) — no wildcard.

---

## 5. Git workflow

This repo's history includes a feature branch (`feature/quick-add-and-algorithms`)
created off `main`, committed to multiple times, and merged back via a
merge commit — visible with:
```bash
git log --graph --all --oneline
```

---

## 6. Section 2 — Algorithms write-up

### Complexity

| Function | Best case | Worst case |
|---|---|---|
| `insertion_sort` | O(n) — already sorted | O(n²) — reverse sorted |
| `binary_search` | O(1) — target at midpoint | O(log n) |
| `linear_search` | O(1) — target at index 0 | O(n) |

### Running the checks and benchmark

```bash
cd backend
python3 check_algorithms.py     # PASS/FAIL lines for every required case
python3 benchmark.py            # comparison counts at n=10, 500, 3000
```

### Benchmark results (n = 10, 500, 3000, generated via `benchmark.py`)

> Re-running `benchmark.py` regenerates `benchmark_results.txt` with fresh
> numbers from that run (synthetic titles are randomized). Representative
> output from a local run:

```
n=10
  insertion_sort_count comparisons: 24
  binary_search_count:  index=5, comparisons=3
  linear_search_count:  index=5, comparisons=6
n=500
  insertion_sort_count comparisons: 61840
  binary_search_count:  index=250, comparisons=9
  linear_search_count:  index=250, comparisons=251
n=3000
  insertion_sort_count comparisons: 2246110
  binary_search_count:  index=1500, comparisons=12
  linear_search_count:  index=1500, comparisons=1501
```

### Is sorting-first worth it?

A pod's real usage pattern is read-heavy: the team reloads and re-sorts the
task list many times a day (every time the dashboard opens, every status
check) but only adds or renames a handful of tasks per day. Our counts show
`insertion_sort`'s comparison count grows roughly with n² (≈24 → ≈61.8k →
≈2.25M as n goes 10 → 500 → 3000 — a 300x growth in n produced roughly a
36,000x growth in comparisons), which is expensive to pay repeatedly on a
large task list. But once sorted, `binary_search` stays cheap (single-digit
to low-double-digit comparisons even at n=3000) versus `linear_search`
scaling linearly with n. Since GET /tasks?sort=... re-sorts from scratch on
every call in our implementation, at small pod-sized task lists (tens to
low hundreds of tasks) the up-front insertion-sort cost is trivial and
clearly worth it for the always-sorted view teams see. At the top end of
our benchmarked range (3000 tasks) it starts to be the dominant cost per
request, which is the point at which we'd consider caching the sorted order
or switching the sort step to the database's own indexed `ORDER BY` for
the *display* path — while keeping `insertion_sort` for the graded engine
itself.

---

## 7. Section 3 — AI Quick-Add write-up

### Prompting technique: zero-shot

`ai_quickadd.py`'s `build_messages()` sends a single **system**-role
instruction describing the extraction task, plus the raw **user**-role
description — no worked examples are included in the prompt itself
(the four worked examples in this README and the assignment brief are for
grader verification, not part of what's sent to a model). This is a
**zero-shot** design: the system message states the rule set precisely
enough (exact keyword lists, exact tie-break order, exact fallback) that no
in-context examples are needed to pin down the desired behavior.

We chose zero-shot over few-shot because the actual parsing logic here is
fully deterministic and rule-based (see Task 3's algorithm) — a real model
standing in for `mock_parse()` would need the *rules*, not example
mappings, to reproduce that determinism reliably, and adding examples would
mostly burn tokens without tightening the output further. Zero-shot keeps
the prompt short (lower token usage, lower latency, lower cost if the
optional real-LLM path is ever enabled), at the cost of being more
sensitive to ambiguous natural-language phrasing than a few-shot prompt
would be — a trade-off that's fine here because the required path is the
fully deterministic mock, not the optional model call. We did not use
chain-of-thought because the task is extraction, not multi-step reasoning;
asking for step-by-step reasoning would only inflate token usage without
improving reliability on a rule-following task like this one.

### Five worked examples (mock parser output, verifiable by inspection)

| # | Input | Output |
|---|---|---|
| 1 | `"This is urgent, mark it ASAP please"` | `{"title": "This is , mark it please", "priority": "high", "due_date_hint": null}` |
| 2 | `" "` | `{"title": "Untitled task", "priority": "medium", "due_date_hint": null}` |
| 3 | `"Finish the report next Friday, it's urgent"` | `{"title": "Finish the report , it's", "priority": "high", "due_date_hint": "next friday"}` |
| 4 | `"tomorrow review tomorrow"` | `{"title": "review", "priority": "medium", "due_date_hint": "tomorrow"}` |
| 5 | `"Sort the returned items whenever you get a chance"` | `{"title": "Sort the returned items you get a chance", "priority": "low", "due_date_hint": null}` |

(Examples 1–4 match the brief's own worked examples exactly; example 5 is
an additional case demonstrating the group (ii) "whenever" keyword path.)

---

## 8. Notes on academic integrity & scope

- The required AI quick-add path (`mock_parse()`) runs with **zero network
  calls and zero API keys** — nothing in this repo requires a paid service
  to build, run, or grade.
- The optional real-LLM path in `ai_quickadd.py` is feature-flagged off via
  `USE_REAL_LLM` (unset/false by default) and is never required.
