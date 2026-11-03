from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

TITLE_MAX_LENGTH = 120
DESCRIPTION_MAX_LENGTH = 2000


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class TaskPriority(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


CLOSED_STATUSES = frozenset({TaskStatus.DONE, TaskStatus.ARCHIVED})


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Identity(BaseModel):
    model_config = ConfigDict(frozen=True)

    username: str
    role: str


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM


class TaskResponse(CamelModel):
    id: int
    title: str
    description: str
    status: str
    owner: str
    priority: str
    created_at: str


class TaskSummary(CamelModel):
    owner: str
    total: int
    by_status: dict[str, int]
    high_priority_open: int


class UploadResponse(CamelModel):
    owner: str
    file_name: str
    stored_at: str
    size: int


class BackendHealthResponse(CamelModel):
    requested_by: str
    status: int
    body: str
