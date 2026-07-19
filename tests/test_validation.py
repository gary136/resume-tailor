from resume_tailor.contracts import Fact, FactInventory
from resume_tailor.validation import parse_resume, validate_resume

INVENTORY = FactInventory(
    updated_at="2026-07-19",
    facts=[
        Fact(id="role-acme-2021", kind="role", statement="Engineer at Acme",
             source="intake 2026-07-19"),
        Fact(id="ach-latency", kind="achievement", parent_id="role-acme-2021",
             statement="Cut p99 latency 40%", source="intake 2026-07-19"),
    ],
)

FRONTMATTER = """---
resume_id: master
kind: master
version: 1
created_at: "2026-07-19"
updated_at: "2026-07-19"
---
"""


def test_valid_resume_passes():
    text = FRONTMATTER + (
        "# Gary\n\n## Experience\n"
        "### Engineer — Acme (2021–present)\n"
        "- Cut p99 latency 40%. <!-- facts: ach-latency -->\n"
        "- Shipped the payments queue. <!-- facts: ach-latency, role-acme-2021 -->\n"
    )
    assert validate_resume(text, INVENTORY) == []


def test_bullet_without_ref_fails():
    text = FRONTMATTER + "- Great team player.\n"
    errors = validate_resume(text, INVENTORY)
    assert errors == ["line 1: bullet has no fact reference"]


def test_unknown_fact_id_fails():
    text = FRONTMATTER + "- Invented a thing. <!-- facts: ach-nonexistent -->\n"
    errors = validate_resume(text, INVENTORY)
    assert errors == ["line 1: unknown fact id 'ach-nonexistent'"]


def test_prose_and_headings_need_no_refs():
    text = FRONTMATTER + "# Gary\n\nBackend engineer, 8 years.\n\n## Skills\n"
    assert validate_resume(text, INVENTORY) == []


def test_missing_frontmatter_is_an_error():
    assert validate_resume("# no frontmatter\n", INVENTORY) == [
        "resume file has no YAML frontmatter block"
    ]


def test_parse_resume_returns_meta_and_body():
    meta, body = parse_resume(FRONTMATTER + "# Gary\n")
    assert meta.resume_id == "master"
    assert meta.kind == "master"
    assert body == "# Gary\n"
