import glob
import logging
import os
import shutil
import tempfile
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request, send_file
import yt_dlp

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # Requests should only contain a video URL.
logging.basicConfig(level=logging.INFO)


def is_tiktok_url(value):
    """Accept TikTok links, including the common short-link subdomains."""
    if not isinstance(value, str) or len(value) > 2000:
        return False
    try:
        parsed = urlparse(value.strip())
        host = (parsed.hostname or "").lower()
        return parsed.scheme in ("http", "https") and (
            host == "tiktok.com" or host.endswith(".tiktok.com")
        )
    except (TypeError, ValueError):
        return False


def ydl_options():
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        # Prefer the best single-file MP4 so the server does not need FFmpeg.
        "format": "best[ext=mp4]/best",
        "socket_timeout": 25,
        "retries": 2,
    }


def get_preview_url(info):
    """Choose a browser-previewable video URL when yt-dlp exposes one."""
    direct_url = info.get("url")
    if direct_url:
        return direct_url

    formats = [
        item for item in (info.get("formats") or [])
        if item.get("url") and item.get("vcodec") != "none"
    ]
    if not formats:
        return None

    mp4_formats = [item for item in formats if item.get("ext") == "mp4"]
    choices = mp4_formats or formats
    best = max(
        choices,
        key=lambda item: (
            item.get("height") or 0,
            item.get("tbr") or 0,
        ),
    )
    return best.get("url")


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/healthz")
def health():
    return jsonify(status="ok")


@app.post("/api/info")
def video_info():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not is_tiktok_url(url):
        return jsonify(error="Cole um link válido do TikTok."), 400

    try:
        with yt_dlp.YoutubeDL(ydl_options()) as ydl:
            info = ydl.extract_info(url, download=False)

        return jsonify(
            title=info.get("title") or "Vídeo do TikTok",
            description=info.get("description") or info.get("title") or "Sem descrição disponível.",
            author=info.get("uploader") or info.get("channel") or "Criador do vídeo",
            thumbnail=info.get("thumbnail"),
            preview_url=get_preview_url(info),
        )
    except Exception:
        app.logger.exception("Não foi possível obter informações do TikTok.")
        return jsonify(
            error="Não consegui carregar esse vídeo. Confira o link e tente novamente."
        ), 422


@app.post("/api/download")
def download_video():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not is_tiktok_url(url):
        return jsonify(error="Cole um link válido do TikTok."), 400

    temp_dir = tempfile.mkdtemp(prefix="download_free_videos_")
    try:
        options = ydl_options()
        options["outtmpl"] = os.path.join(temp_dir, "video.%(ext)s")

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        downloaded_files = [
            path for path in glob.glob(os.path.join(temp_dir, "*"))
            if os.path.isfile(path)
        ]
        if not downloaded_files:
            raise RuntimeError("O arquivo não foi encontrado após o download.")

        file_path = max(downloaded_files, key=os.path.getsize)
        extension = os.path.splitext(file_path)[1].lower()
        download_name = "download-free-videos" + (extension or ".mp4")

        response = send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype="video/mp4" if extension == ".mp4" else "application/octet-stream",
        )
        # Remove the temporary file after the response has been sent/closed.
        response.call_on_close(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        return response

    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        app.logger.exception("O download do TikTok falhou.")
        return jsonify(
            error="O download falhou. O vídeo pode ser privado ou o TikTok pode ter alterado o acesso."
        ), 422


if __name__ == "__main__":
    # Local testing only. Render runs the app with Gunicorn.
    app.run(host="0.0.0.0", port=5000, debug=False)
