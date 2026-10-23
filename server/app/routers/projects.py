"""Projects workspace: capstone projects A-J, milestones, status."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..db import new_session
from ..deps import CurrentUser, SameOrigin
from ..models import Project, ProjectMilestone, now_ms

router = APIRouter()


def _project_out(p: Project, milestones: list[ProjectMilestone] | None = None) -> dict:
    done = sum(1 for m in milestones if m.done) if milestones is not None else 0
    return {
        "id": p.id,
        "key": p.key,
        "title": p.title,
        "objectives": p.objectives,
        "prerequisites": p.prerequisites,
        "status": p.status,
        "origin": p.origin,
        "milestoneCount": len(milestones) if milestones is not None else None,
        "milestonesDone": done,
        "updatedAt": p.updated_at,
    }


@router.get("")
def list_projects(user: CurrentUser):
    db = new_session()
    try:
        rows = db.execute(select(Project).where(Project.owner_id == user.id).order_by(Project.key)).scalars()
        out = []
        for p in rows:
            ms = db.execute(select(ProjectMilestone).where(ProjectMilestone.project_id == p.id)).scalars().all()
            out.append(_project_out(p, ms))
        return {"items": out}
    finally:
        db.close()


@router.get("/{project_id}")
def get_project(project_id: str, user: CurrentUser):
    db = new_session()
    try:
        p = db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id)).scalar_one_or_none()
        if not p:
            raise HTTPException(status_code=404, detail="Project not found.")
        milestones = db.execute(
            select(ProjectMilestone).where(ProjectMilestone.project_id == project_id).order_by(ProjectMilestone.position)
        ).scalars().all()
        return {
            "project": {
                **_project_out(p, milestones),
                "steps": p.steps,
                "requiredFiles": p.required_files,
                "exampleInputs": p.example_inputs,
                "expectedOutputs": p.expected_outputs,
                "acceptanceTests": p.acceptance_tests,
                "failureScenarios": p.failure_scenarios,
                "securityChecks": p.security_checks,
                "completionCriteria": p.completion_criteria,
                "finalAssessment": p.final_assessment,
            },
            "milestones": [
                {
                    "id": m.id,
                    "title": m.title,
                    "detail": m.detail,
                    "position": m.position,
                    "done": m.done,
                    "doneAt": m.done_at,
                }
                for m in milestones
            ],
        }
    finally:
        db.close()


class StatusIn(BaseModel):
    status: str = Field(pattern="^(not_started|in_progress|done)$")


@router.patch("/{project_id}/status")
def set_status(project_id: str, payload: StatusIn, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        p = db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id)).scalar_one_or_none()
        if not p:
            raise HTTPException(status_code=404, detail="Project not found.")
        p.status = payload.status
        p.updated_at = now_ms()
        db.commit()
        return {"ok": True, "status": p.status}
    finally:
        db.close()


class MilestoneIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    detail: str = Field(default="", max_length=4000)
    position: int = 0


@router.post("/{project_id}/milestones")
def add_milestone(project_id: str, payload: MilestoneIn, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        p = db.execute(select(Project).where(Project.id == project_id, Project.owner_id == user.id)).scalar_one_or_none()
        if not p:
            raise HTTPException(status_code=404, detail="Project not found.")
        m = ProjectMilestone(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            project_id=project_id,
            title=payload.title.strip()[:300],
            detail=payload.detail,
            position=payload.position,
        )
        db.add(m)
        db.commit()
        return {"id": m.id}
    finally:
        db.close()


@router.patch("/milestones/{milestone_id}")
def toggle_milestone(milestone_id: str, user: CurrentUser, _: SameOrigin, done: bool | None = None):
    db = new_session()
    try:
        m = db.execute(
            select(ProjectMilestone).where(ProjectMilestone.id == milestone_id, ProjectMilestone.owner_id == user.id)
        ).scalar_one_or_none()
        if not m:
            raise HTTPException(status_code=404, detail="Milestone not found.")
        m.done = (not m.done) if done is None else done
        m.done_at = now_ms() if m.done else None
        m.updated_at = now_ms()
        # Keep project status in sync with real milestone completion.
        p = db.get(Project, m.project_id)
        if p:
            all_ms = db.execute(select(ProjectMilestone).where(ProjectMilestone.project_id == p.id)).scalars().all()
            if all(x.done for x in all_ms) and all_ms:
                p.status = "done"
            elif any(x.done for x in all_ms):
                p.status = "in_progress"
            else:
                p.status = "not_started"
            p.updated_at = now_ms()
        db.commit()
        return {"ok": True, "done": m.done}
    finally:
        db.close()


@router.delete("/milestones/{milestone_id}")
def delete_milestone(milestone_id: str, user: CurrentUser, _: SameOrigin):
    db = new_session()
    try:
        m = db.execute(
            select(ProjectMilestone).where(ProjectMilestone.id == milestone_id, ProjectMilestone.owner_id == user.id)
        ).scalar_one_or_none()
        if not m:
            raise HTTPException(status_code=404, detail="Milestone not found.")
        db.delete(m)
        db.commit()
        return {"ok": True}
    finally:
        db.close()
