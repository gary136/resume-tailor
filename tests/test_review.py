import json

import pytest

from resume_tailor.contracts import HardRequirement, JobRecord
from resume_tailor.review import format_breakdown, render_queue
from resume_tailor.store import db

NOW = "2026-07-20T10:00:00"


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    db.init_db(c)
    yield c
    c.close()


def _job(job_id, title, status, score, breakdown=None):
    return JobRecord(
        job_id=job_id, source="manual", url=f"https://x.example/{job_id}",
        company="Acme", title=title, location="Remote, US",
        description_text="d", fetched_at=NOW, fit_status=status,
        soft_score=score, score_breakdown=breakdown, job_family="backend",
        fit_rationale="because reasons",
        hard_requirements=[
            HardRequirement(requirement="Python", met=True, evidence_fact_id="skill-backend"),
            HardRequirement(requirement="Clearance", met=False),
        ],
    )


def test_format_breakdown_handles_missing_and_present():
    assert "no breakdown stored" in format_breakdown(None)
    assert format_breakdown(json.dumps({"tech_stack": 30, "domain": 10})) == "tech_stack 30 · domain 10"


def test_breakdown_roundtrips_through_store(conn):
    db.add_job(conn, _job("j1", "Backend Engineer", "fits", 78, {"tech_stack": 35, "domain": 15}))
    assert db.get_job(conn, "j1").score_breakdown == {"tech_stack": 35, "domain": 15}


def test_render_queue_orders_fits_before_tailor_and_shows_evidence(conn):
    db.add_job(conn, _job("j1", "Tailor Me", "tailor", 60, {"tech_stack": 20}))
    db.add_job(conn, _job("j2", "Great Fit", "fits", 78, {"tech_stack": 35}))

    out = render_queue(conn, ("fits", "tailor"))
    assert out.index("Great Fit") < out.index("Tailor Me")     # fits first
    assert "OK   Python <- skill-backend" in out               # evidence shown
    assert "MISS Clearance" in out
    assert "tech_stack 35" in out                              # breakdown shown
    assert "1 fits · 1 tailor" in out


def test_render_queue_empty_message(conn):
    assert "No jobs with status" in render_queue(conn, ("fits",))


def test_format_job_tolerates_store_without_breakdown_column(tmp_path):
    """A store created before score_breakdown existed must still render."""
    c = db.connect(tmp_path / "old.db")
    c.execute("""CREATE TABLE jobs (job_id TEXT, source TEXT, external_id TEXT, url TEXT,
                 company TEXT, title TEXT, location TEXT, remote INTEGER,
                 description_text TEXT, job_family TEXT, fetched_at TEXT,
                 fit_status TEXT, hard_requirements TEXT, soft_score INTEGER,
                 fit_rationale TEXT, evaluated_at TEXT)""")
    c.execute("INSERT INTO jobs (job_id, url, company, title, fit_status, soft_score) "
              "VALUES ('j1','u','Acme','Eng','fits',70)")
    c.commit()
    out = render_queue(c, ("fits",))
    assert "no breakdown stored" in out
    c.close()
