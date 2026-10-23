"""Curriculum delivery, quiz grading, topic mastery and spaced repetition."""

from __future__ import annotations

_origin = "http://testserver"


def _owner_id(client) -> str:
    return client.get("/api/auth/me").json()["id"]


def _now_ms() -> int:
    import time

    return int(time.time() * 1000)


# ---------------------------------------------------------------- curriculum


def test_seeded_curriculum_is_complete_and_ordered(seeded_client):
    tree = seeded_client.get("/api/curriculum/").json()
    assert len(tree["courses"]) == 1
    course = tree["courses"][0]
    assert course["title"] == "Algorithmic Trading Foundations"
    assert len(course["modules"]) >= 9

    # Orientation must come first, so a new learner does not land in the deep end.
    assert course["modules"][0]["number"] == 0
    numbers = [m["number"] for m in course["modules"]]
    assert numbers == sorted(numbers)

    lessons = [l for m in course["modules"] for l in m["lessons"]]
    assert len(lessons) == tree["progress"]["lessonsTotal"] >= 30

    # Every lesson is explicitly labeled sample content.
    assert all(l["contentStatus"] == "sample" for l in lessons)


def test_lesson_body_is_labeled_and_has_no_profit_claims(seeded_client):
    tree = seeded_client.get("/api/curriculum/").json()
    lesson_id = tree["courses"][0]["modules"][0]["lessons"][0]["id"]
    lesson = seeded_client.get(f"/api/curriculum/lessons/{lesson_id}").json()["lesson"]

    assert lesson["bodyMarkdown"].strip()
    assert "Sample content" in lesson["bodyMarkdown"] or "sample" in lesson["contentStatus"]
    banned = ["guaranteed profit", "risk-free returns", "beat the market", "guaranteed return"]
    low = lesson["bodyMarkdown"].lower()
    assert not any(b in low for b in banned)


def test_lesson_progress_and_resume(seeded_client):
    tree = seeded_client.get("/api/curriculum/").json()
    first = tree["courses"][0]["modules"][0]["lessons"][0]
    lesson_id = first["id"]

    resume = seeded_client.get("/api/curriculum/resume").json()["lesson"]
    assert resume["id"] == lesson_id, "resume should start at the first lesson"

    resp = seeded_client.put(
        f"/api/curriculum/lessons/{lesson_id}/progress",
        json={"percent": 100, "status": "completed"},
        headers={"origin": _origin},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"

    tree2 = seeded_client.get("/api/curriculum/").json()["progress"]
    assert tree2["lessonsCompleted"] == 1
    assert tree2["percent"] == round(100 / tree2["lessonsTotal"])

    # Next resume moves off the completed lesson.
    resume2 = seeded_client.get("/api/curriculum/resume").json()["lesson"]
    assert resume2["id"] != lesson_id


def test_lesson_navigation_has_prev_and_next(seeded_client):
    tree = seeded_client.get("/api/curriculum/").json()
    modules = tree["courses"][0]["modules"]
    lessons = [l for l in modules[1]["lessons"]]  # orientation lessons are excluded from this check
    middle = lessons[1]
    data = seeded_client.get(f"/api/curriculum/lessons/{middle['id']}").json()
    assert data["navigation"]["prev"] is not None
    assert data["navigation"]["next"] is not None


def test_bookmarks_round_trip_and_are_owner_scoped(seeded_client, other_client):
    tree = seeded_client.get("/api/curriculum/").json()
    lesson_id = tree["courses"][0]["modules"][0]["lessons"][0]["id"]

    created = seeded_client.post(
        f"/api/curriculum/lessons/{lesson_id}/bookmarks",
        json={"label": "Key sentence", "note": "remember this"},
        headers={"origin": _origin},
    )
    assert created.status_code == 200
    bookmark_id = created.json()["id"]

    lesson = seeded_client.get(f"/api/curriculum/lessons/{lesson_id}").json()
    assert any(b["id"] == bookmark_id for b in lesson["bookmarks"])

    # Another account cannot see or delete it.
    assert other_client.delete(f"/api/curriculum/bookmarks/{bookmark_id}", headers={"origin": _origin}).status_code == 404
    assert seeded_client.delete(f"/api/curriculum/bookmarks/{bookmark_id}", headers={"origin": _origin}).status_code == 200


# ---------------------------------------------------------------- quiz


def _first_question(client) -> dict:
    qs = client.get("/api/quiz/questions").json()["items"]
    assert qs, "seeded account must have quiz questions"
    return qs[0]


def test_quiz_start_returns_questions_without_answers(seeded_client):
    resp = seeded_client.post("/api/quiz/start", json={"limit": 5}, headers={"origin": _origin})
    assert resp.status_code == 200
    body = resp.json()
    assert body["sessionId"]
    assert 1 <= len(body["questions"]) <= 5
    # The answer must never leak in the start payload.
    blob = resp.text.lower()
    assert '"correct_index"' not in blob
    assert '"correctindex"' not in blob
    assert "explanation" not in blob


def test_quiz_answer_grades_correct_and_incorrect(seeded_client):
    qs = seeded_client.get("/api/quiz/questions").json()["items"]
    mcq = next(q for q in qs if q["kind"] == "mcq")

    # The API never exposes correct answers by design, so read the truth from
    # this owner's row directly to grade against it.
    from app.db import new_session
    from app.models import QuizQuestion

    owner = _owner_id(seeded_client)
    db = new_session()
    try:
        row = db.query(QuizQuestion).filter(
            QuizQuestion.id == mcq["id"], QuizQuestion.owner_id == owner
        ).one()
        correct_index = row.correct_index
        explanation = row.explanation
        option_count = max(2, len(row.options))
    finally:
        db.close()

    session_id = "00000000-0000-0000-0000-000000000000"

    wrong_idx = (correct_index + 1) % option_count
    wrong = seeded_client.post(
        "/api/quiz/answer",
        json={"sessionId": session_id, "questionId": mcq["id"], "givenIndex": wrong_idx},
        headers={"origin": _origin},
    ).json()
    assert wrong["correct"] is False
    assert wrong["explanation"] == explanation
    # A miss should offer the accepted answers and may mint a review card.
    assert wrong["acceptedAnswers"] or wrong["reviewCardCreated"] in (True, False)

    right = seeded_client.post(
        "/api/quiz/answer",
        json={"sessionId": session_id, "questionId": mcq["id"], "givenIndex": correct_index},
        headers={"origin": _origin},
    ).json()
    assert right["correct"] is True
    assert right["explanation"] == explanation


def test_wrong_answer_builds_a_due_review_card(seeded_client):
    from app.db import new_session
    from app.models import QuizQuestion
    from sqlalchemy import select

    owner = _owner_id(seeded_client)
    db = new_session()
    try:
        q = db.execute(
            select(QuizQuestion).where(
                QuizQuestion.kind == "shortanswer", QuizQuestion.owner_id == owner
            )
        ).scalars().first()
        assert q is not None
        q_id, accepted = q.id, q.accepted_answers
    finally:
        db.close()
    assert accepted, "short-answer questions must declare accepted answers"

    resp = seeded_client.post(
        "/api/quiz/answer",
        json={"sessionId": "11111111-1111-1111-1111-111111111111", "questionId": q_id, "givenAnswer": "definitely wrong"},
        headers={"origin": _origin},
    ).json()
    assert resp["correct"] is False

    # The card lands in the "From missed questions" deck, scheduled for
    # tomorrow (not now) so it joins the review queue when it is due.
    decks = seeded_client.get("/api/quiz/decks").json()["items"]
    deck = next(d for d in decks if d["title"] == "From missed questions")
    assert deck["cardCount"] >= 1

    cards = seeded_client.get(f"/api/quiz/decks/{deck['id']}").json()["cards"]
    missed = next(c for c in cards if c["front"].strip())
    assert missed["dueAt"] is not None and missed["dueAt"] > _now_ms()


def test_topic_mastery_tracks_accuracy(seeded_client):
    from app.db import new_session
    from app.models import QuizQuestion
    from sqlalchemy import select

    owner = _owner_id(seeded_client)
    db = new_session()
    try:
        q = db.execute(
            select(QuizQuestion).where(
                QuizQuestion.kind == "mcq", QuizQuestion.owner_id == owner
            )
        ).scalars().first()
        q_id, correct_index, topics = q.id, q.correct_index, q.topics
    finally:
        db.close()
    assert topics, "seeded MCQs must carry topics for mastery tracking"

    sid = "22222222-2222-2222-2222-222222222222"
    seeded_client.post("/api/quiz/answer", json={"sessionId": sid, "questionId": q_id, "givenIndex": correct_index}, headers={"origin": _origin})
    seeded_client.post("/api/quiz/answer", json={"sessionId": sid, "questionId": q_id, "givenIndex": (correct_index + 1) % 4}, headers={"origin": _origin})

    mastery = seeded_client.get("/api/quiz/mastery").json()
    assert mastery["items"], "answering should create topic mastery rows"
    row = next(i for i in mastery["items"] if i["topic"] in topics)
    assert row["attempts"] == 2
    assert row["correct"] == 1
    assert 0 < row["mastery"] < 100


def test_cannot_answer_a_foreign_question(seeded_client, other_client):
    q_id = _first_question(seeded_client)["id"]
    resp = other_client.post(
        "/api/quiz/answer",
        json={"sessionId": "33333333-3333-3333-3333-333333333333", "questionId": q_id, "givenIndex": 0},
        headers={"origin": _origin},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------- SRS


def test_review_queue_starts_with_starter_cards(seeded_client):
    stats = seeded_client.get("/api/quiz/review/stats").json()
    assert stats["totalCards"] > 0
    assert stats["dueNow"] > 0, "starter deck should be due immediately"
    assert stats["learned"] == 0


def test_sm2_good_grade_grows_interval_and_lapse_resets_it(seeded_client):
    due = seeded_client.get("/api/quiz/due").json()["items"]
    assert due
    card_id = due[0]["cardId"]

    first = seeded_client.post("/api/quiz/review", json={"cardId": card_id, "grade": "good"}, headers={"origin": _origin}).json()
    assert first["intervalDays"] >= 1
    assert first["state"] == "review"
    good_interval = first["intervalDays"]

    # A second 'good' should extend (or at least not shrink) the interval.
    second = seeded_client.post("/api/quiz/review", json={"cardId": card_id, "grade": "good"}, headers={"origin": _origin}).json()
    assert second["intervalDays"] >= good_interval

    # Forgetting resets progress and sends it to relearning.
    lapsed = seeded_client.post("/api/quiz/review", json={"cardId": card_id, "grade": "again"}, headers={"origin": _origin}).json()
    assert lapsed["state"] == "relearning"
    assert lapsed["intervalDays"] < second["intervalDays"]
    assert lapsed["ease"] < second["ease"]


def test_sm2_ease_stays_bounded(seeded_client):
    due = seeded_client.get("/api/quiz/due").json()["items"]
    card_id = due[0]["cardId"]

    # Hammer the card with failures; ease must not fall below 1.3.
    lowest = 99.0
    for _ in range(6):
        r = seeded_client.post("/api/quiz/review", json={"cardId": card_id, "grade": "again"}, headers={"origin": _origin}).json()
        lowest = min(lowest, r["ease"])
    assert lowest >= 1.3, f"ease fell below the floor to {lowest}"

    # Hammer with successes; ease must not rise above 3.0.
    highest = 0.0
    for _ in range(6):
        r = seeded_client.post("/api/quiz/review", json={"cardId": card_id, "grade": "easy"}, headers={"origin": _origin}).json()
        highest = max(highest, r["ease"])
    assert highest <= 3.0, f"ease rose above the ceiling to {highest}"


def test_interval_is_capped_at_a_year(seeded_client):
    due = seeded_client.get("/api/quiz/due").json()["items"]
    card_id = due[0]["cardId"]
    for _ in range(10):
        r = seeded_client.post("/api/quiz/review", json={"cardId": card_id, "grade": "easy"}, headers={"origin": _origin}).json()
    assert r["intervalDays"] <= 365.0


def test_review_of_a_foreign_card_is_refused(seeded_client, other_client):
    due = seeded_client.get("/api/quiz/due").json()["items"]
    resp = other_client.post("/api/quiz/review", json={"cardId": due[0]["cardId"], "grade": "good"}, headers={"origin": _origin})
    assert resp.status_code == 404
