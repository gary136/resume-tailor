"""SQLite store for job records and the application log.

Enforces the application-status state machine from contracts.APPLICATION_TRANSITIONS:
`approved` is only reachable through approve_batch (the explicit user action), and
`submitted` only from `approved`. No other code path may bypass set_application_status.
"""

from __future__ import annotations

import json
import sqlite3
from importlib import resources
from pathlib import Path

from resume_tailor.contracts import (
    APPLICATION_TRANSITIONS,
    ApplicationRecord,
    HardRequirement,
    JobRecord,
)


class TransitionError(Exception):
    """Raised on an illegal application-status transition."""


def connect(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    schema = resources.files("resume_tailor.store").joinpath("schema.sql").read_text()
    conn.executescript(schema)
    conn.commit()


# --- jobs ---------------------------------------------------------------


def add_job(conn: sqlite3.Connection, job: JobRecord) -> None:
    row = job.model_dump()
    row["remote"] = None if job.remote is None else int(job.remote)
    row["hard_requirements"] = (
        None
        if job.hard_requirements is None
        else json.dumps([r.model_dump() for r in job.hard_requirements])
    )
    conn.execute(
        """INSERT INTO jobs (job_id, source, external_id, url, company, title, location,
                             remote, description_text, job_family, fetched_at, fit_status,
                             hard_requirements, soft_score, fit_rationale, evaluated_at)
           VALUES (:job_id, :source, :external_id, :url, :company, :title, :location,
                   :remote, :description_text, :job_family, :fetched_at, :fit_status,
                   :hard_requirements, :soft_score, :fit_rationale, :evaluated_at)""",
        row,
    )
    conn.commit()


def get_job(conn: sqlite3.Connection, job_id: str) -> JobRecord | None:
    row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    if row is None:
        return None
    data = dict(row)
    data["remote"] = None if data["remote"] is None else bool(data["remote"])
    if data["hard_requirements"] is not None:
        data["hard_requirements"] = [
            HardRequirement.model_validate(r) for r in json.loads(data["hard_requirements"])
        ]
    return JobRecord.model_validate(data)


def update_job_fit(
    conn: sqlite3.Connection,
    job_id: str,
    *,
    fit_status: str,
    hard_requirements: list[HardRequirement],
    soft_score: int,
    fit_rationale: str,
    job_family: str | None,
    evaluated_at: str,
) -> None:
    conn.execute(
        """UPDATE jobs SET fit_status = ?, hard_requirements = ?, soft_score = ?,
                           fit_rationale = ?, job_family = ?, evaluated_at = ?
           WHERE job_id = ?""",
        (
            fit_status,
            json.dumps([r.model_dump() for r in hard_requirements]),
            soft_score,
            fit_rationale,
            job_family,
            evaluated_at,
            job_id,
        ),
    )
    conn.commit()


# --- application log ----------------------------------------------------


def queue_application(conn: sqlite3.Connection, application: ApplicationRecord) -> None:
    if application.status != "queued":
        raise TransitionError("applications enter the log as 'queued'")
    conn.execute(
        """INSERT INTO applications (application_id, job_id, resume_id, resume_version,
                                     status, batch_id, method, queued_at, approved_at,
                                     submitted_at, notes)
           VALUES (:application_id, :job_id, :resume_id, :resume_version, :status,
                   :batch_id, :method, :queued_at, :approved_at, :submitted_at, :notes)""",
        application.model_dump(),
    )
    conn.commit()


def get_application(conn: sqlite3.Connection, application_id: str) -> ApplicationRecord | None:
    row = conn.execute(
        "SELECT * FROM applications WHERE application_id = ?", (application_id,)
    ).fetchone()
    return None if row is None else ApplicationRecord.model_validate(dict(row))


def set_application_status(
    conn: sqlite3.Connection,
    application_id: str,
    new_status: str,
    *,
    timestamp: str,
    batch_id: str | None = None,
) -> None:
    current = get_application(conn, application_id)
    if current is None:
        raise KeyError(f"no application {application_id}")
    if new_status not in APPLICATION_TRANSITIONS[current.status]:
        raise TransitionError(f"illegal transition {current.status} -> {new_status}")
    if new_status == "approved" and batch_id is None:
        raise TransitionError("'approved' requires a batch_id from a user approval action")

    sets = ["status = :status"]
    params: dict[str, str | None] = {
        "status": new_status,
        "application_id": application_id,
    }
    if new_status == "approved":
        sets += ["approved_at = :ts", "batch_id = :batch_id"]
        params |= {"ts": timestamp, "batch_id": batch_id}
    elif new_status == "submitted":
        sets.append("submitted_at = :ts")
        params["ts"] = timestamp
    conn.execute(
        f"UPDATE applications SET {', '.join(sets)} WHERE application_id = :application_id",
        params,
    )
    conn.commit()


def approve_batch(
    conn: sqlite3.Connection, application_ids: list[str], *, batch_id: str, timestamp: str
) -> None:
    """The batched-approval gate. Only ever called from an explicit user action."""
    for application_id in application_ids:
        set_application_status(
            conn, application_id, "approved", timestamp=timestamp, batch_id=batch_id
        )
