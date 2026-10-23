"""Test clients: each test gets its own account, and its data is removed after.

Isolation is by owner: every row a test creates belongs to a freshly registered
user with a unique email, and teardown deletes that owner's rows. This exercises
the real multi-tenant scoping the app relies on.
"""

from __future__ import annotations

import itertools
import shutil
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import new_session
from app.main import app
from app.models import User
from app.seed import seed_curriculum

_password = "correct horse battery staple"
_origin = "http://testserver"
_counter = itertools.count()


def _unique_email() -> str:
    return f"user{next(_counter)}-{uuid.uuid4().hex[:8]}@example.com"


def _wipe_owner(owner_id: str) -> None:
    """Delete every owner-scoped row for one user, then the user itself."""
    from sqlalchemy import delete as sa_delete

    import app.models as models

    db = new_session()
    try:
        for name in dir(models):
            model = getattr(models, name)
            if not isinstance(model, type):
                continue
            columns = getattr(model, "__table__", None)
            if columns is None:
                continue
            if "owner_id" in columns.c:
                db.execute(sa_delete(model).where(model.owner_id == owner_id))
        # Auth leftovers are keyed by user_id, not owner_id.
        from app.models import AuthSession, LoginAttempt

        db.execute(sa_delete(AuthSession).where(AuthSession.user_id == owner_id))
        db.execute(sa_delete(LoginAttempt))
        db.execute(sa_delete(User).where(User.id == owner_id))
        db.commit()
    finally:
        db.close()


def _register(client: TestClient, email: str) -> str:
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": _password, "display_name": "Test User"},
        headers={"origin": _origin},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


@pytest.fixture()
def client() -> TestClient:
    """Unauthenticated client for auth-flow tests."""
    with TestClient(app, base_url=_origin) as c:
        yield c


@pytest.fixture()
def auth_client() -> TestClient:
    """A registered, signed-in account with no content."""
    email = _unique_email()
    with TestClient(app, base_url=_origin) as c:
        owner_id = _register(c, email)
        try:
            yield c
        finally:
            _wipe_owner(owner_id)


@pytest.fixture()
def other_client() -> TestClient:
    """A second, independent signed-in account for ownership tests."""
    email = _unique_email()
    with TestClient(app, base_url=_origin) as c:
        owner_id = _register(c, email)
        try:
            yield c
        finally:
            _wipe_owner(owner_id)


@pytest.fixture()
def seeded_client(auth_client: TestClient) -> TestClient:
    """Signed-in account with the full sample curriculum installed."""
    email = auth_client.get("/api/auth/me").json()["email"]
    db = new_session()
    try:
        owner_id = db.execute(
            __import__("sqlalchemy").select(User).where(User.email == email)
        ).scalar_one().id
        summary = seed_curriculum(db, owner_id)
        assert summary.get("lessons", 0) > 0
    finally:
        db.close()
    return auth_client


@pytest.fixture()
def db_session():
    db = new_session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def _cleanup_upload_dir() -> None:
    yield
    upload_dir = Path(get_settings().upload_dir)
    if upload_dir.exists():
        shutil.rmtree(upload_dir, ignore_errors=True)
