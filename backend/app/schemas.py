"""
Pydantic request/response models. Pydantic v2 style (field_validator).
"""
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    created_at: datetime


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    owner_id: int

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    created_at: datetime


class ProjectStatsOut(BaseModel):
    project_id: int
    project_name: str
    total_tasks: int
    todo: int
    in_progress: int
    done: int


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
# CHANGEABLE closed set — keep identical to Section 3's mock parser output
# and to the DB CheckConstraint in models.py.
PriorityLiteral = Literal["low", "medium", "high"]
StatusLiteral = Literal["todo", "in_progress", "done"]


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: PriorityLiteral = "medium"
    due_date: Optional[str] = Field(default=None, max_length=50)
    status: StatusLiteral = "todo"
    project_id: int

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("title must not be blank")
        return stripped


class TaskUpdate(BaseModel):
    """All fields optional — PATCH-style partial update."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[PriorityLiteral] = None
    due_date: Optional[str] = Field(default=None, max_length=50)
    status: Optional[StatusLiteral] = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("title must not be blank")
        return stripped


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: Optional[str] = None
    priority: PriorityLiteral
    due_date: Optional[str] = None
    status: StatusLiteral
    project_id: int
    created_at: datetime


# ---------------------------------------------------------------------------
# AI Quick-Add
# ---------------------------------------------------------------------------
class QuickAddRequest(BaseModel):
    description: str = Field(..., min_length=1)
    project_id: int

    @field_validator("description")
    @classmethod
    def description_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("description must not be blank")
        return v
