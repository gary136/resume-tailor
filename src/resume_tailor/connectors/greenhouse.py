"""Greenhouse job-board connector (stage 2).

Uses the public board API (no auth): validated live 2026-07-19 against
gitlab/anthropic/reddit boards — see spike/FINDINGS.md.
"""

from __future__ import annotations

import html
import re
import sqlite3
import uuid
from datetime import datetime, timezone

import httpx

from resume_tailor.contracts import JobRecord
from resume_tailor.store import db

API = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(content: str) -> str:
    text = html.unescape(content)
    text = _TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def to_job_record(board: str, payload: dict) -> JobRecord:
    """Map one job object from the board API to the canonical JobRecord."""
    location = (payload.get("location") or {}).get("name")
    return JobRecord(
        job_id=str(uuid.uuid4()),
        source="greenhouse",
        external_id=str(payload["id"]),
        url=payload["absolute_url"],
        company=payload.get("company_name") or board,
        title=payload["title"],
        location=location,
        remote="remote" in location.lower() if location else None,
        description_text=_strip_html(payload.get("content", "")),
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def fetch_board(board: str, *, timeout: float = 30.0) -> list[JobRecord]:
    resp = httpx.get(API.format(board=board), timeout=timeout)
    resp.raise_for_status()
    return [to_job_record(board, j) for j in resp.json().get("jobs", [])]


def store_jobs(conn: sqlite3.Connection, jobs: list[JobRecord]) -> tuple[int, int]:
    """Insert jobs, skipping ones already stored. Returns (added, skipped)."""
    added = skipped = 0
    for job in jobs:
        try:
            db.add_job(conn, job)
            added += 1
        except sqlite3.IntegrityError:
            skipped += 1
    return added, skipped
