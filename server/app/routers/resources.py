"""Resource library: private uploads, PDF extraction, listing, download."""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..config import get_settings
from ..db import new_session
from ..deps import CurrentUser, SameOrigin
from ..models import LessonResource, TranscriptChunk, UploadedFile, now_ms

router = APIRouter()

ALLOWED_MIME = {
    "application/pdf": "pdf",
    "image/png": "image",
    "image/jpeg": "image",
    "image/webp": "image",
    "image/gif": "image",
    "text/plain": "code",
    "text/markdown": "code",
    "text/x-python": "code",
    "text/x-script.python": "code",
    "application/javascript": "code",
    "text/javascript": "code",
    "text/x-pine": "code",
    "application/json": "code",
    "text/csv": "code",
    "application/octet-stream": "other",
}


def _safe_name(name: str) -> str:
    name = os.path.basename(name or "file")
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name)[:200]
    return name or "file"


def _upload_root(owner_id: str) -> Path:
    root = Path(get_settings().upload_dir) / owner_id
    root.mkdir(parents=True, exist_ok=True)
    return root


@router.get("")
def list_resources(user: CurrentUser, kind: str | None = None, tag: str | None = None):
    db = new_session()
    try:
        stmt = select(LessonResource).where(LessonResource.owner_id == user.id)
        if kind:
            stmt = stmt.where(LessonResource.kind == kind)
        items = db.execute(stmt.order_by(LessonResource.updated_at.desc())).scalars().all()
        out = []
        for r in items:
            if tag and tag not in (r.tags or []):
                continue
            out.append(
                {
                    "id": r.id,
                    "kind": r.kind,
                    "title": r.title,
                    "url": r.url,
                    "fileId": r.file_id,
                    "mimeType": r.mime_type,
                    "tags": r.tags,
                    "lessonId": r.lesson_id,
                    "contentPreview": (r.content or "")[:200],
                    "hasFile": bool(r.file_id),
                    "createdAt": r.created_at,
                }
            )
        return {"items": out}
    finally:
        db.close()


@router.post("/upload")
async def upload_file(
    user: CurrentUser,
    _: SameOrigin,
    file: UploadFile = File(...),
    title: str = Form(default=""),
    lessonId: str | None = Form(default=None),
    tags: str = Form(default=""),
):
    """Store a file privately; extract PDF text for search and the tutor."""
    settings = get_settings()
    file_id = str(uuid.uuid4())
    filename = _safe_name(file.filename or "file")
    mime = (file.content_type or "application/octet-stream").split(";")[0].strip()
    kind = ALLOWED_MIME.get(mime, "other")

    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB limit.")

    root = _upload_root(user.id)
    storage_rel = f"{user.id}/{file_id}_{filename}"
    storage_abs = Path(settings.upload_dir) / storage_rel
    storage_abs.write_bytes(data)

    db = new_session()
    try:
        row = UploadedFile(
            id=file_id,
            owner_id=user.id,
            filename=filename,
            mime_type=mime,
            size_bytes=len(data),
            storage_path=storage_rel,
            kind=kind,
        )
        db.add(row)

        resource = LessonResource(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            lesson_id=lessonId or None,
            kind=kind if kind in ("pdf", "image", "code") else "note",
            title=(title.strip()[:300] if title.strip() else filename),
            file_id=file_id,
            mime_type=mime,
            tags=[t.strip()[:40] for t in tags.split(",") if t.strip()][:20],
        )
        db.add(resource)
        db.flush()

        extracted = 0
        if kind == "pdf":
            extracted = _index_pdf(db, user.id, file_id, resource.id, data)
        elif kind == "code" and len(data) < 400_000:
            text = data.decode("utf-8", errors="replace")
            db.add(
                TranscriptChunk(
                    id=str(uuid.uuid4()),
                    owner_id=user.id,
                    resource_id=resource.id,
                    locator="file",
                    text=text[:200_000],
                )
            )
            extracted = 1
        row.indexed = extracted > 0
        db.commit()
        return {
            "id": resource.id,
            "fileId": file_id,
            "title": resource.title,
            "kind": resource.kind,
            "indexed": extracted > 0,
            "chunks": extracted,
        }
    except Exception:
        # Never leave a dangling file if the row failed.
        try:
            storage_abs.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    finally:
        db.close()


def _index_pdf(db, owner_id: str, file_id: str, resource_id: str, data: bytes) -> int:
    import io

    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception:
        return 0
    count = 0
    for i, page in enumerate(reader.pages[:500]):
        try:
            text = (page.extract_text() or "").strip()
        except Exception:
            text = ""
        if text:
            db.add(
                TranscriptChunk(
                    id=str(uuid.uuid4()),
                    owner_id=owner_id,
                    resource_id=resource_id,
                    locator=f"page {i + 1}",
                    text=text[:20_000],
                )
            )
            count += 1
    return count


@router.get("/{resource_id}/file")
def download(resource_id: str, user: CurrentUser):
    """Owner-only file access; storage paths are never exposed to clients."""
    from fastapi.responses import FileResponse

    db = new_session()
    try:
        row = db.execute(
            select(UploadedFile).join(LessonResource, LessonResource.file_id == UploadedFile.id)
            .where(LessonResource.id == resource_id, UploadedFile.owner_id == user.id)
        ).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="File not found.")
        path = Path(get_settings().upload_dir) / row.storage_path
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Stored file missing.")
        return FileResponse(path, media_type=row.mime_type, filename=row.filename, headers={"Cache-Control": "private, max-age=60"})
    finally:
        db.close()


class ResourcePatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    tags: list[str] | None = Field(default=None, max_length=20)
    lessonId: str | None = None


@router.patch("/{resource_id}")
def update_resource(resource_id: str, payload: ResourcePatch, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        row = db.execute(
            select(LessonResource).where(LessonResource.id == resource_id, LessonResource.owner_id == user.id)
        ).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Resource not found.")
        if payload.title is not None:
            row.title = payload.title.strip()[:300]
        if payload.tags is not None:
            row.tags = [t.strip()[:40] for t in payload.tags if t.strip()][:20]
        if payload.lessonId is not None:
            row.lesson_id = payload.lessonId or None
        row.updated_at = now_ms()
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.delete("/{resource_id}")
def delete_resource(resource_id: str, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        row = db.execute(
            select(LessonResource).where(LessonResource.id == resource_id, LessonResource.owner_id == user.id)
        ).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Resource not found.")
        if row.file_id:
            file_row = db.get(UploadedFile, row.file_id)
            if file_row and file_row.owner_id == user.id:
                path = Path(get_settings().upload_dir) / file_row.storage_path
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
                db.delete(file_row)
        # Remove extracted chunks belonging to this resource.
        for chunk in db.execute(select(TranscriptChunk).where(TranscriptChunk.resource_id == resource_id)).scalars():
            db.delete(chunk)
        db.delete(row)
        db.commit()
        return {"ok": True}
    finally:
        db.close()
