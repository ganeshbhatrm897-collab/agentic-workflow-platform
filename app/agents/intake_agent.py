from uuid import uuid4

from app.models import Scenario, WorkflowRequest


class IntakeAgent:
    def process(self, request: WorkflowRequest) -> dict[str, str | Scenario | None]:
        task = " ".join(request.task.split())
        if not task:
            raise ValueError("Task must contain non-whitespace text.")
        return {"workflow_id": str(uuid4()), "task": task, "scenario": request.scenario}
