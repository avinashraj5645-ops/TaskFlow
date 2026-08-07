"""
Seed the database with sample users/projects/tasks, and (optionally)
generate synthetic in-memory task records at benchmark sizes for
benchmark.py, using the exact same fields the real endpoints operate on
(title, priority, due_date).

Usage:
    python3 seed.py            # seeds a small realistic dataset into the DB
    python3 seed.py --sizes    # also prints synthetic dataset sizes info
"""
import random
import sys

from app.database import SessionLocal, init_db
from app import models

random.seed(42)

TITLES = [
    "Restock cold storage shelf", "Fix scanner at pack station",
    "Update pick-list for dairy aisle", "Audit expiry dates in freezer",
    "Train new rider on route app", "Resolve payment gateway timeout",
    "Reconcile inventory count", "Clean spill in aisle 3",
    "Replace broken conveyor belt", "Review late-delivery report",
    "Calibrate weighing scale", "Restock urgent items asap",
    "Follow up whenever convenient", "Prepare dark store opening checklist",
    "Escalate refrigeration alarm", "Sort returned items",
]
PRIORITIES = ["low", "medium", "high"]
DUE_DATES = [None, "today", "tomorrow", "next friday", "monday", "2026-08-15"]


def seed_core_data():
    init_db()
    db = SessionLocal()
    try:
        if db.query(models.User).count() > 0:
            print("Database already seeded (users exist) — skipping core seed.")
            return

        u1 = models.User(name="Aditi Sharma", email="aditi@blinkit.example")
        u2 = models.User(name="Rohan Verma", email="rohan@blinkit.example")
        db.add_all([u1, u2])
        db.commit()
        db.refresh(u1)
        db.refresh(u2)

        p1 = models.Project(name="Dark Store Ops - Pod A", description="Day-to-day ops tasks for Pod A", owner_id=u1.id)
        p2 = models.Project(name="Dark Store Ops - Pod B", description="Day-to-day ops tasks for Pod B", owner_id=u2.id)
        db.add_all([p1, p2])
        db.commit()
        db.refresh(p1)
        db.refresh(p2)

        statuses = ["todo", "in_progress", "done"]
        for i in range(12):
            t = models.Task(
                title=random.choice(TITLES) + f" #{i+1}",
                priority=random.choice(PRIORITIES),
                due_date=random.choice(DUE_DATES),
                status=random.choice(statuses),
                project_id=p1.id if i % 2 == 0 else p2.id,
            )
            db.add(t)
        db.commit()
        print("Seeded 2 users, 2 projects, 12 tasks.")
    finally:
        db.close()


def synthetic_records(n: int) -> list[dict]:
    """Generate n synthetic task dicts with the same fields as real tasks."""
    return [
        {
            "id": i,
            "title": f"{random.choice(TITLES)} #{i}",
            "priority": random.choice(PRIORITIES),
            "due_date": random.choice(DUE_DATES),
        }
        for i in range(n)
    ]


if __name__ == "__main__":
    seed_core_data()
    if "--sizes" in sys.argv:
        for n in (10, 500, 3000):
            recs = synthetic_records(n)
            print(f"Generated {len(recs)} synthetic records (sample: {recs[0]})")
