from dataclasses import dataclass
from typing import TYPE_CHECKING

from llm_client import call_llm
from models import Execution, ExecutionStepLog, Step, Workflow

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass
class RunResult:
    """Result of a workflow run."""

    success: bool
    step_outputs: list[str]
    error_message: str | None = None

def check_completion(output: str, criteria: str | None) -> bool:
    print("CHECKING COMPLETION")
    print("OUTPUT:", output)
    print("CRITERIA:", criteria)

    if not criteria or not criteria.strip():
        return True

    return criteria.strip().lower() in output.lower()



def _build_prompt_with_context(prompt: str, previous_output: str | None) -> str:
    if previous_output is None or previous_output.strip() == "":
        return prompt
    return f"Previous step output:\n{previous_output}\n\nCurrent step:\n{prompt}"


def _run_single_step(step: Step, prompt_with_context: str) -> str:
    return call_llm(step.model, prompt_with_context)


def _execute_step_with_retries(step: Step, prompt_with_context: str) -> tuple[str, int]:
    """Returns (output, retry_count). Raises on failure after retries exhausted."""
    last_error = None
    attempts = step.retry_limit + 1

    for attempt in range(attempts):
        try:
            output = _run_single_step(step, prompt_with_context)
            if check_completion(output, step.completion_criteria):
                return output, attempt
            last_error = RuntimeError("Completion criteria not met")
        except Exception as e:
            last_error = e
        if attempt == attempts - 1:
            raise last_error
    raise last_error  # unreachable if attempts > 0


def run_workflow(workflow: Workflow, session: "Session") -> tuple[int, RunResult]:
    """
    Execute workflow with execution tracking. Creates an Execution and
    ExecutionStepLog records, updates them as steps run, and returns
    execution_id and the final RunResult.
    """
    ordered_steps = sorted(
        workflow.steps, key=lambda s: getattr(s, "step_order", s.id))
    for s in ordered_steps:
        print("STEP CRITERIA DEBUG:", s.completion_criteria)

    step_outputs: list[str] = []
    context: str | None = None

    execution = Execution(workflow_id=workflow.id, status="RUNNING")
    session.add(execution)
    session.flush()
    execution_id = execution.id

    try:
        for step_order, step in enumerate(ordered_steps):
            step_log = ExecutionStepLog(
                execution_id=execution_id,
                step_order=step_order,
                status="RUNNING",
            )
            session.add(step_log)
            session.flush()

            prompt_with_context = _build_prompt_with_context(
                step.prompt, context)
            try:
                output, retry_count = _execute_step_with_retries(
                    step, prompt_with_context)
                step_log.output = output
                step_log.retry_count = retry_count
                step_log.status = "COMPLETED"
                step_outputs.append(output)
                context = output
            except Exception as e:
                step_log.status = "FAILED"
                step_log.retry_count = step.retry_limit
                execution.status = "FAILED"
                session.commit()
                return (
                    execution_id,
                    RunResult(
                        success=False,
                        step_outputs=step_outputs,
                        error_message=str(e),
                    ),
                )

        execution.status = "SUCCESS"
        session.commit()
        return (
            execution_id,
            RunResult(success=True, step_outputs=step_outputs,
                      error_message=None),
        )
    except Exception as e:
        execution.status = "FAILED"
        session.commit()
        return (
            execution_id,
            RunResult(
                success=False,
                step_outputs=step_outputs,
                error_message=str(e),
            ),
        )
