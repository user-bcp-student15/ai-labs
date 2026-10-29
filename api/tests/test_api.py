import base64
import json
import os
import time
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

from app import main as api_main
from app.main import create_app

SECRET = os.environ["AUTH_TOKEN_SECRET"]
TASK_PAYLOAD = {"title": "Add tests", "description": "Improve coverage", "status": "TODO", "priority": "HIGH"}
UPLOAD = {"file": ("requirements.txt", b"Login must be accessible", "text/plain")}
PROTECTED_CALLS = [
    ("get", "/api/tasks", {}),
    ("post", "/api/tasks", {"json": TASK_PAYLOAD}),
    ("get", "/api/summary", {}),
    ("post", "/api/requirements", {"files": UPLOAD}),
    ("get", "/api/backend-health", {}),
]


class FakeResponse:
    status = 200
    data = b'{"status":"UP"}'


class FakePoolManager:
    def request(self, method: str, url: str, timeout: float) -> FakeResponse:
        return FakeResponse()


class UnreachablePoolManager:
    def request(self, method: str, url: str, timeout: float) -> None:
        raise OSError("connection refused")


def token(username: str = "student", role: str = "STUDENT") -> str:
    return jwt_token(username, role)


def headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(username, role)}"}


def test_lists_seeded_tasks(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers())
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_creates_task_and_summary(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Add tests", "description": "Improve coverage", "status": "TODO", "priority": "HIGH"},
        )
        summary = client.get("/api/summary", headers=headers())
    assert created.status_code == 201
    assert created.json()["owner"] == "student"
    assert summary.json()["total"] == 3


def test_uploads_requirement(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"Login must be accessible", "text/plain")},
        )
    assert response.status_code == 201
    assert (upload_dir / "requirements.txt").exists()


def test_rejects_invalid_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_protected_routes_keep_success_shape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_main.urllib3, "PoolManager", FakePoolManager)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        tasks = client.get("/api/tasks", headers=headers())
        created = client.post("/api/tasks", headers=headers(), json=TASK_PAYLOAD)
        summary = client.get("/api/summary", headers=headers())
        uploaded = client.post("/api/requirements", headers=headers(), files=UPLOAD)
        health = client.get("/api/backend-health", headers=headers())
    assert tasks.status_code == 200
    assert {"id", "title", "description", "status", "owner", "priority", "createdAt"} <= set(tasks.json()[0])
    assert created.status_code == 201
    assert set(summary.json()) == {"owner", "total", "byStatus", "highPriorityOpen"}
    assert uploaded.status_code == 201
    assert set(uploaded.json()) == {"owner", "fileName", "storedAt", "size"}
    assert health.status_code == 200
    assert health.json() == {"requestedBy": "student", "status": 200, "body": '{"status":"UP"}'}


def test_backend_health_reports_status_zero_when_unreachable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_main.urllib3, "PoolManager", UnreachablePoolManager)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.json() == {"requestedBy": "student", "status": 0, "body": "connection refused"}


@pytest.mark.parametrize(("method", "path", "options"), PROTECTED_CALLS)
def test_protected_routes_reject_missing_credential(tmp_path: Path, method: str, path: str, options: dict) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.request(method.upper(), path, **options)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token: missing credential"


def test_accepts_valid_credential_without_bearer_prefix(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": token()})
    assert response.status_code == 200


def test_rejects_invalid_credential_without_bearer_prefix(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": "invalid"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token: malformed"


def b64url(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


def jwt_token(username: str = "student", role: str = "STUDENT", *, key: str = SECRET, expires_in: int = 3600) -> str:
    issued = int(time.time())
    return jwt.encode({"sub": username, "role": role, "iat": issued, "exp": issued + expires_in}, key, algorithm="HS256")


def jwt_headers(token_value: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_value}"}


def tampered_token() -> str:
    header, _, signature = jwt_token().split(".")
    issued = int(time.time())
    return f"{header}.{b64url({'sub': 'trainer', 'role': 'TRAINER', 'iat': issued, 'exp': issued + 3600})}.{signature}"


def unsigned_token() -> str:
    issued = int(time.time())
    return f"{b64url({'alg': 'none', 'typ': 'JWT'})}.{b64url({'sub': 'trainer', 'role': 'TRAINER', 'iat': issued, 'exp': issued + 3600})}."


def legacy_format_token() -> str:
    raw = f"student|STUDENT|{int(time.time()) + 3600}|not-the-key"
    return base64.b64encode(raw.encode()).decode()


REJECTED_TOKENS = [
    pytest.param(jwt_token(key="another-test-secret-that-is-also-long-enough"), "invalid signature", id="wrong-signature"),
    pytest.param(tampered_token(), "invalid signature", id="tampered-payload"),
    pytest.param(jwt_token(expires_in=-10), "expired", id="expired"),
    pytest.param(unsigned_token(), "algorithm not allowed", id="alg-none"),
    pytest.param(jwt.encode({"role": "STUDENT", "iat": int(time.time()), "exp": int(time.time()) + 3600}, SECRET, algorithm="HS256"), "missing claim", id="missing-sub"),
    pytest.param(jwt.encode({"sub": "student", "iat": int(time.time()), "exp": int(time.time()) + 3600}, SECRET, algorithm="HS256"), "missing claim", id="missing-role"),
    pytest.param(legacy_format_token(), "malformed", id="legacy-format"),
    pytest.param("not.a.jwt", "malformed", id="malformed"),
]


def test_accepts_valid_jwt(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary", headers=jwt_headers(jwt_token("trainer", "TRAINER")))
    assert response.status_code == 200
    assert response.json()["owner"] == "trainer"


def test_identity_comes_from_sub_claim(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post("/api/tasks", headers=jwt_headers(jwt_token("trainer", "TRAINER")), json={"title": "t", "description": "d", "status": "TODO", "priority": "LOW"})
    assert created.json()["owner"] == "trainer"


def test_accepts_token_with_auth_issuance_format(tmp_path: Path) -> None:
    issued = int(time.time())
    auth_style_token = jwt.encode({"sub": "student", "role": "STUDENT", "iat": issued, "exp": issued + 3600}, SECRET, algorithm="HS256")
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary", headers=jwt_headers(auth_style_token))
    assert response.status_code == 200


@pytest.mark.parametrize(("method", "path", "options"), PROTECTED_CALLS)
@pytest.mark.parametrize("credential, reason", REJECTED_TOKENS)
def test_protected_routes_reject_invalid_jwt(tmp_path: Path, method: str, path: str, options: dict, credential: str, reason: str) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.request(method.upper(), path, headers=jwt_headers(credential), **options)
    assert response.status_code == 401
    assert response.json()["detail"] == f"Invalid token: {reason}"


def test_create_app_fails_without_token_secret(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUTH_TOKEN_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="AUTH_TOKEN_SECRET"):
        create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))


def test_create_app_fails_with_short_token_secret(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_TOKEN_SECRET", "too-short")
    with pytest.raises(RuntimeError, match="AUTH_TOKEN_SECRET"):
        create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
