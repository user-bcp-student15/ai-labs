from fastapi import APIRouter, Depends, Request

from app.schemas import BackendHealthResponse, Identity
from app.security import legacy_identity
from app.services.backend_health import check_backend_health

router = APIRouter(prefix="/api")


@router.get("/backend-health")
def backend_health(request: Request, identity: Identity = Depends(legacy_identity)) -> BackendHealthResponse:
    health = check_backend_health(request.app.state.settings.auth_health_url)
    return BackendHealthResponse(requested_by=identity.username, status=health.status, body=health.body)
