# Internship Tracker

A local dashboard for tracking internship applications and drafting honestly
tailored resumes and cover letters — **not** a LinkedIn bot.

## What this does

- Tracks postings you add yourself (paste in company, role, description, URL, deadline)
- Blocks duplicates automatically (same company + role can't be added twice)
- "Activate Assistant" scans every *queued* posting's description against a
  cross-industry skills dictionary, compares it to the skills/experience you
  entered in your profile, and generates a tailored `.docx` resume + cover
  letter per posting — using only what's true, mirrored into the job's own
  phrasing where it genuinely overlaps
- Shows a match score, matched keywords, and "consider adding (only if true)"
  gaps, so you can see exactly what's driving the score
- Lets you move each posting through a pipeline (Queued → Ready → Applied →
  Interview → Offer / Rejected) and download the generated documents
- **Fill Assist** opens a posting's own application page in a real, visible
  browser window (your own persistent profile, so logins you've already done
  stick around) and fills in whatever it can confidently match to your
  profile — name, contact info, school, resume/cover-letter upload if you've
  tailored one. It never touches a submit button; you review everything
  (especially screening/EEO/work-authorization questions, which it leaves
  alone on purpose) and submit yourself in that same window. It refuses to
  run at all on linkedin.com — see "What this deliberately does NOT do."

## What this deliberately does NOT do

It does not touch LinkedIn (Fill Assist explicitly refuses to open a
linkedin.com URL), does not scrape profiles, does not message anyone, and
does not click submit on any application, anywhere, ever. Every document
and every filled form is left for you to review, edit, and send yourself.
Automating LinkedIn's apply flow violates its Terms of Service and risks a
permanent account ban; most ATS platforms (Workday, Greenhouse, etc.) also
prohibit automated submissions and run bot detection specifically on the
submit action. This tool focuses on the parts that are actually safe and
useful to automate — tracking, drafting, and pre-filling — and stops right
before the one action that has to stay yours.

## Running it locally

```bash
cd internship-tracker
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium   # one-time, only needed for Fill Assist
python app.py
```

Then open **http://127.0.0.1:5050**.

Data is stored locally in `data/tracker.db` (SQLite), generated documents in
`data/generated/`, and Fill Assist's browser profile (cookies/logins for
sites you've filled a form on) in `data/browser_profile/` — all three are
gitignored, so none of it leaves your machine unless you choose to share it.

## Using it

1. **My Profile** — enter your real contact info, a short summary, your
   actual skills (comma or Enter to add as chips), and your experience/
   education with real bullet points. This is the only source of truth;
   nothing gets fabricated on top of it.
2. **Add Posting** — paste in a job description for an internship you found.
   Duplicate company+title pairs are rejected with a toast so you never
   double-apply.
3. **Activate Assistant** (top right) — tailors materials for every posting
   still in "Queued" status in one click. You can also tailor a single
   posting from its card.
4. Download the generated resume/cover letter, review and adjust the wording
   yourself.
5. For non-LinkedIn postings with a URL, **Fill Assist** opens the real
   application page and pre-fills what it can. A browser window will pop up
   on your screen — finish anything it left blank, double-check what it
   filled, attach files if it couldn't, and click submit yourself.
6. Update the posting's status on the board once you've applied.

## Tech

Flask + SQLite (stdlib `sqlite3`, no ORM) on the backend, `python-docx` for
document generation, and a dependency-free HTML/CSS/vanilla-JS frontend —
no build step, no external CDN calls, works fully offline once installed.
