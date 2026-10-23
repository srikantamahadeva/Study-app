"""Reports: weekly study reports, mastery, quiz history, revision recommendations.

Every number is computed from recorded activity — nothing is invented.
"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Query
from sqlalchemy import select

from ..db import new_session
from ..deps import CurrentUser
from ..models import (
    Lesson,
    LessonProgress,
    QuizAttempt,
    ReviewLog,
    ReviewSchedule,
    StudySession,
    StudyTimeLog,
    TopicMastery,
    now_ms,
)

router = APIRouter()

DAY_MS = 86_400_000


@router.get("/overview")
def overview(user: CurrentUser):
    """Dashboard metrics: all traceable to recorded rows."""
    db = new_session()
    try:
        now = now_ms()
        lessons = db.execute(select(Lesson).where(Lesson.owner_id == user.id)).scalars().all()
        progress = db.execute(select(LessonProgress).where(LessonProgress.owner_id == user.id)).scalars().all()
        completed = sum(1 for p in progress if p.status == "completed")

        attempts = db.execute(select(QuizAttempt).where(QuizAttempt.owner_id == user.id)).scalars().all()
        recent_attempts = [a for a in attempts if a.answered_at >= now - 7 * DAY_MS]
        quiz_accuracy = round(100 * sum(1 for a in attempts if a.correct) / len(attempts)) if attempts else None
        recent_accuracy = round(100 * sum(1 for a in recent_attempts if a.correct) / len(recent_attempts)) if recent_attempts else None

        study = db.execute(select(StudySession).where(StudySession.owner_id == user.id)).scalars().all()
        week_sessions = [s for s in study if s.created_at >= now - 7 * DAY_MS]
        time_logs = db.execute(
            select(StudyTimeLog).where(StudyTimeLog.owner_id == user.id, StudyTimeLog.day >= _days_ago(7))
        ).scalars().all()

        scheds = db.execute(select(ReviewSchedule).where(ReviewSchedule.owner_id == user.id)).scalars().all()
        due_now = sum(1 for s in scheds if s.due_at <= now)

        mastery = db.execute(select(TopicMastery).where(TopicMastery.owner_id == user.id)).scalars().all()
        weakest = sorted([{"topic": m.topic, "mastery": m.mastery, "attempts": m.attempts} for m in mastery], key=lambda x: x["mastery"])[:5]

        # Streak: consecutive days with any recorded activity.
        active_days = set()
        for s in study:
            active_days.add(_day_key(s.created_at))
        for p in progress:
            if p.updated_at:
                active_days.add(_day_key(p.updated_at))
        for a in attempts:
            active_days.add(_day_key(a.answered_at))
        streak = _streak(active_days)

        # Resume recommendation: from recorded progress ordering.
        next_lesson = None
        ordered = sorted(lessons, key=lambda l: l.position)
        by_lesson = {p.lesson_id: p for p in progress}
        for l in ordered:
            p = by_lesson.get(l.id)
            if not p or p.status != "completed":
                next_lesson = {"id": l.id, "title": l.title, "percent": p.percent if p else 0}
                break

        return {
            "progress": {
                "lessonsTotal": len(lessons),
                "lessonsCompleted": completed,
                "percent": round(completed * 100 / len(lessons)) if lessons else 0,
            },
            "streak": {"current": streak["current"], "longest": streak["longest"]},
            "study": {
                "sessions": len(study),
                "sessionsThisWeek": len(week_sessions),
                "minutesThisWeek": round(sum(s.duration_seconds for s in week_sessions) / 60),
                "byDay": [{"day": t.day, "seconds": t.seconds} for t in sorted(time_logs, key=lambda x: x.day)],
            },
            "quiz": {
                "attempts": len(attempts),
                "accuracy": quiz_accuracy,
                "accuracy7d": recent_accuracy,
            },
            "revisions": {
                "dueNow": due_now,
                "totalCards": len(scheds),
                "reviewsLast7Days": len([r for r in db.execute(select(ReviewLog).where(ReviewLog.owner_id == user.id, ReviewLog.reviewed_at >= now - 7 * DAY_MS)).scalars()]),
            },
            "weakestTopics": weakest,
            "nextLesson": next_lesson,
        }
    finally:
        db.close()


@router.get("/weekly")
def weekly(user: CurrentUser, weeks: int = Query(default=4, ge=1, le=12)):
    """Weekly study report: sessions, accuracy, minutes per ISO week."""
    db = new_session()
    try:
        now = now_ms()
        cutoff = now - weeks * 7 * DAY_MS
        study = [s for s in db.execute(select(StudySession).where(StudySession.owner_id == user.id, StudySession.created_at >= cutoff)).scalars()]
        attempts = [a for a in db.execute(select(QuizAttempt).where(QuizAttempt.owner_id == user.id, QuizAttempt.answered_at >= cutoff)).scalars()]
        reviews = [r for r in db.execute(select(ReviewLog).where(ReviewLog.owner_id == user.id, ReviewLog.reviewed_at >= cutoff)).scalars()]

        buckets: dict[str, dict] = {}
        for i in range(weeks + 1):
            key = _days_ago((weeks - i) * 7)
            buckets[key[:10]] = {"weekStart": key, "sessions": 0, "seconds": 0, "quizTotal": 0, "quizCorrect": 0, "reviews": 0}

        def bucket_key(ts: int) -> str:
            day = _day_key(ts)
            best = None
            for k in buckets:
                if day >= k and (best is None or k > best):
                    best = k
            return best or list(buckets)[0]

        for s in study:
            b = buckets[bucket_key(s.created_at)]
            b["sessions"] += 1
            b["seconds"] += s.duration_seconds
        for a in attempts:
            b = buckets[bucket_key(a.answered_at)]
            b["quizTotal"] += 1
            b["quizCorrect"] += 1 if a.correct else 0
        for r in reviews:
            buckets[bucket_key(r.reviewed_at)]["reviews"] += 1

        out = []
        for b in sorted(buckets.values(), key=lambda x: x["weekStart"]):
            acc = round(100 * b["quizCorrect"] / b["quizTotal"]) if b["quizTotal"] else None
            out.append(
                {
                    "weekStart": b["weekStart"],
                    "sessions": b["sessions"],
                    "minutes": round(b["seconds"] / 60),
                    "quizAttempts": b["quizTotal"],
                    "quizAccuracy": acc,
                    "reviews": b["reviews"],
                }
            )
        return {"weeks": out}
    finally:
        db.close()


@router.get("/mastery")
def mastery_report(user: CurrentUser):
    db = new_session()
    try:
        rows = db.execute(select(TopicMastery).where(TopicMastery.owner_id == user.id)).scalars()
        items = sorted(
            [{"topic": r.topic, "mastery": r.mastery, "attempts": r.attempts, "correct": r.correct} for r in rows],
            key=lambda x: x["mastery"],
        )
        return {"items": items}
    finally:
        db.close()


@router.get("/quiz-history")
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


@router.get("/recommendations")
def recommendations(user: CurrentUser):
    """Revision recommendations from actual performance: due cards + weak topics."""
    db = new_session()
    try:
        now = now_ms()
        due = db.execute(
            select(ReviewSchedule).where(ReviewSchedule.owner_id == user.id, ReviewSchedule.due_at <= now)
        ).scalars().all()
        weak = db.execute(select(TopicMastery).where(TopicMastery.owner_id == user.id)).scalars()
        weak_items = sorted(
            [{"topic": m.topic, "mastery": m.mastery, "attempts": m.attempts} for m in weak if m.attempts >= 3],
            key=lambda x: x["mastery"],
        )[:5]

        incomplete = db.execute(
            select(LessonProgress).where(LessonProgress.owner_id == user.id, LessonProgress.status == "in_progress")
        ).scalars().all()

        return {
            "dueReviews": len(due),
            "weakTopics": [w for w in weak_items if w["mastery"] < 70],
            "inProgressLessons": [
                {"lessonId": p.lesson_id, "percent": p.percent, "updatedAt": p.updated_at} for p in incomplete
            ],
        }
    finally:
        db.close()


@router.get("/export.md")
def export_markdown(user: CurrentUser):
    """Exportable learning summary in Markdown."""
    db = new_session()
    try:
        now = now_ms()
        lessons = db.execute(select(Lesson).where(Lesson.owner_id == user.id)).scalars().all()
        progress = {p.lesson_id: p for p in db.execute(select(LessonProgress).where(LessonProgress.owner_id == user.id)).scalars()}
        attempts = db.execute(select(QuizAttempt).where(QuizAttempt.owner_id == user.id)).scalars().all()
        mastery = db.execute(select(TopicMastery).where(TopicMastery.owner_id == user.id)).scalars()
        scheds = db.execute(select(ReviewSchedule).where(ReviewSchedule.owner_id == user.id)).scalars().all()
        due = sum(1 for s in scheds if s.due_at <= now)

        lines = [
            "# Learning summary",
            "",
            f"Exported: {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## Curriculum",
        ]
        for lesson in sorted(lessons, key=lambda l: l.position):
            p = progress.get(lesson.id)
            status = p.status if p else "not_started"
            mark = "x" if status == "completed" else " "
            lines.append(f"- [{mark}] {lesson.title} ({status})")
        lines += ["", "## Quiz"]
        if attempts:
            acc = 100 * sum(1 for a in attempts if a.correct) / len(attempts)
            lines.append(f"- Attempts: {len(attempts)} | Accuracy: {round(acc)}%")
        else:
            lines.append("- No quiz attempts recorded yet.")
        lines += ["", "## Topic mastery"]
        for m in sorted(mastery, key=lambda x: x.mastery):
            lines.append(f"- {m.topic}: {round(m.mastery)}% ({m.correct}/{m.attempts})")
        lines += ["", "## Revision", f"- Cards due now: {due}", f"- Total cards scheduled: {len(scheds)}", ""]
        lines.append("_Generated from recorded activity only. No performance or profitability claims are made._")
        return {"markdown": "\n".join(lines)}
    finally:
        db.close()


# ---------------------------------------------------------------- helpers


def _day_key(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc).strftime("%Y-%m-%d")


def _days_ago(days: int) -> str:
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y-%m-%d")


def _streak(days: set[str]) -> dict:
    if not days:
        return {"current": 0, "longest": 0}
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    cursor = dt.datetime.now(dt.timezone.utc)
    if today not in days:
        cursor -= dt.timedelta(days=1)
        if cursor.strftime("%Y-%m-%d") not in days:
            cursor = None  # type: ignore
    current = 0
    if cursor is not None:
        while cursor.strftime("%Y-%m-%d") in days:
            current += 1
            cursor -= dt.timedelta(days=1)
    ordered = sorted(days)
    longest = run = 1
    for i in range(1, len(ordered)):
        prev = dt.datetime.strptime(ordered[i - 1], "%Y-%m-%d")
        cur = dt.datetime.strptime(ordered[i], "%Y-%m-%d")
        run = run + 1 if (cur - prev).days == 1 else 1
        longest = max(longest, run)
    return {"current": current, "longest": max(longest, current)}
