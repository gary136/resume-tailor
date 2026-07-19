import pytest

from resume_tailor.connectors import greenhouse
from resume_tailor.store import db

PAYLOAD = {
    "id": 8503792002,
    "absolute_url": "https://job-boards.greenhouse.io/gitlab/jobs/8503792002",
    "title": "Account Executive - Italy",
    "location": {"name": "Remote, Italy"},
    "content": "&lt;p&gt;GitLab is &lt;b&gt;the&lt;/b&gt; platform&lt;/p&gt;",
    "company_name": "GitLab",
}


def test_to_job_record_maps_fields():
    job = greenhouse.to_job_record("gitlab", PAYLOAD)
    assert job.source == "greenhouse"
    assert job.external_id == "8503792002"
    assert job.company == "GitLab"
    assert job.remote is True
    assert job.description_text == "GitLab is the platform"
    assert job.fit_status == "pending"


def test_company_falls_back_to_board_slug():
    payload = {k: v for k, v in PAYLOAD.items() if k != "company_name"}
    assert greenhouse.to_job_record("gitlab", payload).company == "gitlab"


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    db.init_db(c)
    yield c
    c.close()


def test_store_jobs_skips_known_external_ids(conn):
    first = greenhouse.to_job_record("gitlab", PAYLOAD)
    refetched = greenhouse.to_job_record("gitlab", PAYLOAD)  # new uuid, same external_id
    assert greenhouse.store_jobs(conn, [first]) == (1, 0)
    assert greenhouse.store_jobs(conn, [refetched]) == (0, 1)
