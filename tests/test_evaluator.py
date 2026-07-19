import pytest

from resume_tailor import evaluator
from resume_tailor.contracts import Fact, FactInventory, HardRequirement, JobRecord
from resume_tailor.evaluator import FitEvaluation, ScoreBreakdown, build_system_prompt, decide_fit_status
from resume_tailor.store import db

INVENTORY = FactInventory(
    updated_at="2026-07-19",
    facts=[
        Fact(id="skill-backend", kind="skill", statement="Backend: Python, C#",
             source="test"),
    ],
)

NOW = "2026-07-19T12:00:00"


def _breakdown(total: int) -> ScoreBreakdown:
    # distribute a target total across the rubric for test convenience
    tech = min(total, 40)
    rest = total - tech
    return ScoreBreakdown(
        tech_stack=tech, domain=min(rest, 20),
        role_shape=min(max(rest - 20, 0), 20), seniority=min(max(rest - 40, 0), 20),
    )


def _evaluation(soft_score: int = 80, **overrides) -> FitEvaluation:
    defaults = dict(
        hard_requirements=[
            HardRequirement(requirement="Python", met=True, evidence_fact_id="skill-backend")
        ],
        score_breakdown=_breakdown(soft_score),
        rationale="Good match.",
        suggested_job_family="backend-distributed",
    )
    return FitEvaluation.model_validate(defaults | overrides)


def test_hard_miss_means_skip():
    ev = _evaluation(hard_requirements=[
        HardRequirement(requirement="US security clearance", met=False),
    ], score_breakdown=_breakdown(95))
    assert decide_fit_status(ev, threshold=70) == "skip"


def test_high_soft_score_means_fits():
    assert decide_fit_status(_evaluation(soft_score=70), threshold=70) == "fits"


def test_low_soft_score_means_tailor():
    assert decide_fit_status(_evaluation(soft_score=69), threshold=70) == "tailor"


def test_system_prompt_lists_fact_ids():
    prompt = build_system_prompt(INVENTORY)
    assert "[skill-backend]" in prompt
    assert "hard" in prompt.lower()


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    db.init_db(c)
    yield c
    c.close()


def _job(job_id: str) -> JobRecord:
    return JobRecord(
        job_id=job_id, source="manual", url=f"https://x.example/{job_id}",
        company="Acme", title="Backend Engineer", description_text="Python role.",
        fetched_at=NOW,
    )


def test_evaluate_pending_writes_results(conn, monkeypatch):
    db.add_job(conn, _job("j1"))
    db.add_job(conn, _job("j2"))

    monkeypatch.setattr(
        evaluator, "evaluate_job",
        lambda backend, system, job: _evaluation(soft_score=55),
    )
    counts = evaluator.evaluate_pending(
        conn, limit=10, backend=object(), inventory=INVENTORY, threshold=70
    )
    assert counts == {"fits": 0, "tailor": 2, "skip": 0, "refused": 0}

    job = db.get_job(conn, "j1")
    assert job.fit_status == "tailor"
    assert job.soft_score == 55
    assert job.job_family == "backend-distributed"
    assert job.hard_requirements[0].evidence_fact_id == "skill-backend"
    assert job.evaluated_at is not None


def test_refusal_leaves_job_pending(conn, monkeypatch):
    db.add_job(conn, _job("j1"))
    monkeypatch.setattr(evaluator, "evaluate_job", lambda *a: None)
    counts = evaluator.evaluate_pending(
        conn, limit=10, backend=object(), inventory=INVENTORY
    )
    assert counts["refused"] == 1
    assert db.get_job(conn, "j1").fit_status == "pending"


def test_rubric_loaded_from_config():
    from resume_tailor.evaluator import RUBRIC, FIT_THRESHOLD, ScoreBreakdown
    assert RUBRIC["version"] == 1
    assert sum(s["max"] for s in RUBRIC["components"].values()) == 100
    assert FIT_THRESHOLD == RUBRIC["fit_threshold"] == 70
    fields = set(ScoreBreakdown.model_fields)
    assert fields == set(RUBRIC["components"])
