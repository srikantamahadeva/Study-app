"""Authentication: register, login, logout, session status. No secrets stored."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select

from ..config import get_settings
from ..db import new_session
from ..models import AuditEvent, AuthSession, LoginAttempt, User, now_ms
from ..security import (
    check_password_strength,
    evaluate_lockout,
    hash_password,
    new_session_token,
    needs_rehash,
    verify_password,
)
from ..deps import CurrentUser, SameOrigin, clear_session_cookie, set_session_cookie

router = APIRouter()


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)
    display_name: str = Field(min_length=1, max_length=120)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class UserOut(BaseModel):
    id: str
    email: str
    display_name: str
    timezone: str


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, display_name=user.display_name, timezone=user.timezone)


@router.post("/register", response_model=UserOut)
def register(payload: RegisterIn, response: Response, _: SameOrigin):
    error = check_password_strength(payload.password)
    if error:
        raise HTTPException(status_code=400, detail=error)
    db = new_session()
    try:
        email = payload.email.lower().strip()
        existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if existing:
            # Do not reveal whether an account exists via a different path:
            # registration is the one place we must say it plainly.
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=hash_password(payload.password),
            display_name=payload.display_name.strip()[:120],
            preferences={},
        )
        db.add(user)
        # Flush the user before its children: these models declare foreign keys
        # without relationships, so SQLAlchemy has no dependency edge to order
        # the inserts and the FK would be violated.
        db.flush()
        token, digest = new_session_token()
        settings = get_settings()
        db.add(AuthSession(token_hash=digest, user_id=user.id, expires_at=now_ms() + settings.session_ttl_days * 86_400_000))
        db.add(AuditEvent(id=str(uuid.uuid4()), owner_id=user.id, action="auth.register"))
        db.commit()
        db.expunge(user)
    finally:
        db.close()
    set_session_cookie(response, token)
    return _user_out(user)


@router.post("/login", response_model=UserOut)
def login(payload: LoginIn, request: Request, response: Response, _: SameOrigin):
    settings = get_settings()
    email = payload.email.lower().strip()
    db = new_session()
    try:
        attempts = [
            (row.at, row.success)
            for row in db.execute(
                select(LoginAttempt.at, LoginAttempt.success)
                .where(LoginAttempt.email_key == email)
                .order_by(LoginAttempt.at.desc())
                .limit(50)
            ).all()
        ]
        lockout = evaluate_lockout(attempts, settings.login_max_failures, settings.login_lockout_seconds)
        if lockout.locked:
            raise HTTPException(
                status_code=429,
                detail=f"Too many failed attempts. Try again in {lockout.retry_after_seconds}s.",
            )

        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        ok = bool(user and user.is_active and verify_password(user.password_hash, payload.password))
        db.add(LoginAttempt(email_key=email, success=ok))
        if not ok:
            db.commit()
            # Same message for unknown user and wrong password.
            raise HTTPException(status_code=401, detail="Incorrect email or password.")

        if needs_rehash(user.password_hash):
            user.password_hash = hash_password(payload.password)

        token, digest = new_session_token()
        db.add(
            AuthSession(
                token_hash=digest,
                user_id=user.id,
                expires_at=now_ms() + settings.session_ttl_days * 86_400_000,
                user_agent=(request.headers.get("user-agent") or "")[:400],
            )
        )
        db.add(AuditEvent(id=str(uuid.uuid4()), owner_id=user.id, action="auth.login"))
        db.commit()
        db.expunge(user)
    finally:
        db.close()
    set_session_cookie(response, token)
    return _user_out(user)


@router.post("/logout")
def logout(response: Response, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        # Delete all sessions for this user on logout (simple + safe).
        db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
        db.commit()
    finally:
        db.close()
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/me")
def me(user: CurrentUser):
    return _user_out(user)
