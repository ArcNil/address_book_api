"""Pytest fixtures: isolated test database and API test client."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

# Make the app package importable and point the database at a throwaway
# file BEFORE app modules are imported (they read DATABASE_URL at import time).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
TEST_DB_PATH = Path(__file__).resolve().parent / "test_addresses.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    """TestClient with startup/shutdown events (creates tables)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_db(client):
    """Start every test with an empty addresses table."""
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.exec_driver_sql("DELETE FROM addresses")
    yield


def pytest_sessionfinish(session, exitstatus):
    """Remove the throwaway database after the test run."""
    TEST_DB_PATH.unlink(missing_ok=True)