"""Tier-0 prefilter: free keyword/location screening before any LLM call.

User decision 2026-07-19: keep a stored search profile (keywords, locations,
target companies) and screen the whole board with it first, so the paid/slow
LLM tier only sees plausible jobs. Rejected jobs get fit_status='skip' with a
"[prefilter]" rationale — auditable and reversible (re-set to pending to rescue).
"""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import yaml


def _profile_path() -> Path:
    env = os.environ.get("RESUME_TAILOR_SEARCH_PROFILE")
    if env:
        return Path(env)
    data_copy = Path(os.environ.get("RESUME_TAILOR_DATA", "data")) / "search_profile.yaml"
    if data_copy.exists():
        return data_copy
    return Path(__file__).parent / "config" / "search_profile.yaml"


def load_profile() -> dict:
    return yaml.safe_load(_profile_path().read_text())


def title_verdict(title: str, profile: dict) -> str | None:
    """Return a rejection reason, or None if the title passes."""
    t = title.lower()
    hit = next((k for k in profile["title_exclude"] if k.lower() in t), None)
    if hit:
        return f"title matches exclude keyword {hit.strip()!r}"
    if not any(k.lower() in t for k in profile["title_include"]):
        return "title matches no include keyword"
    return None


def _location_matches(keyword: str, location: str) -> bool:
    # All-caps keywords (e.g. "US") match as whole words, case-sensitively —
    # otherwise "us" hides inside "Austria"/"Belarus". Others match loosely.
    if keyword.isupper():
        return re.search(rf"\b{re.escape(keyword)}\b", location) is not None
    return keyword.lower() in location.lower()


def location_verdict(location: str | None, profile: dict) -> str | None:
    if location is None:
        return None  # unknown location: let the LLM tier judge
    if any(_location_matches(k, location) for k in profile["location_include"]):
        return None
    return "location outside profile"


def description_verdict(description: str, profile: dict) -> str | None:
    """Reject postings whose JD explicitly refuses visa sponsorship."""
    d = description.lower()
    hit = next((p for p in profile.get("description_exclude", []) if p.lower() in d), None)
    return f"posting excludes sponsorship ({hit!r})" if hit else None


def prefilter_pending(conn: sqlite3.Connection, profile: dict | None = None) -> dict[str, int]:
    """Mark obviously-out pending jobs as skip. Returns {passed, rejected}."""
    profile = profile or load_profile()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    counts = {"passed": 0, "rejected": 0}
    rows = conn.execute(
        "SELECT job_id, title, location, description_text FROM jobs WHERE fit_status = 'pending'"
    ).fetchall()
    for row in rows:
        reason = (
            title_verdict(row["title"], profile)
            or location_verdict(row["location"], profile)
            or description_verdict(row["description_text"], profile)
        )
        if reason is None:
            counts["passed"] += 1
            continue
        conn.execute(
            """UPDATE jobs SET fit_status = 'skip',
                              fit_rationale = ?, evaluated_at = ?
               WHERE job_id = ?""",
            (f"[prefilter] {reason}", now, row["job_id"]),
        )
        counts["rejected"] += 1
    conn.commit()
    return counts
