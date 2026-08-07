"""
Database engine + session setup.

TaskFlow uses Supabase's managed Postgres as its database. Supabase is just
Postgres under the hood, so from SQLAlchemy's point of view this is a normal
Postgres connection — we don't need the Supabase client library at all, only
a standard `DATABASE_URL` connection string (psycopg2 driver).

CHANGEABLE: DATABASE_URL comes from your .env file (see .env.example). If it
is missing, we fall back to a local SQLite file so the app still boots for
quick local testing — but the graded, "real" setup is the Supabase URL.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./taskflow_fallback.db")

# CHANGEABLE: connect_args is only needed for the SQLite fallback path.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """Create all tables if they don't already exist (called on startup)."""
    # Import models here so they're registered on Base.metadata before create_all.
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
