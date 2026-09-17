import os
import re
import shutil
import tempfile
from urllib.parse import urlparse
from typing import Dict, Any, List
import yt_dlp

ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtube-nocookie.com",
}

def validate_youtube_url(raw_url: str) -> str:
    """Validate that the input string is a valid YouTube URL."""
    if not raw_url:
        raise ValueError("YouTube URL is required.")
    
    parsed = urlparse(raw_url.strip())
    if parsed.scheme not in ("http", "https") or parsed.netloc not in ALLOWED_HOSTS:
        raise ValueError("Please enter a valid YouTube URL.")
    
    return raw_url.strip()

def get_cookie_opts() -> Dict[str, Any]:
    """
    Returns cookie options for yt-dlp if cookies.txt exists,
    YTDLP_COOKIES_CONTENT is set in environment, or YTDLP_COOKIES_FROM_BROWSER is specified.
    """
    opts = {}
    
    # 1. Custom or default cookies file path
    cookie_file = os.getenv("YTDLP_COOKIES_PATH", "cookies.txt")
    if os.path.exists(cookie_file):
        opts["cookiefile"] = os.path.abspath(cookie_file)
        return opts

    # 2. Cookies from environment variable string (for Vercel/serverless environments)
    cookies_content = os.getenv("YTDLP_COOKIES_CONTENT")
    if cookies_content:
        tmp_cookie_path = os.path.join(tempfile.gettempdir(), "yt_cookies.txt")
        try:
            with open(tmp_cookie_path, "w", encoding="utf-8") as f:
                f.write(cookies_content)
            opts["cookiefile"] = tmp_cookie_path
            return opts
        except Exception:
            pass

    # 3. Browser cookies option (e.g. chrome, edge, firefox, brave, opera, safari)
    browser = os.getenv("YTDLP_COOKIES_FROM_BROWSER")
    if browser:
        opts["cookiesfrombrowser"] = (browser.strip().lower(),)
        return opts

    return opts

CLIENT_COMBOS = [
    ["android", "ios", "mweb"],
    ["android", "mweb"],
    ["ios", "android"]
]

def fetch_oembed_info(url: str) -> Dict[str, Any]:
    """Fallback metadata fetcher using YouTube's public oEmbed API."""
    import urllib.request
    import json
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            title = data.get("title", "YouTube Video")
            thumbnail = data.get("thumbnail_url", "")
            return {
                "title": title,
                "thumbnail": thumbnail,
                "duration": None,
                "heights": [1080, 720, 480, 360],
                "resolutions": [
                    {"height": 360, "label": "360p", "badge": "SD"},
                    {"height": 480, "label": "480p", "badge": "SD"},
                    {"height": 720, "label": "720p", "badge": "HD"},
                    {"height": 1080, "label": "1080p", "badge": "FHD"},
                ],
                "audio_formats": [
                    {"id": "mp3_320", "label": "MP3 Audio (320 kbps High)", "ext": "mp3", "bitrate": "320"},
                    {"id": "mp3_192", "label": "MP3 Audio (192 kbps Medium)", "ext": "mp3", "bitrate": "192"},
                    {"id": "m4a_best", "label": "M4A Audio (Native AAC)", "ext": "m4a", "bitrate": "best"}
                ]
            }
    except Exception:
        return None

def get_video_info(url: str) -> Dict[str, Any]:
    """Fetch video metadata, available resolution heights, and audio formats using yt-dlp."""
    valid_url = validate_youtube_url(url)
    cookie_opts = get_cookie_opts()

    info = None
    last_err = None

    for clients in CLIENT_COMBOS:
        ydl_opts = {
            "skip_download": True,
            "no_playlist": True,
            "quiet": True,
            "no_warnings": True,
            "extractor_args": {
                "youtube": {
                    "player_client": clients,
                    "player_skip": ["webpage"]
                }
            }
        }
        ydl_opts.update(cookie_opts)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(valid_url, download=False)
                if info:
                    break
        except Exception as e:
            last_err = e
            continue

    if not info:
        oembed_data = fetch_oembed_info(valid_url)
        if oembed_data:
            return oembed_data
        err_msg = str(last_err) if last_err else "Could not extract video info."
        if "sign in to confirm" in err_msg.lower() or "bot" in err_msg.lower():
            raise ValueError(
                "YouTube requires authentication for this video on cloud server IPs. "
                "Export your YouTube cookies and set the YTDLP_COOKIES_CONTENT environment variable in Vercel settings."
            )
        raise ValueError(err_msg)

    # Extract available video heights
    heights_set = set()
    for fmt in info.get("formats", []):
        vcodec = fmt.get("vcodec")
        height = fmt.get("height")
        if vcodec != "none" and isinstance(height, int) and height > 0:
            heights_set.add(height)

    max_h = max(heights_set) if heights_set else 1080

    # Standard YouTube resolutions (144p, 240p, 360p, 480p, 720p HD, 1080p FHD, 2K, 4K)
    standard_tiers = [
        {"height": 144, "label": "144p", "badge": "SD"},
        {"height": 240, "label": "240p", "badge": "SD"},
        {"height": 360, "label": "360p", "badge": "SD"},
        {"height": 480, "label": "480p", "badge": "SD"},
        {"height": 720, "label": "720p", "badge": "HD"},
        {"height": 1080, "label": "1080p", "badge": "FHD"},
        {"height": 1440, "label": "2K", "badge": "1440p"},
        {"height": 2160, "label": "4K", "badge": "2160p"},
    ]

    # Include all standard resolutions up to maximum available video height
    resolutions = [t for t in standard_tiers if t["height"] <= max_h]
    if not resolutions:
        resolutions = [t for t in standard_tiers if t["height"] <= 720]

    heights = [t["height"] for t in resolutions]

    # Preset audio format options for frontend selection
    audio_formats = [
        {"id": "mp3_320", "label": "MP3 Audio (320 kbps High)", "ext": "mp3", "bitrate": "320"},
        {"id": "mp3_192", "label": "MP3 Audio (192 kbps Medium)", "ext": "mp3", "bitrate": "192"},
        {"id": "m4a_best", "label": "M4A Audio (Native AAC)", "ext": "m4a", "bitrate": "best"}
    ]

    return {
        "title": info.get("title", "YouTube Video"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "heights": heights,
        "resolutions": resolutions,
        "audio_formats": audio_formats,
    }

def download_video(url: str, height: int, output_dir: str) -> str:
    """Legacy helper for video download, delegates to download_media."""
    return download_media(url, media_type="video", quality=str(height), output_dir=output_dir)

def download_media(url: str, media_type: str, quality: str, output_dir: str) -> str:
    """Download requested media (video or audio) and return local file path."""
    valid_url = validate_youtube_url(url)
    output_template = os.path.join(output_dir, "%(title).100s.%(ext)s")
    cookie_opts = get_cookie_opts()

    preferred_format = "mp3"
    allowed_extensions = (".mp4", ".webm", ".mkv", ".mov")

    last_err = None
    success = False

    for clients in CLIENT_COMBOS:
        if media_type == "audio":
            if quality == "mp3_320":
                preferred_format = "mp3"
                preferred_quality = "320"
            elif quality == "mp3_192":
                preferred_format = "mp3"
                preferred_quality = "192"
            elif quality == "m4a_best":
                preferred_format = "m4a"
                preferred_quality = "0"
            else:
                preferred_format = "mp3"
                preferred_quality = "192"

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": output_template,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": clients,
                        "player_skip": ["webpage"]
                    }
                }
            }

            # Only add FFmpeg postprocessor if FFmpeg binary is available on system PATH
            if shutil.which("ffmpeg"):
                ydl_opts["postprocessors"] = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": preferred_format,
                        "preferredquality": preferred_quality,
                    }
                ]

            allowed_extensions = (".mp3", ".m4a", ".aac", ".ogg", ".wav", ".flac", ".webm")
        else:
            try:
                height_val = int(quality)
            except ValueError:
                height_val = 720

            if height_val < 144 or height_val > 4320:
                raise ValueError("Invalid resolution height requested.")

            # Universal format specification matching best available video and audio streams
            format_spec = (
                f"bestvideo[height<={height_val}]+bestaudio/"
                f"best[height<={height_val}]/"
                f"bestvideo+bestaudio/best"
            )

            ydl_opts = {
                "format": format_spec,
                "outtmpl": output_template,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": clients,
                        "player_skip": ["webpage"]
                    }
                }
            }

            if shutil.which("ffmpeg"):
                ydl_opts["merge_output_format"] = "mp4"

            allowed_extensions = (".mp4", ".webm", ".mkv", ".mov")

        ydl_opts.update(cookie_opts)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(valid_url, download=True)
                if info:
                    prepared_path = ydl.prepare_filename(info)
                    base_path = os.path.splitext(prepared_path)[0]
                    expected_ext = ".mp4" if media_type == "video" else f".{preferred_format}"
                    expected_file = base_path + expected_ext
                    if os.path.exists(expected_file):
                        return expected_file
                    if os.path.exists(prepared_path):
                        return prepared_path
                    success = True
                    break
        except Exception as e:
            last_err = e
            continue

    # Fallback search if prepared path differs
    downloaded_files = [
        os.path.join(output_dir, f) for f in os.listdir(output_dir)
        if f.lower().endswith(allowed_extensions)
        and not f.lower().endswith((".part", ".ytdl", ".temp"))
        and not re.search(r'\.f\d+\.', f)
    ]

    if downloaded_files:
        downloaded_files.sort(key=lambda p: os.path.getsize(p), reverse=True)
        return downloaded_files[0]

    err_msg = str(last_err) if last_err else "Downloaded media file was not found."
    if "sign in to confirm" in err_msg.lower() or "bot" in err_msg.lower():
        raise ValueError(
            "YouTube requires authentication for this download on cloud server IPs. "
            "Export your YouTube cookies and set the YTDLP_COOKIES_CONTENT environment variable in Vercel settings."
        )
    raise RuntimeError(err_msg)

