from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app import models, schemas
from app.dependencies import get_db

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=schemas.ProjectOut, status_code=201)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    owner = db.query(models.User).filter(models.User.id == payload.owner_id).first()
    if owner is None:
        raise HTTPException(status_code=422, detail=f"owner_id {payload.owner_id} does not reference an existing user")
    project = models.Project(name=payload.name, description=payload.description, owner_id=payload.owner_id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/stats", response_model=schemas.ProjectStatsOut)
def project_stats(project_id: int, db: Session = Depends(get_db)):
    """
    Per-project task statistics computed with SQL aggregates (COUNT +
    GROUP-BY-style CASE counts) executed via SQLAlchemy over a join of
    projects and tasks — NOT computed in Python after fetching every row.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    row = (
        db.query(
            func.count(models.Task.id).label("total_tasks"),
            func.sum(case((models.Task.status == "todo", 1), else_=0)).label("todo"),
            func.sum(case((models.Task.status == "in_progress", 1), else_=0)).label("in_progress"),
            func.sum(case((models.Task.status == "done", 1), else_=0)).label("done"),
        )
        .select_from(models.Project)
        .outerjoin(models.Task, models.Task.project_id == models.Project.id)
        .filter(models.Project.id == project_id)
        .group_by(models.Project.id)
        .first()
    )

    total = row.total_tasks if row else 0
    return schemas.ProjectStatsOut(
        project_id=project.id,
        project_name=project.name,
        total_tasks=total,
        todo=(row.todo or 0) if row else 0,
        in_progress=(row.in_progress or 0) if row else 0,
        done=(row.done or 0) if row else 0,
    )
