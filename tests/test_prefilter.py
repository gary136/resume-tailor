import pytest

from resume_tailor import prefilter
from resume_tailor.contracts import JobRecord
from resume_tailor.store import db

PROFILE = {
    "title_include": ["engineer", "developer"],
    "title_exclude": ["sales", "manager", "staff", "account executive"],
    "location_include": ["US", "United States", "Americas"],
    "location_exclude": ["India", "Canada", "United Kingdom", "Germany"],
}


@pytest.mark.parametrize("title,expect_pass", [
    ("Senior Backend Engineer", True),
    ("AI Engineer", True),
    ("Account Executive - Italy", False),
    ("Engineering Manager, Growth", False),
    ("Staff Backend Engineer", False),
    ("Customer Success Architect", False),  # no include keyword
])
def test_title_verdict(title, expect_pass):
    verdict = prefilter.title_verdict(title, PROFILE)
    assert (verdict is None) == expect_pass


@pytest.mark.parametrize("location,expect_pass", [
    ("Remote, US", True),
    ("Remote, Canada; Remote, US", True),
    ("Remote, India", False),
    ("Remote, Germany", False),
    ("New York, NY (HQ)", True),        # US city, no literal 'US' — must pass (was a live bug)
    ("San Francisco, CA", True),        # ditto
    ("London, United Kingdom", False),  # foreign, no US signal
    ("Remote, Canada; Remote, US", True),  # mixed but has US
    (None, True),
])
def test_location_verdict(location, expect_pass):
    assert (prefilter.location_verdict(location, PROFILE) is None) == expect_pass


def _job(job_id, title, location):
    return JobRecord(
        job_id=job_id, source="manual", url=f"https://x.example/{job_id}",
        company="Acme", title=title, location=location,
        description_text="d", fetched_at="2026-07-19T12:00:00",
    )


def test_prefilter_marks_rejects_and_leaves_survivors(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    db.init_db(conn)
    db.add_job(conn, _job("j1", "Backend Engineer", "Remote, US"))
    db.add_job(conn, _job("j2", "Account Executive", "Remote, US"))
    db.add_job(conn, _job("j3", "Backend Engineer", "Remote, India"))

    counts = prefilter.prefilter_pending(conn, PROFILE)
    assert counts == {"passed": 1, "rejected": 2}
    assert db.get_job(conn, "j1").fit_status == "pending"
    assert db.get_job(conn, "j2").fit_status == "skip"
    assert "[prefilter]" in db.get_job(conn, "j2").fit_rationale
    assert db.get_job(conn, "j3").fit_status == "skip"
    conn.close()


def test_description_verdict_rejects_no_sponsorship():
    profile = dict(PROFILE, description_exclude=["unable to sponsor", "without sponsorship"])
    ok = prefilter.description_verdict("Great job. Visa sponsorship available.", profile)
    assert ok is None
    bad = prefilter.description_verdict(
        "Applicants must be authorized to work in the US; we are unable to sponsor visas.",
        profile,
    )
    assert "excludes sponsorship" in bad


def test_seniority_range_rescued_but_bare_staff_rejected():
    profile = dict(PROFILE, title_exclude=["staff!", "manager!"],
                   title_include=["engineer"])
    # a level range that includes a level Gary qualifies for -> rescued to LLM tier
    assert prefilter.title_verdict("Intermediate to Senior Staff Backend Engineer", profile) is None
    # a bare Staff title is still rejected
    assert prefilter.title_verdict("Staff Backend Engineer", profile) is not None
    # manager whole-word still rejects
    assert prefilter.title_verdict("Engineering Manager", profile) is not None


def test_widened_includes_catch_more_titles():
    profile = dict(PROFILE, title_include=["engineer", "swe", "full stack", "architect"])
    for t in ["SWE II", "Full Stack Developer", "Solutions Architect"]:
        # each contains an include keyword -> not rejected for "no include"
        v = prefilter.title_verdict(t, profile)
        assert v != "title matches no include keyword", t
