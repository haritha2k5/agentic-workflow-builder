"""FastAPI application for workflow execution."""

from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models import Execution, ExecutionStepLog, Step, Workflow
from runner import run_workflow
from schemas import StepCreate, WorkflowCreate

app = FastAPI()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def create_tables():
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)


@app.post("/workflow")
def create_workflow(
    workflow_data: WorkflowCreate, db: Annotated[Session, Depends(get_db)]
) -> dict:
    """Create a workflow with steps."""
    workflow = Workflow(name=workflow_data.name)
    db.add(workflow)
    db.flush()

    for step_data in workflow_data.steps:
        step = Step(
            workflow_id=workflow.id,
            model=step_data.model,
            prompt=step_data.prompt,
            completion_criteria=step_data.criteria,
            retry_limit=step_data.retry_limit,
            step_order=step_data.step_order,
        )
        db.add(step)

    db.commit()
    return {"workflow_id": workflow.id}


@app.post("/workflow/run/{workflow_id}")
def run_workflow_endpoint(
    workflow_id: int, db: Annotated[Session, Depends(get_db)]
) -> dict:
    """Run a workflow and return execution result."""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    execution_id, result = run_workflow(workflow, db)

    return {
        "execution_id": execution_id,
        "success": result.success,
        "step_outputs": result.step_outputs,
        "error_message": result.error_message,
    }


@app.get("/executions")
def list_executions(
    db: Annotated[Session, Depends(get_db)]
) -> list[dict]:
    """List all executions."""
    executions = db.query(Execution).order_by(
        Execution.created_at.desc()).all()
    return [
        {
            "id": exec.id,
            "workflow_id": exec.workflow_id,
            "status": exec.status,
            "created_at": exec.created_at.isoformat() if exec.created_at else None,
        }
        for exec in executions
    ]


@app.get("/execution/{execution_id}")
def get_execution(
    execution_id: int, db: Annotated[Session, Depends(get_db)]
) -> dict:
    """Get execution details with step logs."""
    execution = db.query(Execution).filter(
        Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    step_logs = (
        db.query(ExecutionStepLog)
        .filter(ExecutionStepLog.execution_id == execution_id)
        .order_by(ExecutionStepLog.step_order)
        .all()
    )

    return {
        "id": execution.id,
        "workflow_id": execution.workflow_id,
        "status": execution.status,
        "created_at": execution.created_at.isoformat() if execution.created_at else None,
        "step_logs": [
            {
                "id": log.id,
                "step_order": log.step_order,
                "status": log.status,
                "output": log.output,
                "retry_count": log.retry_count,
            }
            for log in step_logs
        ],
    }
