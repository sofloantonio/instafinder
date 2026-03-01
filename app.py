"""
Minimal web runner for yesitsme — runs the script on the server's IP (e.g. on Render).
Set INSTAGRAM_SESSION_ID in the environment; never commit it.
"""
import os
import subprocess
import re
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>Yes, it's me — run</title></head>
<body>
  <h1>Run yesitsme (uses this server's IP)</h1>
  <form method="post" action="/run">
    <p>Session ID (required): <input name="session_id" type="text" placeholder="Paste your Instagram sessionid cookie" style="width: 100%; max-width: 400px;" required></p>
    <p>Name (required): <input name="name" value="Jeremiah Bates" required></p>
    <p>Phone hint (e.g. +1 *** *** **30): <input name="phone" value="+1 *** *** **30"></p>
    <p>Email hint (or space to skip): <input name="email" value=" "></p>
    <p><button type="submit">Run search</button></p>
  </form>
  <p><small>Session ID: get it from your browser cookies while logged into Instagram (Application → Cookies → sessionid). Optional: set INSTAGRAM_SESSION_ID on Render to use a default.</small></p>
</body>
</html>
"""


def parse_phone_for_hint(phone: str) -> str:
    """Turn +16464991930 into +1 *** *** **30"""
    digits = re.sub(r"\D", "", phone)
    if len(digits) >= 10:
        # assume +1 NXX NXX XX30
        return f"+{digits[:1]} *** *** **{digits[-2:]}"
    return phone.strip() or " "


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/run", methods=["POST"])
def run():
    data = request.get_json(silent=True) or {}
    session_id = (request.form.get("session_id") or data.get("session_id") or "").strip() or os.environ.get("INSTAGRAM_SESSION_ID")
    if not session_id:
        err = "Session ID is required: add it in the form or set INSTAGRAM_SESSION_ID env var."
        if request.content_type and "application/json" in request.content_type:
            return jsonify({"error": err}), 400
        return f"<h1>Error</h1><p>{err}</p><a href='/'>Back</a>", 400

    name = (request.form.get("name") or data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    phone = (request.form.get("phone") or data.get("phone") or " ").strip() or " "
    email = (request.form.get("email") or data.get("email") or " ").strip() or " "
    # If phone looks like a full number, convert to hint
    if phone and re.search(r"^\+\d{10,}", re.sub(r"\s", "", phone)):
        phone = parse_phone_for_hint(phone)

    timeout_sec = 10
    cmd = [
        "python3", "yesitsme.py",
        "-s", session_id,
        "-n", name,
        "-e", email,
        "-p", phone,
        "-t", str(timeout_sec),
        "--no-input",
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300,
        )
        out = (result.stdout or "") + (result.stderr or "")
        data = {"ok": result.returncode == 0, "returncode": result.returncode, "output": out}
        if request.content_type and "application/json" in request.content_type:
            return jsonify(data)
        # Form submit: show output in browser
        return render_template_string(
            "<!DOCTYPE html><html><head><title>Result</title></head><body><h1>Run result</h1>"
            "<pre>{{ output }}</pre><p><a href='/'>Back</a></p></body></html>",
            output=data["output"] or "(no output)",
        )
    except subprocess.TimeoutExpired:
        if request.content_type and "application/json" in request.content_type:
            return jsonify({"error": "Run timed out", "output": ""}), 408
        return "<h1>Run timed out</h1><a href='/'>Back</a>", 408
    except Exception as e:
        if request.content_type and "application/json" in request.content_type:
            return jsonify({"error": str(e), "output": ""}), 500
        return f"<h1>Error</h1><p>{e}</p><a href='/'>Back</a>", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
