"""Auth safety: hashing, sessions, lockout, CSRF/same-origin, and ownership.

These tests assert the properties the app depends on rather than that a route
returns 200 — for example that passwords are never stored in plaintext and that
one account cannot read another's rows.
"""

from __future__ import annotations

import time
import uuid

import pytest

from app.security import (
    check_password_strength,
    evaluate_lockout,
    hash_password,
    is_same_origin_mutation,
    new_session_token,
    token_digest,
    verify_password,
)

_origin = "http://testserver"


# ---------------------------------------------------------------- unit level


def test_password_hash_is_argon2_and_verifies():
    h = hash_password("a sufficiently long password")
    assert h.startswith("$argon2"), "must be argon2id, not plaintext/bcrypt"
    assert "a sufficiently long password" not in h, "hash must not contain the password"
    assert verify_password(h, "a sufficiently long password") is True
    assert verify_password(h, "a sufficiently long password2") is False


def test_hashing_is_salted_per_call():
    pw = "identical password here"
    assert hash_password(pw) != hash_password(pw), "two hashes of one password must differ"


def test_password_strength_rejects_short():
    assert check_password_strength("short") is not None
    assert check_password_strength("x" * 9) is not None
    assert check_password_strength("x" * 10) is None


def test_session_token_is_only_stored_as_digest():
    token, digest = new_session_token()
    assert token != digest
    assert len(digest) == 64 and digest == token_digest(token)
    assert token not in digest


def test_lockout_triggers_after_max_failures_and_resets_on_success():
    now = int(time.time() * 1000)
    failures = [(now - i * 1000, False) for i in range(10)]
    assert evaluate_lockout(failures, 10, 300, now).locked is True

    # Below threshold -> not locked.
    assert evaluate_lockout(failures[:9], 10, 300, now).locked is False

    # A success anywhere in the window resets the streak.
    reset = [(now, True)] + failures[1:]
    assert evaluate_lockout(reset, 10, 300, now).locked is False


def test_lockout_expires_after_the_window():
    now = int(time.time() * 1000)
    old = [(now - 10 * 60 * 1000 - i * 1000, False) for i in range(10)]
    assert evaluate_lockout(old, 10, 300, now).locked is False


@pytest.mark.parametrize(
    "origin,referer,expected",
    [
        (None, None, True),  # non-browser client
        (_origin, None, True),
        (None, f"{_origin}/lessons/1", True),
        ("https://evil.example", None, False),
        (None, "https://evil.example/x", False),
        (f"{_origin}/", None, True),  # trailing slash normalised
    ],
)
def test_same_origin_mutation(origin, referer, expected):
    assert is_same_origin_mutation(origin, referer, _origin) is expected


# ---------------------------------------------------------------- API level


def test_register_creates_session_and_returns_no_secret(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": f"nosecret-{uuid.uuid4().hex[:8]}@example.com", "password": "a long enough password", "display_name": "N"},
        headers={"origin": _origin},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "password" not in str(body).lower()
    assert "password_hash" not in body
    # Session cookie must be HttpOnly so script cannot read it.
    set_cookie = resp.headers.get("set-cookie", "").lower()
    assert "httponly" in set_cookie
    assert client.get("/api/auth/me").status_code == 200


def test_register_rejects_weak_password(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": f"weak-{uuid.uuid4().hex[:8]}@example.com", "password": "short", "display_name": "W"},
        headers={"origin": _origin},
    )
    assert resp.status_code == 400


def test_register_duplicate_email_is_conflict_but_login_unknown_is_generic(client):
    email = f"dupe-{uuid.uuid4().hex[:8]}@example.com"
    payload = {"email": email, "password": "a long enough password", "display_name": "D"}
    assert client.post("/api/auth/register", json=payload, headers={"origin": _origin}).status_code == 200
    assert client.post("/api/auth/register", json=payload, headers={"origin": _origin}).status_code == 409

    # Unknown user and wrong password must be indistinguishable.
    unknown = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "whatever"}, headers={"origin": _origin})
    wrong = client.post("/api/auth/login", json={"email": email, "password": "wrong password here"}, headers={"origin": _origin})
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json()["detail"] == wrong.json()["detail"]


def test_unauthenticated_reads_are_401(client):
    for path in (
        "/api/auth/me",
        "/api/curriculum/",
        "/api/notes",
        "/api/quiz/questions",
        "/api/labs/exercises",
        "/api/projects",
        "/api/reports/overview",
        "/api/search?q=anything",
        "/api/resources",
        "/api/tutor/sessions",
        "/api/profile",
        "/api/export",
        "/api/audit",
    ):
        assert client.get(path).status_code == 401, f"{path} leaked without auth"


def test_cross_origin_mutation_is_refused(auth_client):
    allowed = auth_client.post(
        "/api/notes", json={"title": "ok", "bodyMarkdown": "x"}, headers={"origin": _origin}
    )
    assert allowed.status_code == 200

    refused = auth_client.post(
        "/api/notes",
        json={"title": "nope", "bodyMarkdown": "x"},
        headers={"origin": "https://evil.example"},
    )
    assert refused.status_code == 403

    # Referer-based CSRF is caught too.
    refused_ref = auth_client.post(
        "/api/notes",
        json={"title": "nope", "bodyMarkdown": "x"},
        headers={"referer": "https://evil.example/attack.html"},
    )
    assert refused_ref.status_code == 403


def test_logout_invalidates_the_session(auth_client):
    assert auth_client.get("/api/auth/me").status_code == 200
    assert auth_client.post("/api/auth/logout", headers={"origin": _origin}).status_code == 200
    assert auth_client.get("/api/auth/me").status_code == 401


def test_another_account_cannot_read_or_mutate_my_data(auth_client, other_client):
    note = auth_client.post(
        "/api/notes", json={"title": "mine", "bodyMarkdown": "private", "kind": "research"},
        headers={"origin": _origin},
    ).json()
    note_id = note["id"]

    # The other account cannot fetch, patch, or delete it.
    assert other_client.get(f"/api/notes/{note_id}").status_code == 404
    assert other_client.patch(
        f"/api/notes/{note_id}", json={"title": "stolen"}, headers={"origin": _origin}
    ).status_code == 404
    assert other_client.delete(f"/api/notes/{note_id}", headers={"origin": _origin}).status_code == 404

    # And its own listing does not contain it.
    titles = [n["title"] for n in other_client.get("/api/notes").json()["items"]]
    assert "mine" not in titles


def test_lesson_progress_is_owner_scoped(seeded_client, other_client):
    lesson = seeded_client.get("/api/curriculum/").json()["courses"][0]["modules"][0]["lessons"][0]
    lesson_id = lesson["id"]

    # Foreign account gets 404 rather than a partial read.
    assert other_client.get(f"/api/curriculum/lessons/{lesson_id}").status_code == 404
    assert other_client.put(
        f"/api/curriculum/lessons/{lesson_id}/progress",
        json={"percent": 100, "status": "completed"},
        headers={"origin": _origin},
    ).status_code == 404


def test_data_export_contains_no_password(auth_client):
    export = auth_client.get("/api/export")
    assert export.status_code == 200
    text = export.text
    assert "password_hash" not in text
    assert "correct horse battery staple" not in text


def test_wipe_requires_confirmation(auth_client):
    bad = auth_client.post("/api/wipe", json={"confirm": "yes"}, headers={"origin": _origin})
    assert bad.status_code == 400
    good = auth_client.post("/api/wipe", json={"confirm": "ERASE"}, headers={"origin": _origin})
    assert good.status_code == 200
    # Account survives a learning-data wipe.
    assert auth_client.get("/api/auth/me").status_code == 200


def test_api_responses_are_not_cached(auth_client):
    resp = auth_client.get("/api/reports/overview")
    assert "no-store" in resp.headers.get("cache-control", "")
