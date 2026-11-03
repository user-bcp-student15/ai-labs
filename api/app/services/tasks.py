import sqlite3
from collections import Counter

from app.repositories.tasks import TaskRepository
from app.schemas import CLOSED_STATUSES, TaskCreate, TaskPriority, TaskResponse, TaskSummary


def as_task(row: sqlite3.Row) -> TaskResponse:
    return TaskResponse.model_validate(dict(row))


def is_open_high_priority(row: sqlite3.Row) -> bool:
    return row["priority"] == TaskPriority.HIGH and row["status"] not in CLOSED_STATUSES


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def list_tasks(self, owner: str) -> list[TaskResponse]:
        return [as_task(row) for row in self._repository.list_by_owner(owner)]

    def create_task(self, task: TaskCreate, owner: str) -> TaskResponse:
        row = self._repository.create(task.title, task.description, task.status, owner, task.priority)
        return as_task(row)

    def summarize(self, owner: str) -> TaskSummary:
        rows = self._repository.status_and_priority_by_owner(owner)
        return TaskSummary(
            owner=owner,
            total=len(rows),
            by_status=dict(Counter(row["status"] for row in rows)),
            high_priority_open=sum(1 for row in rows if is_open_high_priority(row)),
        )
