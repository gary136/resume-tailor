"""Apply engine (stage 4) — DEV-MODE ONLY.

Fills real ATS application forms from the applicant profile + a resume PDF, as
rehearsal. There is deliberately NO submit code path anywhere in this package —
real submission is a separate, later, batched-approval-gated capability that
does not exist yet. See spike/FINDINGS.md and PROGRESS.md.
"""
