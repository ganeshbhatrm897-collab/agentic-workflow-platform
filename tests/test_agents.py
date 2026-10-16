from app.agents.execution_agent import ExecutionAgent
from app.agents.intake_agent import IntakeAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.research_agent import ResearchAgent
from app.agents.validation_agent import ValidationAgent
from app.models import Scenario, WorkflowRequest


def test_intake_normalizes_task_and_assigns_id():
    result = IntakeAgent().process(WorkflowRequest(task="  hello   workflow "))
    assert result["task"] == "hello workflow"
    assert result["workflow_id"]


def test_planning_is_bounded_and_has_dependencies():
    plan = PlanningAgent().create_plan("Plan something", None)
    assert [step.agent_id for step in plan] == ["research", "execution", "validation", "summarization"]
    assert plan[-1].dependencies == ["validate"]


def test_meeting_agent_extracts_decisions_actions_and_explicit_owner():
    result = ExecutionAgent().execute(
        "Notes:\nDecision: Ship on Friday.\nSam will prepare the checklist. Owner: Sam",
        Scenario.meeting,
    )
    assert "Decision: Ship on Friday." in result["decisions"]
    assert "Sam will prepare the checklist. Owner: Sam" in result["action_items"]
    assert result["owners"] == ["Sam"]


def test_project_agent_creates_prioritized_checklist():
    result = ExecutionAgent().execute("Goal: Launch the local library.", Scenario.project)
    assert len(result["checklist"]) == 4
    assert result["checklist"][0]["priority"] == "High"


def test_document_agent_does_not_invent_missing_fields():
    result = ExecutionAgent().execute("Text:\nName: Ari\nEmail: ari@example.test", Scenario.document)
    assert result["fields"]["email"] == ["ari@example.test"]
    assert result["fields"]["phone"] is None
    assert "phone" in result["missing_fields"]


def test_support_agent_classifies_urgent_access_problem():
    result = ExecutionAgent().execute("Request: Urgent, I cannot access my account.", Scenario.support)
    assert result["category"] == "account access"
    assert result["priority"] == "high"


def test_research_agent_labels_simulated_source_and_limitations():
    result = ResearchAgent().analyze("Some supplied text", Scenario.meeting)
    assert result["simulated"] is True
    assert "No live web search" in result["limitations"][0]


def test_validator_returns_actionable_failure_and_accepts_valid_output():
    validator = ValidationAgent()
    assert validator.validate({})["valid"] is False
    assert validator.validate({"operation": "text_summary", "summary": "A summary."})["valid"] is True
