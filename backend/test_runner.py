from database import SessionLocal, Base, engine
from models import Workflow, Step, Execution, ExecutionStepLog
from runner import run_workflow

# ⭐ Ensure tables exist
Base.metadata.create_all(bind=engine)


def create_dummy_workflow(db):

    workflow = Workflow(name="Test Workflow")
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    steps = [
        Step(
            workflow_id=workflow.id,
            model="kimi-k2-instruct-0905",
            prompt="Say HELLO",
            completion_criteria="HELLO",
            retry_limit=2,
            step_order=1
        ),
        Step(
            workflow_id=workflow.id,
            model="kimi-k2-instruct-0905",
            prompt="Repeat previous output and add WORLD",
            completion_criteria="WORLD",
            retry_limit=2,
            step_order=2
        )
    ]

    for step in steps:
        db.add(step)

    db.commit()
    db.refresh(workflow)

    return workflow


def print_execution_logs(db, execution_id):

    execution = db.query(Execution).filter(
        Execution.id == execution_id
    ).first()

    print("\nExecution Status:", execution.status)

    logs = (
        db.query(ExecutionStepLog)
        .filter(ExecutionStepLog.execution_id == execution_id)
        .order_by(ExecutionStepLog.step_order)
        .all()
    )

    for log in logs:
        print(
            f"Step {log.step_order} | "
            f"Status: {log.status} | "
            f"Retries: {log.retry_count} | "
            f"Output: {log.output}"
        )


def main():

    db = SessionLocal()

    workflow = create_dummy_workflow(db)

    # ⭐ Correct call order
    execution_id, result = run_workflow(workflow, db)

    print("\nRun Result:", result)

    print_execution_logs(db, execution_id)

    db.close()


if __name__ == "__main__":
    main()
