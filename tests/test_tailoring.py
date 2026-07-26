from pathlib import Path

import pytest

from resume_tailor import tailoring
from resume_tailor.contracts import Fact, FactInventory, JobRecord, PreferenceRecord

INVENTORY = FactInventory(
    updated_at="2026-07-26",
    facts=[
        Fact(id="role-x", kind="role", statement="Engineer at Acme", source="t"),
        Fact(id="ach-y", kind="achievement", parent_id="role-x", fidelity="plausible",
             statement="Cut latency 40%", source="t"),
    ],
)
PREFS = PreferenceRecord(voice=["Number-first bullets"])
JOB = JobRecord(job_id="j1", source="manual", url="https://x.example/1", company="Acme",
                title="Backend Engineer", description_text="Python role.",
                fetched_at="2026-07-26T00:00:00", job_family="backend")

MASTER = """---
resume_id: master
kind: master
version: 3
status: confirmed
created_at: "2026-07-19"
updated_at: "2026-07-19"
---
# Gary

## Experience
- Cut latency 40%. <!-- facts: ach-y -->
"""

GOOD_VARIANT = """---
resume_id: backend
kind: variant
job_family: backend
based_on: master
version: 1
status: draft
created_at: "2026-07-26"
updated_at: "2026-07-26"
---
# Gary

## Experience
- Slashed latency 40% on core services. <!-- facts: ach-y, role-x -->
"""

BAD_VARIANT = GOOD_VARIANT.replace("ach-y, role-x", "ach-fake")


class FakeBackend:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def complete_text(self, *, system, user):
        self.calls.append({"system": system, "user": user})
        return self.responses.pop(0)

    def complete_structured(self, **kw):  # pragma: no cover
        raise NotImplementedError


def test_system_prompt_carries_policy_voice_and_facts():
    s = tailoring.build_system_prompt(INVENTORY, PREFS)
    assert "never doubt-arousing" in s
    assert "Number-first bullets" in s
    assert "[ach-y] (achievement, plausible)" in s
    assert "EXACTLY" in s  # checkable-facts rule


def test_generate_valid_first_try():
    backend = FakeBackend([f"```markdown\n{GOOD_VARIANT}```"])
    variant, errors = tailoring.generate_variant(
        backend, INVENTORY, PREFS, MASTER, JOB, "backend")
    assert errors == []
    assert "Slashed latency" in variant
    assert len(backend.calls) == 1


def test_invalid_draft_triggers_repair_with_error_feedback():
    backend = FakeBackend([BAD_VARIANT, GOOD_VARIANT])
    variant, errors = tailoring.generate_variant(
        backend, INVENTORY, PREFS, MASTER, JOB, "backend")
    assert errors == []
    assert len(backend.calls) == 2
    assert "ach-fake" in backend.calls[1]["user"]  # violations fed back


def test_still_invalid_after_repair_reports_errors():
    backend = FakeBackend([BAD_VARIANT, BAD_VARIANT])
    variant, errors = tailoring.generate_variant(
        backend, INVENTORY, PREFS, MASTER, JOB, "backend")
    assert errors and "ach-fake" in errors[0]


def test_diff_strips_fact_comments():
    d = tailoring.diff_against_master(MASTER, GOOD_VARIANT)
    assert "Slashed latency 40% on core services." in d
    assert "facts:" not in d


def test_save_variant_writes_family_file(tmp_path):
    p = tailoring.save_variant(GOOD_VARIANT, "backend", tmp_path)
    assert p == tmp_path / "backend.md"
    assert p.read_text().startswith("---")
