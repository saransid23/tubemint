import os
import re
import shutil
import tempfile
import uuid
import time
import threading
import urllib.parse
from fastapi import FastAPI, Query, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from utils import get_video_info, download_media, validate_youtube_url

app = FastAPI(
    title="Tubemint",
    description="Python-based YouTube Video & Audio Downloader",
    version="1.1.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# In-memory store for prepared downloads: token -> {path, filename, temp_dir, created_at}
prepared_downloads: dict = {}

def cleanup_directory(path: str):
    """Clean up temporary download folder after response is sent."""
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)

def cleanup_stale_downloads():
    """Remove prepared downloads older than 10 minutes."""
    while True:
        time.sleep(300)  # Check every 5 minutes
        now = time.time()
        stale_tokens = [
            token for token, info in prepared_downloads.items()
            if now - info["created_at"] > 600
        ]
        for token in stale_tokens:
            info = prepared_downloads.pop(token, None)
            if info:
                cleanup_directory(info["temp_dir"])

# Start background cleanup thread
cleanup_thread = threading.Thread(target=cleanup_stale_downloads, daemon=True)
cleanup_thread.start()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/info")
async def api_info(url: str = Query(..., description="YouTube Video URL")):
    try:
        info = get_video_info(url)
        return JSONResponse(content=info)
    except ValueError as ve:
        return JSONResponse(content={"error": str(ve)}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": f"Could not read video: {str(e)}"}, status_code=400)

@app.post("/api/prepare")
async def api_prepare(
    url: str = Query(..., description="YouTube Video URL"),
    media_type: str = Query("video", description="Media type: 'video' or 'audio'"),
    quality: str = Query(None, description="Resolution height (e.g. 720) or audio preset (e.g. mp3_320)"),
    height: int = Query(None, description="Legacy parameter for video resolution height")
):
    """Phase 1: Download requested media server-side and return a temporary download token."""
    temp_dir = tempfile.mkdtemp(prefix="tubemint-")
    try:
        # Determine quality string if using legacy height param
        selected_quality = quality if quality is not None else (str(height) if height is not None else "720")
        
        file_path = download_media(url, media_type, selected_quality, temp_dir)
        filename = os.path.basename(file_path)

        # Generate a unique token for this download
        token = uuid.uuid4().hex
        prepared_downloads[token] = {
            "path": file_path,
            "filename": filename,
            "temp_dir": temp_dir,
            "created_at": time.time(),
        }

        return JSONResponse(content={
            "token": token,
            "filename": filename,
            "size": os.path.getsize(file_path),
        })
    except ValueError as ve:
        cleanup_directory(temp_dir)
        return JSONResponse(content={"error": str(ve)}, status_code=400)
    except Exception as e:
        cleanup_directory(temp_dir)
        return JSONResponse(content={"error": f"Download failed: {str(e)}"}, status_code=500)

@app.get("/api/serve/{token}")
@app.get("/api/serve/{token}/{filename}")
async def api_serve(token: str, filename: str = None):
    """Phase 2: Serve the prepared media file to the browser for download."""
    info = prepared_downloads.get(token)
    if not info or not os.path.exists(info["path"]):
        return JSONResponse(content={"error": "Download link expired or invalid."}, status_code=404)

    actual_filename = info["filename"]
    ext = os.path.splitext(actual_filename)[1].lower()
    media_types = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mkv": "video/x-matroska",
        ".mov": "video/quicktime",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg"
    }
    media_type = media_types.get(ext, "application/octet-stream")

    # Safe ASCII fallback for headers + RFC 5987 utf-8 filename
    ascii_name = re.sub(r'[^\w\s\.-]', '', actual_filename).strip() or "download"
    if not ascii_name.lower().endswith(ext):
        ascii_name += ext
    utf8_name = urllib.parse.quote(actual_filename)

    headers = {
        "Content-Disposition": f'attachment; filename="{ascii_name}"; filename*=utf-8\'\'{utf8_name}'
    }

    return FileResponse(
        path=info["path"],
        media_type=media_type,
        headers=headers
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8050, reload=True)

