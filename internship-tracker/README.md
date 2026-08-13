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

## What this deliberately does NOT do

It does not touch LinkedIn, does not scrape profiles, does not message
anyone, and does not submit any application on its own. Every document is a
draft for you to review, edit, and send yourself. See the note in the app's
header for why: automating LinkedIn violates its Terms of Service and risks
a permanent account ban, and mass automated outreach to strangers is spam.
This tool focuses on the parts that are actually safe and useful to
automate — tracking and drafting.

## Running it locally

```bash
cd internship-tracker
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5050**.

Data is stored locally in `data/tracker.db` (SQLite) and generated documents
in `data/generated/` — both are gitignored, so your resume content and
application history never leave your machine unless you choose to share the
downloaded files.

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
   yourself, then apply through the company's own site/Workday/LinkedIn
   Easy Apply, and update the posting's status on the board.

## Tech

Flask + SQLite (stdlib `sqlite3`, no ORM) on the backend, `python-docx` for
document generation, and a dependency-free HTML/CSS/vanilla-JS frontend —
no build step, no external CDN calls, works fully offline once installed.
