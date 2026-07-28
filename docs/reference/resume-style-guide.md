# Resume style guide — one page by default

Decision (Gary, 2026-07-27): **every rendered resume PDF fits one page by default.**
This guide records why and how, so the rule survives across sessions and agents.

## Why one page (the honest reason)

One page does **not** help the ATS parser — applicant-tracking software reads the text
regardless of length; a clean two-page resume parses exactly as well as a one-page one.
What actually matters for the ATS is what this project already does: real selectable text
(not an image), a single column, standard section headings, no tables or graphics.

One page helps the **human** who reads the resume *after* the ATS surfaces it. Recruiters
skim in ~6–10 seconds, and for a mid-level candidate (~5 years) a crisp one-pager reads as
focused and senior; two pages read as padded. So one page is a real benefit — for the
reader, not the software. Optimize for it for that reason, not a myth.

## How it's enforced

`resume_tailor.render.render_pdf(..., one_page=True)` (the default) does two things, in order:

1. **Dense, ATS-safe stylesheet** — Letter page, 0.42in × 0.6in margins, 10pt Georgia,
   1.24 line-height, tight section spacing. This alone fits a full ~25-bullet resume on
   one page (the confirmed master fits with *zero* content dropped).
2. **Bullet trimming, only if still overflowing** — trims each role to its top-N bullets
   (never below `min_bullets_per_role=3`), re-rendering until it fits. Whole bullets are
   dropped so fact-citations stay intact. **The source `.md` is never modified** — only the
   PDF is capped. Because the tailoring engine orders strongest-first, "top-N" is the most
   relevant N; for the master, it's the user-confirmed order.

The tailoring engine (`tailoring.build_system_prompt`) also *targets* one page at draft
time — it's told to prefer the 4–5 strongest bullets per role and drop the weakest rather
than pad. So variants arrive concise, and trimming rarely triggers.

## Using it

- `resume-tailor render <id>` — one page by default; prints the final page count, and
  WARNS if it couldn't fit one (meaning: trim bullets in the `.md` yourself).
- `resume-tailor render <id> --full` — opt out, allow multi-page (rare; e.g. a senior CV).

## If a resume won't fit one page

The floor is 3 bullets/role. If a resume still overflows at the floor, the content is
genuinely too long — shorten bullet wording or cut a low-value role in the `.md`. Don't
lower the floor or shrink the font further; past this density it stops reading cleanly.
