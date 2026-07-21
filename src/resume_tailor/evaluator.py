"""Fit evaluator (stage 2): score stored jobs against the fact inventory.

Three-way branch per the design doc: any hard-requirement miss -> "skip";
hard requirements met + soft score >= threshold -> "fits"; otherwise "tailor".
Thresholds live in config (env), not the schema — tuned against Gary's judgment.

LLM calls go through resume_tailor.llm (provider-agnostic; GLM/OpenAI-compatible
by default per user decision 2026-07-19, Anthropic as configurable alternative).
The soft-score rubric lives in config (rubric.yaml) — see load_rubric().
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, create_model

from resume_tailor.contracts import FactInventory, HardRequirement, JobRecord
from resume_tailor.llm import LLMBackend, get_backend
from resume_tailor.store import db


def _rubric_path() -> Path:
    env = os.environ.get("RESUME_TAILOR_RUBRIC")
    if env:
        return Path(env)
    data_copy = Path(os.environ.get("RESUME_TAILOR_DATA", "data")) / "rubric.yaml"
    if data_copy.exists():
        return data_copy
    return Path(__file__).parent / "config" / "rubric.yaml"


def load_rubric() -> dict:
    return yaml.safe_load(_rubric_path().read_text())


def _build_breakdown_model(rubric: dict) -> type[BaseModel]:
    fields = {
        name: (int, Field(ge=0, le=spec["max"], description=spec["criteria"]))
        for name, spec in rubric["components"].items()
    }
    return create_model("ScoreBreakdown", **fields)


RUBRIC = load_rubric()
FIT_THRESHOLD = int(
    os.environ.get("RESUME_TAILOR_FIT_THRESHOLD", RUBRIC["fit_threshold"])
)
ScoreBreakdown = _build_breakdown_model(RUBRIC)


class FitEvaluation(BaseModel):
    """Structured output the model must return for one job."""

    hard_requirements: list[HardRequirement] = Field(
        description="Every non-negotiable requirement in the posting (degrees, years, "
        "authorizations, must-have technologies), each judged against the fact inventory"
    )
    score_breakdown: ScoreBreakdown  # type: ignore[valid-type]
    rationale: str = Field(description="2-3 sentences explaining the scores")
    suggested_job_family: str = Field(
        description="Short kebab-case family slug for resume-variant reuse, "
        "e.g. 'backend-distributed', 'full-stack-product'"
    )

    @property
    def soft_score(self) -> int:
        return sum(getattr(self.score_breakdown, name) for name in RUBRIC["components"])


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
        "they belong in the soft-score rubric. Then score each rubric component ("
        + ", ".join(f"{name} 0-{spec['max']}" for name, spec in RUBRIC["components"].items())
        + ") strictly per its criteria — never a holistic guess; each component must "
        "be justifiable from specific facts.\n"
        "Work authorization: judge sponsorship language against the candidate's "
        "auth-us-work fact. A posting that excludes visa sponsorship (now or in the "
        "future) is a hard-requirement miss for an H-1B candidate. If the posting "
        "explicitly offers visa/green-card sponsorship or immigration support, say so "
        "in the rationale — it is a strong plus for this candidate.\n\n"
        f"Candidate fact inventory:\n{facts}"
    )


def decide_fit_status(evaluation: FitEvaluation, threshold: int = FIT_THRESHOLD) -> str:
    if any(not r.met for r in evaluation.hard_requirements):
        return "skip"
    return "fits" if evaluation.soft_score >= threshold else "tailor"


def evaluate_job(
    backend: LLMBackend, system_prompt: str, job: JobRecord
) -> Optional[FitEvaluation]:
    """Call the configured LLM for one job. Returns None on refusal/invalid output."""
    return backend.complete_structured(
        system=system_prompt,
        user=(
            f"Job posting:\ncompany: {job.company}\ntitle: {job.title}\n"
            f"location: {job.location or 'unknown'}\n\n{job.description_text[:20000]}"
        ),
        output_model=FitEvaluation,
    )


def evaluate_pending(
    conn: sqlite3.Connection,
    *,
    limit: int = 10,
    backend: Optional[LLMBackend] = None,
    inventory: Optional[FactInventory] = None,
    threshold: int = FIT_THRESHOLD,
) -> dict[str, int]:
    """Evaluate up to `limit` pending jobs, writing each result as it lands."""
    from resume_tailor.store.files import load_fact_inventory

    backend = backend or get_backend()
    inventory = inventory or load_fact_inventory()
    system_prompt = build_system_prompt(inventory)

    rows = conn.execute(
        "SELECT job_id FROM jobs WHERE fit_status = 'pending' ORDER BY fetched_at LIMIT ?",
        (limit,),
    ).fetchall()

    counts = {"fits": 0, "tailor": 0, "skip": 0, "refused": 0, "error": 0}
    for row in rows:
        job = db.get_job(conn, row["job_id"])
        try:
            evaluation = evaluate_job(backend, system_prompt, job)
        except Exception as exc:  # timeout/HTTP blip: leave job pending, keep batch alive
            print(f"error on {job.title[:40]!r}: {type(exc).__name__}: {exc}")
            counts["error"] += 1
            continue
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
            score_breakdown=evaluation.score_breakdown.model_dump(),
            fit_rationale=evaluation.rationale,
            job_family=evaluation.suggested_job_family,
            evaluated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        counts[status] += 1
    return counts
