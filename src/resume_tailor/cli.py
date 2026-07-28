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
def render(
    resume_id: str = typer.Argument("master"),
    full: bool = typer.Option(False, "--full", help="Allow multi-page (default: fit to one page)"),
) -> None:
    """Render a resume markdown file to PDF (data/resumes/<id>.pdf). One page by default."""
    from resume_tailor.render import render_pdf

    src = files.resumes_dir() / f"{resume_id}.md"
    if not src.exists():
        typer.echo(f"no such resume: {src}")
        raise typer.Exit(code=1)
    out, pages = render_pdf(src, one_page=not full)
    note = "" if pages == 1 else f" — WARNING: {pages} pages (couldn't fit one; trim bullets in the .md)"
    typer.echo(f"rendered {out} ({pages} page{'s' if pages != 1 else ''}){note}")


@app.command()
def intake() -> None:
    """Intake interview -> fact inventory -> master resume. (stage 1b)"""
    _stub("stage 1b (phase-1 intake)")


@app.command()
def tailor(job_id_prefix: str) -> None:
    """Draft a validator-gated variant for a job (by job_id prefix); prints the diff."""
    from resume_tailor import tailoring
    from resume_tailor.llm import get_backend
    from resume_tailor.store.files import load_fact_inventory, load_preferences

    conn = db.connect(files.db_path())
    row = conn.execute(
        "SELECT job_id FROM jobs WHERE job_id LIKE ?", (job_id_prefix + "%",)
    ).fetchone()
    if row is None:
        typer.echo(f"no job matching {job_id_prefix!r}")
        raise typer.Exit(code=1)
    job = db.get_job(conn, row["job_id"])
    conn.close()
    family = job.job_family or "general"
    master_text = (files.resumes_dir() / "master.md").read_text()

    variant, errors = tailoring.generate_variant(
        get_backend(), load_fact_inventory(), load_preferences(), master_text, job, family
    )
    if variant is None or errors:
        typer.echo("draft FAILED the no-fabrication gate:")
        for e in errors:
            typer.echo(f"  - {e}")
        raise typer.Exit(code=1)
    path = tailoring.save_variant(variant, family, files.resumes_dir())
    typer.echo(f"draft variant saved: {path} (status: draft — confirm after review)\n")
    typer.echo(tailoring.diff_against_master(master_text, variant))


jobs_app = typer.Typer(no_args_is_help=True, help="Source jobs and evaluate fit. (stage 2)")
app.add_typer(jobs_app, name="jobs")


@jobs_app.command("fetch")
def jobs_fetch(board: str, source: str = typer.Option("greenhouse", help="greenhouse|ashby|lever")) -> None:
    """Fetch one board into the store (e.g. `jobs fetch ramp --source ashby`)."""
    from resume_tailor.connectors import CONNECTORS, fetch_board

    records = fetch_board(source, board)
    conn = db.connect(files.db_path())
    db.init_db(conn)
    added, skipped = CONNECTORS[source].store_jobs(conn, records)
    conn.close()
    typer.echo(f"{source}/{board}: {added} new jobs stored, {skipped} already known")


@jobs_app.command("fetch-all")
def jobs_fetch_all() -> None:
    """Fetch every board in the search profile's target_boards, via each ATS connector."""
    from resume_tailor.connectors import CONNECTORS, fetch_board
    from resume_tailor.prefilter import load_profile

    conn = db.connect(files.db_path())
    db.init_db(conn)
    total_new = total_known = 0
    for source, slugs in (load_profile().get("target_boards") or {}).items():
        for slug in slugs:
            try:
                records = fetch_board(source, slug)
                added, skipped = CONNECTORS[source].store_jobs(conn, records)
                total_new += added
                total_known += skipped
                typer.echo(f"  {source}/{slug}: {added} new, {skipped} known")
            except Exception as exc:
                typer.echo(f"  {source}/{slug}: FAILED — {type(exc).__name__}: {exc}")
    conn.close()
    typer.echo(f"total: {total_new} new jobs stored, {total_known} already known")


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


@jobs_app.command("review")
def jobs_review(
    status: str = typer.Option("fits,tailor", help="Comma-separated: fits,tailor,skip,pending"),
) -> None:
    """Readable review queue: verdicts with rubric breakdown, evidence, and URLs."""
    from resume_tailor.review import render_queue

    conn = db.connect(files.db_path())
    db.init_db(conn)  # applies additive migrations to older stores
    typer.echo(render_queue(conn, tuple(s.strip() for s in status.split(","))))
    conn.close()


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
