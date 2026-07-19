from resume_tailor.render import resume_to_html

RESUME = """---
resume_id: master
kind: master
version: 1
created_at: "2026-07-19"
updated_at: "2026-07-19"
---
# Gary Lee

555-000-0000 | g@example.com

## Experience

- Cut latency 40%. <!-- facts: ach-x -->
- Built pipelines. <!-- facts: ach-y, role-z -->
"""


def test_fact_ref_comments_stripped():
    html = resume_to_html(RESUME)
    assert "facts:" not in html
    assert "<!--" not in html


def test_markdown_structure_rendered():
    html = resume_to_html(RESUME)
    assert "<h1>Gary Lee</h1>" in html
    assert "<h2>Experience</h2>" in html
    assert "<li>Cut latency 40%.</li>" in html
    assert "font-family" in html  # styling embedded


def test_frontmatter_not_in_output():
    html = resume_to_html(RESUME)
    assert "resume_id" not in html
