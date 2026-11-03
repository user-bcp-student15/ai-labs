"""Pruebas por endpoint según docs/ENDPOINTS.md: camino feliz, casos borde y errores.

Cada prueba cita entre paréntesis el caso de la tabla de docs/TESTING.md.
"""
import sys
from types import SimpleNamespace

import pytest
import urllib3
from fastapi.testclient import TestClient
from helpers import auth_headers, build_token

from app.main import create_app

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
TITLE_MAX_LENGTH = 120
DESCRIPTION_MAX_LENGTH = 2000
STUDENT_SEEDED_TASKS = 2
UPSTREAM_TIMEOUT_SECONDS = 3.0
INVALID_TOKEN_BODY = {"detail": "Invalid token"}
FORBIDDEN_BODY = {"detail": "Forbidden"}
TRAINER = {"username": "trainer", "role": "TRAINER"}

INVALID_TOKEN_HEADERS = {
    "missing": {},
    "malformed": {"Authorization": "Bearer not-base64"},
    "expired": {"Authorization": f"Bearer {build_token(ttl_seconds=-10)}"},
}


def post_task(client: TestClient, payload: dict, **headers_args: str):
    return client.post("/api/tasks", headers=auth_headers(**headers_args), json=payload)


def upload(client: TestClient, name: str, content: bytes = b"x"):
    return client.post("/api/requirements", headers=auth_headers(), files={"file": (name, content, "text/plain")})


@pytest.fixture
def fake_backend(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Sustituye la consulta HTTP al backend de auth y registra los argumentos recibidos."""
    backend = SimpleNamespace(response=SimpleNamespace(status=200, data=b"UP"), error=None, calls=[])

    def request(self, method, url, **kwargs):
        backend.calls.append((method, url, kwargs))
        if backend.error:
            raise backend.error
        return backend.response

    monkeypatch.setattr(urllib3.PoolManager, "request", request)
    return backend


# ---------------------------------------------------------------- GET /api/tasks


def test_get_tasks_lists_trainer_tasks_with_trainer_token(client: TestClient) -> None:  # GT-01
    body = client.get("/api/tasks", headers=auth_headers(**TRAINER)).json()
    assert [(task["id"], task["owner"], task["title"]) for task in body] == [(3, "trainer", "Trainer notes")]


def test_get_tasks_for_user_without_tasks_is_empty_list(client: TestClient) -> None:  # GT-02
    response = client.get("/api/tasks", headers=auth_headers("nobody"))
    assert (response.status_code, response.json()) == (200, [])


def test_get_tasks_empty_owner_parameter_uses_token_user(client: TestClient) -> None:  # GT-03
    response = client.get("/api/tasks", params={"owner": ""}, headers=auth_headers())
    assert response.status_code == 200
    assert {task["owner"] for task in response.json()} == {"student"}
    assert len(response.json()) == STUDENT_SEEDED_TASKS


def test_get_tasks_are_ordered_by_ascending_id(client: TestClient) -> None:  # GT-04
    post_task(client, {"title": "first"})
    post_task(client, {"title": "second"})
    ids = [task["id"] for task in client.get("/api/tasks", headers=auth_headers()).json()]
    assert ids == sorted(ids)
    assert len(ids) == STUDENT_SEEDED_TASKS + 2


def test_get_tasks_other_owner_is_forbidden_and_leaks_nothing(client: TestClient) -> None:  # GT-05
    as_student = client.get("/api/tasks", params={"owner": "trainer"}, headers=auth_headers())
    as_trainer = client.get("/api/tasks", params={"owner": "student"}, headers=auth_headers(**TRAINER))

    assert (as_student.status_code, as_student.json()) == (403, FORBIDDEN_BODY)
    assert (as_trainer.status_code, as_trainer.json()) == (403, FORBIDDEN_BODY)
    assert "Trainer notes" not in as_student.text
    assert "Refactor login" not in as_trainer.text


@pytest.mark.parametrize("headers", INVALID_TOKEN_HEADERS.values(), ids=INVALID_TOKEN_HEADERS.keys())
def test_get_tasks_invalid_token_is_401_with_generic_body(client: TestClient, headers: dict) -> None:  # GT-06
    response = client.get("/api/tasks", headers=headers)
    assert (response.status_code, response.json()) == (401, INVALID_TOKEN_BODY)


def test_get_tasks_method_not_allowed_is_405(client: TestClient) -> None:  # GT-07
    response = client.delete("/api/tasks", headers=auth_headers())
    assert (response.status_code, response.json()) == (405, {"detail": "Method Not Allowed"})


# --------------------------------------------------------------- POST /api/tasks


def test_post_task_with_all_fields_returns_201_and_is_listed(client: TestClient) -> None:  # PT-01
    payload = {"title": "Add tests", "description": "Improve coverage", "status": "IN_PROGRESS", "priority": "HIGH"}
    response = post_task(client, payload)

    assert response.status_code == 201
    created = response.json()
    assert {key: created[key] for key in payload} == payload
    assert created["owner"] == "student"
    assert created in client.get("/api/tasks", headers=auth_headers()).json()


@pytest.mark.parametrize("status", ["TODO", "IN_PROGRESS", "DONE", "ARCHIVED"])
@pytest.mark.parametrize("priority", ["HIGH", "MEDIUM", "LOW"])
def test_post_task_accepts_every_documented_status_and_priority(client: TestClient, status: str, priority: str) -> None:  # PT-02
    response = post_task(client, {"title": "t", "status": status, "priority": priority})
    assert response.status_code == 201
    assert (response.json()["status"], response.json()["priority"]) == (status, priority)


@pytest.mark.parametrize("length,expected", [(1, 201), (TITLE_MAX_LENGTH, 201), (TITLE_MAX_LENGTH + 1, 422)])
def test_post_task_title_length_boundaries(client: TestClient, length: int, expected: int) -> None:  # PT-03
    assert post_task(client, {"title": "a" * length}).status_code == expected


@pytest.mark.parametrize("length,expected", [(0, 201), (DESCRIPTION_MAX_LENGTH, 201), (DESCRIPTION_MAX_LENGTH + 1, 422)])
def test_post_task_description_length_boundaries(client: TestClient, length: int, expected: int) -> None:  # PT-04
    assert post_task(client, {"title": "t", "description": "d" * length}).status_code == expected


def test_post_task_ignores_unknown_fields_and_owner(client: TestClient) -> None:  # PT-05
    response = post_task(client, {"title": "t", "owner": "trainer", "unknown": 1})

    assert response.status_code == 201
    assert response.json()["owner"] == "student"
    assert "unknown" not in response.json()
    assert "t" not in [task["title"] for task in client.get("/api/tasks", headers=auth_headers(**TRAINER)).json()]


def test_post_task_empty_object_is_rejected_not_defaulted(client: TestClient) -> None:  # PT-06
    assert post_task(client, {}).status_code == 422
    assert len(client.get("/api/tasks", headers=auth_headers()).json()) == STUDENT_SEEDED_TASKS


@pytest.mark.parametrize(
    "payload,error_type,location",
    [
        ({}, "missing", ["body", "title"]),
        ({"title": ""}, "string_too_short", ["body", "title"]),
        ({"title": "a" * (TITLE_MAX_LENGTH + 1)}, "string_too_long", ["body", "title"]),
        ({"title": "t", "description": "d" * (DESCRIPTION_MAX_LENGTH + 1)}, "string_too_long", ["body", "description"]),
        ({"title": "t", "status": "WHATEVER"}, "enum", ["body", "status"]),
        ({"title": "t", "priority": "URGENT"}, "enum", ["body", "priority"]),
        ({"title": 5}, "string_type", ["body", "title"]),
    ],
    ids=["missing-title", "empty-title", "long-title", "long-description", "bad-status", "bad-priority", "title-not-string"],
)
def test_post_task_validation_errors_are_422_with_field_location(
    client: TestClient, payload: dict, error_type: str, location: list
) -> None:  # PT-07
    response = post_task(client, payload)

    assert response.status_code == 422
    (detail,) = response.json()["detail"]
    assert (detail["type"], detail["loc"]) == (error_type, location)


def test_post_task_without_body_is_422(client: TestClient) -> None:  # PT-08
    response = client.post("/api/tasks", headers=auth_headers())
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body"]


def test_post_task_malformed_json_is_422(client: TestClient) -> None:  # PT-09
    headers = {**auth_headers(), "Content-Type": "application/json"}
    response = client.post("/api/tasks", headers=headers, content="{bad")
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "json_invalid"


@pytest.mark.parametrize("headers", INVALID_TOKEN_HEADERS.values(), ids=INVALID_TOKEN_HEADERS.keys())
def test_post_task_invalid_token_is_401_and_creates_nothing(client: TestClient, headers: dict) -> None:  # PT-10
    response = client.post("/api/tasks", headers=headers, json={"title": "t"})

    assert (response.status_code, response.json()) == (401, INVALID_TOKEN_BODY)
    assert len(client.get("/api/tasks", headers=auth_headers()).json()) == STUDENT_SEEDED_TASKS


# ------------------------------------------------------------- GET /api/summary


def test_summary_of_trainer_is_not_affected_by_student_tasks(client: TestClient) -> None:  # GS-01
    post_task(client, {"title": "t", "priority": "HIGH"})
    body = client.get("/api/summary", headers=auth_headers(**TRAINER)).json()
    assert body == {"owner": "trainer", "total": 1, "byStatus": {"TODO": 1}, "highPriorityOpen": 0}


def test_summary_of_seeded_student_matches_documented_example(client: TestClient) -> None:  # GS-02
    body = client.get("/api/summary", headers=auth_headers()).json()
    assert body == {"owner": "student", "total": 2, "byStatus": {"TODO": 1, "IN_PROGRESS": 1}, "highPriorityOpen": 1}


@pytest.mark.parametrize("owner", ["", "student"])
def test_summary_accepts_empty_or_own_owner_parameter(client: TestClient, owner: str) -> None:  # GS-03
    response = client.get("/api/summary", params={"owner": owner}, headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["owner"] == "student"


def test_summary_high_priority_closed_tasks_are_not_open(client: TestClient) -> None:  # GS-04
    post_task(client, {"title": "done", "priority": "HIGH", "status": "DONE"})
    post_task(client, {"title": "archived", "priority": "HIGH", "status": "ARCHIVED"})
    body = client.get("/api/summary", headers=auth_headers()).json()
    assert body["highPriorityOpen"] == 1
    assert body["total"] == STUDENT_SEEDED_TASKS + 2


def test_summary_other_owner_is_forbidden_and_leaks_nothing(client: TestClient) -> None:  # GS-05
    as_student = client.get("/api/summary", params={"owner": "trainer"}, headers=auth_headers())
    as_trainer = client.get("/api/summary", params={"owner": "student"}, headers=auth_headers(**TRAINER))

    assert (as_student.status_code, as_student.json()) == (403, FORBIDDEN_BODY)
    assert (as_trainer.status_code, as_trainer.json()) == (403, FORBIDDEN_BODY)


@pytest.mark.parametrize("headers", INVALID_TOKEN_HEADERS.values(), ids=INVALID_TOKEN_HEADERS.keys())
def test_summary_invalid_token_is_401_with_generic_body(client: TestClient, headers: dict) -> None:  # GS-06
    response = client.get("/api/summary", headers=headers)
    assert (response.status_code, response.json()) == (401, INVALID_TOKEN_BODY)


# ------------------------------------------------------- POST /api/requirements


@pytest.mark.parametrize("name", ["notes.txt", "notes.md", "notes.pdf", "notes.docx", "NOTES.TXT", "my req-1.md"])
def test_upload_accepts_allowed_extensions_and_stores_the_content(client: TestClient, upload_dir, name: str) -> None:  # PR-01
    response = upload(client, name, b"contenido")

    assert response.status_code == 201
    assert response.json() == {"owner": "student", "fileName": name, "storedAt": name, "size": 9}
    assert (upload_dir / name).read_bytes() == b"contenido"


def test_upload_empty_file_is_accepted_with_size_zero(client: TestClient, upload_dir) -> None:  # PR-02
    response = upload(client, "empty.txt", b"")
    assert response.status_code == 201
    assert response.json()["size"] == 0
    assert (upload_dir / "empty.txt").read_bytes() == b""


def test_upload_exactly_at_size_limit_is_accepted(client: TestClient) -> None:  # PR-03
    response = upload(client, "max.txt", b"0" * MAX_UPLOAD_BYTES)
    assert (response.status_code, response.json()["size"]) == (201, MAX_UPLOAD_BYTES)


def test_upload_one_byte_over_the_limit_is_413_and_stores_nothing(client: TestClient, upload_dir) -> None:  # PR-04
    response = upload(client, "big.txt", b"0" * (MAX_UPLOAD_BYTES + 1))
    assert (response.status_code, response.json()) == (413, {"detail": "File too large"})
    assert not (upload_dir / "big.txt").exists()


@pytest.mark.parametrize("name", ["README", "archivo", "notes."])
def test_upload_name_without_allowed_extension_is_415(client: TestClient, name: str) -> None:  # PR-05
    response = upload(client, name)
    assert (response.status_code, response.json()) == (415, {"detail": "File type not allowed"})


@pytest.mark.parametrize("name", ["payload.exe", "script.py", "archive.txt.exe"])
def test_upload_disallowed_extension_is_415(client: TestClient, name: str) -> None:  # PR-06
    response = upload(client, name)
    assert (response.status_code, response.json()) == (415, {"detail": "File type not allowed"})


@pytest.mark.parametrize("name", ["..", "bad*name.txt", ".txt"])
def test_upload_invalid_name_is_400(client: TestClient, name: str) -> None:  # PR-07
    response = upload(client, name)
    assert (response.status_code, response.json()) == (400, {"detail": "Invalid file name"})


@pytest.mark.xfail(
    sys.platform == "win32",
    strict=True,
    reason="H-API-16: en Windows Path('a:b.txt').name devuelve 'b.txt' y la API responde 201 en vez de 400",
)
def test_upload_name_with_colon_is_400(client: TestClient) -> None:  # PR-07b
    response = upload(client, "a:b.txt")
    assert (response.status_code, response.json()) == (400, {"detail": "Invalid file name"})


@pytest.mark.parametrize("raw_name", ["../outside.txt", "..\\outside.txt", "a/b/outside.txt"])
def test_upload_path_in_name_is_reduced_to_the_last_segment(client: TestClient, tmp_path, upload_dir, raw_name: str) -> None:  # PR-08
    response = upload(client, raw_name)

    assert response.status_code == 201
    assert response.json()["fileName"] == "outside.txt"
    assert (upload_dir / "outside.txt").exists()
    assert not (tmp_path / "outside.txt").exists()


def test_upload_without_file_part_is_422(client: TestClient) -> None:  # PR-09
    response = client.post("/api/requirements", headers=auth_headers())
    assert response.status_code == 422
    assert response.json() == {"detail": [{"type": "missing", "loc": ["body", "file"], "msg": "Field required", "input": None}]}


@pytest.mark.parametrize("headers", INVALID_TOKEN_HEADERS.values(), ids=INVALID_TOKEN_HEADERS.keys())
def test_upload_invalid_token_is_401_and_stores_nothing(client: TestClient, upload_dir, headers: dict) -> None:  # PR-10
    response = client.post("/api/requirements", headers=headers, files={"file": ("a.txt", b"x", "text/plain")})

    assert (response.status_code, response.json()) == (401, INVALID_TOKEN_BODY)
    assert not (upload_dir / "a.txt").exists()


# ------------------------------------------------------------------------- CORS


def test_cors_preflight_from_allowed_origin_is_200_with_documented_policy(client: TestClient) -> None:  # CO-01
    response = client.options(
        "/api/tasks",
        headers={
            "Origin": "http://localhost:4200",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:4200"
    assert response.headers["access-control-allow-methods"] == "GET, POST, OPTIONS"
    assert "access-control-allow-credentials" not in response.headers


def test_cors_preflight_from_unknown_origin_is_400(client: TestClient) -> None:  # CO-02
    response = client.options(
        "/api/tasks", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"}
    )

    assert (response.status_code, response.text) == (400, "Disallowed CORS origin")
    assert "access-control-allow-origin" not in response.headers


# ------------------------------------------------------ GET /api/backend-health


def test_backend_health_happy_path_uses_configured_url_and_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path, fake_backend: SimpleNamespace
) -> None:  # BH-01
    monkeypatch.setenv("AUTH_HEALTH_URL", "http://auth.test:8080/q/health")
    fake_backend.response = SimpleNamespace(status=200, data=b'{"status":"UP"}')

    with TestClient(create_app(str(tmp_path / "w.db"), str(tmp_path / "u"))) as client:
        response = client.get("/api/backend-health", headers=auth_headers())

    assert response.json() == {"requestedBy": "student", "status": 200, "body": '{"status":"UP"}'}
    ((method, url, kwargs),) = fake_backend.calls
    assert (method, url, kwargs["timeout"]) == ("GET", "http://auth.test:8080/q/health", UPSTREAM_TIMEOUT_SECONDS)


def test_backend_health_reports_the_requesting_user(client: TestClient, fake_backend: SimpleNamespace) -> None:  # BH-02
    body = client.get("/api/backend-health", headers=auth_headers(**TRAINER)).json()
    assert body["requestedBy"] == "trainer"


def test_backend_health_upstream_error_status_is_passed_through_with_200(client: TestClient, fake_backend: SimpleNamespace) -> None:  # BH-03
    fake_backend.response = SimpleNamespace(status=503, data=b'{"status":"DOWN"}')

    response = client.get("/api/backend-health", headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 503, "body": '{"status":"DOWN"}'}


def test_backend_health_empty_upstream_body_is_an_empty_string(client: TestClient, fake_backend: SimpleNamespace) -> None:  # BH-04
    fake_backend.response = SimpleNamespace(status=204, data=b"")
    assert client.get("/api/backend-health", headers=auth_headers()).json()["body"] == ""


@pytest.mark.parametrize(
    "error",
    [
        urllib3.exceptions.HTTPError("down"),
        urllib3.exceptions.MaxRetryError(None, "/q/health"),
        urllib3.exceptions.ReadTimeoutError(None, "/q/health", "timed out"),
    ],
    ids=["http-error", "max-retries", "timeout"],
)
def test_backend_health_unreachable_backend_is_200_with_status_zero(
    client: TestClient, fake_backend: SimpleNamespace, error: Exception
) -> None:  # BH-05
    fake_backend.error = error

    response = client.get("/api/backend-health", headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 0, "body": "Backend unavailable"}


def test_backend_health_non_utf8_body_is_reported_as_unavailable(client: TestClient, fake_backend: SimpleNamespace) -> None:  # BH-06
    fake_backend.response = SimpleNamespace(status=200, data=b"\xff\xfe")
    body = client.get("/api/backend-health", headers=auth_headers()).json()
    assert (body["status"], body["body"]) == (0, "Backend unavailable")


@pytest.mark.parametrize("headers", INVALID_TOKEN_HEADERS.values(), ids=INVALID_TOKEN_HEADERS.keys())
def test_backend_health_invalid_token_is_401_and_does_not_call_the_backend(
    client: TestClient, fake_backend: SimpleNamespace, headers: dict
) -> None:  # BH-07
    response = client.get("/api/backend-health", headers=headers)

    assert (response.status_code, response.json()) == (401, INVALID_TOKEN_BODY)
    assert fake_backend.calls == []
