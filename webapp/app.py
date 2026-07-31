"""Local MarkItDown web UI — upload a file, download Markdown."""

from __future__ import annotations

import io
import sys
import tempfile
import threading
import webbrowser
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from markitdown import MarkItDown
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {
    ".xlsx",
    ".xls",
    ".xlsm",
    ".pdf",
    ".docx",
    ".pptx",
    ".html",
    ".htm",
    ".csv",
    ".json",
    ".xml",
    ".txt",
    ".epub",
    ".zip",
    ".png",
    ".jpg",
    ".jpeg",
    ".wav",
    ".mp3",
}

HOST = "127.0.0.1"
PORT = 5000
IS_FROZEN = getattr(sys, "frozen", False)


def app_base_dir() -> Path:
    if IS_FROZEN:
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


app = Flask(__name__, template_folder=str(app_base_dir() / "templates"))
app.secret_key = "markitdown-local-dev"
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB
app.config["TEMPLATES_AUTO_RELOAD"] = not IS_FROZEN
app.jinja_env.auto_reload = not IS_FROZEN
if not IS_FROZEN:
    app.jinja_env.cache = None

md = MarkItDown()


@app.after_request
def disable_caching(response):
    """Keep browser from sticking to an old HTML/CSS/JS snapshot during local edits."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    wants_json = request.headers.get("X-Requested-With") == "fetch"

    def fail(message: str, status: int = 400):
        if wants_json:
            return {"error": message}, status
        flash(message)
        return redirect(url_for("index"))

    uploaded = request.files.get("file")
    if uploaded is None or uploaded.filename is None or uploaded.filename.strip() == "":
        return fail("Please choose a file to convert.")

    filename = secure_filename(uploaded.filename)
    if not allowed_file(filename):
        return fail(f"Unsupported file type: {Path(filename).suffix or '(none)'}")

    suffix = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        uploaded.save(tmp.name)
        tmp_path = Path(tmp.name)

    try:
        result = md.convert(str(tmp_path))
        markdown_text = result.text_content or ""
    except Exception as exc:  # noqa: BLE001 — surface conversion errors in UI
        tmp_path.unlink(missing_ok=True)
        return fail(f"Conversion failed: {exc}", status=500)
    finally:
        tmp_path.unlink(missing_ok=True)

    out_name = f"{Path(filename).stem}.md"
    buffer = io.BytesIO(markdown_text.encode("utf-8"))
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=out_name,
        mimetype="text/markdown; charset=utf-8",
    )


def open_browser() -> None:
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    url = f"http://{HOST}:{PORT}"
    print(f"MarkItDown local UI -> {url}")
    print("Close this window to stop the app.")
    threading.Timer(1.0, open_browser).start()
    app.run(host=HOST, port=PORT, debug=not IS_FROZEN, use_reloader=False)
