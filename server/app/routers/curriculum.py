"""Curriculum: courses, modules, lessons, progress, bookmarks, resume."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from ..db import new_session
from ..deps import CurrentUser, SameOrigin
from ..models import (
    Bookmark,
    Course,
    Lesson,
    LessonProgress,
    LessonResource,
    Module,
    StudySession,
    now_ms,
)

router = APIRouter()


def _slug(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in text.strip()]
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:280] or "lesson"


# ---------------------------------------------------------------- reads

@router.get("/")
def tree(user: CurrentUser):
    """Whole curriculum with per-lesson progress, ordered for navigation."""
    db = new_session()
    try:
        courses = db.execute(
            select(Course).where(Course.owner_id == user.id).order_by(Course.position, Course.created_at)
        ).scalars().all()
        modules = db.execute(
            select(Module).where(Module.owner_id == user.id).order_by(Module.position, Module.created_at)
        ).scalars().all()
        lessons = db.execute(
            select(Lesson).where(Lesson.owner_id == user.id).order_by(Lesson.position, Lesson.created_at)
        ).scalars().all()
        progress = {
            p.lesson_id: p
            for p in db.execute(select(LessonProgress).where(LessonProgress.owner_id == user.id)).scalars()
        }
        resource_counts = dict(
            db.execute(
                select(LessonResource.lesson_id, func.count())
                .where(LessonResource.owner_id == user.id, LessonResource.lesson_id.is_not(None))
                .group_by(LessonResource.lesson_id)
            ).all()
        )

        by_module: dict[str, list] = {}
        for lesson in lessons:
            p = progress.get(lesson.id)
            by_module.setdefault(lesson.module_id, []).append(
                {
                    "id": lesson.id,
                    "title": lesson.title,
                    "contentStatus": lesson.content_status,
                    "verifyFlag": lesson.verify_flag,
                    "summary": lesson.summary,
                    "difficulty": lesson.difficulty,
                    "estimatedMinutes": lesson.estimated_minutes,
                    "position": lesson.position,
                    "hasVideo": bool(lesson.video_url),
                    "resourceCount": resource_counts.get(lesson.id, 0),
                    "status": p.status if p else "not_started",
                    "percent": p.percent if p else 0,
                    "completedAt": p.completed_at if p else None,
                }
            )

        module_rows = []
        for m in modules:
            module_rows.append(
                {
                    "id": m.id,
                    "courseId": m.course_id,
                    "number": m.number,
                    "title": m.title,
                    "summary": m.summary,
                    "position": m.position,
                    "lessons": by_module.get(m.id, []),
                }
            )

        total = len(lessons)
        done = sum(1 for p in progress.values() if p.status == "completed")
        return {
            "courses": [
                {
                    "id": c.id,
                    "title": c.title,
                    "description": c.description,
                    "position": c.position,
                    "modules": [m for m in module_rows if m["courseId"] == c.id],
                }
                for c in courses
            ],
            "progress": {"lessonsTotal": total, "lessonsCompleted": done, "percent": round(done * 100 / total) if total else 0},
        }
    finally:
        db.close()


@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: str, user: CurrentUser):
    db = new_session()
    try:
        lesson = db.execute(
            select(Lesson).where(Lesson.id == lesson_id, Lesson.owner_id == user.id)
        ).scalar_one_or_none()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found.")
        module = db.get(Module, lesson.module_id)
        progress = db.execute(
            select(LessonProgress).where(LessonProgress.lesson_id == lesson_id, LessonProgress.owner_id == user.id)
        ).scalar_one_or_none()
        resources = db.execute(
            select(LessonResource)
            .where(LessonResource.lesson_id == lesson_id, LessonResource.owner_id == user.id)
            .order_by(LessonResource.position)
        ).scalars().all()
        bookmarks = db.execute(
            select(Bookmark).where(Bookmark.lesson_id == lesson_id, Bookmark.owner_id == user.id).order_by(Bookmark.created_at)
        ).scalars().all()

        siblings = db.execute(
            select(Lesson)
            .where(Lesson.module_id == lesson.module_id, Lesson.owner_id == user.id)
            .order_by(Lesson.position)
        ).scalars().all()
        index = next((i for i, s in enumerate(siblings) if s.id == lesson.id), 0)
        prev_ = siblings[index - 1] if index > 0 else None
        next_ = siblings[index + 1] if index + 1 < len(siblings) else None

        return {
            "lesson": {
                "id": lesson.id,
                "moduleId": lesson.module_id,
                "moduleTitle": module.title if module else "",
                "title": lesson.title,
                "contentStatus": lesson.content_status,
                "verifyFlag": lesson.verify_flag,
                "summary": lesson.summary,
                "bodyMarkdown": lesson.body_markdown,
                "topics": lesson.topics,
                "difficulty": lesson.difficulty,
                "estimatedMinutes": lesson.estimated_minutes,
                "videoUrl": lesson.video_url,
                "videoDurationSeconds": lesson.video_duration_seconds,
                "position": lesson.position,
            },
            "progress": {
                "status": progress.status if progress else "not_started",
                "percent": progress.percent if progress else 0,
                "videoPositionSeconds": progress.video_position_seconds if progress else 0,
                "timeSpentSeconds": progress.time_spent_seconds if progress else 0,
                "completedAt": progress.completed_at if progress else None,
            },
            "resources": [
                {
                    "id": r.id,
                    "kind": r.kind,
                    "title": r.title,
                    "url": r.url,
                    "fileId": r.file_id,
                    "mimeType": r.mime_type,
                    "content": r.content,
                    "tags": r.tags,
                }
                for r in resources
            ],
            "bookmarks": [
                {"id": b.id, "label": b.label, "position": b.position, "note": b.note, "createdAt": b.created_at}
                for b in bookmarks
            ],
            "navigation": {
                "prev": {"id": prev_.id, "title": prev_.title} if prev_ else None,
                "next": {"id": next_.id, "title": next_.title} if next_ else None,
            },
        }
    finally:
        db.close()


# ---------------------------------------------------------------- progress

class ProgressIn(BaseModel):
    percent: int | None = Field(default=None, ge=0, le=100)
    status: str | None = Field(default=None, pattern="^(not_started|in_progress|completed)$")
    videoPositionSeconds: int | None = Field(default=None, ge=0)
    timeSpentSeconds: int | None = Field(default=None, ge=0, le=86_400)


@router.put("/lessons/{lesson_id}/progress")
def put_progress(lesson_id: str, payload: ProgressIn, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        lesson = db.execute(
            select(Lesson.id).where(Lesson.id == lesson_id, Lesson.owner_id == user.id)
        ).scalar_one_or_none()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found.")
        row = db.execute(
            select(LessonProgress).where(LessonProgress.lesson_id == lesson_id, LessonProgress.owner_id == user.id)
        ).scalar_one_or_none()
        if not row:
            row = LessonProgress(id=str(uuid.uuid4()), owner_id=user.id, lesson_id=lesson_id)
            db.add(row)
        if payload.percent is not None:
            row.percent = payload.percent
        if payload.videoPositionSeconds is not None:
            row.video_position_seconds = payload.videoPositionSeconds
        if payload.timeSpentSeconds is not None:
            row.time_spent_seconds += payload.timeSpentSeconds  # additive heartbeat
        if payload.status is not None:
            row.status = payload.status
            if payload.status == "completed" and not row.completed_at:
                row.completed_at = now_ms()
                row.percent = 100
        elif row.percent >= 100 and row.status != "completed":
            row.status = "completed"
            row.completed_at = row.completed_at or now_ms()
        row.updated_at = now_ms()
        db.commit()
        return {
            "status": row.status,
            "percent": row.percent,
            "completedAt": row.completed_at,
            "timeSpentSeconds": row.time_spent_seconds,
        }
    finally:
        db.close()


@router.get("/resume")
def resume(user: CurrentUser):
    """Recommended next lesson: first in-progress, else first not-started."""
    db = new_session()
    try:
        lessons = db.execute(
            select(Lesson).where(Lesson.owner_id == user.id).order_by(Lesson.position, Lesson.created_at)
        ).scalars().all()
        if not lessons:
            return {"lesson": None}
        progress = {
            p.lesson_id: p
            for p in db.execute(select(LessonProgress).where(LessonProgress.owner_id == user.id)).scalars()
        }
        in_progress = [l for l in lessons if (progress.get(l.id) and progress[l.id].status == "in_progress")]
        not_started = [l for l in lessons if not progress.get(l.id) or progress[l.id].status != "completed"]
        pick = in_progress[0] if in_progress else (not_started[0] if not_started else None)
        if not pick:
            return {"lesson": None}
        module = db.get(Module, pick.module_id)
        p = progress.get(pick.id)
        return {
            "lesson": {
                "id": pick.id,
                "title": pick.title,
                "moduleTitle": module.title if module else "",
                "summary": pick.summary,
                "difficulty": pick.difficulty,
                "estimatedMinutes": pick.estimated_minutes,
                "percent": p.percent if p else 0,
                "status": p.status if p else "not_started",
            }
        }
    finally:
        db.close()


# ---------------------------------------------------------------- bookmarks

class BookmarkIn(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    position: int | None = Field(default=None, ge=0)
    note: str = Field(default="", max_length=2000)


@router.post("/lessons/{lesson_id}/bookmarks")
def add_bookmark(lesson_id: str, payload: BookmarkIn, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        lesson = db.execute(
            select(Lesson.id).where(Lesson.id == lesson_id, Lesson.owner_id == user.id)
        ).scalar_one_or_none()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found.")
        b = Bookmark(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            lesson_id=lesson_id,
            label=payload.label.strip()[:200],
            position=payload.position,
            note=payload.note.strip(),
        )
        db.add(b)
        db.commit()
        return {"id": b.id, "label": b.label, "position": b.position, "note": b.note, "createdAt": b.created_at}
    finally:
        db.close()


@router.delete("/bookmarks/{bookmark_id}")
def delete_bookmark(bookmark_id: str, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        row = db.execute(
            select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.owner_id == user.id)
        ).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Bookmark not found.")
        db.delete(row)
        db.commit()
        return {"ok": True}
    finally:
        db.close()
