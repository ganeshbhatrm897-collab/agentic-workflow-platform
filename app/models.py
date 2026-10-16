from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Scenario(StrEnum):
    meeting = "meeting"
    project = "project"
    document = "document"
    support = "support"


class StepStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


class WorkflowStatus(StrEnum):
    completed = "completed"
    failed = "failed"
    partial = "partial"


class WorkflowRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    task: str = Field(min_length=1, max_length=10_000)
    scenario: Scenario | None = None


class AgentInfo(BaseModel):
    id: str
    name: str
    description: str
    operations: list[str]


class PlanStep(BaseModel):
    id: str
    agent_id: str
    description: str
    dependencies: list[str] = Field(default_factory=list)
    expected_output: str
    status: StepStatus = StepStatus.pending
    attempts: int = 0
    output: Any = None
    validation: dict[str, Any] | None = None
    error: str | None = None


class ExecutionEvent(BaseModel):
    timestamp: datetime
    step_id: str | None = None
    level: str = "info"
    message: str


class WorkflowRecord(BaseModel):
    workflow_id: str
    task: str
    scenario: Scenario | None
    created_at: datetime
    status: WorkflowStatus
    mode: str
    plan: list[PlanStep]
    events: list[ExecutionEvent]
    final_summary: str
    result: dict[str, Any] = Field(default_factory=dict)


class WorkflowListItem(BaseModel):
    workflow_id: str
    task: str
    scenario: Scenario | None
    created_at: datetime
    status: WorkflowStatus
    final_summary: str


class WorkflowExample(BaseModel):
    scenario: Scenario
    title: str
    description: str
    task: str


class HealthResponse(BaseModel):
    status: str
    demo_mode: bool
    execution: str
