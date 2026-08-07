"""
Shared FastAPI dependencies. `get_db` is written once here and reused across
every router in the app (users, projects, tasks, algorithms endpoints, and
the AI quick-add endpoint) via `Depends(get_db)`.
"""
from typing import Generator

from app.database import SessionLocal


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
