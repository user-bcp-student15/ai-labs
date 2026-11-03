from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def upload_dir(tmp_path: Path) -> Path:
    return tmp_path / "uploads"


@pytest.fixture
def client(tmp_path: Path, upload_dir: Path) -> Iterator[TestClient]:
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as test_client:
        yield test_client
