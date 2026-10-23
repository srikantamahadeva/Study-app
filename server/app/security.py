"""Password hashing, session tokens, lockout, and same-origin enforcement.

Passwords are hashed with Argon2id. Session tokens are random; only their
SHA-256 digest is stored. Mutations must come from the configured origin.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

_hasher = PasswordHasher(time_cost=2, memory_cost=64 * 1024, parallelism=2)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return False


def new_session_token() -> tuple[str, str]:
    """Return (plaintext token, digest to store). Token never stored raw."""
    token = secrets.token_urlsafe(32)
    return token, hashlib.sha256(token.encode()).hexdigest()


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def check_password_strength(password: str) -> str | None:
    """Return an error message if the password is too weak, else None."""
    if len(password) < 10:
        return "Password must be at least 10 characters."
    if len(password) > 200:
        return "Password must be at most 200 characters."
    return None


_SAME_ORIGIN_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def is_same_origin_mutation(origin: str | None, referer: str | None, app_origin: str) -> bool:
    """CSRF defence: mutations must arrive from our own origin.

    Allows absent Origin for non-browser clients (curl/tests) only when no
    Referer claims a foreign origin; browsers always send one of the two.
    """
    allowed = app_origin.rstrip("/")
    if origin:
        return origin.rstrip("/") == allowed
    if referer:
        return referer.rstrip("/").startswith(allowed)
    return True


@dataclass
class LockoutState:
    locked: bool
    failures: int
    retry_after_seconds: int


def evaluate_lockout(attempts: list[tuple[int, bool]], max_failures: int, lockout_seconds: int, now: int | None = None) -> LockoutState:
    """Decide whether an email is temporarily locked after failed logins.

    `attempts` is [(timestamp_ms, success), ...] newest first for one email.
    A success anywhere in the window clears the lock.
    """
    now = now if now is not None else int(time.time() * 1000)
    window_start = now - lockout_seconds * 1000
    failures = 0
    for at, success in attempts:
        if success:
            break  # a success resets the streak
        if at >= window_start:
            failures += 1
    if failures >= max_failures:
        oldest = attempts[-1][0]
        retry = max(0, (oldest + lockout_seconds * 1000 - now) // 1000)
        return LockoutState(True, failures, int(retry))
    return LockoutState(False, failures, 0)


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
