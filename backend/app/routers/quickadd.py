from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import models, schemas
from app.dependencies import get_db
from app.ai_quickadd import build_messages, parse_description

router = APIRouter(prefix="/tasks", tags=["ai-quick-add"])


@router.post("/quick-add", response_model=schemas.TaskOut, status_code=201)
def quick_add_task(payload: schemas.QuickAddRequest, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == payload.project_id).first()
    if project is None:
        raise HTTPException(status_code=422, detail=f"project_id {payload.project_id} does not reference an existing project")

    # Role-based prompt construction (system + user) — built even though the
    # mock, not a live model, answers it. Keeps the code path identical to
    # the optional real-LLM path.
    _messages = build_messages(payload.description)  # noqa: F841 (kept for parity/inspection)

    parsed = parse_description(payload.description)

    # Whatever produced the fields (mock or optional real LLM) must be
    # validated against the Pydantic response model before persisting.
    try:
        candidate = schemas.TaskCreate(
            title=parsed["title"],
            priority=parsed["priority"],
            due_date=parsed["due_date_hint"],
            project_id=payload.project_id,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())

    task = models.Task(**candidate.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
