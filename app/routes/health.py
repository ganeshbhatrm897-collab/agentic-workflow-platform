from fastapi import APIRouter, Request

from app.config import Settings
from app.models import HealthResponse


router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings: Settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        demo_mode=settings.demo_mode,
        execution="sequential-local",
    )
