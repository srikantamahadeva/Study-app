"""Notes and knowledge base: notes, concepts/glossary. AI drafts are flagged."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select

from ..db import new_session
from ..deps import CurrentUser, SameOrigin
from ..models import AuditEvent, Concept, Note, now_ms

router = APIRouter()

NOTE_KINDS = {"lesson", "research", "concept", "snippet", "spec", "mistake", "bookmark"}


class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    bodyMarkdown: str = Field(default="", max_length=200_000)
    kind: str = Field(default="research", pattern="^(lesson|research|concept|snippet|spec|mistake|bookmark)$")
    lessonId: str | None = None
    tags: list[str] = Field(default_factory=list, max_length=30)
    isPinned: bool = False


class NotePatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    bodyMarkdown: str | None = Field(default=None, max_length=200_000)
    tags: list[str] | None = Field(default=None, max_length=30)
    isPinned: bool | None = None
    # Overwriting an existing note requires an explicit confirm from the user.
    confirmOverwrite: bool = False


def _note_out(n: Note) -> dict:
    return {
        "id": n.id,
        "kind": n.kind,
        "title": n.title,
        "bodyMarkdown": n.body_markdown,
        "lessonId": n.lesson_id,
        "tags": n.tags,
        "aiDraft": n.ai_draft,
        "isPinned": n.is_pinned,
        "createdAt": n.created_at,
        "updatedAt": n.updated_at,
    }


@router.get("")
def list_notes(
    user: CurrentUser,
    kind: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=200),
):
    db = new_session()
    try:
        stmt = select(Note).where(Note.owner_id == user.id)
        if kind:
            stmt = stmt.where(Note.kind == kind)
        if q:
            like = f"%{q.lower()}%"
            stmt = stmt.where(or_(func_lower(Note.title).like(like), func_lower(Note.body_markdown).like(like)))
        notes = db.execute(stmt.order_by(Note.is_pinned.desc(), Note.updated_at.desc())).scalars()
        return {"items": [_note_out(n) for n in notes]}
    finally:
        db.close()


def func_lower(column):
    from sqlalchemy import func

    return func.lower(column)


@router.post("")
def create_note(payload: NoteIn, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        note = Note(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            lesson_id=payload.lessonId,
            kind=payload.kind,
            title=payload.title.strip()[:300],
            body_markdown=payload.bodyMarkdown,
            tags=[t.strip()[:40] for t in payload.tags if t.strip()][:30],
            is_pinned=payload.isPinned,
        )
        db.add(note)
        db.commit()
        db.expunge(note)
        return _note_out(note)
    finally:
        db.close()


# ---------------------------------------------------------------- concepts / glossary
#
# Registered before the dynamic /{note_id} route below: FastAPI matches routes
# in registration order, and /concepts would otherwise be read as a note id.


class ConceptIn(BaseModel):
    term: str = Field(min_length=1, max_length=200)
    definition: str = Field(min_length=1, max_length=4000)
    lessonId: str | None = None
    tags: list[str] = Field(default_factory=list, max_length=20)


@router.get("/concepts")
def list_concepts(user: CurrentUser, q: str | None = Query(default=None, max_length=200)):
    db = new_session()
    try:
        stmt = select(Concept).where(Concept.owner_id == user.id)
        if q:
            like = f"%{q.lower()}%"
            stmt = stmt.where(or_(func_lower(Concept.term).like(like), func_lower(Concept.definition).like(like)))
        items = db.execute(stmt.order_by(Concept.term)).scalars()
        return {
            "items": [
                {"id": c.id, "term": c.term, "definition": c.definition, "lessonId": c.lesson_id, "tags": c.tags}
                for c in items
            ]
        }
    finally:
        db.close()


@router.post("/concepts")
def create_concept(payload: ConceptIn, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        existing = db.execute(
            select(Concept).where(Concept.owner_id == user.id, Concept.term == payload.term.strip())
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="This term already exists.")
        c = Concept(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            term=payload.term.strip()[:200],
            definition=payload.definition.strip(),
            lesson_id=payload.lessonId,
            tags=payload.tags,
        )
        db.add(c)
        db.commit()
        return {"id": c.id, "term": c.term}
    finally:
        db.close()


@router.delete("/concepts/{concept_id}")
def delete_concept(concept_id: str, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        row = db.execute(select(Concept).where(Concept.id == concept_id, Concept.owner_id == user.id)).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Concept not found.")
        db.delete(row)
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.get("/{note_id}")
def get_note(note_id: str, user: CurrentUser):
    db = new_session()
    try:
        note = db.execute(select(Note).where(Note.id == note_id, Note.owner_id == user.id)).scalar_one_or_none()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found.")
        return _note_out(note)
    finally:
        db.close()


@router.patch("/{note_id}")
def update_note(note_id: str, payload: NotePatch, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        note = db.execute(select(Note).where(Note.id == note_id, Note.owner_id == user.id)).scalar_one_or_none()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found.")
        if payload.bodyMarkdown is not None and payload.bodyMarkdown != note.body_markdown:
            # Replacing content needs an explicit confirmation (AI-draft safety rule).
            if not payload.confirmOverwrite:
                raise HTTPException(
                    status_code=409,
                    detail="Replacing existing note content requires confirmOverwrite=true.",
                )
            db.add(
                AuditEvent(
                    id=str(uuid.uuid4()),
                    owner_id=user.id,
                    action="note.overwrite",
                    entity="note",
                    entity_id=note.id,
                )
            )
        if payload.title is not None:
            note.title = payload.title.strip()[:300]
        if payload.bodyMarkdown is not None:
            note.body_markdown = payload.bodyMarkdown
        if payload.tags is not None:
            note.tags = [t.strip()[:40] for t in payload.tags if t.strip()][:30]
        if payload.isPinned is not None:
            note.is_pinned = payload.isPinned
        # Accepting/editing an AI draft clears the flag.
        note.ai_draft = False
        note.updated_at = now_ms()
        db.commit()
        db.expunge(note)
        return _note_out(note)
    finally:
        db.close()


@router.delete("/{note_id}")
def delete_note(note_id: str, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        note = db.execute(select(Note).where(Note.id == note_id, Note.owner_id == user.id)).scalar_one_or_none()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found.")
        db.delete(note)
        db.commit()
        return {"ok": True}
    finally:
        db.close()



