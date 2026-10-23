"""Pytest bootstrap: puts the server root on sys.path and builds a test database.

Tests run against a real PostgreSQL instance (the embedded one for development),
never a mock, because the value of these tests is exercising real SQL.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parent
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

# Configure a disposable environment BEFORE importing the app.
_TEST_DIR = tempfile.mkdtemp(prefix="algo-study-tests-")
os.environ.setdefault("UPLOAD_DIR", os.path.join(_TEST_DIR, "uploads"))
os.environ["APP_ORIGIN"] = "http://testserver"
os.environ.setdefault("AI_API_KEY", "")

from app.config import get_settings, reset_settings_cache  # noqa: E402

reset_settings_cache()
get_settings()

from app.db import Base, get_engine, reset_engine_cache, _embedded_server_uri  # noqa: E402

# Build the schema once; every test runs inside a transaction it rolls back,
# so tests stay isolated without paying for a fresh server each time.
_embedded_server_uri()
Base.metadata.create_all(get_engine())


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "slow: test spins up its own database")


__all__ = ["client", "auth_client", "other_client", "seeded_client", "db_session"]
