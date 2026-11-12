from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.db import get_engine
from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_db_returns_503_when_database_unreachable(client: TestClient) -> None:
    # Nothing listens on port 1; connection is refused immediately.
    dead = create_engine(
        "postgresql+psycopg://x:x@127.0.0.1:1/x", connect_args={"connect_timeout": 1}
    )
    app.dependency_overrides[get_engine] = lambda: dead
    resp = client.get("/health/db")
    assert resp.status_code == 503
    assert resp.json() == {"status": "error", "database": "down"}


def test_health_db_ok_against_real_database(client: TestClient, database_url: str) -> None:
    engine = create_engine(database_url)
    app.dependency_overrides[get_engine] = lambda: engine
    resp = client.get("/health/db")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "up"}
    engine.dispose()
