from fastapi import APIRouter, Depends

from app.dependencies import get_task_service, resolve_owner
from app.schemas import Identity, TaskCreate, TaskResponse, TaskSummary
from app.security import legacy_identity
from app.services.tasks import TaskService

router = APIRouter(prefix="/api")


@router.get("/tasks")
def list_tasks(
    owner: str = Depends(resolve_owner),
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    return service.list_tasks(owner)


@router.post("/tasks", status_code=201)
def create_task(
    task: TaskCreate,
    identity: Identity = Depends(legacy_identity),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return service.create_task(task, identity.username)


@router.get("/summary")
def summary(
    owner: str = Depends(resolve_owner),
    service: TaskService = Depends(get_task_service),
) -> TaskSummary:
    return service.summarize(owner)
