from dataclasses import dataclass

from llm_client import call_llm
from models import Step, Workflow


@dataclass
class RunResult:
    """Result of a workflow run."""

    success: bool
    step_outputs: list[str]
    error_message: str | None = None


def check_completion(output: str, criteria: str | None) -> bool:
    if not criteria or not criteria.strip():
        return True
    return criteria.strip() in output


def _build_prompt_with_context(prompt: str, previous_output: str | None) -> str:
    if previous_output is None or previous_output.strip() == "":
        return prompt
    return f"Previous step output:\n{previous_output}\n\nCurrent step:\n{prompt}"


def _run_single_step(step: Step, prompt_with_context: str) -> str:
    return call_llm(step.model, prompt_with_context)


def _execute_step_with_retries(step: Step, prompt_with_context: str) -> str:
    last_error = None
    attempts = step.retry_limit + 1

    for attempt in range(attempts):
        try:
            output = _run_single_step(step, prompt_with_context)
            if check_completion(output, step.completion_criteria):
                return output
            last_error = RuntimeError("Completion criteria not met")
        except Exception as e:
            last_error = e
        if attempt == attempts - 1:
            raise last_error
    raise last_error  # unreachable if attempts > 0


def run_workflow(workflow: Workflow) -> RunResult:
    ordered_steps = sorted(workflow.steps, key=lambda s: s.step_order)
    step_outputs: list[str] = []
    context: str | None = None

    for step in ordered_steps:
        prompt_with_context = _build_prompt_with_context(step.prompt, context)
        try:
            output = _execute_step_with_retries(step, prompt_with_context)
            step_outputs.append(output)
            context = output
        except Exception as e:
            return RunResult(
                success=False,
                step_outputs=step_outputs,
                error_message=str(e),
            )

    return RunResult(success=True, step_outputs=step_outputs, error_message=None)
