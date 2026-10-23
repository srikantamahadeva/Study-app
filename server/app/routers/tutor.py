"""AI tutor: source-grounded answers with citations over uploaded material.

Provider-independent OpenAI-compatible adapter. Without an API key the tutor
reports 'not configured' and never pretends to answer. Answers must cite the
lesson/page/section used; external knowledge is flagged separately.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select

from ..config import get_settings
from ..db import new_session
from ..deps import CurrentUser, SameOrigin
from ..models import Lesson, LessonResource, Note, TutorMessage, TutorSession, TranscriptChunk

router = APIRouter()

SYSTEM_PROMPT = """You are a study tutor inside a personal algorithmic-trading learning app.
The app is EDUCATION AND RESEARCH ONLY: it never places orders and has no trading credentials.

Rules you must follow:
1. Answer primarily from the SOURCE MATERIAL provided in the user message. Quote or paraphrase it closely.
2. After the answer, list citations: the exact source labels given (lesson titles, page numbers, section names).
3. If the sources do not contain the answer, say "Not covered in your uploaded material." first, then optionally add general knowledge clearly marked as [External knowledge].
4. Never claim code compiles, a strategy is profitable, or a backtest guarantees future results.
5. If asked to place trades, give orders, or use credentials: refuse and explain this app does not do that.
6. Be concise and pedagogical: short paragraphs, plain language, one worked example when helpful.
"""


class AskIn(BaseModel):
    sessionId: str | None = None
    lessonId: str | None = None
    question: str = Field(min_length=1, max_length=8000)


class ChatIn(BaseModel):
    sessionId: str
    message: str = Field(min_length=1, max_length=8000)


def _gather_context(db, user_id: str, question: str, lesson_id: str | None, limit_chars: int) -> list[dict]:
    """Keyword retrieval over lessons, notes and extracted document text."""
    terms = [t for t in _keywords(question)][:12]
    chunks: list[dict] = []

    def score(text: str) -> int:
        low = text.lower()
        return sum(low.count(t) for t in terms)

    lessons = db.execute(select(Lesson).where(Lesson.owner_id == user_id)).scalars().all()
    if lesson_id:
        lessons = [l for l in lessons if l.id == lesson_id] or lessons
    for lesson in lessons:
        text = f"{lesson.title}\n{lesson.summary}\n{lesson.body_markdown}"
        s = score(text) + (5 if lesson_id == lesson.id else 0)
        if s > 0:
            chunks.append((s, {"label": f"Lesson: {lesson.title}", "locator": lesson.summary[:120], "text": text[:6000]}))

    for note in db.execute(select(Note).where(Note.owner_id == user_id)).scalars():
        text = f"{note.title}\n{note.body_markdown}"
        s = score(text)
        if s > 0:
            chunks.append((s, {"label": f"Note: {note.title}", "locator": "personal note", "text": text[:4000]}))

    for row in db.execute(select(TranscriptChunk).where(TranscriptChunk.owner_id == user_id)).scalars():
        s = score(row.text)
        if s > 0:
            label = "Uploaded document"
            if row.resource_id:
                res = db.get(LessonResource, row.resource_id)
                if res:
                    label = res.title
            chunks.append((s, {"label": label, "locator": row.locator or "", "text": row.text[:4000]}))

    chunks.sort(key=lambda x: -x[0])
    picked: list[dict] = []
    used = 0
    for _, c in chunks:
        if used + len(c["text"]) > limit_chars:
            continue
        picked.append(c)
        used += len(c["text"])
        if len(picked) >= 8:
            break
    return picked


def _keywords(question: str) -> list[str]:
    stop = {
        "the", "a", "an", "is", "are", "was", "were", "what", "how", "why", "when", "does", "do",
        "explain", "me", "my", "i", "this", "that", "it", "to", "of", "in", "on", "for", "and",
        "or", "with", "about", "please", "can", "you", "your", "from", "be", "as", "at", "by",
    }
    import re

    words = re.findall(r"[a-z0-9_]+", question.lower())
    return [w for w in words if len(w) > 2 and w not in stop]


async def _call_llm(messages: list[dict]) -> tuple[str, bool]:
    """Call the configured OpenAI-compatible endpoint. Returns (content, external_flag)."""
    import httpx

    settings = get_settings()
    if not settings.ai_configured:
        raise HTTPException(status_code=503, detail="AI tutor is not configured. Set the AI API key in the environment.")

    payload = {
        "model": settings.ai_model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
        "temperature": 0.2,
        "max_tokens": 1200,
    }
    headers = {"Authorization": f"Bearer {settings.ai_api_key}"}
    try:
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            resp = await client.post(f"{settings.ai_base_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error ({exc.response.status_code}).")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"AI provider unreachable: {type(exc).__name__}.")

    content = data["choices"][0]["message"]["content"] if data.get("choices") else ""
    external = "[External knowledge]" in content or "external knowledge" in content.lower()
    return content, external


def _extract_citations(answer: str, context: list[dict]) -> list[dict]:
    citations = []
    for c in context:
        if c["label"].split(":")[-1].strip().lower() in answer.lower() or (c.get("locator") and str(c["locator"]).lower() in answer.lower()):
            citations.append({"lesson": c["label"], "locator": c["locator"], "excerpt": c["text"][:300]})
    return citations[:6]


@router.get("/status")
def status(user: CurrentUser):
    settings = get_settings()
    return {"configured": settings.ai_configured, "model": settings.ai_model if settings.ai_configured else None}


@router.get("/sessions")
def sessions(user: CurrentUser):
    db = new_session()
    try:
        rows = db.execute(
            select(TutorSession).where(TutorSession.owner_id == user.id).order_by(TutorSession.updated_at.desc()).limit(50)
        ).scalars()
        return {
            "items": [
                {"id": s.id, "title": s.title, "lessonId": s.lesson_id, "updatedAt": s.updated_at}
                for s in rows
            ]
        }
    finally:
        db.close()


@router.post("/sessions")
def create_session(user: CurrentUser, _: SameOrigin, payload: AskIn | None = None):
    db = new_session()
    try:
        s = TutorSession(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            lesson_id=(payload.lessonId if payload else None),
            title=(payload.question[:80] if payload and payload.question else "New session"),
        )
        db.add(s)
        db.commit()
        return {"id": s.id, "title": s.title}
    finally:
        db.close()


@router.get("/sessions/{session_id}")
def get_session(session_id: str, user: CurrentUser):
    db = new_session()
    try:
        s = db.execute(
            select(TutorSession).where(TutorSession.id == session_id, TutorSession.owner_id == user.id)
        ).scalar_one_or_none()
        if not s:
            raise HTTPException(status_code=404, detail="Session not found.")
        messages = db.execute(
            select(TutorMessage).where(TutorMessage.session_id == session_id).order_by(TutorMessage.created_at)
        ).scalars()
        return {
            "session": {"id": s.id, "title": s.title, "lessonId": s.lesson_id},
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "citations": m.citations,
                    "includesExternalKnowledge": m.includes_external_knowledge,
                    "createdAt": m.created_at,
                }
                for m in messages
            ],
        }
    finally:
        db.close()


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        s = db.execute(
            select(TutorSession).where(TutorSession.id == session_id, TutorSession.owner_id == user.id)
        ).scalar_one_or_none()
        if not s:
            raise HTTPException(status_code=404, detail="Session not found.")
        db.execute(delete(TutorMessage).where(TutorMessage.session_id == session_id))
        db.delete(s)
        db.commit()
        return {"ok": True}
    finally:
        db.close()


async def _respond(user, payload_question: str, session_id: str, lesson_id: str | None) -> dict:
    settings = get_settings()
    if not settings.ai_configured:
        raise HTTPException(status_code=503, detail="AI tutor is not configured. Add an API key in Settings to enable it.")

    db = new_session()
    try:
        context = _gather_context(db, user.id, payload_question, lesson_id, settings.ai_max_context_chars)
        history = db.execute(
            select(TutorMessage)
            .where(TutorMessage.session_id == session_id, TutorMessage.owner_id == user.id)
            .order_by(TutorMessage.created_at.desc())
            .limit(10)
        ).scalars().all()
        history = list(reversed(history))

        source_block = "\n\n".join(
            f"[Source {i + 1}: {c['label']}{(' | ' + str(c['locator'])) if c.get('locator') else ''}]\n{c['text']}"
            for i, c in enumerate(context)
        ) or "(no matching source material found for this question)"

        user_message = (
            f"SOURCE MATERIAL:\n{source_block}\n\n"
            f"QUESTION: {payload_question}\n\n"
            "Answer using the source material. Cite the source labels you used. "
            "If not covered, say so, then mark anything extra as [External knowledge]."
        )
        messages = [{"role": m.role, "content": m.content} for m in history if m.role in ("user", "assistant")]
        messages.append({"role": "user", "content": user_message})

        answer, external = await _call_llm(messages)
        citations = _extract_citations(answer, context)

        assistant_row = TutorMessage(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            session_id=session_id,
            role="assistant",
            content=answer,
            citations=citations,
            includes_external_knowledge=external,
        )
        db.add(assistant_row)
        session = db.get(TutorSession, session_id)
        if session and session.title == "New session":
            session.title = payload_question[:80]
        db.commit()
        return {
            "id": assistant_row.id,
            "role": "assistant",
            "content": answer,
            "citations": citations,
            "includesExternalKnowledge": external,
            "createdAt": assistant_row.created_at,
        }
    finally:
        db.close()


@router.post("/ask")
async def ask(payload: AskIn, user: CurrentUser, _: SameOrigin):
    """One-off question (auto-creates a session)."""
    db = new_session()
    try:
        session = TutorSession(
            id=payload.sessionId or str(uuid.uuid4()),
            owner_id=user.id,
            lesson_id=payload.lessonId,
            title=payload.question[:80],
        )
        existing = None
        if payload.sessionId:
            existing = db.execute(
                select(TutorSession).where(TutorSession.id == payload.sessionId, TutorSession.owner_id == user.id)
            ).scalar_one_or_none()
        if not existing:
            db.add(session)
            # Flush before the message insert: without relationship() metadata
            # SQLAlchemy cannot order these, and the FK would fire early.
            db.flush()
            session_id = session.id
        else:
            session_id = existing.id
        db.add(
            TutorMessage(
                id=str(uuid.uuid4()),
                owner_id=user.id,
                session_id=session_id,
                role="user",
                content=payload.question,
            )
        )
        db.commit()
    finally:
        db.close()

    reply = await _respond(user, payload.question, session_id, payload.lessonId)
    return {"sessionId": session_id, "reply": reply}


@router.post("/chat")
async def chat(payload: ChatIn, user: CurrentUser, _: SameOrigin):
    """Follow-up message in an existing session."""
    db = new_session()
    try:
        session = db.execute(
            select(TutorSession).where(TutorSession.id == payload.sessionId, TutorSession.owner_id == user.id)
        ).scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found.")
        db.add(
            TutorMessage(
                id=str(uuid.uuid4()),
                owner_id=user.id,
                session_id=session.id,
                role="user",
                content=payload.message,
            )
        )
        db.commit()
        lesson_id = session.lesson_id
    finally:
        db.close()
    reply = await _respond(user, payload.message, payload.sessionId, lesson_id)
    return {"reply": reply}
