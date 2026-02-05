from runner import run_workflow

class DummyStep:
    def __init__(self, model, prompt, completion_criteria, retry_limit, step_order):
        self.model = model
        self.prompt = prompt
        self.completion_criteria = completion_criteria
        self.retry_limit = retry_limit
        self.step_order = step_order


class DummyWorkflow:
    def __init__(self, steps):
        self.steps = steps


steps = [
    DummyStep(
        model="kimi-k2-instruct-0905",
        prompt="Say HELLO",
        completion_criteria="HELLO",
        retry_limit=2,
        step_order=1
    ),
    DummyStep(
        model="kimi-k2-instruct-0905",
        prompt="Repeat previous output and add WORLD",
        completion_criteria="WORLD",
        retry_limit=2,
        step_order=2
    )
]

workflow = DummyWorkflow(steps)

result = run_workflow(workflow)

print(result)
