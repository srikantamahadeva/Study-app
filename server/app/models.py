"""SQLAlchemy models: the complete study-platform data model.

Every table is scoped by owner_id so one user's data can never leak into
another's. Timestamps are stored as UTC epoch milliseconds (BigInt) for
portability. There is deliberately NO model for orders, positions, broker
credentials or live execution of any kind: this platform is education and
research only, paper/simulated by design.
"""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy import JSON, BigInteger, Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def now_ms() -> int:
    return int(time.time() * 1000)


class TimestampMixin:
    created_at: Mapped[int] = mapped_column(BigInteger, default=now_ms)
    updated_at: Mapped[int] = mapped_column(BigInteger, default=now_ms, onupdate=now_ms)


# ---------------------------------------------------------------- users


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(String(120))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[int] = mapped_column(BigInteger, default=now_ms)
    expires_at: Mapped[int] = mapped_column(BigInteger)
    user_agent: Mapped[str | None] = mapped_column(String(400))


class LoginAttempt(Base):
    """Failed-login tracking for lockout. Stores no passwords."""

    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email_key: Mapped[str] = mapped_column(String(255), index=True)  # lowercased email
    at: Mapped[int] = mapped_column(BigInteger, default=now_ms)
    success: Mapped[bool] = mapped_column(Boolean, default=False)


# ---------------------------------------------------------------- curriculum


class Course(Base, TimestampMixin):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (UniqueConstraint("owner_id", "slug", name="uq_course_owner_slug"),)


class Module(Base, TimestampMixin):
    __tablename__ = "modules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(Integer, default=0)  # 0 = orientation section
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (UniqueConstraint("owner_id", "course_id", "slug", name="uq_module_owner_slug"),)


class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    slug: Mapped[str] = mapped_column(String(300))
    # 'sample' = clearly-labeled example content written for this app;
    # 'imported' = added by the user; 'stub' = title only, body pending.
    content_status: Mapped[str] = mapped_column(String(20), default="stub")
    # Set when a syllabus title was hard to read and needs manual checking.
    verify_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    body_markdown: Mapped[str] = mapped_column(Text, default="")
    # Key concepts / topics for mastery tracking, e.g. ["repainting","lookahead"].
    topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    difficulty: Mapped[str] = mapped_column(String(12), default="beginner")  # beginner|intermediate|advanced
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=15)
    position: Mapped[int] = mapped_column(Integer, default=0)
    # For video lessons supplied by the user.
    video_url: Mapped[str | None] = mapped_column(String(1000))
    video_duration_seconds: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("owner_id", "module_id", "slug", name="uq_lesson_owner_slug"),
        Index("ix_lessons_owner_position", "owner_id", "module_id", "position"),
    )


class LessonResource(Base, TimestampMixin):
    """A file or link attached to a lesson (PDF, image, code snippet, URL)."""

    __tablename__ = "lesson_resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str | None] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # pdf|image|code|link|note|checklist
    title: Mapped[str] = mapped_column(String(300))
    # For 'link': the URL. For stored files: the private file id.
    url: Mapped[str | None] = mapped_column(String(1000))
    file_id: Mapped[str | None] = mapped_column(String(36), index=True)
    mime_type: Mapped[str | None] = mapped_column(String(120))
    # Inline content for code snippets / checklists / plain notes.
    content: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    position: Mapped[int] = mapped_column(Integer, default=0)


class TranscriptChunk(Base):
    """Searchable text extracted from uploaded PDFs/videos' captions."""

    __tablename__ = "transcript_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str | None] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    resource_id: Mapped[str | None] = mapped_column(ForeignKey("lesson_resources.id", ondelete="CASCADE"), index=True)
    # e.g. "page 12" for PDFs or "00:14:32" for captions.
    locator: Mapped[str | None] = mapped_column(String(60))
    text: Mapped[str] = mapped_column(Text)

    __table_args__ = (Index("ix_transcript_owner_text", "owner_id"),)


class LessonProgress(Base, TimestampMixin):
    __tablename__ = "lesson_progress"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="not_started")  # not_started|in_progress|completed
    percent: Mapped[int] = mapped_column(Integer, default=0)
    video_position_seconds: Mapped[int] = mapped_column(Integer, default=0)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[int | None] = mapped_column(BigInteger)

    __table_args__ = (UniqueConstraint("owner_id", "lesson_id", name="uq_progress_owner_lesson"),)


class Bookmark(Base, TimestampMixin):
    __tablename__ = "bookmarks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(200))
    # Optional position: video seconds or character offset in the body.
    position: Mapped[int | None] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(Text, default="")


# ---------------------------------------------------------------- notes / knowledge base


class Note(Base, TimestampMixin):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str | None] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"), index=True)
    # 'lesson' | 'research' | 'concept' | 'snippet' | 'spec' | 'mistake' | 'bookmark'
    kind: Mapped[str] = mapped_column(String(20), default="research")
    title: Mapped[str] = mapped_column(String(300))
    body_markdown: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    # Set when AI produced the draft; user must explicitly accept.
    ai_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (Index("ix_notes_owner_kind", "owner_id", "kind"),)


class Concept(Base, TimestampMixin):
    """Personal glossary: searchable concept definitions."""

    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    term: Mapped[str] = mapped_column(String(200))
    definition: Mapped[str] = mapped_column(Text)
    lesson_id: Mapped[str | None] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    __table_args__ = (UniqueConstraint("owner_id", "term", name="uq_concept_owner_term"),)


# ---------------------------------------------------------------- flashcards + spaced repetition


class FlashcardDeck(Base, TimestampMixin):
    __tablename__ = "flashcard_decks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str | None] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    # 'manual' | 'ai_generated' (AI decks need user acceptance before review).
    origin: Mapped[str] = mapped_column(String(20), default="manual")
    accepted: Mapped[bool] = mapped_column(Boolean, default=True)


class Flashcard(Base, TimestampMixin):
    __tablename__ = "flashcards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    deck_id: Mapped[str] = mapped_column(ForeignKey("flashcard_decks.id", ondelete="CASCADE"), index=True)
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0)


class ReviewSchedule(Base):
    """SM-2 style scheduling state per card, owned per user."""

    __tablename__ = "review_schedules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    card_id: Mapped[str] = mapped_column(ForeignKey("flashcards.id", ondelete="CASCADE"), index=True)
    ease: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[float] = mapped_column(Float, default=0.0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    due_at: Mapped[int] = mapped_column(BigInteger, default=now_ms)
    last_reviewed_at: Mapped[int | None] = mapped_column(BigInteger)
    # 'new' | 'learning' | 'review' | 'relearning'
    state: Mapped[str] = mapped_column(String(16), default="new")

    __table_args__ = (UniqueConstraint("owner_id", "card_id", name="uq_review_owner_card"),)


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    card_id: Mapped[str] = mapped_column(ForeignKey("flashcards.id", ondelete="CASCADE"), index=True)
    # user grade: 'again' | 'difficult' | 'good' | 'easy'
    grade: Mapped[str] = mapped_column(String(12))
    reviewed_at: Mapped[int] = mapped_column(BigInteger, default=now_ms)
    next_due_at: Mapped[int] = mapped_column(BigInteger)

    __table_args__ = (Index("ix_review_logs_owner_time", "owner_id", "reviewed_at"),)


# ---------------------------------------------------------------- quizzes


class QuizQuestion(Base, TimestampMixin):
    __tablename__ = "quiz_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str | None] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    # mcq | truefalse | shortanswer | code_reading | debugging | scenario | audit
    kind: Mapped[str] = mapped_column(String(24))
    prompt: Mapped[str] = mapped_column(Text)
    # For mcq: list of options; correct_index picks the right one.
    options: Mapped[list[str]] = mapped_column(JSON, default=list)
    correct_index: Mapped[int | None] = mapped_column(Integer)
    # For short answer / code questions: expected keywords or exact answer.
    accepted_answers: Mapped[list[str]] = mapped_column(JSON, default=list)
    explanation: Mapped[str] = mapped_column(Text, default="")
    source_ref: Mapped[str | None] = mapped_column(String(300))  # "Lesson §heading" or "PDF page 12"
    topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    origin: Mapped[str] = mapped_column(String(20), default="sample")  # sample|imported|ai_generated


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("quiz_questions.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)  # groups attempts into quiz runs
    given_answer: Mapped[str] = mapped_column(Text, default="")
    given_index: Mapped[int | None] = mapped_column(Integer)
    correct: Mapped[bool] = mapped_column(Boolean)
    answered_at: Mapped[int] = mapped_column(BigInteger, default=now_ms)
    topics: Mapped[list[str]] = mapped_column(JSON, default=list)

    __table_args__ = (Index("ix_quiz_attempts_owner_time", "owner_id", "answered_at"),)


class TopicMastery(Base):
    """Running accuracy per topic, updated from quiz attempts and reviews."""

    __tablename__ = "topic_mastery"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    topic: Mapped[str] = mapped_column(String(120))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    # exponential moving average 0..100
    mastery: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[int] = mapped_column(BigInteger, default=now_ms)

    __table_args__ = (UniqueConstraint("owner_id", "topic", name="uq_topic_owner"),)


# ---------------------------------------------------------------- coding labs


class CodingExercise(Base, TimestampMixin):
    __tablename__ = "coding_exercises"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str | None] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"), index=True)
    language: Mapped[str] = mapped_column(String(16))  # pine | python | bash | json
    title: Mapped[str] = mapped_column(String(300))
    requirement: Mapped[str] = mapped_column(Text)  # original requirement text
    starter_code: Mapped[str] = mapped_column(Text, default="")
    reference_solution: Mapped[str] = mapped_column(Text, default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    # Static checks: list of {kind, pattern, message, level} run in the browser/worker.
    checks: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    expected_behavior: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, default=0)


class ExerciseSubmission(Base, TimestampMixin):
    __tablename__ = "exercise_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[str] = mapped_column(ForeignKey("coding_exercises.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(Text)
    # Result of static checks / sandboxed run; never claims profitability.
    result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)


# ---------------------------------------------------------------- projects


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    key: Mapped[str] = mapped_column(String(4))  # A..J
    title: Mapped[str] = mapped_column(String(300))
    objectives: Mapped[list[str]] = mapped_column(JSON, default=list)
    prerequisites: Mapped[list[str]] = mapped_column(JSON, default=list)
    steps: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    required_files: Mapped[list[str]] = mapped_column(JSON, default=list)
    example_inputs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    expected_outputs: Mapped[str] = mapped_column(Text, default="")
    acceptance_tests: Mapped[list[str]] = mapped_column(JSON, default=list)
    failure_scenarios: Mapped[list[str]] = mapped_column(JSON, default=list)
    security_checks: Mapped[list[str]] = mapped_column(JSON, default=list)
    completion_criteria: Mapped[list[str]] = mapped_column(JSON, default=list)
    final_assessment: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="not_started")  # not_started|in_progress|done
    # 'sample' content is labeled example material, not course material.
    origin: Mapped[str] = mapped_column(String(20), default="sample")

    __table_args__ = (UniqueConstraint("owner_id", "key", name="uq_project_owner_key"),)


class ProjectMilestone(Base, TimestampMixin):
    __tablename__ = "project_milestones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    detail: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_at: Mapped[int | None] = mapped_column(BigInteger)


# ---------------------------------------------------------------- uploads


class UploadedFile(Base, TimestampMixin):
    """Private, owner-scoped file storage metadata. Bytes live on disk."""

    __tablename__ = "uploaded_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(400))
    mime_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    # Relative path under upload_dir; never exposed to clients directly.
    storage_path: Mapped[str] = mapped_column(String(600))
    kind: Mapped[str] = mapped_column(String(20), default="other")  # pdf|image|code|other
    indexed: Mapped[bool] = mapped_column(Boolean, default=False)


# ---------------------------------------------------------------- AI tutor


class TutorSession(Base, TimestampMixin):
    __tablename__ = "tutor_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str | None] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(300), default="New session")


class TutorMessage(Base):
    __tablename__ = "tutor_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("tutor_sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(12))  # user|assistant|system
    content: Mapped[str] = mapped_column(Text)
    # Citations: [{"lesson": "...", "locator": "§heading or page 12", "excerpt": "..."}]
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    # True when the answer included knowledge beyond the provided sources.
    includes_external_knowledge: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[int] = mapped_column(BigInteger, default=now_ms)


# ---------------------------------------------------------------- study sessions / audit


class StudySession(Base):
    """One recorded study activity (quiz run, flashcard review burst, lesson time)."""

    __tablename__ = "study_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # quiz | flashcards | lesson | match (kept generic on purpose)
    kind: Mapped[str] = mapped_column(String(16))
    lesson_id: Mapped[str | None] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"))
    score: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[int] = mapped_column(BigInteger, default=now_ms)

    __table_args__ = (Index("ix_study_sessions_owner_time", "owner_id", "created_at"),)


class StudyTimeLog(Base):
    """Daily study-time buckets for the dashboard heatmap."""

    __tablename__ = "study_time_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    day: Mapped[str] = mapped_column(String(10))  # YYYY-MM-DD in user's timezone
    seconds: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (UniqueConstraint("owner_id", "day", name="uq_time_owner_day"),)


class AuditEvent(Base):
    """Application audit trail: security-relevant and user-visible actions."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    action: Mapped[str] = mapped_column(String(80))  # e.g. login, note.overwrite, export
    entity: Mapped[str | None] = mapped_column(String(80))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    at: Mapped[int] = mapped_column(BigInteger, default=now_ms)

    __table_args__ = (Index("ix_audit_owner_time", "owner_id", "at"),)
