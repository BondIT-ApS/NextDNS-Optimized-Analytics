# file: backend/app.py
from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from models import init_db, get_logs, add_log
import os

app = Flask(__name__)
auth = HTTPBasicAuth()

# API Key for authentication
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY")

users = {"admin": LOCAL_API_KEY}

@auth.verify_password
def verify_password(username, password):
    return username in users and users[username] == password

@app.route("/logs", methods=["GET"])
@auth.login_required
def logs():
    exclude_domains = request.args.getlist("exclude")
    logs = get_logs(exclude_domains)
    return jsonify({"data": logs})

if __name__ == "__main__":
    init_db()  # Ensure the database is initialized
    app.run(host="0.0.0.0", port=5000)
