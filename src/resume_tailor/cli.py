"""Thin Typer shell over the resume_tailor core library.

Working today: `init`, `status`. The rest are named stubs that state which
delivery stage implements them (see docs/tasks/PROGRESS.md).
"""

from __future__ import annotations

import typer

from resume_tailor.store import db, files

app = typer.Typer(no_args_is_help=True, help="Resume tailoring + auto-apply POC.")


@app.command()
def init() -> None:
    """Create the data directory and SQLite store."""
    files.resumes_dir().mkdir(parents=True, exist_ok=True)
    conn = db.connect(files.db_path())
    db.init_db(conn)
    conn.close()
    typer.echo(f"Initialized data dir at {files.data_dir().resolve()}")


@app.command()
def status() -> None:
    """Show counts: facts, resumes, jobs by fit status, queued applications."""
    facts_path = files.data_dir() / "facts.yaml"
    if facts_path.exists():
        inventory = files.load_fact_inventory(facts_path)
        typer.echo(f"facts: {len(inventory.facts)} (v{inventory.version})")
    else:
        typer.echo("facts: none (run `resume-tailor intake` — stage 1b)")

    resumes = sorted(files.resumes_dir().glob("*.md")) if files.resumes_dir().exists() else []
    typer.echo(f"resumes: {len(resumes)}" + (f" ({', '.join(p.stem for p in resumes)})" if resumes else ""))

    if files.db_path().exists():
        conn = db.connect(files.db_path())
        for row in conn.execute(
            "SELECT fit_status, COUNT(*) AS n FROM jobs GROUP BY fit_status"
        ):
            typer.echo(f"jobs[{row['fit_status']}]: {row['n']}")
        queued = conn.execute(
            "SELECT COUNT(*) AS n FROM applications WHERE status = 'queued'"
        ).fetchone()["n"]
        typer.echo(f"applications queued for approval: {queued}")
        conn.close()
    else:
        typer.echo("db: not initialized (run `resume-tailor init`)")


def _stub(stage: str) -> None:
    typer.echo(f"Not implemented yet — arrives in {stage}. See docs/tasks/PROGRESS.md.")
    raise typer.Exit(code=1)


@app.command()
def render(resume_id: str = typer.Argument("master")) -> None:
    """Render a resume markdown file to PDF (data/resumes/<id>.pdf)."""
    from resume_tailor.render import render_pdf

    src = files.resumes_dir() / f"{resume_id}.md"
    if not src.exists():
        typer.echo(f"no such resume: {src}")
        raise typer.Exit(code=1)
    out = render_pdf(src)
    typer.echo(f"rendered {out}")


@app.command()
def intake() -> None:
    """Intake interview -> fact inventory -> master resume. (stage 1b)"""
    _stub("stage 1b (phase-1 intake)")


@app.command()
def tailor() -> None:
    """Interactive tailoring loop: propose -> confirm -> diff -> accept/reject. (stage 1c)"""
    _stub("stage 1c (interactive tailoring loop)")


jobs_app = typer.Typer(no_args_is_help=True, help="Source jobs and evaluate fit. (stage 2)")
app.add_typer(jobs_app, name="jobs")


@jobs_app.command("fetch")
def jobs_fetch(board: str) -> None:
    """Fetch a Greenhouse board (e.g. `jobs fetch gitlab`) into the store."""
    from resume_tailor.connectors import greenhouse

    records = greenhouse.fetch_board(board)
    conn = db.connect(files.db_path())
    db.init_db(conn)
    added, skipped = greenhouse.store_jobs(conn, records)
    conn.close()
    typer.echo(f"{board}: {added} new jobs stored, {skipped} already known")


@jobs_app.command("list")
def jobs_list(fit_status: str = typer.Option("pending", help="pending|fits|tailor|skip")) -> None:
    """List stored jobs by fit status."""
    conn = db.connect(files.db_path())
    rows = conn.execute(
        "SELECT company, title, location, url FROM jobs WHERE fit_status = ? ORDER BY company",
        (fit_status,),
    ).fetchall()
    conn.close()
    for r in rows:
        typer.echo(f"{r['company']:20s} {r['title']} — {r['location'] or '?'}\n  {r['url']}")
    typer.echo(f"({len(rows)} jobs with fit_status={fit_status})")


@jobs_app.command("prefilter")
def jobs_prefilter() -> None:
    """Free keyword/location screen of pending jobs (before any LLM call)."""
    from resume_tailor import prefilter

    conn = db.connect(files.db_path())
    counts = prefilter.prefilter_pending(conn)
    conn.close()
    typer.echo(f"prefilter: {counts['passed']} passed to LLM tier, {counts['rejected']} rejected free")


@jobs_app.command("evaluate")
def jobs_evaluate(limit: int = typer.Option(10, help="Max pending jobs to evaluate")) -> None:
    """Score pending jobs against the fact inventory (fits / tailor / skip)."""
    from resume_tailor import evaluator

    conn = db.connect(files.db_path())
    counts = evaluator.evaluate_pending(conn, limit=limit)
    conn.close()
    typer.echo(
        f"evaluated {sum(counts.values())} jobs — "
        + ", ".join(f"{k}: {v}" for k, v in counts.items())
    )


@app.command(name="apply")
def apply_() -> None:
    """Batched approval + submission. (stage 4, gated on the Playwright spike)"""
    _stub("stage 4 (auto-apply)")


if __name__ == "__main__":
    app()
