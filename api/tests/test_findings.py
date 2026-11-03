"""Pruebas de corrección por hallazgo (comportamiento objetivo de PLAN.md).

Mientras el hallazgo no está resuelto, la prueba está marcada xfail(strict); al resolverlo se quita el marcador.
"""
import importlib
import threading
import warnings
from concurrent.futures import ThreadPoolExecutor
from importlib import metadata
from pathlib import Path

import pytest
import urllib3
from fastapi.testclient import TestClient

from app.main import create_app
from helpers import auth_headers

INJECTION_USERNAME = "x' OR '1'='1"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MIN_URLLIB3 = (2, 8, 0)
MIN_PYTHON_MULTIPART = (0, 0, 31)
CONCURRENT_WRITERS = 8
TASKS_PER_WRITER = 5
SEEDED_STUDENT_TASKS = 2


def installed_version(package: str) -> tuple[int, ...]:
    return tuple(int(part) for part in metadata.version(package).split(".")[:3])


def upload(client: TestClient, name: str, content: bytes = b"x"):
    return client.post("/api/requirements", headers=auth_headers(), files={"file": (name, content, "text/plain")})


def test_urllib3_has_no_known_advisories() -> None:  # H-API-07
    assert installed_version("urllib3") >= MIN_URLLIB3


def test_python_multipart_has_no_known_advisories() -> None:  # H-API-06
    assert installed_version("python-multipart") >= MIN_PYTHON_MULTIPART


def test_list_filter_is_parameterized(client: TestClient) -> None:  # H-API-03
    response = client.get("/api/tasks", headers=auth_headers(INJECTION_USERNAME))
    assert response.status_code == 200
    assert response.json() == []


def test_summary_filter_is_parameterized(client: TestClient) -> None:  # H-API-03
    body = client.get("/api/summary", headers=auth_headers(INJECTION_USERNAME)).json()
    assert body["total"] == 0


def test_create_stores_quotes_literally(client: TestClient) -> None:  # H-API-04
    title = "Fix \"login\" & o'brien"
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": title, "description": "it's ok"})
    assert response.status_code == 201
    assert response.json()["title"] == title
    assert response.json()["description"] == "it's ok"


def test_create_does_not_run_injected_sql(client: TestClient) -> None:  # H-API-04
    payload = {"title": "x','y','TODO','student','LOW',datetime('now')); DELETE FROM tasks; --"}
    client.post("/api/tasks", headers=auth_headers(), json=payload)
    assert len(client.get("/api/tasks", headers=auth_headers("trainer", "TRAINER")).json()) == 1


def test_task_response_is_a_declared_model(client: TestClient) -> None:  # H-API-11
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    assert "createdAt" in schemas["TaskResponse"]["properties"]


@pytest.mark.parametrize("field,value", [("status", "WHATEVER"), ("priority", "URGENT"), ("title", "")])
def test_create_rejects_invalid_values(client: TestClient, field: str, value: str) -> None:  # H-API-11
    payload = {"title": "ok", field: value}
    assert client.post("/api/tasks", headers=auth_headers(), json=payload).status_code == 422


def test_other_owner_query_is_forbidden(client: TestClient) -> None:  # H-API-02
    assert client.get("/api/tasks", params={"owner": "trainer"}, headers=auth_headers()).status_code == 403
    assert client.get("/api/summary", params={"owner": "trainer"}, headers=auth_headers()).status_code == 403


def test_own_owner_query_is_allowed(client: TestClient) -> None:  # H-API-02
    response = client.get("/api/tasks", params={"owner": "student"}, headers=auth_headers())
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_create_ignores_owner_from_body(client: TestClient) -> None:  # H-API-02
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": "x", "owner": "trainer"})
    assert response.json()["owner"] == "student"


def test_upload_traversal_name_stays_inside_upload_dir(client: TestClient, tmp_path: Path, upload_dir: Path) -> None:  # H-API-05
    response = upload(client, "../outside.txt")
    assert not (tmp_path / "outside.txt").exists()
    assert response.status_code == 201
    assert (upload_dir / "outside.txt").exists()


def test_upload_rejects_disallowed_extension(client: TestClient) -> None:  # H-API-05
    assert upload(client, "payload.exe").status_code == 415


@pytest.mark.parametrize("name", ["..", "bad*name.txt", "con\x00trol.txt"])
def test_upload_rejects_unsafe_names(client: TestClient, name: str) -> None:  # H-API-05
    assert upload(client, name).status_code == 400


def test_upload_accepts_uppercase_extension_and_backslash_paths(client: TestClient, upload_dir: Path) -> None:  # H-API-05
    assert upload(client, "..\\notes.MD").status_code == 201
    assert (upload_dir / "notes.MD").exists()


def test_upload_rejects_oversized_file(client: TestClient, upload_dir: Path) -> None:  # H-API-05
    assert upload(client, "big.txt", b"0" * (MAX_UPLOAD_BYTES + 1)).status_code == 413
    assert not (upload_dir / "big.txt").exists()


def test_upload_response_does_not_expose_server_path(client: TestClient, upload_dir: Path) -> None:  # H-API-05
    stored_at = upload(client, "requirements.txt").json()["storedAt"]
    assert str(upload_dir) not in stored_at


def test_invalid_token_detail_is_generic(client: TestClient) -> None:  # H-API-09
    detail = client.get("/api/tasks", headers={"Authorization": "Bearer %%%"}).json()["detail"]
    assert detail == "Invalid token"


def test_backend_health_failure_hides_internal_details(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:  # H-API-09
    def unreachable(self, method, url, **kwargs):
        raise urllib3.exceptions.HTTPError("internal-host-9999 refused")

    monkeypatch.setattr(urllib3.PoolManager, "request", unreachable)

    with caplog.at_level("WARNING"):
        body = client.get("/api/backend-health", headers=auth_headers()).json()

    assert "internal-host-9999" not in body["body"]
    assert "internal-host-9999" in caplog.text


def test_cors_origins_come_from_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:  # H-API-10
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://a.test, http://b.test")
    with TestClient(create_app(str(tmp_path / "w.db"), str(tmp_path / "u"))) as test_client:
        response = test_client.options(
            "/api/tasks", headers={"Origin": "http://b.test", "Access-Control-Request-Method": "GET"}
        )
    assert response.headers["access-control-allow-origin"] == "http://b.test"


def test_cors_rejects_unknown_origin(client: TestClient) -> None:  # H-API-10
    response = client.options(
        "/api/tasks",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_concurrent_task_creation_keeps_every_insert(client: TestClient) -> None:  # H-API-12
    barrier = threading.Barrier(CONCURRENT_WRITERS)

    def write_tasks(writer: int) -> int:
        barrier.wait()
        return sum(
            client.post("/api/tasks", headers=auth_headers(), json={"title": f"w{writer}-{n}"}).status_code == 201
            for n in range(TASKS_PER_WRITER)
        )

    with ThreadPoolExecutor(max_workers=CONCURRENT_WRITERS) as pool:
        created = sum(pool.map(write_tasks, range(CONCURRENT_WRITERS)))

    total = client.get("/api/summary", headers=auth_headers()).json()["total"]
    assert created == CONCURRENT_WRITERS * TASKS_PER_WRITER
    assert total == SEEDED_STUDENT_TASKS + created


def test_restarting_on_an_existing_database_does_not_reseed(tmp_path: Path) -> None:  # H-API-13
    paths = (str(tmp_path / "w.db"), str(tmp_path / "u"))
    for _ in range(2):
        with TestClient(create_app(*paths)) as test_client:
            tasks = test_client.get("/api/tasks", headers=auth_headers()).json()
    assert len(tasks) == 2


def test_importing_main_has_no_side_effects(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:  # H-API-13
    import app.main as main_module

    database = tmp_path / "import-check" / "workshop.db"
    monkeypatch.setenv("WORKSHOP_DB_PATH", str(database))
    monkeypatch.setenv("WORKSHOP_UPLOAD_DIR", str(tmp_path / "import-check" / "uploads"))
    importlib.reload(main_module)
    assert not database.parent.exists()


def test_create_app_does_not_use_deprecated_on_event(tmp_path: Path) -> None:  # H-API-13
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        create_app(str(tmp_path / "w.db"), str(tmp_path / "u"))
    assert not [w for w in caught if issubclass(w.category, DeprecationWarning)]
