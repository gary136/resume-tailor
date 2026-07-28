from resume_tailor.render import cap_bullets_per_role, resume_to_html, _role_bullet_groups

BODY = """# Gary

## Experience
### Role A
- a1 <!-- facts: x -->
- a2 <!-- facts: x -->
- a3 <!-- facts: x -->
### Role B
- b1 <!-- facts: x -->
- b2 <!-- facts: x -->

## Skills
- s1 <!-- facts: y -->
"""

FRONT = """---
resume_id: master
kind: master
version: 1
status: confirmed
created_at: "2026-07-27"
updated_at: "2026-07-27"
---
"""


def test_cap_keeps_top_n_per_role():
    out = cap_bullets_per_role(BODY, 2)
    assert "a1" in out and "a2" in out and "a3" not in out   # role A capped
    assert "b1" in out and "b2" in out                        # role B under cap, all kept
    assert "s1" in out                                        # skills bullets NOT capped (not a role)


def test_cap_zero_is_noop():
    assert cap_bullets_per_role(BODY, 0) == BODY


def test_role_groups_counts():
    groups = list(_role_bullet_groups(BODY))
    assert [len(g) for g in groups] == [3, 2]  # role A has 3, role B has 2


def test_html_cap_strips_facts_and_drops_bullets():
    html = resume_to_html(FRONT + BODY, max_bullets_per_role=1)
    assert "facts:" not in html
    assert "a1" in html and "a2" not in html  # only first bullet of role A
