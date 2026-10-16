from fastapi import APIRouter, HTTPException, Request, status

from app.models import WorkflowExample, WorkflowListItem, WorkflowRecord, WorkflowRequest, Scenario
from app.orchestrator import WorkflowOrchestrator


router = APIRouter(prefix="/api/workflows")

EXAMPLES = [
    WorkflowExample(
        scenario=Scenario.meeting, title="Meeting notes processor",
        description="Summarize notes, decisions, and explicitly stated action owners.",
        task="Process these fictional meeting notes into a summary, decisions, and action items.\nNotes:\n- Agreed to ship the first draft on Friday.\n- Maya will prepare the release checklist. Owner: Maya\n- Decision: postpone the analytics review until next week.",
    ),
    WorkflowExample(
        scenario=Scenario.project, title="Project planner",
        description="Turn a goal into a practical, prioritized milestone checklist.",
        task="Create a prioritized project checklist for launching a neighborhood book exchange.\nGoal: Launch a neighborhood book exchange with a simple catalog and monthly meetup.",
    ),
    WorkflowExample(
        scenario=Scenario.document, title="Document information extractor",
        description="Extract fields present in text and leave missing values blank.",
        task="Extract contact fields from this fictional document.\nText:\nName: Jordan Lee\nEmail: jordan@example.test\nCompany: Northstar Studio\nDate: 2026-11-04",
    ),
    WorkflowExample(
        scenario=Scenario.support, title="Support request analyzer",
        description="Classify a fictional support request and suggest safe next steps.",
        task="Analyze this fictional support request and recommend next steps.\nRequest: Urgent: I cannot access my account after resetting my password and need help restoring sign in.",
    ),
]


@router.get("/examples", response_model=list[WorkflowExample])
def examples() -> list[WorkflowExample]:
    return EXAMPLES


@router.post("", response_model=WorkflowRecord, status_code=status.HTTP_201_CREATED)
def create_workflow(payload: WorkflowRequest, request: Request) -> WorkflowRecord:
    settings = request.app.state.settings
    if len(payload.task) > settings.max_task_length:
        raise HTTPException(status_code=422, detail=f"Task must be at most {settings.max_task_length} characters.")
    record = WorkflowOrchestrator(settings).run(payload)
    request.app.state.workflow_store.save(record)
    return record


@router.get("", response_model=list[WorkflowListItem])
def list_workflows(request: Request) -> list[WorkflowListItem]:
    records = request.app.state.workflow_store.list_recent()
    return [
        WorkflowListItem(
            workflow_id=item.workflow_id,
            task=item.task,
            scenario=item.scenario,
            created_at=item.created_at,
            status=item.status,
            final_summary=item.final_summary,
        )
        for item in records
    ]


@router.get("/{workflow_id}", response_model=WorkflowRecord)
def get_workflow(workflow_id: str, request: Request) -> WorkflowRecord:
    record = request.app.state.workflow_store.get(workflow_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    return record
