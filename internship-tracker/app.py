from pathlib import Path

from flask import Flask, jsonify, request, render_template, send_file, abort

import db
import tailoring

app = Flask(__name__)
GENERATED_DIR = Path(__file__).parent / "data" / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

db.init_db()


@app.route("/")
def index():
    return render_template("index.html")


# ---------- profile ----------

@app.route("/api/profile", methods=["GET"])
def get_profile():
    return jsonify(db.get_profile())


@app.route("/api/profile", methods=["PUT"])
def put_profile():
    data = request.get_json(force=True)
    return jsonify(db.save_profile(data))


# ---------- jobs ----------

@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    status = request.args.get("status")
    return jsonify(db.list_jobs(status))


@app.route("/api/jobs", methods=["POST"])
def post_job():
    data = request.get_json(force=True)
    try:
        job, conflict = db.add_job(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if conflict:
        return jsonify({
            "error": "duplicate",
            "message": f"You already have {conflict['title']} at {conflict['company']} tracked "
                       f"(status: {conflict['status']}). Not adding it again.",
            "existing": conflict,
        }), 409
    return jsonify(job), 201


@app.route("/api/jobs/<int:job_id>", methods=["GET"])
def get_job(job_id):
    job = db.get_job(job_id)
    if not job:
        abort(404)
    return jsonify(job)


@app.route("/api/jobs/<int:job_id>", methods=["PATCH"])
def patch_job(job_id):
    if not db.get_job(job_id):
        abort(404)
    fields = request.get_json(force=True)
    if fields.get("status") == "applied":
        fields.setdefault("applied_at", db.now_iso())
    job = db.update_job(job_id, fields)
    return jsonify(job)


@app.route("/api/jobs/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
    ok = db.delete_job(job_id)
    if not ok:
        abort(404)
    return jsonify({"deleted": True})


def _tailor_job(job: dict, profile: dict) -> dict:
    keywords = tailoring.extract_keywords(job.get("description", ""))
    matched, missing = tailoring.match_resume_skills(profile.get("skills", []), keywords)
    score = tailoring.compute_match_score(matched, keywords)

    resume_path = GENERATED_DIR / f"resume_job{job['id']}.docx"
    cover_path = GENERATED_DIR / f"cover_letter_job{job['id']}.docx"
    tailoring.generate_resume_docx(profile, job, matched, str(resume_path))
    tailoring.generate_cover_letter_docx(profile, job, matched, str(cover_path))

    new_status = "ready" if job["status"] == "queued" else job["status"]
    return db.update_job(job["id"], {
        "match_score": score,
        "keywords_matched": matched,
        "keywords_missing": missing,
        "resume_path": str(resume_path),
        "cover_letter_path": str(cover_path),
        "status": new_status,
    })


@app.route("/api/jobs/<int:job_id>/tailor", methods=["POST"])
def tailor_job(job_id):
    job = db.get_job(job_id)
    if not job:
        abort(404)
    profile = db.get_profile()
    updated = _tailor_job(job, profile)
    return jsonify(updated)


@app.route("/api/activate", methods=["POST"])
def activate():
    """The 'Activate Assistant' button: tailors materials for every queued
    posting. Nothing here touches LinkedIn or submits anything — it only
    generates draft documents for you to review and send yourself."""
    profile = db.get_profile()
    queued = db.list_jobs(status="queued")
    results = [_tailor_job(job, profile) for job in queued]
    return jsonify({"tailored": len(results), "jobs": results})


@app.route("/api/jobs/<int:job_id>/download/resume")
def download_resume(job_id):
    job = db.get_job(job_id)
    if not job or not job.get("resume_path"):
        abort(404)
    return send_file(job["resume_path"], as_attachment=True,
                      download_name=f"resume_{job['company']}_{job['title']}.docx".replace(" ", "_"))


@app.route("/api/jobs/<int:job_id>/download/cover-letter")
def download_cover_letter(job_id):
    job = db.get_job(job_id)
    if not job or not job.get("cover_letter_path"):
        abort(404)
    return send_file(job["cover_letter_path"], as_attachment=True,
                      download_name=f"cover_letter_{job['company']}_{job['title']}.docx".replace(" ", "_"))


@app.route("/api/stats")
def get_stats():
    return jsonify(db.stats())


if __name__ == "__main__":
    app.run(debug=True, port=5050)
