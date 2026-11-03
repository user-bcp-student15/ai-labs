import sqlite3
from collections.abc import Iterator

from fastapi import Depends, HTTPException, Query, Request

from app.database import open_connection
from app.repositories.tasks import TaskRepository
from app.schemas import Identity
from app.security import legacy_identity
from app.services.tasks import TaskService


def get_connection(request: Request) -> Iterator[sqlite3.Connection]:
    connection = open_connection(request.app.state.settings.db_path)
    try:
        yield connection
    finally:
        connection.close()


def get_task_service(connection: sqlite3.Connection = Depends(get_connection)) -> TaskService:
    return TaskService(TaskRepository(connection))


def resolve_owner(owner: str | None = Query(default=None), identity: Identity = Depends(legacy_identity)) -> str:
    if not owner or owner == identity.username:
        return identity.username
    raise HTTPException(status_code=403, detail="Forbidden")
