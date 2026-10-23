"""Quiz engine and spaced repetition: attempts, explanations, review queue."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..db import new_session
from ..deps import CurrentUser, SameOrigin
from ..models import (
    Flashcard,
    FlashcardDeck,
    Lesson,
    QuizAttempt,
    QuizQuestion,
    ReviewLog,
    ReviewSchedule,
    StudySession,
    TopicMastery,
    now_ms,
)

router = APIRouter()

DAY_MS = 86_400_000


# ---------------------------------------------------------------- quiz

class QuizStartIn(BaseModel):
    lessonId: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


@router.post("/start")
def start_quiz(payload: QuizStartIn, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        stmt = select(QuizQuestion).where(QuizQuestion.owner_id == user.id)
        if payload.lessonId:
            stmt = stmt.where(QuizQuestion.lesson_id == payload.lessonId)
        questions = db.execute(stmt.order_by(QuizQuestion.created_at)).scalars().all()
        # Weakest topics first is handled by client using mastery; server shuffles lightly.
        import random

        random.shuffle(questions)
        picked = questions[: payload.limit]
        session_id = str(uuid.uuid4())
        return {
            "sessionId": session_id,
            "questions": [
                {
                    "id": q.id,
                    "kind": q.kind,
                    "prompt": q.prompt,
                    "options": q.options,
                    "topics": q.topics,
                    "sourceRef": q.source_ref,
                }
                for q in picked
            ],
        }
    finally:
        db.close()


class AnswerIn(BaseModel):
    sessionId: str = Field(min_length=8, max_length=64)
    questionId: str
    givenIndex: int | None = None
    givenAnswer: str = Field(default="", max_length=4000)


@router.post("/answer")
def answer(payload: AnswerIn, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        q = db.execute(
            select(QuizQuestion).where(QuizQuestion.id == payload.questionId, QuizQuestion.owner_id == user.id)
        ).scalar_one_or_none()
        if not q:
            raise HTTPException(status_code=404, detail="Question not found.")

        correct = False
        if q.kind == "mcq":
            correct = payload.givenIndex is not None and payload.givenIndex == q.correct_index
        elif q.kind == "truefalse":
            correct = payload.givenIndex is not None and payload.givenIndex == q.correct_index
        else:
            given = payload.givenAnswer.strip().lower()
            accepted = [a.strip().lower() for a in (q.accepted_answers or [])]
            correct = bool(given) and any(a == given or a in given or given in a for a in accepted if a)

        db.add(
            QuizAttempt(
                id=str(uuid.uuid4()),
                owner_id=user.id,
                question_id=q.id,
                session_id=payload.sessionId,
                given_answer=payload.givenAnswer.strip()[:4000],
                given_index=payload.givenIndex,
                correct=correct,
                topics=q.topics,
            )
        )

        # Topic mastery: exponential moving average, actual results only.
        updates = []
        for topic in q.topics or []:
            row = db.execute(
                select(TopicMastery).where(TopicMastery.owner_id == user.id, TopicMastery.topic == topic)
            ).scalar_one_or_none()
            if not row:
                row = TopicMastery(
                    id=str(uuid.uuid4()),
                    owner_id=user.id,
                    topic=topic,
                    attempts=0,
                    correct=0,
                    mastery=0.0,
                )
                db.add(row)
            row.attempts += 1
            row.correct += 1 if correct else 0
            sample = 100.0 if correct else 0.0
            row.mastery = round(row.mastery * 0.7 + sample * 0.3, 2)
            row.updated_at = now_ms()
            updates.append({"topic": topic, "mastery": row.mastery, "attempts": row.attempts})

        # A wrong answer generates a due-tomorrow review card if none exists.
        made_card = False
        if not correct and (q.topics or q.source_ref):
            made_card = _card_from_wrong_answer(db, user.id, q)
        db.commit()
        return {
            "correct": correct,
            "explanation": q.explanation,
            "sourceRef": q.source_ref,
            "acceptedAnswers": q.accepted_answers if not correct else [],
            "topicMastery": updates,
            "reviewCardCreated": made_card,
        }
    finally:
        db.close()


def _card_from_wrong_answer(db, owner_id: str, q: QuizQuestion) -> bool:
    """Flashcard from an incorrect answer, due tomorrow."""
    front = q.prompt[:1000]
    deck = db.execute(
        select(FlashcardDeck).where(FlashcardDeck.owner_id == owner_id, FlashcardDeck.title == "From missed questions")
    ).scalar_one_or_none()
    if not deck:
        deck = FlashcardDeck(id=str(uuid.uuid4()), owner_id=owner_id, title="From missed questions", origin="manual")
        db.add(deck)
        db.flush()
    existing = db.execute(
        select(Flashcard).where(
            Flashcard.owner_id == owner_id,
            Flashcard.deck_id == deck.id,
            Flashcard.front == front,
        )
    ).scalar_one_or_none()
    if existing:
        return False
    card = Flashcard(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        deck_id=deck.id,
        front=front,
        back=(q.explanation or (q.accepted_answers or [""])[0])[:2000],
    )
    db.add(card)
    db.flush()
    db.add(ReviewSchedule(id=str(uuid.uuid4()), owner_id=owner_id, card_id=card.id, due_at=now_ms() + DAY_MS, state="learning"))
    return True


@router.get("/history")
def quiz_history(user: CurrentUser, limit: int = 100):
    db = new_session()
    try:
        rows = db.execute(
            select(QuizAttempt).where(QuizAttempt.owner_id == user.id).order_by(QuizAttempt.answered_at.desc()).limit(min(limit, 500))
        ).scalars()
        return {
            "items": [
                {
                    "id": a.id,
                    "questionId": a.question_id,
                    "sessionId": a.session_id,
                    "correct": a.correct,
                    "topics": a.topics,
                    "answeredAt": a.answered_at,
                }
                for a in rows
            ]
        }
    finally:
        db.close()


@router.get("/questions")
def list_questions(user: CurrentUser, lessonId: str | None = Query(default=None)):
    db = new_session()
    try:
        stmt = select(QuizQuestion).where(QuizQuestion.owner_id == user.id)
        if lessonId:
            stmt = stmt.where(QuizQuestion.lesson_id == lessonId)
        qs = db.execute(stmt.order_by(QuizQuestion.created_at)).scalars()
        return {
            "items": [
                {
                    "id": q.id,
                    "kind": q.kind,
                    "prompt": q.prompt,
                    "topics": q.topics,
                    "sourceRef": q.source_ref,
                    "lessonId": q.lesson_id,
                    "origin": q.origin,
                }
                for q in qs
            ]
        }
    finally:
        db.close()


class QuestionIn(BaseModel):
    kind: str = Field(pattern="^(mcq|truefalse|shortanswer|code_reading|debugging|scenario|audit)$")
    prompt: str = Field(min_length=1, max_length=8000)
    options: list[str] = Field(default_factory=list, max_length=8)
    correctIndex: int | None = None
    acceptedAnswers: list[str] = Field(default_factory=list, max_length=20)
    explanation: str = Field(default="", max_length=4000)
    sourceRef: str | None = Field(default=None, max_length=300)
    topics: list[str] = Field(default_factory=list, max_length=10)
    lessonId: str | None = None


@router.post("/questions")
def create_question(payload: QuestionIn, user: CurrentUser, _: SameOrigin):
    if payload.kind in ("mcq", "truefalse"):
        if len(payload.options) < 2 or payload.correctIndex is None or not (0 <= payload.correctIndex < len(payload.options)):
            raise HTTPException(status_code=400, detail="Multiple-choice questions need options and a valid correctIndex.")
    db = new_session()
    try:
        q = QuizQuestion(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            lesson_id=payload.lessonId,
            kind=payload.kind,
            prompt=payload.prompt,
            options=payload.options,
            correct_index=payload.correctIndex,
            accepted_answers=payload.acceptedAnswers,
            explanation=payload.explanation,
            source_ref=payload.sourceRef,
            topics=payload.topics,
            origin="imported",
        )
        db.add(q)
        db.commit()
        return {"id": q.id}
    finally:
        db.close()


# ---------------------------------------------------------------- flashcards + SRS

@router.get("/mastery")
def mastery(user: CurrentUser):
    db = new_session()
    try:
        rows = db.execute(select(TopicMastery).where(TopicMastery.owner_id == user.id)).scalars()
        items = sorted(
            [{"topic": r.topic, "mastery": r.mastery, "attempts": r.attempts, "correct": r.correct} for r in rows],
            key=lambda x: x["mastery"],
        )
        return {"items": items, "weakest": items[:5]}
    finally:
        db.close()


class DeckIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    lessonId: str | None = None


class CardIn(BaseModel):
    front: str = Field(min_length=1, max_length=4000)
    back: str = Field(min_length=1, max_length=8000)


@router.get("/decks")
def decks(user: CurrentUser):
    db = new_session()
    try:
        rows = db.execute(
            select(FlashcardDeck).where(FlashcardDeck.owner_id == user.id).order_by(FlashcardDeck.created_at)
        ).scalars()
        out = []
        for d in rows:
            card_count = 0
            due_count = 0
            now = now_ms()
            for card in db.execute(select(Flashcard).where(Flashcard.deck_id == d.id)).scalars():
                card_count += 1
                sched = db.execute(
                    select(ReviewSchedule).where(ReviewSchedule.card_id == card.id, ReviewSchedule.owner_id == user.id)
                ).scalar_one_or_none()
                if not sched or sched.due_at <= now:
                    due_count += 1
            out.append({"id": d.id, "title": d.title, "lessonId": d.lesson_id, "cardCount": card_count, "dueCount": due_count})
        return {"items": out}
    finally:
        db.close()


@router.post("/decks")
def create_deck(payload: DeckIn, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        d = FlashcardDeck(id=str(uuid.uuid4()), owner_id=user.id, title=payload.title.strip()[:200], lesson_id=payload.lessonId)
        db.add(d)
        db.commit()
        return {"id": d.id, "title": d.title}
    finally:
        db.close()


@router.get("/decks/{deck_id}")
def get_deck(deck_id: str, user: CurrentUser):
    db = new_session()
    try:
        deck = db.execute(
            select(FlashcardDeck).where(FlashcardDeck.id == deck_id, FlashcardDeck.owner_id == user.id)
        ).scalar_one_or_none()
        if not deck:
            raise HTTPException(status_code=404, detail="Deck not found.")
        cards = db.execute(
            select(Flashcard).where(Flashcard.deck_id == deck_id).order_by(Flashcard.position, Flashcard.created_at)
        ).scalars().all()
        now = now_ms()
        items = []
        for c in cards:
            sched = db.execute(
                select(ReviewSchedule).where(ReviewSchedule.card_id == c.id, ReviewSchedule.owner_id == user.id)
            ).scalar_one_or_none()
            items.append(
                {
                    "id": c.id,
                    "front": c.front,
                    "back": c.back,
                    "dueAt": sched.due_at if sched else None,
                    "state": sched.state if sched else "new",
                    "repetitions": sched.repetitions if sched else 0,
                    "ease": sched.ease if sched else None,
                }
            )
        return {"deck": {"id": deck.id, "title": deck.title}, "cards": items, "dueNow": sum(1 for i in items if i["dueAt"] is None or i["dueAt"] <= now)}
    finally:
        db.close()


@router.post("/decks/{deck_id}/cards")
def add_card(deck_id: str, payload: CardIn, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        deck = db.execute(
            select(FlashcardDeck).where(FlashcardDeck.id == deck_id, FlashcardDeck.owner_id == user.id)
        ).scalar_one_or_none()
        if not deck:
            raise HTTPException(status_code=404, detail="Deck not found.")
        count = len(db.execute(select(Flashcard).where(Flashcard.deck_id == deck_id)).scalars().all())
        c = Flashcard(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            deck_id=deck_id,
            front=payload.front.strip(),
            back=payload.back.strip(),
            position=count,
        )
        db.add(c)
        db.flush()
        db.add(ReviewSchedule(id=str(uuid.uuid4()), owner_id=user.id, card_id=c.id, due_at=now_ms(), state="new"))
        db.commit()
        return {"id": c.id}
    finally:
        db.close()


@router.get("/due")
def due_cards(user: CurrentUser, limit: int = 30):
    """Review queue: cards whose next due time has passed."""
    db = new_session()
    try:
        now = now_ms()
        scheds = db.execute(
            select(ReviewSchedule).where(ReviewSchedule.owner_id == user.id, ReviewSchedule.due_at <= now).order_by(ReviewSchedule.due_at)
        ).scalars().all()
        out = []
        seen = set()
        for s in scheds:
            if s.card_id in seen:
                continue
            seen.add(s.card_id)
            card = db.get(Flashcard, s.card_id)
            if not card:
                continue
            deck = db.get(FlashcardDeck, card.deck_id)
            out.append({"cardId": card.id, "front": card.front, "back": card.back, "deckTitle": deck.title if deck else "", "state": s.state})
            if len(out) >= limit:
                break
        return {"items": out, "dueCount": len(out)}
    finally:
        db.close()


class ReviewIn(BaseModel):
    cardId: str
    # 'again' | 'difficult' | 'good' | 'easy'
    grade: str = Field(pattern="^(again|difficult|good|easy)$")


@router.post("/review")
def review_card(payload: ReviewIn, user: CurrentUser, _: SameOrigin):
    """SM-2 style scheduling updated from the user's own grades."""
    db = new_session()
    try:
        card = db.execute(select(Flashcard).where(Flashcard.id == payload.cardId, Flashcard.owner_id == user.id)).scalar_one_or_none()
        if not card:
            raise HTTPException(status_code=404, detail="Card not found.")
        sched = db.execute(
            select(ReviewSchedule).where(ReviewSchedule.card_id == card.id, ReviewSchedule.owner_id == user.id)
        ).scalar_one_or_none()
        if not sched:
            sched = ReviewSchedule(
                id=str(uuid.uuid4()),
                owner_id=user.id,
                card_id=card.id,
                ease=2.5,
                interval_days=0.0,
                repetitions=0,
                lapses=0,
                due_at=now_ms(),
                state="new",
            )
            db.add(sched)

        grade = payload.grade
        ease = max(1.3, sched.ease)
        if grade == "again":
            ease = max(1.3, ease - 0.2)
            interval = 0.01  # ~15 min: comes back in the same session
            repetitions = 0
            state = "relearning"
            lapses = sched.lapses + 1
        elif grade == "difficult":
            ease = max(1.3, ease - 0.15)
            interval = max(1.0, sched.interval_days * 1.2) if sched.repetitions else 1.0
            repetitions = sched.repetitions + 1
            state = "review"
            lapses = sched.lapses
        elif grade == "good":
            interval = sched.interval_days * ease if sched.repetitions > 1 else (2.0 if sched.repetitions else 1.0)
            repetitions = sched.repetitions + 1
            state = "review"
            lapses = sched.lapses
        else:  # easy
            interval = (sched.interval_days * ease * 1.3) if sched.repetitions > 1 else (4.0 if sched.repetitions else 2.0)
            repetitions = sched.repetitions + 1
            state = "review"
            lapses = sched.lapses
            ease = min(3.0, ease + 0.15)

        interval = min(interval, 365.0)
        next_due = now_ms() + int(interval * DAY_MS)
        sched.ease = round(ease, 3)
        sched.interval_days = round(interval, 3)
        sched.repetitions = repetitions
        sched.lapses = lapses
        sched.state = state
        sched.due_at = next_due
        sched.last_reviewed_at = now_ms()
        db.add(
            ReviewLog(
                id=str(uuid.uuid4()),
                owner_id=user.id,
                card_id=card.id,
                grade=grade,
                next_due_at=next_due,
            )
        )
        db.commit()
        return {"cardId": card.id, "nextDueAt": next_due, "intervalDays": round(interval, 2), "state": state, "ease": round(ease, 2)}
    finally:
        db.close()


@router.get("/review/stats")
def review_stats(user: CurrentUser):
    db = new_session()
    try:
        now = now_ms()
        all_scheds = db.execute(select(ReviewSchedule).where(ReviewSchedule.owner_id == user.id)).scalars().all()
        due_today = sum(1 for s in all_scheds if s.due_at <= now)
        learned = sum(1 for s in all_scheds if s.repetitions > 0)
        mature = sum(1 for s in all_scheds if s.interval_days >= 21)
        recent = db.execute(
            select(ReviewLog).where(ReviewLog.owner_id == user.id, ReviewLog.reviewed_at >= now - 7 * DAY_MS)
        ).scalars().all()
        return {
            "totalCards": len(all_scheds),
            "dueNow": due_today,
            "learned": learned,
            "mature": mature,
            "reviewsLast7Days": len(recent),
            "last7Days": _review_counts(recent),
        }
    finally:
        db.close()


def _review_counts(logs) -> list[dict]:
    from collections import Counter

    days: Counter[str] = Counter()
    for log in logs:
        import datetime as _dt

        day = _dt.datetime.fromtimestamp(log.reviewed_at / 1000, _dt.timezone.utc).strftime("%Y-%m-%d")
        days[day] += 1
    return [{"day": d, "count": c} for d, c in sorted(days.items())]
