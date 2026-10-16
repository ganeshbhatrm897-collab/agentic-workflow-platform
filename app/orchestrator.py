from datetime import datetime, timezone
import json
from typing import Any

from app.agents.execution_agent import ExecutionAgent
from app.agents.intake_agent import IntakeAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.research_agent import ResearchAgent
from app.agents.summarization_agent import SummarizationAgent
from app.agents.validation_agent import ValidationAgent
from app.config import Settings
from app.models import (
    ExecutionEvent, PlanStep, Scenario, StepStatus, WorkflowRecord, WorkflowRequest, WorkflowStatus,
)
from app.services.llm_service import LLMService


class WorkflowOrchestrator:
    def __init__(
        self,
        settings: Settings,
        intake: IntakeAgent | None = None,
        planning: PlanningAgent | None = None,
        research: ResearchAgent | None = None,
        execution: ExecutionAgent | None = None,
        validation: ValidationAgent | None = None,
        summarization: SummarizationAgent | None = None,
        llm_service: LLMService | None = None,
    ):
        self.settings = settings
        self.intake = intake or IntakeAgent()
        self.planning = planning or PlanningAgent()
        self.research = research or ResearchAgent()
        self.execution = execution or ExecutionAgent()
        self.validation = validation or ValidationAgent()
        self.summarization = summarization or SummarizationAgent()
        self.llm_service = llm_service or LLMService(settings)

    def run(self, request: WorkflowRequest) -> WorkflowRecord:
        data = self.intake.process(request)
        workflow_id, task, scenario = data["workflow_id"], data["task"], data["scenario"]
        assert isinstance(workflow_id, str) and isinstance(task, str)
        assert scenario is None or isinstance(scenario, Scenario)
        plan = self.planning.create_plan(task, scenario)[: self.settings.max_steps]
        events: list[ExecutionEvent] = []
        outputs: dict[str, Any] = {}
        summary = "Workflow did not complete."
        status = WorkflowStatus.completed
        mode = "demo"

        for step in plan:
            step.status = StepStatus.running
            succeeded = False
            self._event(events, f"Started {step.agent_id} step.", step.id)
            for attempt in range(self.settings.retry_limit + 1):
                step.attempts = attempt + 1
                try:
                    if step.agent_id == "research":
                        step.output = self.research.analyze(task, scenario)
                    elif step.agent_id == "execution":
                        step.output = self.execution.execute(task, scenario)
                    elif step.agent_id == "validation":
                        step.validation = self.validation.validate(outputs.get("execute"))
                        if not step.validation.get("valid"):
                            step.error = str(step.validation.get("feedback", "Output validation failed."))
                            if attempt < self.settings.retry_limit:
                                execution_step = next(item for item in plan if item.id == "execute")
                                execution_step.status = StepStatus.running
                                execution_step.attempts += 1
                                self._event(events, "Validation failed; retrying execution once.", step.id, "warning")
                                outputs["execute"] = self.execution.execute(task, scenario)
                                execution_step.output = outputs["execute"]
                                execution_step.status = StepStatus.completed
                                step.error = None
                                continue
                            raise ValueError(step.error)
                        step.output = step.validation
                    elif step.agent_id == "summarization":
                        step.output = self.summarization.summarize(
                            task, outputs.get("research", {}), outputs.get("execute", {}), self.llm_service
                        )
                    else:
                        raise ValueError(f"Unsupported agent: {step.agent_id}")
                    if len(json.dumps(step.output, ensure_ascii=False, default=str)) > self.settings.max_output_length:
                        raise ValueError("Agent output exceeded the configured size limit.")
                    outputs[step.id] = step.output
                    step.status = StepStatus.completed
                    self._event(events, f"Completed {step.agent_id} step on attempt {step.attempts}.", step.id)
                    succeeded = True
                    break
                except Exception as exc:
                    if step.agent_id != "validation":
                        step.error = "Agent failed while processing this step."
                    elif not step.error:
                        step.error = "Output validation failed."
                    self._event(events, f"{step.error} ({type(exc).__name__}).", step.id, "warning")
                    if attempt == self.settings.retry_limit:
                        step.status = StepStatus.failed
                        status = WorkflowStatus.failed
                        self._event(events, step.error, step.id, "error")
            if not succeeded:
                break

        if status != WorkflowStatus.completed:
            failed_index = next((i for i, step in enumerate(plan) if step.status == StepStatus.failed), len(plan))
            for step in plan[failed_index + 1:]:
                step.status = StepStatus.skipped
                self._event(events, "Skipped because an earlier step failed.", step.id, "warning")
        if status == WorkflowStatus.completed:
            summary_output = outputs.get("summarize", {})
            summary = summary_output.get("summary", "Workflow completed.")
            if summary_output.get("llm_used"):
                mode = "llm-assisted"
            elif summary_output.get("fallback"):
                self._event(events, "Optional LLM unavailable; used the deterministic local summary.", "summarize", "warning")
        return WorkflowRecord(
            workflow_id=workflow_id,
            task=task,
            scenario=scenario,
            created_at=datetime.now(timezone.utc),
            status=status,
            mode=mode,
            plan=plan,
            events=events,
            final_summary=summary,
            result=outputs,
        )

    @staticmethod
    def _event(events: list[ExecutionEvent], message: str, step_id: str, level: str = "info") -> None:
        events.append(ExecutionEvent(timestamp=datetime.now(timezone.utc), step_id=step_id, level=level, message=message))
