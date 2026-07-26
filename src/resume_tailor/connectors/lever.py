"""Lever job-board connector (stage 2).

Public postings API (no auth): validated live 2026-07-26 against the `ro` board.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone

import httpx

from resume_tailor.contracts import JobRecord
from resume_tailor.connectors.greenhouse import store_jobs  # shared, source-agnostic

API = "https://api.lever.co/v0/postings/{board}?mode=json"

__all__ = ["to_job_record", "fetch_board", "store_jobs"]


def to_job_record(board: str, payload: dict) -> JobRecord:
    location = (payload.get("categories") or {}).get("location")
    return JobRecord(
        job_id=str(uuid.uuid4()),
        source="lever",
        external_id=str(payload["id"]),
        url=payload["hostedUrl"],
        company=board,
        title=payload["text"].strip(),
        location=location,
        remote="remote" in location.lower() if location else None,
        description_text=payload.get("descriptionPlain", ""),
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def fetch_board(board: str, *, timeout: float = 30.0) -> list[JobRecord]:
    resp = httpx.get(API.format(board=board), timeout=timeout)
    resp.raise_for_status()
    return [to_job_record(board, j) for j in resp.json()]
