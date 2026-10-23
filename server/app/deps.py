"""Shared request dependencies: current user, session cookie, CSRF, ownership."""

from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Response

from .config import get_settings
from .db import new_session
from .models import AuthSession, User, now_ms
from .security import is_same_origin_mutation, token_digest

SESSION_COOKIE = "study_session"


def _load_user(token: str | None) -> User | None:
    if not token:
        return None
    db = new_session()
    try:
        row = db.execute(
            AuthSession.__table__.select().where(
                AuthSession.token_hash == token_digest(token),
                AuthSession.expires_at > now_ms(),
            )
        ).first()
        if not row:
            return None
        user = db.get(User, row.user_id)
        if not user or not user.is_active:
            return None
        # Detach a plain copy so the caller can use it after this session closes.
        db.expunge(user)
        return user
    finally:
        db.close()


def current_user(
    session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> User:
    user = _load_user(session)
    if not user:
        raise HTTPException(status_code=401, detail="Sign in required.")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def same_origin(
    origin: Annotated[str | None, Header()] = None,
    referer: Annotated[str | None, Header()] = None,
) -> None:
    """CSRF check for mutations; applied by routers on write endpoints."""
    settings = get_settings()
    if not is_same_origin_mutation(origin, referer, settings.app_origin):
        raise HTTPException(status_code=403, detail="Cross-origin request refused.")


SameOrigin = Annotated[None, Depends(same_origin)]


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    secure = settings.app_origin.startswith("https://")
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_ttl_days * 86_400,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


def owner_filter(model, user: User):
    """Every query in this app is scoped to the signed-in owner."""
    return model.owner_id == user.id
