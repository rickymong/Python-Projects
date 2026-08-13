"""
Fill-assist: opens a real, visible browser window (your own persistent
profile, so logins you've already done stick around) on a job posting's own
application page, fills in the fields it can confidently match to your
profile, and stops. It never looks for or clicks a submit/apply button —
that decision, and everything it can't confidently fill (screening
questions, work-authorization/EEO questions, essay prompts), stays yours.

Deliberately refuses to run on linkedin.com — automating LinkedIn's own
apply flow is the specific behavior its Terms of Service and bot detection
target, regardless of whether the last click is automated.
"""
import queue
import re
import threading
from pathlib import Path
from urllib.parse import urlparse

from docx import Document
from playwright.sync_api import sync_playwright

PROFILE_DIR = Path(__file__).parent / "data" / "browser_profile"
BLOCKED_HOSTS = ("linkedin.com",)

# (field key, regex patterns to match against a form field's label/name/id).
# Order matters — more specific patterns are checked before generic ones so
# e.g. "First Name" doesn't get swallowed by a generic "name" rule.
TEXT_FIELD_MATCHERS = [
    ("email", [r"e-?mail"]),
    ("phone", [r"phone", r"mobile", r"telephone"]),
    ("linkedin_url", [r"linkedin"]),
    ("portfolio_url", [r"portfolio", r"personal site", r"\bgithub\b", r"\bwebsite\b"]),
    ("first_name", [r"first name", r"given name"]),
    ("last_name", [r"last name", r"surname", r"family name"]),
    ("full_name", [r"full name", r"your name", r"^name$"]),
    ("location", [r"\bcity\b", r"current location", r"\baddress\b"]),
    ("school", [r"school", r"university", r"college"]),
    ("degree", [r"degree", r"major", r"field of study"]),
]
FILE_FIELD_MATCHERS = [
    ("resume_file", [r"r[ée]sum[ée]", r"\bcv\b"]),
    ("cover_letter_file", [r"cover letter"]),
]
COVER_LETTER_TEXTAREA = [r"cover letter"]

FIELD_SCAN_JS = """
() => {
  const nodes = document.querySelectorAll(
    "input:not([type=hidden]):not([type=submit]):not([type=button])"
    + ":not([type=reset]):not([type=checkbox]):not([type=radio]), textarea, select"
  );
  const out = [];
  let idx = 0;
  for (const el of nodes) {
    let label = "";
    if (el.labels && el.labels.length) {
      label = Array.from(el.labels).map(l => l.innerText).join(" ");
    }
    if (!label && el.getAttribute("aria-label")) label = el.getAttribute("aria-label");
    if (!label && el.getAttribute("aria-labelledby")) {
      label = el.getAttribute("aria-labelledby").split(" ")
        .map(id => document.getElementById(id)?.innerText || "").join(" ");
    }
    if (!label) {
      const wrap = el.closest("label");
      if (wrap) label = wrap.innerText;
    }
    if (!label) label = el.getAttribute("placeholder") || "";
    el.setAttribute("data-fillassist-idx", String(idx));
    out.push({
      idx, tag: el.tagName.toLowerCase(), type: (el.type || "").toLowerCase(),
      name: el.name || "", id: el.id || "", label: label.trim().slice(0, 200),
    });
    idx += 1;
  }
  return out;
}
"""


def _read_docx_text(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _match(label: str, name: str, field_id: str, matchers):
    haystack = f"{label} {name} {field_id}".lower()
    for key, patterns in matchers:
        if any(re.search(p, haystack) for p in patterns):
            return key
    return None


def _value_for(key: str, profile: dict, job: dict):
    name = (profile.get("name") or "").strip()
    parts = name.split()
    education = profile.get("education") or []
    latest_edu = education[0] if education else {}
    return {
        "email": profile.get("email"),
        "phone": profile.get("phone"),
        "linkedin_url": profile.get("linkedin_url"),
        "portfolio_url": profile.get("portfolio_url"),
        "first_name": parts[0] if parts else None,
        "last_name": parts[-1] if len(parts) > 1 else None,
        "full_name": name or None,
        "location": profile.get("location"),
        "school": latest_edu.get("school"),
        "degree": latest_edu.get("degree"),
        "resume_file": job.get("resume_path") or None,
        "cover_letter_file": job.get("cover_letter_path") or None,
    }.get(key)


def _fill_application(context, job: dict, profile: dict) -> dict:
    url = job.get("url", "").strip()
    if not url:
        raise ValueError("This posting has no URL saved — add one before running fill-assist.")
    host = urlparse(url if "://" in url else f"https://{url}").netloc.lower()
    if any(blocked in host for blocked in BLOCKED_HOSTS):
        raise ValueError(
            "Fill-assist doesn't run on LinkedIn. Automating LinkedIn's own apply flow risks "
            "your account even in fill-only mode — use LinkedIn's native Easy Apply yourself."
        )

    page = context.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    fields = page.evaluate(FIELD_SCAN_JS)

    filled, skipped_no_data, left_for_you = [], [], []
    for f in fields:
        selector = f'[data-fillassist-idx="{f["idx"]}"]'
        label = f["label"] or f["name"] or f["id"] or "(unlabeled field)"

        if f["type"] == "file":
            key = _match(f["label"], f["name"], f["id"], FILE_FIELD_MATCHERS)
            if not key:
                continue
            value = _value_for(key, profile, job)
            if not value:
                skipped_no_data.append(label)
                continue
            page.locator(selector).set_input_files(value)
            filled.append(label)
            continue

        if f["tag"] == "textarea" and _match(f["label"], f["name"], f["id"], [("cover_letter_text", COVER_LETTER_TEXTAREA)]):
            cover_path = job.get("cover_letter_path")
            if not cover_path:
                skipped_no_data.append(label)
                continue
            page.locator(selector).fill(_read_docx_text(cover_path))
            filled.append(label)
            continue

        key = _match(f["label"], f["name"], f["id"], TEXT_FIELD_MATCHERS)
        if not key:
            left_for_you.append(label)
            continue
        value = _value_for(key, profile, job)
        if not value:
            skipped_no_data.append(label)
            continue
        try:
            if f["tag"] == "select":
                page.locator(selector).select_option(label=re.compile(re.escape(str(value)), re.I))
            else:
                page.locator(selector).fill(str(value))
            filled.append(label)
        except Exception:
            skipped_no_data.append(label)

    return {
        "filled": filled,
        "skipped_no_data": skipped_no_data,
        "left_for_you": left_for_you,
        "url": url,
    }


class BrowserWorker:
    """Runs all Playwright calls on one dedicated thread, since Playwright's
    sync API is bound to the OS thread that started it — Flask's own
    request threads can't touch it directly. The browser + its persistent
    profile (so site logins survive across runs) live for the life of the
    process and are only closed on app shutdown."""

    def __init__(self):
        self._q: queue.Queue = queue.Queue()
        self._ready = threading.Event()
        self._startup_error: str | None = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            PROFILE_DIR.mkdir(parents=True, exist_ok=True)
            playwright = sync_playwright().start()
            context = playwright.chromium.launch_persistent_context(
                str(PROFILE_DIR), headless=False, viewport={"width": 1300, "height": 900},
            )
        except Exception as e:
            self._startup_error = (
                f"Couldn't launch the browser ({e}). If this is the first run, install "
                "Chromium for Playwright with: python -m playwright install chromium"
            )
            self._ready.set()
            return
        self._ready.set()
        while True:
            job, profile, result_q = self._q.get()
            try:
                result_q.put(("ok", _fill_application(context, job, profile)))
            except Exception as e:
                result_q.put(("error", str(e)))

    def fill(self, job: dict, profile: dict, timeout: float = 45) -> dict:
        if not self._ready.wait(timeout=30):
            raise RuntimeError("Browser is still starting up — try again in a moment.")
        if self._startup_error:
            raise RuntimeError(self._startup_error)
        result_q: queue.Queue = queue.Queue()
        self._q.put((job, profile, result_q))
        try:
            status, value = result_q.get(timeout=timeout)
        except queue.Empty:
            raise RuntimeError("Fill-assist timed out waiting on the browser.")
        if status == "error":
            raise RuntimeError(value)
        return value


_worker = None
_worker_lock = threading.Lock()


def get_worker() -> BrowserWorker:
    global _worker
    with _worker_lock:
        if _worker is None:
            _worker = BrowserWorker()
        return _worker
