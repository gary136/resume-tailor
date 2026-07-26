from resume_tailor.connectors import ashby, lever, fetch_board, CONNECTORS


def test_ashby_maps_fields():
    payload = {"id": "abc", "title": " Backend Engineer ", "location": "Remote - US",
               "jobUrl": "https://jobs.ashbyhq.com/ramp/abc", "isRemote": True,
               "descriptionPlain": "Build things.", "isListed": True}
    job = ashby.to_job_record("ramp", payload)
    assert job.source == "ashby" and job.external_id == "abc"
    assert job.title == "Backend Engineer"  # trimmed
    assert job.company == "ramp" and job.remote is True
    assert job.url.endswith("/abc")


def test_lever_maps_fields_and_location_from_categories():
    payload = {"id": "xyz", "text": "Full Stack Engineer",
               "hostedUrl": "https://jobs.lever.co/ro/xyz",
               "categories": {"location": "New York"}, "descriptionPlain": "d"}
    job = lever.to_job_record("ro", payload)
    assert job.source == "lever" and job.location == "New York"
    assert job.remote is False and job.company == "ro"


def test_dispatch_rejects_unknown_source():
    import pytest
    with pytest.raises(ValueError, match="unknown source"):
        fetch_board("indeed", "whatever")


def test_all_connectors_share_store_jobs():
    # store_jobs is source-agnostic; every connector re-exports the same function
    assert CONNECTORS["ashby"].store_jobs is CONNECTORS["greenhouse"].store_jobs
    assert CONNECTORS["lever"].store_jobs is CONNECTORS["greenhouse"].store_jobs
