"""
Honest keyword-alignment engine.

This intentionally does NOT invent skills or experience. It only:
  1. extracts candidate keywords/phrases that actually appear in a job
     description, using a broad cross-industry skills dictionary
  2. intersects those against the skills the user themselves entered
  3. re-orders / mirrors phrasing so the *real* overlap is easy for an ATS
     and a human reviewer to find

Anything in "missing" is a suggestion to double check your resume wording,
never something to fabricate.
"""
import re
from datetime import datetime

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

STOPWORDS = {
    "the", "and", "for", "are", "with", "you", "your", "our", "this", "that",
    "will", "have", "has", "from", "who", "all", "can", "not", "but", "any",
    "may", "such", "into", "than", "then", "them", "they", "these", "those",
    "about", "over", "under", "per", "etc", "including", "include", "includes",
    "role", "job", "work", "working", "team", "teams", "company", "years",
    "year", "experience", "experiences", "ability", "abilities", "strong",
    "excellent", "good", "great", "must", "should", "would", "could", "also",
    "other", "using", "used", "use", "within", "across", "we", "us", "our",
    "a", "an", "of", "to", "in", "on", "as", "is", "be", "or", "at", "by",
    "it", "its", "their", "his", "her", "he", "she", "if", "when", "while",
    "new", "one", "two", "three", "some", "each", "every", "more", "most",
    "up", "out", "so", "no", "yes", "do", "does", "did", "done",
}

# Canonical skill -> aliases (lowercase). Cross-industry on purpose: tech,
# data, business, finance, marketing, design, ops. Matching is dictionary
# based rather than fuzzy NLP so it never "hallucinates" a keyword that
# isn't actually in the posting.
SKILLS_DB = {
    "Python": ["python"],
    "Java": ["java "],
    "JavaScript": ["javascript", "js "],
    "TypeScript": ["typescript"],
    "C++": ["c++"],
    "C#": ["c#"],
    "SQL": ["sql"],
    "R": [" r programming", " r language"],
    "HTML/CSS": ["html", "css"],
    "React": ["react.js", "reactjs", "react "],
    "Node.js": ["node.js", "nodejs", "node "],
    "Git": ["git ", "github", "version control"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure"],
    "GCP": ["gcp", "google cloud"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Linux": ["linux", "unix"],
    "REST APIs": ["rest api", "restful"],
    "Machine Learning": ["machine learning", "ml "],
    "Deep Learning": ["deep learning"],
    "Data Analysis": ["data analysis", "data analytics"],
    "Data Visualization": ["data visualization", "dashboards"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "Excel": ["excel", "spreadsheets"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"],
    "A/B Testing": ["a/b test", "ab testing"],
    "Statistics": ["statistics", "statistical"],
    "Financial Modeling": ["financial modeling", "financial models"],
    "Financial Analysis": ["financial analysis", "financial analyst"],
    "Valuation": ["valuation", "dcf"],
    "Accounting": ["accounting", "gaap"],
    "Bloomberg Terminal": ["bloomberg terminal", "bloomberg"],
    "Forecasting": ["forecasting", "forecast"],
    "Budgeting": ["budgeting", "budget"],
    "Salesforce": ["salesforce"],
    "CRM": ["crm"],
    "SEO": ["seo", "search engine optimization"],
    "SEM": ["sem", "paid search"],
    "Social Media Marketing": ["social media"],
    "Content Marketing": ["content marketing", "content creation"],
    "Email Marketing": ["email marketing"],
    "Google Analytics": ["google analytics"],
    "Adobe Photoshop": ["photoshop"],
    "Adobe Illustrator": ["illustrator"],
    "Figma": ["figma"],
    "UI/UX Design": ["ui/ux", "user experience", "user interface"],
    "Wireframing": ["wireframe", "wireframing"],
    "Project Management": ["project management"],
    "Agile": ["agile", "scrum"],
    "JIRA": ["jira"],
    "Product Management": ["product management", "product roadmap"],
    "Market Research": ["market research"],
    "Business Development": ["business development"],
    "Supply Chain": ["supply chain"],
    "Logistics": ["logistics"],
    "Operations": ["operations management", "operations"],
    "Six Sigma": ["six sigma"],
    "Lean Manufacturing": ["lean manufacturing", "lean process"],
    "Customer Service": ["customer service", "client-facing"],
    "Sales": ["sales quota", "sales targets", "outbound sales", " sales "],
    "Negotiation": ["negotiation"],
    "Public Speaking": ["public speaking", "presentation skills"],
    "Communication": ["communication skills", "verbal and written"],
    "Leadership": ["leadership"],
    "Teamwork": ["teamwork", "collaborative", "cross-functional"],
    "Problem Solving": ["problem solving", "problem-solving", "analytical skills"],
    "Time Management": ["time management", "prioritiz"],
    "Attention to Detail": ["attention to detail", "detail-oriented"],
    "Research": ["research skills", "conducting research"],
    "Writing": ["writing skills", "copywriting", "technical writing"],
    "Editing": ["editing", "proofreading"],
    "Legal Research": ["legal research", "westlaw", "lexisnexis"],
    "Clinical Research": ["clinical research", "clinical trials"],
    "Laboratory Skills": ["laboratory", "lab techniques", "pipetting"],
    "CAD": ["cad ", "solidworks", "autocad"],
    "Circuit Design": ["circuit design", "pcb design"],
    "MATLAB": ["matlab"],
    "Data Structures & Algorithms": ["data structures", "algorithms"],
    "Cybersecurity": ["cybersecurity", "infosec", "penetration testing"],
    "Cloud Computing": ["cloud computing", "cloud infrastructure"],
    "Mobile Development": ["ios development", "android development", "swift", "kotlin"],
    "API Integration": ["api integration", "third-party api"],
    "Testing/QA": ["quality assurance", "unit testing", "test automation"],
}

# Build a flat lookup: alias phrase -> canonical name, longest phrases first
# so multi-word aliases are matched before their substrings.
_ALIAS_PAIRS = sorted(
    ((alias.strip(), canon) for canon, aliases in SKILLS_DB.items() for alias in aliases),
    key=lambda p: -len(p[0]),
)


def extract_keywords(job_description: str) -> list[str]:
    """Return canonical skills that literally appear in the job description,
    ordered by first appearance."""
    text = f" {job_description.lower()} "
    found = []
    seen = set()
    for alias, canon in _ALIAS_PAIRS:
        if canon in seen:
            continue
        pattern = r"(?<![a-z0-9])" + re.escape(alias.strip()) + r"(?![a-z0-9])"
        if re.search(pattern, text):
            found.append(canon)
            seen.add(canon)
    return found


def _normalize(term: str) -> str:
    return re.sub(r"[^a-z0-9+#/. ]", "", term.lower()).strip()


def match_resume_skills(resume_skills: list[str], jd_keywords: list[str]):
    """Case/whitespace-insensitive intersection. Returns (matched, missing),
    both using the job posting's own canonical phrasing."""
    resume_norm = {_normalize(s) for s in resume_skills}
    matched, missing = [], []
    for kw in jd_keywords:
        if _normalize(kw) in resume_norm:
            matched.append(kw)
        else:
            missing.append(kw)
    return matched, missing


def compute_match_score(matched: list[str], jd_keywords: list[str]) -> int:
    if not jd_keywords:
        return 0
    return round(100 * len(matched) / len(jd_keywords))


def _bullet_has_keyword(bullet: str, keywords: list[str]) -> bool:
    b = _normalize(bullet)
    return any(_normalize(k) in b for k in keywords)


def generate_resume_docx(profile: dict, job: dict, matched: list[str], out_path: str):
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)

    for section in doc.sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)

    name_p = doc.add_paragraph()
    name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = name_p.add_run(profile.get("name") or "Your Name")
    run.bold = True
    run.font.size = Pt(18)

    contact_bits = [b for b in [
        profile.get("email"), profile.get("phone"), profile.get("location"),
        profile.get("linkedin_url"), profile.get("portfolio_url"),
    ] if b]
    contact_p = doc.add_paragraph(" | ".join(contact_bits))
    contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Summary — mentions only skills the candidate actually listed AND that
    # genuinely appear in this posting.
    doc.add_paragraph()
    heading = doc.add_paragraph()
    heading.add_run("SUMMARY").bold = True
    top_matched = matched[:4]
    base_summary = profile.get("summary", "").strip()
    if top_matched:
        tail = f" Skilled in {', '.join(top_matched)}, applying that background to the {job.get('title', 'role')} role at {job.get('company', 'this company')}."
    else:
        tail = ""
    doc.add_paragraph((base_summary + tail).strip())

    # Skills — matched keywords surfaced first, in the job's own phrasing,
    # everything else the candidate listed follows.
    doc.add_paragraph()
    heading = doc.add_paragraph()
    heading.add_run("SKILLS").bold = True
    all_skills = profile.get("skills", [])
    matched_norm = {_normalize(m) for m in matched}
    rest = [s for s in all_skills if _normalize(s) not in matched_norm]
    ordered_skills = matched + rest
    doc.add_paragraph(" • ".join(ordered_skills) if ordered_skills else "—")

    # Experience — unchanged content, bullets that already demonstrate a
    # matched skill are simply listed first within each role.
    doc.add_paragraph()
    heading = doc.add_paragraph()
    heading.add_run("EXPERIENCE").bold = True
    for exp in profile.get("experience", []):
        role_p = doc.add_paragraph()
        role_p.add_run(f"{exp.get('title', '')} — {exp.get('company', '')}").bold = True
        if exp.get("dates") or exp.get("location"):
            meta = doc.add_paragraph(f"{exp.get('location', '')}  {exp.get('dates', '')}".strip())
            meta.runs[0].italic = True
        bullets = exp.get("bullets", [])
        bullets_sorted = sorted(bullets, key=lambda b: not _bullet_has_keyword(b, matched))
        for b in bullets_sorted:
            doc.add_paragraph(b, style="List Bullet")

    # Education — unchanged.
    doc.add_paragraph()
    heading = doc.add_paragraph()
    heading.add_run("EDUCATION").bold = True
    for edu in profile.get("education", []):
        edu_p = doc.add_paragraph()
        edu_p.add_run(f"{edu.get('school', '')} — {edu.get('degree', '')}").bold = True
        if edu.get("dates") or edu.get("details"):
            doc.add_paragraph(f"{edu.get('details', '')}  {edu.get('dates', '')}".strip())

    doc.save(out_path)


def generate_cover_letter_docx(profile: dict, job: dict, matched: list[str], out_path: str):
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    doc.add_paragraph(profile.get("name", ""))
    contact_bits = [b for b in [profile.get("email"), profile.get("phone"), profile.get("location")] if b]
    doc.add_paragraph(" | ".join(contact_bits))
    doc.add_paragraph(datetime.now().strftime("%B %d, %Y"))
    doc.add_paragraph()
    doc.add_paragraph(f"Hiring Team, {job.get('company', '')}")
    doc.add_paragraph()

    doc.add_paragraph(
        f"Dear {job.get('company', 'Hiring')} Team,"
    )
    doc.add_paragraph(
        f"I'm writing to apply for the {job.get('title', 'internship')} position at "
        f"{job.get('company', 'your company')}. {profile.get('summary', '').strip()}"
    )

    # Pull real bullets that back up the top matched skills, so every claim
    # traces to something already on the resume — nothing invented here.
    proof_bullets = []
    for exp in profile.get("experience", []):
        for b in exp.get("bullets", []):
            if _bullet_has_keyword(b, matched):
                proof_bullets.append(b)
    proof_bullets = proof_bullets[:2]

    if matched:
        body = f"My background aligns closely with what you're looking for, particularly in {', '.join(matched[:5])}."
        if proof_bullets:
            body += " For example: " + " ".join(proof_bullets)
        doc.add_paragraph(body)
    else:
        doc.add_paragraph(
            "I'd welcome the chance to bring my background to your team and grow into the areas this role requires."
        )

    doc.add_paragraph(
        f"I'd welcome the opportunity to discuss how I can contribute to {job.get('company', 'your team')}. "
        "Thank you for your time and consideration."
    )
    doc.add_paragraph()
    doc.add_paragraph("Sincerely,")
    doc.add_paragraph(profile.get("name", ""))

    doc.save(out_path)
