"""CAPTCHA DETECTION for the apply flow — reconnaissance only, never bypass.

This answers a design question: what bot-protection guards the submit step, and
does it make *unattended* auto-submit feasible? It only inspects the page DOM.

It deliberately does NOT solve, bypass, or evade any CAPTCHA — that would be
anti-abuse circumvention and a ToS violation. The finding instead informs the
design: where a human-verification challenge exists (especially invisible,
score-based reCAPTCHA v3), the correct model is human-in-the-loop — the person
reviews the filled form and presses submit themselves. Automating around the
challenge is out of scope by policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CaptchaReport:
    present: bool
    kind: str                       # "recaptcha-v2" | "recaptcha-v3" | "hcaptcha" | "none" | "unknown"
    signals: list[str] = field(default_factory=list)
    submit_button: bool = False
    unattended_submit_ok: bool = False   # True only when nothing blocks a headless submit

    @property
    def design_note(self) -> str:
        if not self.present:
            return ("No bot-protection detected on this form. Unattended submit *might* work, "
                    "but confirm on a real (user-approved) submit before trusting it.")
        if self.kind == "recaptcha-v3":
            return ("Invisible score-based reCAPTCHA v3: a headless/automated submit is likely "
                    "flagged as a bot and blocked or silently down-scored. DESIGN: the human "
                    "reviews the filled form and presses submit (a real browser, real session). "
                    "Do NOT attempt to defeat it.")
        if self.kind in ("recaptcha-v2", "hcaptcha"):
            return ("Interactive challenge (checkbox/puzzle) can appear at submit. DESIGN: the "
                    "human completes it and presses submit. No automated bypass.")
        return ("Some bot-protection present. Treat submit as human-in-the-loop until proven "
                "otherwise on a real approved submit.")


def detect_captcha(page) -> CaptchaReport:
    """Inspect an application page for bot-protection. Read-only; never submits.

    reCAPTCHA (incl. Enterprise) loads its scripts lazily, so this touches a field
    first and relies on the durable badge + config-object signals, not just script URLs.
    """
    signals: list[str] = []

    def _has(selector: str) -> bool:
        try:
            return page.locator(selector).count() > 0
        except Exception:
            return False

    def _js(expr: str) -> bool:
        try:
            return bool(page.evaluate(f"() => {expr}"))
        except Exception:
            return False

    # nudge the form so lazily-injected challenge scripts load, then settle
    try:
        page.locator("#first_name, input[type='text']").first.fill("test", timeout=2000)
        page.wait_for_timeout(2000)
    except Exception:
        pass

    badge = _has(".grecaptcha-badge")                       # invisible reCAPTCHA badge
    cfg = _js("!!window.___grecaptcha_cfg")
    grecaptcha_obj = _js("!!window.grecaptcha")
    checkbox_frame = _has("iframe[src*='/recaptcha/'][src*='anchor'], .g-recaptcha, [data-sitekey]")
    enterprise = _has("script[src*='recaptcha/enterprise']") or _js(
        "!!(window.grecaptcha && window.grecaptcha.enterprise)")
    render_script = _has("script[src*='render=']") or _has(
        "script[src*='recaptcha.net'], script[src*='gstatic.com/recaptcha']")
    hcaptcha = _has("iframe[src*='hcaptcha'], .h-captcha, script[src*='hcaptcha.com']")

    recaptcha = badge or cfg or grecaptcha_obj or checkbox_frame or enterprise or render_script

    if hcaptcha:
        present, kind = True, "hcaptcha"
        signals.append("hCaptcha element/script present")
    elif recaptcha:
        present = True
        if checkbox_frame and not badge:
            kind = "recaptcha-v2"
            signals.append("reCAPTCHA v2 checkbox challenge present")
        else:
            kind = "recaptcha-v3"   # invisible / score-based (incl. Enterprise)
            signals.append("invisible score-based reCAPTCHA present"
                           + (" (Enterprise)" if enterprise else ""))
            if badge:
                signals.append(".grecaptcha-badge visible")
    else:
        present, kind = False, "none"

    submit_button = _has("button[type='submit'], input[type='submit'], "
                         "button:has-text('Submit'), button:has-text('Submit application')")
    return CaptchaReport(
        present=present, kind=kind, signals=signals,
        submit_button=submit_button,
        unattended_submit_ok=(not present),
    )
