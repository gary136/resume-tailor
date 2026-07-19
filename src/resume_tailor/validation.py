"""Resume ↔ fact-inventory validation: the no-fabrication mechanism.

Every bullet line in a resume must end with `<!-- facts: id[, id…] -->` and every
referenced id must exist in the fact inventory. See docs/reference/data-contracts.md §2.
"""

from __future__ import annotations

import re

import yaml

from resume_tailor.contracts import FactInventory, ResumeMeta

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.*)$")
_FACT_REF_RE = re.compile(r"<!--\s*facts:\s*([a-z0-9-]+(?:\s*,\s*[a-z0-9-]+)*)\s*-->\s*$")


def parse_resume(text: str) -> tuple[ResumeMeta, str]:
    """Split a resume markdown file into validated frontmatter and body."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError("resume file has no YAML frontmatter block")
    meta = ResumeMeta.model_validate(yaml.safe_load(m.group(1)))
    return meta, m.group(2)


def validate_resume(text: str, inventory: FactInventory) -> list[str]:
    """Return a list of violations; empty list means the resume passes."""
    errors: list[str] = []
    try:
        _, body = parse_resume(text)
    except ValueError as exc:
        return [str(exc)]

    known = inventory.ids()
    for lineno, line in enumerate(body.splitlines(), start=1):
        bullet = _BULLET_RE.match(line)
        if not bullet:
            continue
        ref = _FACT_REF_RE.search(bullet.group(1))
        if not ref:
            errors.append(f"line {lineno}: bullet has no fact reference")
            continue
        for fact_id in re.split(r"\s*,\s*", ref.group(1)):
            if fact_id not in known:
                errors.append(f"line {lineno}: unknown fact id '{fact_id}'")
    return errors
