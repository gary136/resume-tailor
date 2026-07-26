"""Auto-tailoring engine (stage 3; absorbs stage 1c).

The machine drafts a resume variant for a job family; the no-fabrication
validator gates the draft (one repair round on violations); Gary's accept/reject
of the resulting diff IS the preference-learning loop. Success is measured by
Gary's accept-rate (phase proxy metric, see PROGRESS.md); if it stays below
~50% after calibration rounds, pivot the approach — don't polish.
"""

from __future__ import annotations

import difflib
import re
from datetime import date
from pathlib import Path
from typing import Optional

from resume_tailor.contracts import FactInventory, JobRecord, PreferenceRecord
from resume_tailor.llm import LLMBackend
from resume_tailor.validation import parse_resume, validate_resume

_MD_FENCE_RE = re.compile(r"```(?:markdown|md)?\s*(.*?)```", re.DOTALL)


def build_system_prompt(inventory: FactInventory, preferences: PreferenceRecord) -> str:
    facts = "\n".join(
        f"- [{f.id}] ({f.kind}, {f.fidelity}) {f.statement}" for f in inventory.facts
    )
    voice = "\n".join(f"- {v}" for v in preferences.voice) or "- (none yet)"
    signals = "\n".join(
        f"- [{s.verdict}] {s.proposal} ({s.note})" for s in preferences.edit_signals[:6]
    ) or "- (none yet)"
    return (
        "You tailor a candidate's master resume into a variant for one job family.\n"
        "HARD RULES:\n"
        "1. Every bullet line MUST end with `<!-- facts: id[, id...] -->` citing only ids "
        "from the fact inventory below. A bullet without a valid citation is a defect.\n"
        "2. Background-checkable content — employers, titles, dates, degrees — must appear "
        "EXACTLY as in the facts. Never touch these.\n"
        "3. Facts marked (achievement, plausible) may be reframed/emphasized within the "
        "calibrated-exaggeration policy: impressive but never doubt-arousing; numbers stay "
        "as given; never invent skills, tools, or experience absent from the inventory.\n"
        "4. Tailoring = reordering, reframing, emphasis, and selective omission — "
        "never fabrication.\n"
        "5. Keep the frontmatter block EXACTLY as provided by the user prompt.\n"
        "6. Output ONLY the complete variant resume as markdown inside one ```markdown fence.\n\n"
        f"CANDIDATE RULES — lines marked HARD have the same force as the HARD RULES "
        f"above; violating one is a defect:\n{voice}\n\n"
        f"PAST EDIT SIGNALS (respect verdicts):\n{signals}\n\n"
        f"FACT INVENTORY (the only permitted sources):\n{facts}"
    )


def build_user_prompt(master_text: str, job: JobRecord, job_family: str) -> str:
    _, master_body = parse_resume(master_text)
    frontmatter = (
        "---\n"
        f"resume_id: {job_family}\n"
        "kind: variant\n"
        f"job_family: {job_family}\n"
        "based_on: master\n"
        "version: 1\n"
        "status: draft\n"
        f'created_at: "{date.today().isoformat()}"\n'
        f'updated_at: "{date.today().isoformat()}"\n'
        "---"
    )
    return (
        f"TARGET JOB ({job.company} — {job.title}):\n{job.description_text[:8000]}\n\n"
        f"MASTER RESUME BODY:\n{master_body}\n\n"
        f"Produce the variant now. Start the file with exactly this frontmatter:\n{frontmatter}\n"
        "Then the tailored resume body (reordered/reframed for this job, every bullet "
        "fact-cited)."
    )


def extract_markdown(raw: str) -> str:
    m = _MD_FENCE_RE.search(raw)
    text = (m.group(1) if m else raw).strip()
    if not text.startswith("---"):
        # tolerate stray preamble before the frontmatter (anchor on resume_id)
        idx = text.find("---\nresume_id")
        if idx == -1:
            idx = text.find("---")
        text = text[idx:] if idx != -1 else text
    return text + ("\n" if not text.endswith("\n") else "")


def missing_sections(master_text: str, variant_text: str) -> list[str]:
    """Structural completeness: every H2 section of the master must survive.

    Catches truncated model output, which the fact-validator alone cannot see
    (a cut-off file's remaining bullets all validate). Found live 2026-07-26.
    """
    heads = lambda text: {l.strip() for l in text.splitlines() if l.startswith("## ")}
    _, master_body = parse_resume(master_text)
    _, variant_body = parse_resume(variant_text)
    return [f"missing section {h!r} (present in master)"
            for h in sorted(heads(master_body) - heads(variant_body))]


def generate_variant(
    backend: LLMBackend,
    inventory: FactInventory,
    preferences: PreferenceRecord,
    master_text: str,
    job: JobRecord,
    job_family: str,
) -> tuple[Optional[str], list[str]]:
    """Draft a validated variant. Returns (variant_text, violations).

    variant_text is None only if the model refused/failed twice; violations
    non-empty means the returned draft still fails the no-fabrication gate
    (caller must NOT save it as a usable variant).
    """
    system = build_system_prompt(inventory, preferences)
    user = build_user_prompt(master_text, job, job_family)

    raw = backend.complete_text(system=system, user=user)
    if raw is None:
        return None, ["model refused"]
    variant = extract_markdown(raw)
    errors = validate_resume(variant, inventory) or missing_sections(master_text, variant)
    if not errors:
        return variant, []

    # one repair round: feed the exact violations back
    repair = (
        f"{user}\n\nYour previous draft failed validation:\n"
        + "\n".join(f"- {e}" for e in errors)
        + "\nFix every violation and output the corrected complete file again."
    )
    raw = backend.complete_text(system=system, user=repair)
    if raw is None:
        return None, ["model refused on repair"]
    variant = extract_markdown(raw)
    errors = validate_resume(variant, inventory) or missing_sections(master_text, variant)
    return variant, errors


def diff_against_master(master_text: str, variant_text: str) -> str:
    _, master_body = parse_resume(master_text)
    _, variant_body = parse_resume(variant_text)
    strip = lambda s: [re.sub(r"\s*<!--.*?-->", "", line) for line in s.splitlines()]
    return "\n".join(
        difflib.unified_diff(
            strip(master_body), strip(variant_body),
            fromfile="master", tofile="variant", lineterm="",
        )
    )


def save_variant(variant_text: str, job_family: str, resumes_dir: Path) -> Path:
    resumes_dir.mkdir(parents=True, exist_ok=True)
    path = resumes_dir / f"{job_family}.md"
    path.write_text(variant_text)
    return path
