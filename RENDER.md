# Deploying on Render

This app runs on **native Python** (no Docker).

- **runtime.txt** pins Python 3.12 so the app works with the current dependencies.
- In the dashboard: **Build command** = `pip install -r requirements.txt`, **Start command** = `gunicorn app:app`.
- Add **INSTAGRAM_SESSION_ID** in Environment if you want a default session (or paste it in the form).
