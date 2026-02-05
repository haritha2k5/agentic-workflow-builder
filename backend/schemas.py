"""Pydantic schemas for workflow creation."""

from pydantic import BaseModel, Field


class StepCreate(BaseModel):
    model: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    criteria: str | None = None
    retry_limit: int = Field(default=0, ge=0)
    step_order: int = Field(..., ge=0)


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1)
    steps: list[StepCreate]
