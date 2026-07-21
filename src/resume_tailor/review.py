"""Review queue rendering (plan-review gap: 'how does Gary actually review verdicts').

Turns evaluated jobs into a readable console report: verdict, score with its
rubric breakdown, hard-requirement evidence, rationale, and the apply URL.
"""

from __future__ import annotations

import json
import sqlite3

_ORDER = {"fits": 0, "tailor": 1, "skip": 2, "pending": 3}


def queue_rows(conn: sqlite3.Connection, statuses: tuple[str, ...]) -> list[sqlite3.Row]:
    placeholders = ",".join("?" for _ in statuses)
    return conn.execute(
        f"""SELECT * FROM jobs WHERE fit_status IN ({placeholders})
            ORDER BY soft_score DESC NULLS LAST, company""",
        statuses,
    ).fetchall()


def format_breakdown(raw: str | None) -> str:
    if not raw:
        return "(no breakdown stored — evaluated before sub-scores were persisted)"
    parts = json.loads(raw)
    return " · ".join(f"{name} {score}" for name, score in parts.items())


def _get(row: sqlite3.Row, key: str):
    """Column-tolerant access — older stores may lack newer columns."""
    return row[key] if key in row.keys() else None


def format_job(row: sqlite3.Row) -> str:
    lines = [
        f"[{row['fit_status'].upper()}] {row['title']} — {row['company']}"
        f"  (score {row['soft_score'] if row['soft_score'] is not None else '?'})",
        f"  location: {row['location'] or 'unknown'}",
        f"  family:   {row['job_family'] or '-'}",
        f"  rubric:   {format_breakdown(_get(row, 'score_breakdown'))}",
    ]
    if row["hard_requirements"]:
        lines.append("  hard requirements:")
        for req in json.loads(row["hard_requirements"]):
            mark = "OK  " if req["met"] else "MISS"
            evidence = f" <- {req['evidence_fact_id']}" if req.get("evidence_fact_id") else ""
            lines.append(f"    {mark} {req['requirement']}{evidence}")
    if row["fit_rationale"]:
        lines.append(f"  why:      {row['fit_rationale']}")
    lines.append(f"  url:      {row['url']}")
    return "\n".join(lines)


def render_queue(conn: sqlite3.Connection, statuses: tuple[str, ...]) -> str:
    rows = sorted(
        queue_rows(conn, statuses), key=lambda r: (_ORDER.get(r["fit_status"], 9), -(r["soft_score"] or 0))
    )
    if not rows:
        return f"No jobs with status: {', '.join(statuses)}."
    blocks = [format_job(r) for r in rows]
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["fit_status"]] = counts.get(r["fit_status"], 0) + 1
    summary = " · ".join(f"{v} {k}" for k, v in sorted(counts.items(), key=lambda kv: _ORDER.get(kv[0], 9)))
    return "\n\n".join(blocks) + f"\n\n— {summary} —"
