from pathlib import Path

import pytest

from resume_tailor.apply.greenhouse_form import FillResult, fill_application
from resume_tailor.apply.profile import build_profile
from resume_tailor.contracts import AnswerBank, Fact, FactInventory

FACTS = FactInventory(updated_at="2026-07-27", facts=[
    Fact(id="contact-info", kind="other",
         statement="Hung-Ting (Gary) Lee — 571-356-3056 — garyhungting@gmail.com — 72-01 Queens Blvd, Woodside, NY",
         source="t"),
])
ANSWERS = AnswerBank(salary_base_range="$140k–$180k", salary_total_range="$170k–$250k",
                     start_date="Flexible", location_policy="Remote or NYC ≤3 days",
                     why_company_seed="ownership + depth")


def test_profile_parses_identity_from_contact_fact():
    p = build_profile(FACTS, ANSWERS)
    assert p.first_name == "Hung-Ting" and p.last_name == "Lee"
    assert p.email == "garyhungting@gmail.com"
    assert p.phone == "571-356-3056"
    assert p.location == "Remote or NYC ≤3 days"


def test_profile_requires_contact_fact():
    empty = FactInventory(updated_at="2026-07-27", facts=[])
    with pytest.raises(ValueError, match="contact-info"):
        build_profile(empty, ANSWERS)


def test_fillresult_ok_needs_core_fields():
    good = FillResult(filled={"first_name": "#f", "last_name": "#l", "email": "#e", "resume": "#r"},
                      screenshot=Path("x.png"))
    bad = FillResult(filled={"first_name": "#f", "resume": None}, screenshot=Path("x.png"))
    assert good.ok and not bad.ok
    assert good.submitted is False  # invariant


def test_no_submit_code_path_in_module():
    """Guard: the form module must contain no submit action, ever."""
    src = Path("src/resume_tailor/apply/greenhouse_form.py").read_text().lower()
    assert "submit" in src  # the word appears (in the invariant comment / field name)
    # but never as an action: no click-submit, no .click() on a submit button
    assert "submit()" not in src
    assert 'name="submit"' not in src
    assert "click_submit" not in src
