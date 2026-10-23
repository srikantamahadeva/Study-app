"""Global search across lessons, notes, concepts, flashcards, projects, documents."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import select

from ..config import get_settings
from ..db import new_session
from ..deps import CurrentUser
from ..models import Concept, Flashcard, FlashcardDeck, Lesson, Note, Project, QuizQuestion, TranscriptChunk

router = APIRouter()


def _excerpt(text: str, terms: list[str], width: int = 160) -> str:
    low = text.lower()
    pos = -1
    for t in terms:
        i = low.find(t)
        if i >= 0 and (pos < 0 or i < pos):
            pos = i
    if pos < 0:
        pos = 0
    start = max(0, pos - width // 3)
    snippet = text[start : start + width].replace("\n", " ").strip()
    prefix = "…" if start > 0 else ""
    suffix = "…" if start + width < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


@router.get("")
def search(user: CurrentUser, q: str = Query(min_length=1, max_length=200)):
    import re

    terms = [t for t in re.findall(r"[a-z0-9_]+", q.lower()) if len(t) > 1][:8]
    if not terms:
        return {"items": [], "total": 0}

    def matches(*fields: str) -> int:
        low = " ".join(f or "" for f in fields).lower()
        return sum(low.count(t) for t in terms)

    results: list[dict] = []
    limit = 40

    db = new_session()
    try:
        for lesson in db.execute(select(Lesson).where(Lesson.owner_id == user.id)).scalars():
            score = matches(lesson.title, lesson.summary, lesson.body_markdown)
            if score:
                results.append(
                    {
                        "type": "lesson",
                        "id": lesson.id,
                        "title": lesson.title,
                        "excerpt": _excerpt(lesson.body_markdown or lesson.summary or lesson.title, terms),
                        "score": score * 2,
                        "href": f"/lessons/{lesson.id}",
                    }
                )

        for note in db.execute(select(Note).where(Note.owner_id == user.id)).scalars():
            score = matches(note.title, note.body_markdown, " ".join(note.tags or []))
            if score:
                results.append(
                    {
                        "type": "note",
                        "id": note.id,
                        "title": note.title,
                        "excerpt": _excerpt(note.body_markdown or note.title, terms),
                        "score": score * 2,
                        "href": f"/notes?open={note.id}",
                    }
                )

        for c in db.execute(select(Concept).where(Concept.owner_id == user.id)).scalars():
            score = matches(c.term, c.definition)
            if score:
                results.append(
                    {
                        "type": "concept",
                        "id": c.id,
                        "title": c.term,
                        "excerpt": _excerpt(c.definition, terms),
                        "score": score * 2,
                        "href": "/notes?tab=concepts",
                    }
                )

        for card in db.execute(select(Flashcard).where(Flashcard.owner_id == user.id)).scalars():
            score = matches(card.front, card.back)
            if score:
                results.append(
                    {
                        "type": "flashcard",
                        "id": card.id,
                        "title": card.front[:80],
                        "excerpt": _excerpt(card.back, terms),
                        "score": score,
                        "href": f"/flashcards?deck={card.deck_id}",
                    }
                )

        for q_ in db.execute(select(QuizQuestion).where(QuizQuestion.owner_id == user.id)).scalars():
            score = matches(q_.prompt, q_.explanation)
            if score:
                results.append(
                    {
                        "type": "quiz",
                        "id": q_.id,
                        "title": _excerpt(q_.prompt, terms, 100),
                        "excerpt": _excerpt(q_.explanation or q_.prompt, terms),
                        "score": score,
                        "href": "/quiz",
                    }
                )

        for p in db.execute(select(Project).where(Project.owner_id == user.id)).scalars():
            score = matches(p.title, " ".join(p.objectives or []))
            if score:
                results.append(
                    {
                        "type": "project",
                        "id": p.id,
                        "title": f"Project {p.key}: {p.title}",
                        "excerpt": _excerpt(" ".join(p.objectives or []) or p.title, terms),
                        "score": score,
                        "href": f"/projects/{p.id}",
                    }
                )

        # Extracted document text (PDF pages, uploaded code) — highest-value hits.
        for row in db.execute(select(TranscriptChunk).where(TranscriptChunk.owner_id == user.id)).scalars():
            score = matches(row.text)
            if score:
                label = "Uploaded document"
                if row.resource_id:
                    from ..models import LessonResource

                    res = db.get(LessonResource, row.resource_id)
                    if res:
                        label = res.title
                results.append(
                    {
                        "type": "document",
                        "id": row.id,
                        "title": f"{label} ({row.locator or 'file'})",
                        "excerpt": _excerpt(row.text, terms),
                        "score": score * 2,
                        "href": "/resources",
                    }
                )
    finally:
        db.close()

    results.sort(key=lambda r: -r["score"])
    return {"items": results[:limit], "total": len(results)}
