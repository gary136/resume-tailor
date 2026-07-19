"""Fit evaluator (stage 2): score stored jobs against the fact inventory.

Three-way branch per the design doc: any hard-requirement miss -> "skip";
hard requirements met + soft score >= threshold -> "fits"; otherwise "tailor".
Thresholds live in config (env), not the schema — tuned against Gary's judgment.

Model calls follow the claude-api skill guidance: structured outputs via
messages.parse(), adaptive thinking, fact inventory cached in the system prompt
(stable prefix across a batch of jobs).
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

import anthropic
from pydantic import BaseModel, Field

from resume_tailor.contracts import FactInventory, HardRequirement, JobRecord
from resume_tailor.store import db

MODEL = os.environ.get("RESUME_TAILOR_MODEL", "claude-opus-4-8")
FIT_THRESHOLD = int(os.environ.get("RESUME_TAILOR_FIT_THRESHOLD", "70"))


class ScoreBreakdown(BaseModel):
    """Rubric components; the code sums them — the model never emits a total."""

    tech_stack: int = Field(
        ge=0, le=40,
        description="Overlap of the posting's technologies with the fact inventory: "
        "40 = candidate's daily stack, ~20 = adjacent/transferable, 0 = disjoint",
    )
    domain: int = Field(
        ge=0, le=20,
        description="Industry/problem-domain familiarity per the facts (e.g. insurance "
        "data, billing pipelines): 20 = same domain, 0 = unfamiliar",
    )
    role_shape: int = Field(
        ge=0, le=20,
        description="Role type vs candidate's experience: backend/full-stack IC high; "
        "SRE/sales/management low unless facts support it",
    )
    seniority: int = Field(
        ge=0, le=20,
        description="Level alignment with the candidate's experience: mid/senior high; "
        "staff/principal or entry-level low",
    )


class FitEvaluation(BaseModel):
    """Structured output the model must return for one job."""

    hard_requirements: list[HardRequirement] = Field(
        description="Every non-negotiable requirement in the posting (degrees, years, "
        "authorizations, must-have technologies), each judged against the fact inventory"
    )
    score_breakdown: ScoreBreakdown
    rationale: str = Field(description="2-3 sentences explaining the scores")
    suggested_job_family: str = Field(
        description="Short kebab-case family slug for resume-variant reuse, "
        "e.g. 'backend-distributed', 'full-stack-product'"
    )

    @property
    def soft_score(self) -> int:
        b = self.score_breakdown
        return b.tech_stack + b.domain + b.role_shape + b.seniority


def build_system_prompt(inventory: FactInventory) -> str:
    facts = "\n".join(
        f"- [{f.id}] ({f.kind}) {f.statement}" for f in inventory.facts
    )
    return (
        "You evaluate job postings against a candidate's verified fact inventory.\n"
        "For each posting: extract every HARD requirement (non-negotiable: required "
        "degrees, minimum years, work authorization, must-have technologies) and judge "
        "each strictly — met only if a fact supports it, citing that fact's id as "
        "evidence_fact_id. Preferred/nice-to-have items are NOT hard requirements; "
        "they belong in the soft-score rubric. Then score four rubric components "
        "(tech_stack 0-40, domain 0-20, role_shape 0-20, seniority 0-20) strictly "
        "per their field descriptions — never a holistic guess; each component must "
        "be justifiable from specific facts.\n"
        "Work authorization: judge sponsorship language against the candidate's "
        "auth-us-work fact. A posting that excludes visa sponsorship (now or in the "
        "future) is a hard-requirement miss for an H-1B candidate.\n\n"
        f"Candidate fact inventory:\n{facts}"
    )


def decide_fit_status(evaluation: FitEvaluation, threshold: int = FIT_THRESHOLD) -> str:
    if any(not r.met for r in evaluation.hard_requirements):
        return "skip"
    return "fits" if evaluation.soft_score >= threshold else "tailor"


def evaluate_job(
    client: anthropic.Anthropic, system_prompt: str, job: JobRecord
) -> Optional[FitEvaluation]:
    """Call the model for one job. Returns None if the model refused."""
    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=[{
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{
            "role": "user",
            "content": (
                f"Job posting:\ncompany: {job.company}\ntitle: {job.title}\n"
                f"location: {job.location or 'unknown'}\n\n{job.description_text[:20000]}"
            ),
        }],
        output_format=FitEvaluation,
    )
    if response.stop_reason == "refusal":
        return None
    return response.parsed_output


def evaluate_pending(
    conn: sqlite3.Connection,
    *,
    limit: int = 10,
    client: Optional[anthropic.Anthropic] = None,
    inventory: Optional[FactInventory] = None,
    threshold: int = FIT_THRESHOLD,
) -> dict[str, int]:
    """Evaluate up to `limit` pending jobs, writing each result as it lands."""
    from resume_tailor.store.files import load_fact_inventory

    client = client or anthropic.Anthropic()
    inventory = inventory or load_fact_inventory()
    system_prompt = build_system_prompt(inventory)

    rows = conn.execute(
        "SELECT job_id FROM jobs WHERE fit_status = 'pending' ORDER BY fetched_at LIMIT ?",
        (limit,),
    ).fetchall()

    counts = {"fits": 0, "tailor": 0, "skip": 0, "refused": 0}
    for row in rows:
        job = db.get_job(conn, row["job_id"])
        evaluation = evaluate_job(client, system_prompt, job)
        if evaluation is None:
            counts["refused"] += 1
            continue
        status = decide_fit_status(evaluation, threshold)
        db.update_job_fit(
            conn,
            job.job_id,
            fit_status=status,
            hard_requirements=evaluation.hard_requirements,
            soft_score=evaluation.soft_score,
            fit_rationale=evaluation.rationale,
            job_family=evaluation.suggested_job_family,
            evaluated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        counts[status] += 1
    return counts
