"""Local MarkItDown web UI — upload a file, download Markdown."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

from flask import Flask, render_template, request, send_file, flash, redirect, url_for
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

app = Flask(__name__)
app.secret_key = "markitdown-local-dev"
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

md = MarkItDown()


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    uploaded = request.files.get("file")
    if uploaded is None or uploaded.filename is None or uploaded.filename.strip() == "":
        flash("Please choose a file to convert.")
        return redirect(url_for("index"))

    filename = secure_filename(uploaded.filename)
    if not allowed_file(filename):
        flash(f"Unsupported file type: {Path(filename).suffix or '(none)'}")
        return redirect(url_for("index"))

    suffix = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        uploaded.save(tmp.name)
        tmp_path = Path(tmp.name)

    try:
        result = md.convert(str(tmp_path))
        markdown_text = result.text_content or ""
    except Exception as exc:  # noqa: BLE001 — surface conversion errors in UI
        tmp_path.unlink(missing_ok=True)
        flash(f"Conversion failed: {exc}")
        return redirect(url_for("index"))
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


if __name__ == "__main__":
    # Always pick up template/CSS edits without a manual restart.
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.jinja_env.auto_reload = True
    print("MarkItDown local UI -> http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=True)
