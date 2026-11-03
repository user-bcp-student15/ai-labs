import os
from dataclasses import dataclass

DEFAULT_DB_PATH = "./data/workshop.db"
DEFAULT_UPLOAD_DIR = "./uploads"
DEFAULT_AUTH_HEALTH_URL = "http://localhost:8080/q/health"
DEFAULT_CORS_ORIGINS = "http://localhost:4200"
HEALTH_TIMEOUT_SECONDS = 3.0
CORS_ALLOWED_METHODS = ["GET", "POST", "OPTIONS"]
CORS_ALLOWED_HEADERS = ["Authorization", "Content-Type"]


@dataclass(frozen=True)
class Settings:
    db_path: str
    upload_dir: str
    auth_health_url: str
    cors_origins: tuple[str, ...]


def parse_origins(raw_origins: str) -> tuple[str, ...]:
    return tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())


def load_settings(db_path: str | None = None, upload_dir: str | None = None) -> Settings:
    return Settings(
        db_path=db_path or os.getenv("WORKSHOP_DB_PATH", DEFAULT_DB_PATH),
        upload_dir=upload_dir or os.getenv("WORKSHOP_UPLOAD_DIR", DEFAULT_UPLOAD_DIR),
        auth_health_url=os.getenv("AUTH_HEALTH_URL", DEFAULT_AUTH_HEALTH_URL),
        cors_origins=parse_origins(os.getenv("CORS_ALLOWED_ORIGINS", DEFAULT_CORS_ORIGINS)),
    )
