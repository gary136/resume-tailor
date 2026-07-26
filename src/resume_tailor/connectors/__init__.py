"""Job-board connectors, dispatched by ATS source.

All connectors expose the same interface: fetch_board(slug) -> list[JobRecord],
store_jobs(conn, jobs) -> (added, skipped). Add a provider here to make it
reachable from `jobs fetch-all`.
"""

from __future__ import annotations

from resume_tailor.connectors import ashby, greenhouse, lever

CONNECTORS = {
    "greenhouse": greenhouse,
    "ashby": ashby,
    "lever": lever,
}


def fetch_board(source: str, slug: str):
    if source not in CONNECTORS:
        raise ValueError(f"unknown source {source!r}; known: {sorted(CONNECTORS)}")
    return CONNECTORS[source].fetch_board(slug)
