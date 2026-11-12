import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Points at the compose database published on the host. Override with TEST_DATABASE_URL.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://ledger:ledger@localhost:5433/ledger"
)


@pytest.fixture(scope="session")
def database_url() -> str:
    engine = create_engine(TEST_DATABASE_URL, connect_args={"connect_timeout": 2})
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip(f"database not reachable at {engine.url.render_as_string()}")
    finally:
        engine.dispose()
    return TEST_DATABASE_URL
