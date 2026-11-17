import glob, logging, os, re, shutil, tempfile
from urllib.parse import urlparse
import requests
import yt_dlp
from flask import Flask, jsonify, render_template, request, send_file

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
URL_RE = re.compile(r"https?://[^\\s<>'\"`]+", re.I)
TRAILING = ".,;:!?)]}>"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Referer": "https://www.tiktok.com/",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

def valid_tiktok_url(url):
    try:
        p = urlparse(url.strip())
        host = (p.hostname or "").lower()
        return p.scheme in ("http", "https") and (host == "tiktok.com" or host.endswith(".tiktok.com"))
    except (TypeError, ValueError, AttributeError):
        return False

def extract_tiktok_url(text):
    if not isinstance(text, str):
        return None
    for raw in URL_RE.findall(text):
        url = raw.rstrip(TRAILING)
        if not valid_tiktok_url(url):
            continue
        p = urlparse(url)
        if (p.path or "").lower().startswith("/tiktoklite"):
            continue
        if (p.hostname or "").lower() in ("tiktok.com", "www.tiktok.com") and p.path in ("", "/"):
            continue
        return url
    return None

def resolve_short_link(url):
    host = (urlparse(url).hostname or "").lower()
    if host not in ("vm.tiktok.com", "vt.tiktok.com"):
        return url
    try:
        r = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=15)
        final_url = r.url
        final_host = (urlparse(final_url).hostname or "").lower()
        if valid_tiktok_url(final_url) and final_host not in ("vm.tiktok.com", "vt.tiktok.com"):
            return final_url
    except requests.RequestException:
        app.logger.info("Falha ao expandir link curto; tentando URL original.")
    return url

def get_video_url(value):
    url = extract_tiktok_url(value)
    return resolve_short_link(url) if url else None

def ydl_options():
    return {
        "quiet": True, "no_warnings": True, "noplaylist": True,
        "format": "best[ext=mp4]/best", "socket_timeout": 30, "retries": 3,
        "http_headers": HEADERS,
    }

def preview_url(info):
    if info.get("url"):
        return info["url"]
    formats = [f for f in (info.get("formats") or []) if f.get("url") and f.get("vcodec") != "none"]
    if not formats:
        return None
    mp4 = [f for f in formats if f.get("ext") == "mp4"]
    best = max(mp4 or formats, key=lambda f: (f.get("height") or 0, f.get("tbr") or 0))
    return best.get("url")

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/healthz")
def health():
    return jsonify(status="ok")

@app.post("/api/info")
def info():
    data = request.get_json(silent=True) or {}
    url = get_video_url((data.get("url") or "").strip())
    if not url:
        return jsonify(error="Não encontrei um link de vídeo do TikTok nessa mensagem."), 400
    try:
        with yt_dlp.YoutubeDL(ydl_options()) as ydl:
            item = ydl.extract_info(url, download=False)
        return jsonify(
            title=item.get("title") or "Vídeo do TikTok",
            description=item.get("description") or item.get("title") or "Sem descrição disponível.",
            author=item.get("uploader") or item.get("channel") or "Criador do vídeo",
            thumbnail=item.get("thumbnail"), preview_url=preview_url(item),
        )
    except Exception as e:
        app.logger.exception("Falha ao obter dados do TikTok")
        return jsonify(error="Encontrei o link, mas o TikTok não liberou os dados. Tente outro vídeo público. Detalhe: " + str(e)[:160]), 422

@app.post("/api/download")
def download():
    data = request.get_json(silent=True) or {}
    url = get_video_url((data.get("url") or "").strip())
    if not url:
        return jsonify(error="Não encontrei um link de vídeo do TikTok nessa mensagem."), 400
    folder = tempfile.mkdtemp(prefix="download_free_videos_")
    try:
        opts = ydl_options()
        opts["outtmpl"] = os.path.join(folder, "video.%(ext)s")
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        files = [p for p in glob.glob(os.path.join(folder, "*")) if os.path.isfile(p)]
        if not files:
            raise RuntimeError("Arquivo não encontrado.")
        path = max(files, key=os.path.getsize)
        ext = os.path.splitext(path)[1].lower() or ".mp4"
        response = send_file(path, as_attachment=True, download_name="download-free-videos" + ext)
        response.call_on_close(lambda: shutil.rmtree(folder, ignore_errors=True))
        return response
    except Exception as e:
        shutil.rmtree(folder, ignore_errors=True)
        app.logger.exception("Falha no download do TikTok")
        return jsonify(error="Encontrei o link, mas não consegui baixar. O vídeo pode ser privado ou o TikTok pode estar bloqueando a extração. Detalhe: " + str(e)[:160]), 422

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
