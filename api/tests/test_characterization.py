"""Caracterización del comportamiento observado de la API (H-API-14).

Estas pruebas fijan lo que la API hace hoy y deben seguir en verde durante todo el refactor.
"""
from types import SimpleNamespace

import pytest
import urllib3
from fastapi.testclient import TestClient

from helpers import auth_headers, build_token

TASK_KEYS = {"id", "title", "description", "status", "owner", "priority", "createdAt"}
SEEDED_STUDENT_TASKS = 2
SEEDED_TRAINER_TASKS = 1


def create_task(client: TestClient, **fields: str) -> dict:
    response = client.post("/api/tasks", headers=auth_headers(), json=fields)
    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer not-base64"},
        {"Authorization": f"Bearer {build_token(ttl_seconds=-10)}"},
    ],
    ids=["missing", "malformed", "expired"],
)
def test_protected_routes_reject_invalid_tokens(client: TestClient, headers: dict[str, str]) -> None:
    assert client.get("/api/tasks", headers=headers).status_code == 401
    assert client.get("/api/summary", headers=headers).status_code == 401
    assert client.get("/api/backend-health", headers=headers).status_code == 401


def test_token_with_other_secret_is_rejected(client: TestClient) -> None:
    import base64
    import time

    raw = f"student|STUDENT|{int(time.time()) + 60}|OTHER"
    headers = {"Authorization": "Bearer " + base64.b64encode(raw.encode()).decode()}
    assert client.get("/api/tasks", headers=headers).status_code == 401


def test_list_returns_only_the_token_users_tasks_with_expected_shape(client: TestClient) -> None:
    student = client.get("/api/tasks", headers=auth_headers("student")).json()
    trainer = client.get("/api/tasks", headers=auth_headers("trainer", "TRAINER")).json()

    assert len(student) == SEEDED_STUDENT_TASKS
    assert len(trainer) == SEEDED_TRAINER_TASKS
    assert {task["owner"] for task in student} == {"student"}
    assert set(student[0]) == TASK_KEYS
    assert [task["id"] for task in student] == sorted(task["id"] for task in student)


def test_create_task_applies_defaults_and_returns_created_task(client: TestClient) -> None:
    created = create_task(client, title="Only title")

    assert set(created) == TASK_KEYS
    assert created["title"] == "Only title"
    assert created["description"] == ""
    assert created["status"] == "TODO"
    assert created["priority"] == "MEDIUM"
    assert created["owner"] == "student"
    assert created in client.get("/api/tasks", headers=auth_headers()).json()


def test_create_task_without_title_is_rejected_after_decision_d4(client: TestClient) -> None:
    # Cambio de contrato aprobado (D4): antes se aceptaba un título vacío (201).
    assert client.post("/api/tasks", headers=auth_headers(), json={}).status_code == 422


def test_summary_counts_by_status_and_open_high_priority(client: TestClient) -> None:
    create_task(client, title="a", priority="HIGH", status="TODO")
    create_task(client, title="b", priority="HIGH", status="DONE")
    create_task(client, title="c", priority="HIGH", status="ARCHIVED")
    create_task(client, title="d", priority="LOW", status="TODO")

    body = client.get("/api/summary", headers=auth_headers()).json()

    assert body == {
        "owner": "student",
        "total": 6,
        "byStatus": {"TODO": 3, "IN_PROGRESS": 1, "DONE": 1, "ARCHIVED": 1},
        "highPriorityOpen": 2,
    }


def test_summary_of_user_without_tasks_is_empty(client: TestClient) -> None:
    body = client.get("/api/summary", headers=auth_headers("nobody")).json()
    assert body == {"owner": "nobody", "total": 0, "byStatus": {}, "highPriorityOpen": 0}


def test_upload_returns_owner_name_path_and_size(client: TestClient, upload_dir) -> None:
    response = client.post(
        "/api/requirements",
        headers=auth_headers(),
        files={"file": ("requirements.txt", b"abc", "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"owner", "fileName", "storedAt", "size"}
    assert (body["owner"], body["fileName"], body["size"]) == ("student", "requirements.txt", 3)
    assert (upload_dir / "requirements.txt").read_bytes() == b"abc"


def test_upload_without_file_is_unprocessable(client: TestClient) -> None:
    assert client.post("/api/requirements", headers=auth_headers()).status_code == 422


def test_backend_health_returns_status_and_body(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = SimpleNamespace(status=200, data=b"UP")
    monkeypatch.setattr(urllib3.PoolManager, "request", lambda self, method, url, **kwargs: fake)

    response = client.get("/api/backend-health", headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 200, "body": "UP"}


def test_backend_health_failure_still_answers_200_with_status_zero(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def unreachable(self, method, url, **kwargs):
        raise urllib3.exceptions.HTTPError("unreachable")

    monkeypatch.setattr(urllib3.PoolManager, "request", unreachable)

    body = client.get("/api/backend-health", headers=auth_headers()).json()

    assert (body["requestedBy"], body["status"]) == ("student", 0)


def test_unknown_route_and_method_not_allowed(client: TestClient) -> None:
    assert client.get("/api/unknown", headers=auth_headers()).status_code == 404
    assert client.delete("/api/tasks", headers=auth_headers()).status_code == 405


def test_cors_preflight_allows_the_web_origin(client: TestClient) -> None:
    response = client.options(
        "/api/tasks",
        headers={"Origin": "http://localhost:4200", "Access-Control-Request-Method": "GET"},
    )

    assert response.headers["access-control-allow-origin"] in ("*", "http://localhost:4200")
