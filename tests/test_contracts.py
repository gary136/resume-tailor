import pytest
from pydantic import ValidationError

from resume_tailor.contracts import Fact, FactInventory, ResumeMeta


def _fact(id: str, **overrides) -> Fact:
    defaults = dict(id=id, kind="skill", statement="Python", source="intake 2026-07-19")
    return Fact.model_validate(defaults | overrides)


def test_inventory_rejects_duplicate_ids():
    with pytest.raises(ValidationError, match="duplicate fact ids"):
        FactInventory(
            updated_at="2026-07-19",
            facts=[_fact("skill-python"), _fact("skill-python")],
        )


def test_inventory_rejects_unknown_parent():
    with pytest.raises(ValidationError, match="unknown parent_id"):
        FactInventory(
            updated_at="2026-07-19",
            facts=[_fact("ach-x", kind="achievement", parent_id="role-missing")],
        )


def test_inventory_accepts_valid_parent_chain():
    inv = FactInventory(
        updated_at="2026-07-19",
        facts=[
            _fact("role-acme-2021", kind="role", statement="Engineer at Acme"),
            _fact("ach-x", kind="achievement", parent_id="role-acme-2021"),
        ],
    )
    assert inv.ids() == {"role-acme-2021", "ach-x"}


def test_fact_rejects_bad_id_and_date():
    with pytest.raises(ValidationError):
        _fact("Bad_ID")
    with pytest.raises(ValidationError):
        _fact("role-x", date_start="2021")


def test_variant_requires_job_family():
    with pytest.raises(ValidationError, match="job_family"):
        ResumeMeta(
            resume_id="v1", kind="variant",
            created_at="2026-07-19", updated_at="2026-07-19",
        )


def test_master_cannot_have_based_on():
    with pytest.raises(ValidationError, match="based_on"):
        ResumeMeta(
            resume_id="master", kind="master", based_on="other",
            created_at="2026-07-19", updated_at="2026-07-19",
        )
