"""Account: profile, preferences, export, audit trail, destructive actions."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select

from ..db import new_session
from ..deps import CurrentUser, SameOrigin
from ..models import (
    AuditEvent,
    Concept,
    Course,
    Flashcard,
    FlashcardDeck,
    Lesson,
    LessonProgress,
    Module,
    Note,
    Project,
    ProjectMilestone,
    QuizAttempt,
    QuizQuestion,
    ReviewLog,
    ReviewSchedule,
    TopicMastery,
    User,
    now_ms,
)

router = APIRouter()


class ProfileIn(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    preferences: dict | None = None


@router.get("/profile")
def profile(user: CurrentUser):
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "timezone": user.timezone,
        "preferences": user.preferences or {},
    }


@router.patch("/profile")
def update_profile(payload: ProfileIn, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        row = db.get(User, user.id)
        if payload.display_name is not None:
            row.display_name = payload.display_name.strip()[:120]
        if payload.timezone is not None:
            row.timezone = payload.timezone.strip()[:64]
        if payload.preferences is not None:
            row.preferences = payload.preferences
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.get("/export")
def export_data(user: CurrentUser):
    """Full personal-data export as JSON (GDPR-friendly, and a backup path)."""
    db = new_session()
    try:
        def rows(model):
            return [dict(r._mapping) for r in db.execute(select(model).where(model.owner_id == user.id)).all()]

        export = {
            "exported_at": now_ms(),
            "profile": {"email": user.email, "display_name": user.display_name, "timezone": user.timezone, "preferences": user.preferences},
            "courses": rows(Course),
            "modules": rows(Module),
            "lessons": rows(Lesson),
            "lesson_progress": rows(LessonProgress),
            "notes": rows(Note),
            "concepts": rows(Concept),
            "flashcard_decks": rows(FlashcardDeck),
            "flashcards": rows(Flashcard),
            "review_schedules": rows(ReviewSchedule),
            "review_logs": rows(ReviewLog),
            "quiz_questions": rows(QuizQuestion),
            "quiz_attempts": rows(QuizAttempt),
            "topic_mastery": rows(TopicMastery),
            "projects": rows(Project),
            "project_milestones": rows(ProjectMilestone),
            "audit_events": rows(AuditEvent),
        }
        db.add(AuditEvent(id=str(uuid.uuid4()), owner_id=user.id, action="data.export"))
        db.commit()
        return export
    finally:
        db.close()


@router.get("/audit")
def audit_trail(user: CurrentUser, limit: int = 100):
    db = new_session()
    try:
        items = db.execute(
            select(AuditEvent).where(AuditEvent.owner_id == user.id).order_by(AuditEvent.at.desc()).limit(min(limit, 500))
        ).scalars()
        return {
            "items": [
                {"action": e.action, "entity": e.entity, "entity_id": e.entity_id, "detail": e.detail, "at": e.at}
                for e in items
            ]
        }
    finally:
        db.close()


class WipeIn(BaseModel):
    confirm: str


@router.post("/wipe")
def wipe_learning_data(payload: WipeIn, user: CurrentUser, _: SameOrigin):
    """Removes learning data only; the account itself survives."""
    if payload.confirm != "ERASE":
        raise HTTPException(status_code=400, detail='Type "ERASE" to confirm.')
    db = new_session()
    try:
        # Children cascade from courses/lessons/decks; delete in safe order.
        for model in (
            ReviewLog,
            ReviewSchedule,
            QuizAttempt,
            TopicMastery,
            Flashcard,
            FlashcardDeck,
            QuizQuestion,
            LessonProgress,
            Lesson,
            Module,
            Course,
            Note,
            Concept,
            ProjectMilestone,
            Project,
        ):
            db.execute(delete(model).where(model.owner_id == user.id))
        db.add(AuditEvent(id=str(uuid.uuid4()), owner_id=user.id, action="data.wipe"))
        db.commit()
        return {"ok": True}
    finally:
        db.close()
