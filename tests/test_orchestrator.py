from app.config import Settings
from app.models import Scenario, WorkflowRequest, WorkflowStatus
from app.orchestrator import WorkflowOrchestrator


def test_successful_workflow_runs_in_order_and_has_events():
    record = WorkflowOrchestrator(Settings()).run(WorkflowRequest(
        task="Process these meeting notes.\nNotes:\nDecision: Ship Friday.", scenario=Scenario.meeting
    ))
    assert record.status == WorkflowStatus.completed
    assert [step.agent_id for step in record.plan] == ["research", "execution", "validation", "summarization"]
    assert all(step.status == "completed" for step in record.plan)
    assert record.events[0].message.startswith("Started research")
    assert record.result["execute"]["operation"] == "meeting_notes"
    assert "simulated locally" in record.final_summary


def test_failed_agent_is_retried_only_to_configured_limit():
    class BrokenResearch:
        calls = 0

        def analyze(self, task, scenario):
            self.calls += 1
            raise RuntimeError("private implementation details")

    agent = BrokenResearch()
    result = WorkflowOrchestrator(Settings(retry_limit=2), research=agent).run(
        WorkflowRequest(task="A task")
    )
    assert result.status == WorkflowStatus.failed
    assert agent.calls == 3
    assert result.plan[0].attempts == 3
    assert result.plan[0].error == "Agent failed while processing this step."
    assert all(step.status == "skipped" for step in result.plan[1:])


def test_validation_failure_retries_execution_and_stops_at_limit():
    class RejectFirstOutput:
        calls = 0

        def validate(self, output):
            self.calls += 1
            if self.calls == 1:
                return {"valid": False, "feedback": "Please retry the result."}
            return {"valid": True, "feedback": "Looks good."}

    class CountingExecution:
        calls = 0

        def execute(self, task, scenario):
            self.calls += 1
            return {"operation": "text_summary", "summary": f"attempt {self.calls}"}

    execution = CountingExecution()
    result = WorkflowOrchestrator(
        Settings(retry_limit=1), execution=execution, validation=RejectFirstOutput()
    ).run(WorkflowRequest(task="A task"))
    assert result.status == WorkflowStatus.completed
    assert execution.calls == 2
    assert result.plan[1].attempts == 2
    assert result.plan[2].validation["valid"] is True


def test_validation_failure_after_retry_returns_failed_record():
    class AlwaysReject:
        def validate(self, output):
            return {"valid": False, "feedback": "Output needs a required field."}

    result = WorkflowOrchestrator(Settings(retry_limit=1), validation=AlwaysReject()).run(
        WorkflowRequest(task="A task")
    )
    assert result.status == WorkflowStatus.failed
    assert result.plan[2].status == "failed"
