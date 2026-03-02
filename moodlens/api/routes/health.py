from fastapi import APIRouter

from moodlens import __version__
from ...models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)
