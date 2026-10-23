"""Install the sample curriculum, quiz questions, labs and projects for a user.

Idempotent: re-running does not duplicate content. Sample material is labeled
`content_status="sample"` / `origin="sample"` so the app can show it as example
content rather than course material.

Usage:
    python -m app.seed --email you@example.com          # seed if not present
    python -m app.seed --email you@example.com --reset  # wipe and re-seed
"""

from __future__ import annotations

import argparse
import uuid

from sqlalchemy import delete, select

from .db import new_session
from .models import (
    CodingExercise,
    Course,
    Flashcard,
    FlashcardDeck,
    Lesson,
    Module,
    Project,
    ProjectMilestone,
    QuizQuestion,
    ReviewSchedule,
    now_ms,
)
from fixtures.curriculum import COURSE, MODULES
from fixtures.labs import EXERCISES
from fixtures.projects import PROJECTS
from fixtures.questions import QUESTIONS

# Start-of-course flashcards: front/back pairs keyed by lesson slug.
STARTER_CARDS: dict[str, list[tuple[str, str]]] = {
    "orders-and-the-book": [
        ("Best bid / best ask", "Highest buy price and lowest sell price resting in the book."),
        ("Spread", "ask − bid. The implicit cost of crossing the book once."),
        ("Market impact", "Price movement caused by your own order consuming depth."),
    ],
    "slippage-fees-and-the-cost-of-getting-in": [
        ("Three sources of slippage", "Spread (you crossed it), impact (your size moved the book), timing (price moved before your fill)."),
        ("Why sweep costs", "Running the same backtest at 1x, 2x and 3x cost shows whether an idea is fragile."),
    ],
    "survivorship-bias": [
        ("Survivorship bias", "Testing only on symbols that still exist, which drops the worst performers and inflates results."),
        ("Best fix for survivorship bias", "Point-in-time membership data; second best is including delisted symbols."),
    ],
    "position-sizing-and-risk-of-ruin": [
        ("Fixed-fractional sizing", "units = (equity × risk_per_trade) / |entry − stop|"),
        ("Risk of ruin vs bet size", "Ruin falls exponentially as the bet fraction shrinks."),
    ],
    "drawdown-math-and-psychology": [
        ("Recovery from a 50% drawdown", "Requires a 100% gain to return to the original equity."),
        ("Circuit breakers", "Daily loss limit, drawdown-based size cut, and a consecutive-loss review trigger."),
    ],
    "repainting-and-lookahead": [
        ("Repainting", "A script that revises values or signals for bars that already closed."),
        ("Lookahead bias", "Using information that was not yet known at the decision time."),
        ("Non-repainting request.security", "Use an explicit lookahead setting together with a shifted callee series."),
    ],
    "train-validate-test": [
        ("Walk-forward evaluation", "Rolling train/test windows refit in sequence, concatenated into an out-of-sample curve."),
        ("Purge and embargo", "Remove overlapping rows between windows and gap by at least the label horizon."),
    ],
    "overfitting-and-degrees-of-freedom": [
        ("Degree of freedom", "Every parameter tuned, filter added, or regime excluded is one chance for the data to cooperate by accident."),
        ("Robust vs fitted", "Robust ideas show a broad plateau under ±20% parameter perturbation; fitted noise shows a sharp peak."),
    ],
}


def _slugify(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in text.strip()]
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:280] or "item"


def _reset(db, user_id: str) -> None:
    """Remove all curriculum content for a user (keeps notes, attempts, reviews)."""
    for model in (
        QuizQuestion,
        Flashcard,
        FlashcardDeck,
        CodingExercise,
        ProjectMilestone,
        Project,
        Lesson,
        Module,
        Course,
    ):
        db.execute(delete(model).where(model.owner_id == user_id))


def seed_curriculum(db, user_id: str, reset: bool = False) -> dict[str, int]:
    """Populate one user's account. Returns a count summary."""
    existing = db.execute(
        select(Course).where(Course.owner_id == user_id, Course.slug == COURSE["slug"])
    ).scalar_one_or_none()
    if existing and not reset:
        return {"skipped": 1, "course": 0, "modules": 0, "lessons": 0, "questions": 0, "exercises": 0, "projects": 0, "cards": 0}
    if existing and reset:
        _reset(db, user_id)

    counts = {"modules": 0, "lessons": 0, "questions": 0, "exercises": 0, "projects": 0, "cards": 0}

    course = Course(
        id=str(uuid.uuid4()),
        owner_id=user_id,
        title=COURSE["title"],
        slug=COURSE["slug"],
        description=COURSE["description"],
        position=0,
    )
    db.add(course)
    db.flush()

    # lesson slug -> lesson id, so questions can attach to their lesson.
    lesson_ids: dict[str, str] = {}

    position = 0
    for module_spec in MODULES:
        module = Module(
            id=str(uuid.uuid4()),
            owner_id=user_id,
            course_id=course.id,
            number=module_spec["number"],
            title=module_spec["title"],
            slug=module_spec["slug"],
            summary=module_spec["summary"],
            position=module_spec["number"],
        )
        db.add(module)
        db.flush()
        counts["modules"] += 1

        for lesson_position, lesson_spec in enumerate(module_spec["lessons"]):
            lesson = Lesson(
                id=str(uuid.uuid4()),
                owner_id=user_id,
                module_id=module.id,
                title=lesson_spec["title"],
                slug=lesson_spec["slug"],
                # Labeled sample content, per the content policy for this app.
                content_status="sample",
                verify_flag=False,
                summary=lesson_spec["summary"],
                body_markdown=lesson_spec["body"],
                topics=lesson_spec["topics"],
                difficulty=lesson_spec["difficulty"],
                estimated_minutes=lesson_spec["minutes"],
                position=position,
            )
            db.add(lesson)
            db.flush()
            lesson_ids[lesson_spec["slug"]] = lesson.id
            counts["lessons"] += 1
            position += 1

    for lesson_slug, q in QUESTIONS:
        lesson_id = lesson_ids.get(lesson_slug)
        if not lesson_id:
            continue
        db.add(
            QuizQuestion(
                id=str(uuid.uuid4()),
                owner_id=user_id,
                lesson_id=lesson_id,
                kind=q["kind"],
                prompt=q["prompt"],
                options=q.get("options", []),
                correct_index=q.get("correct_index"),
                accepted_answers=q.get("accepted_answers", []),
                explanation=q.get("explanation", ""),
                source_ref=q.get("source_ref"),
                topics=q.get("topics", []),
                origin="sample",
            )
        )
        counts["questions"] += 1

    for position, ex in enumerate(EXERCISES):
        db.add(
            CodingExercise(
                id=str(uuid.uuid4()),
                owner_id=user_id,
                lesson_id=None,
                language=ex["language"],
                title=ex["title"],
                requirement=ex["requirement"],
                starter_code=ex["starter_code"],
                reference_solution=ex.get("reference_solution", ""),
                explanation=ex["explanation"],
                checks=ex["checks"],
                expected_behavior=ex["expected_behavior"],
                position=position,
            )
        )
        counts["exercises"] += 1

    for p in PROJECTS:
        project = Project(
            id=str(uuid.uuid4()),
            owner_id=user_id,
            key=p["key"],
            title=p["title"],
            objectives=p["objectives"],
            prerequisites=p["prerequisites"],
            steps=p["steps"],
            required_files=p["required_files"],
            example_inputs=p["example_inputs"],
            expected_outputs=p["expected_outputs"],
            acceptance_tests=p["acceptance_tests"],
            failure_scenarios=p["failure_scenarios"],
            security_checks=p["security_checks"],
            completion_criteria=p["completion_criteria"],
            final_assessment=p["final_assessment"],
            status="not_started",
            origin="sample",
        )
        db.add(project)
        db.flush()
        counts["projects"] += 1
        for i, step in enumerate(p["steps"]):
            db.add(
                ProjectMilestone(
                    id=str(uuid.uuid4()),
                    owner_id=user_id,
                    project_id=project.id,
                    title=step["title"],
                    detail=step["detail"],
                    position=i,
                    done=False,
                )
            )

    # One starter flashcard deck so the review queue is not empty on day one.
    deck = FlashcardDeck(
        id=str(uuid.uuid4()),
        owner_id=user_id,
        title="Foundations — starter deck",
        origin="manual",
        accepted=True,
    )
    db.add(deck)
    db.flush()
    for slug, cards in STARTER_CARDS.items():
        if slug not in lesson_ids:
            continue
        for i, (front, back) in enumerate(cards):
            card = Flashcard(
                id=str(uuid.uuid4()),
                owner_id=user_id,
                deck_id=deck.id,
                front=front,
                back=back,
                position=counts["cards"] + i,
            )
            db.add(card)
            db.flush()
            # Due immediately so the queue has something to review.
            db.add(
                ReviewSchedule(
                    id=str(uuid.uuid4()),
                    owner_id=user_id,
                    card_id=card.id,
                    due_at=now_ms(),
                    state="new",
                )
            )
            counts["cards"] += 1

    db.commit()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the sample curriculum for an account.")
    parser.add_argument("--email", required=True, help="Email of the account to seed.")
    parser.add_argument("--reset", action="store_true", help="Wipe and re-seed curriculum content.")
    args = parser.parse_args()

    from .models import User

    db = new_session()
    try:
        user = db.execute(select(User).where(User.email == args.email.lower().strip())).scalar_one_or_none()
        if not user:
            raise SystemExit(f"No account found for {args.email}. Register in the app first.")
        summary = seed_curriculum(db, user.id, reset=args.reset)
        print(f"Seeded curriculum for {user.email}: {summary}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
