from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, get_settings
from app.models import AgentInfo
from app.routes.health import router as health_router
from app.routes.workflows import router as workflows_router
from app.services.agent_registry import list_agents
from app.services.workflow_store import WorkflowStore


FRONTEND_DIR = Path(__file__).parent / "frontend"


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Agentic Workflow Orchestration Platform", version="1.0.0")
    app.state.settings = settings or get_settings()
    app.state.workflow_store = WorkflowStore(app.state.settings.max_workflows)
    app.include_router(health_router)
    app.include_router(workflows_router)

    @app.get("/api/agents", response_model=list[AgentInfo])
    def agents() -> list[AgentInfo]:
        return list_agents()

    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")

    return app


app = create_app()
