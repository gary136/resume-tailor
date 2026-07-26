"""Ashby job-board connector (stage 2).

Public posting API (no auth): validated live 2026-07-26 against ramp + plaid
(both moved off Lever/Greenhouse to Ashby).
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone

import httpx

from resume_tailor.contracts import JobRecord
from resume_tailor.connectors.greenhouse import store_jobs  # shared, source-agnostic

API = "https://api.ashbyhq.com/posting-api/job-board/{board}"

__all__ = ["to_job_record", "fetch_board", "store_jobs"]


def to_job_record(board: str, payload: dict) -> JobRecord:
    location = payload.get("location") or None
    remote = payload.get("isRemote")
    if remote is None and location:
        remote = "remote" in location.lower()
    return JobRecord(
        job_id=str(uuid.uuid4()),
        source="ashby",
        external_id=str(payload["id"]),
        url=payload.get("jobUrl") or payload.get("applyUrl"),
        company=board,
        title=payload["title"].strip(),
        location=location,
        remote=remote,
        description_text=payload.get("descriptionPlain", ""),
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def fetch_board(board: str, *, timeout: float = 30.0) -> list[JobRecord]:
    resp = httpx.get(API.format(board=board), timeout=timeout)
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])
    return [to_job_record(board, j) for j in jobs if j.get("isListed", True)]
