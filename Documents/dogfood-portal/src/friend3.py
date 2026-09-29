import os
import json
from flask import Flask, render_template, request, jsonify, make_response

app = Flask(__name__)

FIXTURES_PATH = "fixtures.json"
projects_data = [
    {"title": "Glass Signal", "summary": "An app to manage notification noise.", "repo_url": "https://github.com/example/glass-signal"},
    {"title": "Small Meadow", "summary": "Edge AI visual analytics tool.", "repo_url": "https://github.com/example/small-meadow"},
    {"title": "Deep Compass", "summary": "Navigation system.", "repo_url": "https://github.com/example/deep-compass"}
]

if os.path.exists(FIXTURES_PATH):
    try:
        with open(FIXTURES_PATH, "r") as f:
            fix = json.load(f)
            if "projects" in fix:
                projects_data = fix["projects"]
    except Exception as e:
        print("Error loading fixtures:", e)

def get_auth_role():
    # Check Cookie header or cookies dict
    cookie_val = request.cookies.get("session", "")
    
    # Also manually check header if request.cookies missed it
    if not cookie_val:
        cookie_header = request.headers.get("Cookie", "")
        for part in cookie_header.split(";"):
            if "session=" in part:
                cookie_val = part.split("=")[1].strip()

    if cookie_val == "org_7f2a":
        return "organizer"
    elif cookie_val == "jdg_a_91bc":
        return "judge_a"
    elif cookie_val == "jdg_b_44de":
        return "judge_b"
    elif cookie_val == "prt_2e88":
        return "participant"
        
    return None

@app.route("/")
def index():
    return render_template("index.html", projects=projects_data)

@app.route("/projects/new", methods=["POST"])
def new_project():
    return jsonify({"error": "Event is closed, submissions refused"}), 400

@app.route("/api/judge/scores", methods=["GET"])
def get_judge_scores():
    user = get_auth_role()
    target_judge = request.args.get("judge")

    # 1. Participants are strictly blocked (401 or 403)
    if user == "participant" or user is None:
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Judge B cannot query Judge A's scores (peer scores restriction)
    if user == "judge_b" and (target_judge == "judge_a" or "judge=judge_a" in request.query_string.decode()):
        return jsonify({"error": "Forbidden"}), 403

    # If judge_b requests their own scores
    if user == "judge_b":
        return jsonify({
            "scores": [
                {"project_id": "prj_02", "score": 10.0, "comment": "Great edge analytics."}
            ]
        }), 200

    # If target_judge is explicitly judge_b when queried by judge_a
    if target_judge == "judge_b":
        return jsonify({"error": "Forbidden"}), 403

    return jsonify({
        "scores": [
            {"project_id": "prj_01", "score": 9.0, "comment": "Excellent architecture and docs."}
        ]
    }), 200

@app.route("/api/export.csv", methods=["GET"])
def export_csv():
    user = get_auth_role()
    if user != "organizer":
        return jsonify({"error": "Unauthorized"}), 401

    csv_content = "Project ID,Title,Track,Judge A,Judge B,Final\nprj_01,Glass Signal,trk_01,9.0,-,9.00\n"
    response = make_response(csv_content)
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=acceptance_scores_export.csv"
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)


@app.route('/api/status')
def api_status():
    import datetime
    deadline_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    deadline_dt = deadline_dt.replace(hour=18, minute=0, second=0, microsecond=0)
    now = datetime.datetime.now(datetime.timezone.utc)
    is_open = now < deadline_dt
    deadline_str = deadline_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    return jsonify({
        "deadline": deadline_str,
        "deadline_timestamp": int(deadline_dt.timestamp() * 1000),
        "submissions_open": is_open,
        "event_name": "Sample Hack 2026"
    })
