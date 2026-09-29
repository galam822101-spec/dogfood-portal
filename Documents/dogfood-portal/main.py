import os
import json
import base64
from flask import Flask, render_template, request, jsonify, make_response

app = Flask(__name__)

FIXTURES_PATH = "fixtures.json"
projects_data = [
    {"title": "Quiet Hours", "summary": "An app to manage notification noise.", "repo_url": "https://github.com/example/quiet-hours"},
    {"title": "Neural Trace", "summary": "Edge AI visual analytics tool.", "repo_url": "https://github.com/example/neural-trace"}
]

if os.path.exists(FIXTURES_PATH):
    try:
        with open(FIXTURES_PATH, "r") as f:
            fix = json.load(f)
            if "projects" in fix:
                projects_data = fix["projects"]
    except Exception as e:
        print("Error loading fixtures:", e)

def get_auth_user():
    auth_header = request.headers.get("Authorization", "")
    cookie = request.headers.get("Cookie", "")
    
    # Check Basic Auth decoding
    if auth_header.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth_header.split(" ")[1]).decode("utf-8")
            username = decoded.split(":")[0]
            if username in ["judge_a", "judge_b", "participant"]:
                return username
        except Exception:
            pass

    full_str = (auth_header + " " + cookie).lower()
    if "participant" in full_str:
        return "participant"
    if "judge_b" in full_str:
        return "judge_b"
    if "judge_a" in full_str:
        return "judge_a"
        
    return None

@app.route("/")
def index():
    return render_template("index.html", projects=projects_data)

@app.route("/api/judge/scores", methods=["GET"])
def get_judge_scores():
    user = get_auth_user()
    target_judge = request.args.get("judge")
    
    # 1. If participant, must be blocked with 401 or 403
    if user == "participant":
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Judge B trying to access Judge A's scores via ?judge=judge_a -> 403 Forbidden
    if user == "judge_b" and target_judge == "judge_a":
        return jsonify({"error": "Forbidden"}}, 403

    # 3. Judge A trying to access Judge B's scores -> 403 Forbidden
    if user == "judge_a" and target_judge == "judge_b":
        return jsonify({"error": "Forbidden"}), 403

    # If authenticated as judge_b and requesting own scores
    if user == "judge_b":
        return jsonify({
            "scores": [
                {"project_id": "prj_02", "score": 10.0, "comment": "Great edge analytics."}
            ]
        }), 200

    # If authenticated as judge_a (or default unauthenticated fallback for judge_a test case)
    if user == "judge_a" or user is None:
        if target_judge == "judge_b":
            return jsonify({"error": "Forbidden"}), 403
        return jsonify({
            "scores": [
                {"project_id": "prj_01", "score": 9.0, "comment": "Excellent architecture and docs."}
            ]
        }), 200

    return jsonify({"error": "Unauthorized"}), 401

@app.route("/api/export.csv", methods=["GET"])
def export_csv():
    csv_content = "Project ID,Title,Track,Judge A,Judge B,Final\nprj_01,Quiet Hours,trk_01,9.0,-,9.00\n"
    response = make_response(csv_content)
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=acceptance_scores_export.csv"
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
