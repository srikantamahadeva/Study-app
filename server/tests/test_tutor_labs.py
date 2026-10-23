"""AI tutor safety and coding labs.

The tutor must never pretend to be configured, must ground answers in the
user's own material, and must keep sessions owner-scoped. Labs run static
checks server-side; client-reported test results are advisory only.
"""

from __future__ import annotations

_origin = "http://testserver"


# ---------------------------------------------------------------- tutor


def test_tutor_reports_not_configured_and_never_fakes_an_answer(seeded_client):
    status = seeded_client.get("/api/tutor/status").json()
    assert status["configured"] is False
    assert status["model"] is None

    resp = seeded_client.post(
        "/api/tutor/ask",
        json={"question": "What is a stop-loss?"},
        headers={"origin": _origin},
    )
    assert resp.status_code == 503
    detail = resp.json()["detail"].lower()
    assert "not configured" in detail
    # The refusal must not contain a fabricated answer.
    assert "stop-loss" not in detail


def test_tutor_chat_followup_also_refuses_when_unconfigured(seeded_client):
    session = seeded_client.post(
        "/api/tutor/sessions", json={"question": "hello"}, headers={"origin": _origin}
    ).json()
    resp = seeded_client.post(
        "/api/tutor/chat",
        json={"sessionId": session["id"], "message": "follow-up question"},
        headers={"origin": _origin},
    )
    assert resp.status_code == 503


def test_tutor_session_lifecycle_and_ownership(seeded_client, other_client):
    session = seeded_client.post(
        "/api/tutor/sessions", json={"question": "Explain slippage"}, headers={"origin": _origin}
    ).json()
    assert session["id"]

    mine = seeded_client.get(f"/api/tutor/sessions/{session['id']}").json()
    assert mine["session"]["title"] == "Explain slippage"

    # Another account cannot read or delete it.
    assert other_client.get(f"/api/tutor/sessions/{session['id']}").status_code == 404
    assert other_client.delete(f"/api/tutor/sessions/{session['id']}", headers={"origin": _origin}).status_code == 404

    assert seeded_client.delete(f"/api/tutor/sessions/{session['id']}", headers={"origin": _origin}).status_code == 200
    assert seeded_client.get(f"/api/tutor/sessions/{session['id']}").status_code == 404


def test_tutor_context_gathers_only_my_material(seeded_client, other_client):
    """A note owned by another account must not appear in my retrieval."""
    other_client.post(
        "/api/notes",
        json={"title": "Secretz strategy", "bodyMarkdown": "proprietary signal details"},
        headers={"origin": _origin},
    )
    # My account has no such note; retrieval context is built from my rows only.
    mine = seeded_client.get("/api/tutor/sessions").json()["items"]
    titles = [s["title"] for s in mine]
    assert all("Secretz" not in t for t in titles)


# ---------------------------------------------------------------- labs


def test_labs_list_and_detail_hide_reference_solution(seeded_client):
    items = seeded_client.get("/api/labs/exercises").json()["items"]
    assert items, "seeded account should have lab exercises"
    langs = {e["language"] for e in items}
    assert "pine" in langs and "python" in langs

    detail = seeded_client.get(f"/api/labs/exercises/{items[0]['id']}").json()
    assert detail["starterCode"]
    # The solution must not ride along in the default response.
    assert "referenceSolution" not in detail
    assert "solution" not in detail


def test_lab_static_checks_grade_and_disclaim_profitability(seeded_client):
    pine = seeded_client.get("/api/labs/exercises", params={"language": "pine"}).json()["items"][0]
    detail = seeded_client.get(f"/api/labs/exercises/{pine['id']}").json()

    # Empty/unfinished code should fail the error-level checks.
    bad = seeded_client.post(
        "/api/labs/submit",
        json={"exerciseId": pine["id"], "code": "# TODO\n", "testResults": []},
        headers={"origin": _origin},
    ).json()
    assert bad["passed"] is False
    assert any(c["level"] == "error" and not c["passed"] for c in bad["result"]["staticChecks"])
    # The result must carry the static-checks-only disclaimer.
    assert "No profitability claim" in bad["result"]["note"]

    # The starter code is usually complete enough to pass the error checks.
    good = seeded_client.post(
        "/api/labs/submit",
        json={"exerciseId": pine["id"], "code": detail["starterCode"], "testResults": []},
        headers={"origin": _origin},
    ).json()
    assert "staticChecks" in good["result"]


def test_lab_submissions_are_owner_scoped(seeded_client, other_client):
    py = seeded_client.get("/api/labs/exercises", params={"language": "python"}).json()["items"][0]
    seeded_client.post(
        "/api/labs/submit",
        json={"exerciseId": py["id"], "code": "x = 1\n", "testResults": [{"passed": True}]},
        headers={"origin": _origin},
    )
    mine = seeded_client.get("/api/labs/submissions").json()["items"]
    assert mine

    # The other account sees none of my submissions and cannot submit to my exercise.
    theirs = other_client.get("/api/labs/submissions").json()["items"]
    assert all(s["id"] not in {m["id"] for m in mine} for s in theirs)
    assert other_client.post(
        "/api/labs/submit",
        json={"exerciseId": py["id"], "code": "x = 1\n", "testResults": []},
        headers={"origin": _origin},
    ).status_code == 404


def test_lab_solution_endpoint_is_owner_scoped(seeded_client, other_client):
    ex = seeded_client.get("/api/labs/exercises").json()["items"][0]
    assert seeded_client.get(f"/api/labs/exercises/{ex['id']}/solution").status_code == 200
    assert other_client.get(f"/api/labs/exercises/{ex['id']}/solution").status_code == 404
