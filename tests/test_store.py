import sqlite3

import pytest

from resume_tailor.contracts import ApplicationRecord, HardRequirement, JobRecord
from resume_tailor.store import db

NOW = "2026-07-19T12:00:00"


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "test.db")
    db.init_db(c)
    yield c
    c.close()


def _job(job_id="job-1", url="https://boards.example/1", **overrides) -> JobRecord:
    defaults = dict(
        job_id=job_id, source="manual", url=url, company="Acme",
        title="Backend Engineer", description_text="Build things.", fetched_at=NOW,
    )
    return JobRecord.model_validate(defaults | overrides)


def _application(application_id="app-1", job_id="job-1", **overrides) -> ApplicationRecord:
    defaults = dict(
        application_id=application_id, job_id=job_id, resume_id="master",
        resume_version=1, queued_at=NOW,
    )
    return ApplicationRecord.model_validate(defaults | overrides)


def test_job_roundtrip_with_hard_requirements(conn):
    job = _job(
        fit_status="tailor",
        soft_score=55,
        hard_requirements=[
            HardRequirement(requirement="5y Python", met=True, evidence_fact_id="skill-python")
        ],
    )
    db.add_job(conn, job)
    assert db.get_job(conn, "job-1") == job


def test_duplicate_url_rejected(conn):
    db.add_job(conn, _job())
    with pytest.raises(sqlite3.IntegrityError):
        db.add_job(conn, _job(job_id="job-2", url="https://boards.example/1"))


def test_double_apply_rejected_by_unique_constraint(conn):
    db.add_job(conn, _job())
    db.queue_application(conn, _application())
    with pytest.raises(sqlite3.IntegrityError):
        db.queue_application(conn, _application(application_id="app-2"))


def test_application_must_enter_as_queued(conn):
    db.add_job(conn, _job())
    with pytest.raises(db.TransitionError):
        db.queue_application(conn, _application(status="approved", batch_id="b1"))


def test_submit_without_approval_is_illegal(conn):
    db.add_job(conn, _job())
    db.queue_application(conn, _application())
    with pytest.raises(db.TransitionError, match="queued -> submitted"):
        db.set_application_status(conn, "app-1", "submitted", timestamp=NOW)


def test_approval_requires_batch_id(conn):
    db.add_job(conn, _job())
    db.queue_application(conn, _application())
    with pytest.raises(db.TransitionError, match="batch_id"):
        db.set_application_status(conn, "app-1", "approved", timestamp=NOW)


def test_approve_then_submit_happy_path(conn):
    db.add_job(conn, _job())
    db.queue_application(conn, _application())
    db.approve_batch(conn, ["app-1"], batch_id="batch-1", timestamp=NOW)
    db.set_application_status(conn, "app-1", "submitted", timestamp=NOW)

    final = db.get_application(conn, "app-1")
    assert final.status == "submitted"
    assert final.batch_id == "batch-1"
    assert final.approved_at == NOW
    assert final.submitted_at == NOW


def test_terminal_states_reject_moves(conn):
    db.add_job(conn, _job())
    db.queue_application(conn, _application())
    db.set_application_status(conn, "app-1", "withdrawn_by_user", timestamp=NOW)
    with pytest.raises(db.TransitionError):
        db.set_application_status(conn, "app-1", "approved", timestamp=NOW, batch_id="b1")
