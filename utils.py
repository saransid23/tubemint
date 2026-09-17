import os
import re
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

def get_video_info(url: str) -> Dict[str, Any]:
    """Fetch video metadata, available resolution heights, and audio formats using yt-dlp."""
    valid_url = validate_youtube_url(url)

    ydl_opts = {
        "skip_download": True,
        "no_playlist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(valid_url, download=False)
        if not info:
            raise ValueError("Could not extract video info.")

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

    if media_type == "audio":
        # Determine audio output format & quality settings
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
                    "player_client": ["web", "mweb", "android"]
                }
            },
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": preferred_format,
                    "preferredquality": preferred_quality,
                }
            ],
        }
        allowed_extensions = (".mp3", ".m4a", ".aac", ".ogg", ".wav", ".flac")
    else:
        # Video download mode
        try:
            height_val = int(quality)
        except ValueError:
            height_val = 720

        if height_val < 144 or height_val > 4320:
            raise ValueError("Invalid resolution height requested.")

        format_spec = (
            f"bestvideo[height<={height_val}][ext=mp4]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={height_val}]+bestaudio/"
            f"best[height<={height_val}]/best"
        )

        ydl_opts = {
            "format": format_spec,
            "merge_output_format": "mp4",
            "outtmpl": output_template,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["web", "mweb", "android"]
                }
            },
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4"
                }
            ]
        }
        allowed_extensions = (".mp4", ".webm", ".mkv", ".mov")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([valid_url])

    # Find the downloaded file
    downloaded_files = [
        os.path.join(output_dir, f) for f in os.listdir(output_dir)
        if f.lower().endswith(allowed_extensions)
        and not f.lower().endswith((".part", ".ytdl", ".temp"))
    ]

    if not downloaded_files:
        raise RuntimeError("Downloaded media file was not found.")

    downloaded_files.sort(key=lambda p: os.path.getsize(p), reverse=True)
    return downloaded_files[0]

