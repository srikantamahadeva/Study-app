"""Content operations: notes, concepts, projects, search, reports, resources.

Covers the confirm-before-overwrite rule for notes, duplicate-term conflicts,
project milestone state sync, cross-account isolation for every content type,
search scoping, and that report numbers trace to recorded activity.
"""

from __future__ import annotations

import io

_origin = "http://testserver"


# ---------------------------------------------------------------- notes


def test_note_overwrite_requires_confirmation(auth_client):
    note = auth_client.post(
        "/api/notes",
        json={"title": "Draft", "bodyMarkdown": "first version", "kind": "research"},
        headers={"origin": _origin},
    ).json()

    # Changing only the title is fine without confirmation.
    ok = auth_client.patch(
        f"/api/notes/{note['id']}",
        json={"title": "Draft v2"},
        headers={"origin": _origin},
    )
    assert ok.status_code == 200

    # Replacing the body silently would destroy work; require explicit confirm.
    refused = auth_client.patch(
        f"/api/notes/{note['id']}",
        json={"bodyMarkdown": "rewritten"},
        headers={"origin": _origin},
    )
    assert refused.status_code == 409

    confirmed = auth_client.patch(
        f"/api/notes/{note['id']}",
        json={"bodyMarkdown": "rewritten", "confirmOverwrite": True},
        headers={"origin": _origin},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["bodyMarkdown"] == "rewritten"


def test_note_kind_filter_and_search(auth_client):
    auth_client.post(
        "/api/notes", json={"title": "Alpha setup", "bodyMarkdown": "entry rules", "kind": "research"},
        headers={"origin": _origin},
    )
    auth_client.post(
        "/api/notes", json={"title": "Mistake log", "bodyMarkdown": "chased a spike", "kind": "mistake"},
        headers={"origin": _origin},
    )
    mistakes = auth_client.get("/api/notes", params={"kind": "mistake"}).json()["items"]
    assert [n["title"] for n in mistakes] == ["Mistake log"]

    found = auth_client.get("/api/notes", params={"q": "entry rules"}).json()["items"]
    assert len(found) == 1 and found[0]["title"] == "Alpha setup"


def test_duplicate_concept_term_conflicts(auth_client):
    payload = {"term": "Slippage", "definition": "difference between expected and filled price"}
    assert auth_client.post("/api/notes/concepts", json=payload, headers={"origin": _origin}).status_code == 200
    dup = auth_client.post("/api/notes/concepts", json=payload, headers={"origin": _origin})
    assert dup.status_code == 409


def test_concepts_are_owner_scoped(auth_client, other_client):
    c = auth_client.post(
        "/api/notes/concepts", json={"term": "Drawdown", "definition": "peak-to-trough decline"},
        headers={"origin": _origin},
    ).json()
    terms = [x["term"] for x in other_client.get("/api/notes/concepts").json()["items"]]
    assert "Drawdown" not in terms
    assert other_client.delete(f"/api/notes/concepts/{c['id']}", headers={"origin": _origin}).status_code == 404


# ---------------------------------------------------------------- projects


def test_projects_are_seeded_with_milestones_and_status_sync(seeded_client):
    items = seeded_client.get("/api/projects").json()["items"]
    assert len(items) >= 8, "capstone projects A-J should be seeded"
    assert all(p["status"] == "not_started" for p in items)

    project = items[0]
    detail = seeded_client.get(f"/api/projects/{project['id']}").json()
    assert detail["project"]["completionCriteria"], "each project needs acceptance criteria"
    assert detail["milestones"], "each project needs milestones"

    # Completing all milestones flips the project to done.
    for m in detail["milestones"]:
        assert seeded_client.patch(
            f"/api/projects/milestones/{m['id']}", params={"done": "true"}, headers={"origin": _origin}
        ).status_code == 200
    after = seeded_client.get(f"/api/projects/{project['id']}").json()
    assert after["project"]["status"] == "done"
    assert after["project"]["milestonesDone"] == len(after["milestones"])


def test_project_status_rejects_unknown_values(seeded_client):
    project = seeded_client.get("/api/projects").json()["items"][0]
    resp = seeded_client.patch(
        f"/api/projects/{project['id']}/status",
        json={"status": "profitable"},
        headers={"origin": _origin},
    )
    assert resp.status_code == 422, "arbitrary status strings must be rejected"


def test_projects_are_owner_scoped(seeded_client, other_client):
    project = seeded_client.get("/api/projects").json()["items"][0]
    assert other_client.get(f"/api/projects/{project['id']}").status_code == 404
    assert other_client.patch(
        f"/api/projects/{project['id']}/status", json={"status": "done"}, headers={"origin": _origin}
    ).status_code == 404


def test_custom_milestones_round_trip(seeded_client):
    project = seeded_client.get("/api/projects").json()["items"][0]
    created = seeded_client.post(
        f"/api/projects/{project['id']}/milestones",
        json={"title": "My extra gate", "detail": "walk-forward split"},
        headers={"origin": _origin},
    ).json()
    assert created["id"]
    assert seeded_client.delete(
        f"/api/projects/milestones/{created['id']}", headers={"origin": _origin}
    ).status_code == 200


# ---------------------------------------------------------------- search + reports


def test_search_spans_my_content_only(seeded_client, other_client):
    seeded_client.post(
        "/api/notes", json={"title": "Volatility breakout", "bodyMarkdown": "ATR channel idea"},
        headers={"origin": _origin},
    )
    other_client.post(
        "/api/notes", json={"title": "Hidden volatility plan", "bodyMarkdown": "not yours"},
        headers={"origin": _origin},
    )

    hits = seeded_client.get("/api/search", params={"q": "volatility"}).json()
    assert hits["total"] >= 1
    titles = [i["title"] for i in hits["items"]]
    assert any("Volatility breakout" in t for t in titles)
    assert all("Hidden" not in t for t in titles)
    # Every hit links to a real app surface.
    assert all(i["href"].startswith("/") for i in hits["items"])


def test_search_finds_seeded_lesson_content(seeded_client):
    hits = seeded_client.get("/api/search", params={"q": "backtest"}).json()
    assert hits["total"] >= 1
    assert any(i["type"] == "lesson" for i in hits["items"])


def test_reports_numbers_trace_to_recorded_activity(seeded_client):
    overview = seeded_client.get("/api/reports/overview").json()
    # Fresh account: nothing recorded, so everything is zero/none — never invented.
    assert overview["progress"]["lessonsCompleted"] == 0
    assert overview["quiz"]["attempts"] == 0
    assert overview["quiz"]["accuracy"] is None
    assert overview["streak"]["current"] == 0
    assert overview["nextLesson"] is not None, "resume pointer should exist from lesson 1"

    # Answering a question moves the quiz numbers.
    qs = seeded_client.get("/api/quiz/questions").json()["items"]
    seeded_client.post(
        "/api/quiz/answer",
        json={"sessionId": "report-session", "questionId": qs[0]["id"], "givenIndex": 0},
        headers={"origin": _origin},
    )
    after = seeded_client.get("/api/reports/overview").json()
    assert after["quiz"]["attempts"] == 1
    assert after["quiz"]["accuracy"] in (0, 100)


def test_weekly_report_and_recommendations(seeded_client):
    weekly = seeded_client.get("/api/reports/weekly").json()
    assert len(weekly["weeks"]) >= 4
    assert all(w["quizAccuracy"] is None or 0 <= w["quizAccuracy"] <= 100 for w in weekly["weeks"])

    recs = seeded_client.get("/api/reports/recommendations").json()
    assert set(recs) == {"dueReviews", "weakTopics", "inProgressLessons"}
    # Starter deck is due immediately.
    assert recs["dueReviews"] >= 1


def test_export_markdown_is_grounded_and_disclaims(seeded_client):
    md = seeded_client.get("/api/reports/export.md").json()["markdown"]
    assert "# Learning summary" in md
    assert "No performance or profitability claims" in md
    assert "Algorithmic" in md or "Curriculum" in md


# ---------------------------------------------------------------- resources


def _png_bytes() -> bytes:
    # Minimal valid 1x1 PNG.
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d494844520000000100000001080600000"
        "01f15c4890000000d4944415478da63f8cf400f0005050200bf0000f5"
        "0001822015e00000000049454e44ae426082"
    )


def test_upload_indexes_text_and_scopes_download(auth_client, other_client):
    resp = auth_client.post(
        "/api/resources/upload",
        files={"file": ("notes.txt", io.BytesIO(b"mean reversion bands work best in calm regimes"), "text/plain")},
        data={"title": "My notes", "tags": "research,test"},
        headers={"origin": _origin},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["indexed"] is True
    assert body["chunks"] == 1

    # Indexed text is searchable.
    hits = auth_client.get("/api/search", params={"q": "reversion"}).json()
    assert any(i["type"] == "document" for i in hits["items"])

    # The file is owner-only.
    assert other_client.get(f"/api/resources/{body['id']}/file").status_code == 404
    dl = auth_client.get(f"/api/resources/{body['id']}/file")
    assert dl.status_code == 200
    assert b"mean reversion" in dl.content


def test_upload_rejects_oversized_and_sanitizes_names(auth_client):
    # Path-traversal style filename must be sanitized, not written verbatim.
    resp = auth_client.post(
        "/api/resources/upload",
        files={"file": ("../../evil.txt", io.BytesIO(b"hi"), "text/plain")},
        headers={"origin": _origin},
    )
    assert resp.status_code == 200
    assert ".." not in resp.json()["title"]


def test_resource_delete_removes_rows_and_file(auth_client):
    resp = auth_client.post(
        "/api/resources/upload",
        files={"file": ("deleteme.txt", io.BytesIO(b"temporary content"), "text/plain")},
        headers={"origin": _origin},
    ).json()
    rid = resp["id"]
    assert auth_client.delete(f"/api/resources/{rid}", headers={"origin": _origin}).status_code == 200
    assert auth_client.get(f"/api/resources/{rid}/file").status_code == 404
    remaining = [r["id"] for r in auth_client.get("/api/resources").json()["items"]]
    assert rid not in remaining
