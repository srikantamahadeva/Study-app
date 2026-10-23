"""Coding labs: exercises, submissions, static checks (Pine), Pyodide harness info.

Pine Script's compiler exists only inside TradingView, so Pine exercises are
validated by static checks only — never by claims of compilation or profit.
Python exercises run client-side in Pyodide (isolated WASM, no network/FS);
the server records code and self-reported results, and runs its own copy of
the static checks so client results cannot be trusted blindly.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..db import new_session
from ..deps import CurrentUser, SameOrigin
from ..models import CodingExercise, ExerciseSubmission

router = APIRouter()


class SubmitIn(BaseModel):
    exerciseId: str
    code: str = Field(min_length=1, max_length=200_000)
    # Client (Pyodide) self-reported test results; re-checked statically here.
    testResults: list[dict] = Field(default_factory=list, max_length=100)


@router.get("/exercises")
def exercises(user: CurrentUser, language: str | None = None):
    db = new_session()
    try:
        stmt = select(CodingExercise).where(CodingExercise.owner_id == user.id)
        if language:
            stmt = stmt.where(CodingExercise.language == language)
        rows = db.execute(stmt.order_by(CodingExercise.language, CodingExercise.position)).scalars()
        return {
            "items": [
                {
                    "id": e.id,
                    "language": e.language,
                    "title": e.title,
                    "requirement": e.requirement,
                    "lessonId": e.lesson_id,
                    "position": e.position,
                }
                for e in rows
            ]
        }
    finally:
        db.close()


@router.get("/exercises/{exercise_id}")
def get_exercise(exercise_id: str, user: CurrentUser):
    db = new_session()
    try:
        e = db.execute(
            select(CodingExercise).where(CodingExercise.id == exercise_id, CodingExercise.owner_id == user.id)
        ).scalar_one_or_none()
        if not e:
            raise HTTPException(status_code=404, detail="Exercise not found.")
        # Reference solution is fetched explicitly via ?withSolution=1 to keep
        # it out of accidental default responses.
        return {
            "id": e.id,
            "language": e.language,
            "title": e.title,
            "requirement": e.requirement,
            "starterCode": e.starter_code,
            "explanation": e.explanation,
            "checks": e.checks,
            "expectedBehavior": e.expected_behavior,
        }
    finally:
        db.close()


@router.get("/exercises/{exercise_id}/solution")
def get_solution(exercise_id: str, user: CurrentUser):
    db = new_session()
    try:
        e = db.execute(
            select(CodingExercise).where(CodingExercise.id == exercise_id, CodingExercise.owner_id == user.id)
        ).scalar_one_or_none()
        if not e:
            raise HTTPException(status_code=404, detail="Exercise not found.")
        return {"solution": e.reference_solution, "explanation": e.explanation}
    finally:
        db.close()


def run_static_checks(code: str, checks: list[dict]) -> list[dict]:
    """Server-side static checks. Levels: error | warn | info."""
    import re

    results = []
    for check in checks:
        kind = check.get("kind", "contains")
        pattern = check.get("pattern", "")
        message = check.get("message", "")
        level = check.get("level", "error")
        try:
            if kind == "contains":
                passed = re.search(pattern, code, re.MULTILINE) is not None
            elif kind == "not_contains":
                passed = re.search(pattern, code, re.MULTILINE) is None
            elif kind == "balanced":
                for open_c, close_c in (("(", ")"), ("[", "]"), ("{", "}")):
                    if code.count(open_c) != code.count(close_c):
                        passed = False
                        break
                else:
                    passed = True
            else:
                passed = True
        except re.error:
            passed = True
        results.append({"message": message, "level": level, "passed": bool(passed)})
    return results


@router.post("/submit")
def submit(payload: SubmitIn, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        e = db.execute(
            select(CodingExercise).where(CodingExercise.id == payload.exerciseId, CodingExercise.owner_id == user.id)
        ).scalar_one_or_none()
        if not e:
            raise HTTPException(status_code=404, detail="Exercise not found.")

        checks = run_static_checks(payload.code, e.checks or [])
        static_ok = all(c["passed"] for c in checks if c["level"] == "error")
        client_tests = payload.testResults
        client_ok = all(bool(t.get("passed")) for t in client_tests) if client_tests else None

        passed = bool(static_ok and (client_ok is not False))
        result = {
            "staticChecks": checks,
            "staticPassed": static_ok,
            "clientTests": client_tests,
            "clientPassed": client_ok,
            "note": "Static checks only; Pine Script compilation happens in TradingView. "
            "Python tests ran in your browser's sandbox (Pyodide). No profitability claim is made.",
        }
        row = ExerciseSubmission(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            exercise_id=e.id,
            code=payload.code,
            result=result,
            passed=passed,
        )
        db.add(row)
        db.commit()
        return {"passed": passed, "result": result, "submissionId": row.id}
    finally:
        db.close()


@router.get("/submissions")
def submissions(user: CurrentUser, limit: int = 50):
    db = new_session()
    try:
        rows = db.execute(
            select(ExerciseSubmission).where(ExerciseSubmission.owner_id == user.id).order_by(ExerciseSubmission.created_at.desc()).limit(min(limit, 200))
        ).scalars()
        return {
            "items": [
                {"id": s.id, "exerciseId": s.exercise_id, "passed": s.passed, "createdAt": s.created_at}
                for s in rows
            ]
        }
    finally:
        db.close()
