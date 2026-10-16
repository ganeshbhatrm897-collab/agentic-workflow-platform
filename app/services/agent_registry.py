from app.models import AgentInfo


AGENTS = [
    AgentInfo(
        id="intake", name="Intake", description="Normalizes and validates each request.",
        operations=["input validation", "task normalization"],
    ),
    AgentInfo(
        id="planning", name="Planning", description="Creates a bounded deterministic execution plan.",
        operations=["workflow planning", "step assignment"],
    ),
    AgentInfo(
        id="research", name="Research", description="Summarizes supplied context and labels limitations.",
        operations=["context analysis", "assumptions and limitations"],
    ),
    AgentInfo(
        id="execution", name="Execution", description="Runs safe, predefined text-processing operations.",
        operations=["meeting notes", "project checklist", "field extraction", "support analysis", "summary"],
    ),
    AgentInfo(
        id="validation", name="Validation", description="Checks result shape and flags missing information.",
        operations=["schema checks", "output quality checks"],
    ),
    AgentInfo(
        id="summarization", name="Summarization", description="Builds a transparent final report.",
        operations=["result synthesis", "evidence labeling"],
    ),
]


def list_agents() -> list[AgentInfo]:
    return AGENTS
