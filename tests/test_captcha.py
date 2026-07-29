from resume_tailor.apply.captcha import detect_captcha


class FakePage:
    """Minimal stand-in: locators/JS match by substring against 'present' signals."""
    def __init__(self, present_selectors, js_true=()):
        self._present = present_selectors
        self._js_true = js_true

    def locator(self, selector):
        return _Loc(any(p in selector for p in self._present))

    def evaluate(self, script):
        return any(k in script for k in self._js_true)


class _Loc:
    def __init__(self, hit): self._hit = hit
    def count(self): return 1 if self._hit else 0


def test_detects_invisible_recaptcha_via_badge():
    page = FakePage({".grecaptcha-badge"}, js_true=("___grecaptcha_cfg",))
    r = detect_captcha(page)
    assert r.present and r.kind == "recaptcha-v3"
    assert not r.unattended_submit_ok
    assert "human" in r.design_note.lower()


def test_detects_recaptcha_enterprise():
    page = FakePage({"recaptcha/enterprise"})
    r = detect_captcha(page)
    assert r.present and r.kind == "recaptcha-v3"


def test_detects_recaptcha_v2_checkbox():
    page = FakePage({"anchor", "data-sitekey"})
    r = detect_captcha(page)
    assert r.kind == "recaptcha-v2" and r.present


def test_detects_hcaptcha():
    page = FakePage({"hcaptcha"})
    assert detect_captcha(page).kind == "hcaptcha"


def test_no_captcha_allows_unattended():
    page = FakePage({"button[type='submit']"})
    r = detect_captcha(page)
    assert not r.present and r.kind == "none"
    assert r.unattended_submit_ok and r.submit_button
