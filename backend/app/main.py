import os
import time
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.database import init_db
from app.routers import users, projects, tasks, quickadd

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("taskflow")

app = FastAPI(title="TaskFlow API", version="1.0.0")


# ---------------------------------------------------------------------------
# Custom middleware — logs method, path, and processing time (ms) for every
# request. Runs for every route in the app, including Sections 2 & 3.
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(f"{request.method} {request.url.path} - {duration_ms:.2f}ms - {response.status_code}")
    return response


# ---------------------------------------------------------------------------
# CORS — CHANGEABLE: FRONTEND_ORIGIN must match wherever you actually serve
# frontend/ from (see README "Running the app").
# ---------------------------------------------------------------------------
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://task-flow-sandy-sigma.vercel.app/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(quickadd.router)


@app.get("/")
def health():
    return {"status": "ok", "service": "TaskFlow API"}


# ---------------------------------------------------------------------------
# OPTIONAL single-process run: uncomment to have this same process also
# serve frontend/ so the dashboard and API share one origin (see README,
# "Single-process run"). Left commented by default because the recommended
# path is the two-process run described in the README.
# ---------------------------------------------------------------------------
# frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
# if frontend_dir.exists():
#     app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
