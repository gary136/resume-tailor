"""Canonical data contracts (stage 1a).

Authoritative spec: docs/reference/data-contracts.md. The three dev tracks
(resume / job / apply) build against these models; change them only together
with that document.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

FactKind = Literal[
    "role",
    "education",
    "skill",
    "achievement",
    "certification",
    "project",
    "language",
    "other",
]

FitStatus = Literal["pending", "fits", "tailor", "skip"]

ApplicationStatus = Literal[
    "queued", "approved", "submitted", "confirmed", "failed", "withdrawn_by_user"
]

# The only legal status moves. `approved` is reachable solely through an explicit
# user batch-approval action (store.db enforces the transition, cli supplies the action).
APPLICATION_TRANSITIONS: dict[str, set[str]] = {
    "queued": {"approved", "withdrawn_by_user"},
    "approved": {"submitted", "withdrawn_by_user", "failed"},
    "submitted": {"confirmed", "failed"},
    "confirmed": set(),
    "failed": set(),
    "withdrawn_by_user": set(),
}


class Fact(BaseModel):
    """One fact from intake. Fidelity policy (user decision 2026-07-19):

    - "verified": literally true, user-confirmed. REQUIRED for background-checkable
      claims — employers, titles, dates, degrees, certifications.
    - "plausible": exaggerated-but-possible framing of real work (metrics, scale).
      Allowed for achievement claims; must stay internally consistent.

    Impossible claims (invented employers/roles/skills, timeline contradictions)
    have no tier — they don't enter the inventory at all.
    """

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    kind: FactKind
    fidelity: Literal["verified", "plausible"] = "verified"
    statement: str
    org: Optional[str] = None
    date_start: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    date_end: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    details: Optional[str] = None
    parent_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    source: str


class FactInventory(BaseModel):
    version: int = 1
    updated_at: str
    facts: list[Fact] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_ids(self) -> "FactInventory":
        ids = [f.id for f in self.facts]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise ValueError(f"duplicate fact ids: {sorted(dupes)}")
        known = set(ids)
        orphans = [f.id for f in self.facts if f.parent_id and f.parent_id not in known]
        if orphans:
            raise ValueError(f"facts with unknown parent_id: {orphans}")
        return self

    def ids(self) -> set[str]:
        return {f.id for f in self.facts}


class ResumeMeta(BaseModel):
    """Frontmatter of a resume markdown file (master or variant)."""

    resume_id: str
    kind: Literal["master", "variant"]
    job_family: Optional[str] = None
    based_on: Optional[str] = None
    version: int = 1
    status: Literal["draft", "confirmed"] = "draft"
    created_at: str
    updated_at: str

    @model_validator(mode="after")
    def _variant_needs_family(self) -> "ResumeMeta":
        if self.kind == "variant" and not self.job_family:
            raise ValueError("variant resumes must set job_family")
        if self.kind == "master" and self.based_on:
            raise ValueError("master resume cannot set based_on")
        return self


class HardRequirement(BaseModel):
    requirement: str
    met: bool
    evidence_fact_id: Optional[str] = None


class JobRecord(BaseModel):
    job_id: str
    source: Literal["greenhouse", "lever", "ashby", "aggregator", "manual"]
    external_id: Optional[str] = None
    url: str
    company: str
    title: str
    location: Optional[str] = None
    remote: Optional[bool] = None
    description_text: str
    job_family: Optional[str] = None
    fetched_at: str
    fit_status: FitStatus = "pending"
    hard_requirements: Optional[list[HardRequirement]] = None
    soft_score: Optional[int] = Field(default=None, ge=0, le=100)
    score_breakdown: Optional[dict[str, int]] = None
    fit_rationale: Optional[str] = None
    evaluated_at: Optional[str] = None


class ApplicationRecord(BaseModel):
    application_id: str
    job_id: str
    resume_id: str
    resume_version: int
    status: ApplicationStatus = "queued"
    batch_id: Optional[str] = None
    method: Optional[str] = None
    queued_at: str
    approved_at: Optional[str] = None
    submitted_at: Optional[str] = None
    notes: Optional[str] = None


class EditSignal(BaseModel):
    date: str
    job_family: Optional[str] = None
    proposal: str
    verdict: Literal["accepted", "rejected", "edited"]
    note: str = ""


class PreferenceRecord(BaseModel):
    voice: list[str] = Field(default_factory=list)
    edit_signals: list[EditSignal] = Field(default_factory=list)
