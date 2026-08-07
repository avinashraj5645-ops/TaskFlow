from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.dependencies import get_db
from app.algorithms import (
    insertion_sort,
    binary_search,
    linear_search,
    with_priority_rank,
    NOT_FOUND,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _task_to_dict(t: models.Task) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "priority": t.priority,
        "due_date": t.due_date,
        "status": t.status,
        "project_id": t.project_id,
        "created_at": t.created_at,
    }


@router.post("", response_model=schemas.TaskOut, status_code=201)
def create_task(payload: schemas.TaskCreate, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == payload.project_id).first()
    if project is None:
        raise HTTPException(status_code=422, detail=f"project_id {payload.project_id} does not reference an existing project")
    task = models.Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=None)
def list_tasks(
    sort: Optional[str] = Query(default=None, description="e.g. priority or due_date"),
    project_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Plain list, OR — when ?sort=priority (or ?sort=due_date) is given — the
    Section 2 algorithms engine's own insertion_sort() produces the ordering
    (never the database's ORDER BY, never Python's built-in sort).
    """
    query = db.query(models.Task)
    if project_id is not None:
        query = query.filter(models.Task.project_id == project_id)
    tasks = [_task_to_dict(t) for t in query.all()]

    if sort is None:
        return tasks

    if sort == "priority":
        tasks = with_priority_rank(tasks)
        insertion_sort(tasks, "priority_rank")
        for t in tasks:
            t.pop("priority_rank", None)
        return tasks

    if sort == "due_date":
        # CHANGEABLE: nulls sort last for a friendlier task list.
        for t in tasks:
            t["_due_sort_key"] = t["due_date"] or "\uffff"
        insertion_sort(tasks, "_due_sort_key")
        for t in tasks:
            t.pop("_due_sort_key", None)
        return tasks

    raise HTTPException(status_code=422, detail="sort must be one of: priority, due_date")


@router.get("/search", response_model=None)
def search_tasks(
    title: str = Query(...),
    algo: str = Query(default="binary", pattern="^(binary|linear)$"),
    db: Session = Depends(get_db),
):
    """
    Exact-title lookup powered by Section 2's binary_search / linear_search
    over an in-memory index built from real database rows.
    """
    all_tasks = db.query(models.Task).all()
    index = [{"id": t.id, "title": t.title} for t in all_tasks]

    if algo == "binary":
        insertion_sort(index, "title")
        found_at = binary_search(index, title, "title")
    else:
        found_at = linear_search(index, title, "title")

    if found_at == NOT_FOUND:
        raise HTTPException(status_code=404, detail=f"No task with exact title '{title}'")

    matched_id = index[found_at]["id"]
    task = db.query(models.Task).filter(models.Task.id == matched_id).first()
    return _task_to_dict(task)


@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, payload: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=200)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"deleted": True, "id": task_id}
