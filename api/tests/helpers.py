import base64
import time

TEST_TOKEN_SECRET = "WORKSHOP_SECRET_2026"
TEST_TOKEN_TTL_SECONDS = 3600


def build_token(username: str = "student", role: str = "STUDENT", ttl_seconds: int = TEST_TOKEN_TTL_SECONDS) -> str:
    raw = f"{username}|{role}|{int(time.time()) + ttl_seconds}|{TEST_TOKEN_SECRET}"
    return base64.b64encode(raw.encode()).decode()


def auth_headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    return {"Authorization": f"Bearer {build_token(username, role)}"}
