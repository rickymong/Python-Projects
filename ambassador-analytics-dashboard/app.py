"""
The backend for my ambassador dashboard.

I'm a Google Student Ambassador and I wanted one place to see how my events and
posts are actually doing instead of checking five different tabs. This is a small
Flask API that reads the numbers from data/metrics.json and hands them to the
frontend, which draws the charts.

Right now the data is a json file I fill in myself. The idea is to later swap that
out for real pulls from the different analytics pages, but the api stays the same
either way so the frontend doesn't have to change.

To run it:
    pip install -r requirements.txt
    python app.py     (opens at http://127.0.0.1:5000)
"""

from __future__ import annotations

import json
import os

from flask import Flask, jsonify, render_template

app = Flask(__name__, template_folder=".")

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "metrics.json")


def load_data() -> dict:
    # read the metrics file fresh each time so I can edit it while the server runs
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/summary")
def api_summary():
    # the totals for the tiles at the top
    data = load_data()
    months = data["months"]
    return jsonify({
        "events": sum(m["events"] for m in months),
        "attendees": sum(m["attendees"] for m in months),
        "signups": sum(m["gemini_signups"] for m in months),
        "reach": sum(m["social_reach"] for m in months),
        "site_visits": sum(m["site_visits"] for m in months),
    })


@app.get("/api/timeseries")
def api_timeseries():
    # month-by-month numbers for the charts
    data = load_data()
    months = data["months"]
    return jsonify({
        "labels": [m["month"] for m in months],
        "attendees": [m["attendees"] for m in months],
        "signups": [m["gemini_signups"] for m in months],
        "reach": [m["social_reach"] for m in months],
        "site_visits": [m["site_visits"] for m in months],
    })


@app.get("/api/events")
def api_events():
    # the list of individual events I've run
    return jsonify(load_data()["events"])


if __name__ == "__main__":
    app.run(debug=True)
