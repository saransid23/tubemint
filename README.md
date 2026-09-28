<div align="center">

# 🍃 Tubemint

### Self-Hosted YouTube Video Inspector & Downloader

<img src="https://readme-typing-svg.demolab.com/?lines=Inspect+any+video.;Detect+up+to+4K.;Download+video+or+audio.&amp;center=true&amp;width=420&amp;height=35&amp;color=10B981&amp;vCenter=true&amp;size=18" />

<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" />
<img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&amp;logo=fastapi&amp;logoColor=white" />
<img src="https://img.shields.io/badge/yt--dlp-FF0000?style=flat-square&amp;logo=youtube&amp;logoColor=white" />
<img src="https://img.shields.io/badge/FFmpeg-007808?style=flat-square&amp;logo=ffmpeg&amp;logoColor=white" />

</div>

<br>

**Tubemint** is a high-performance, self-hosted YouTube video inspector and downloader web app built with **FastAPI**, **yt-dlp** and **FFmpeg**. It has a modern glassmorphic dark-mode UI with emerald accents, real-time resolution detection, and audio conversion (MP3 / M4A).

> Needs Python 3.10+ and FFmpeg available on your system `PATH`.

<br>

## ✨ Key Features

| | Feature | What it does |
|:---:|---|---|
| 🎥 | **Metadata Extraction** | Instantly shows the video title, high-resolution thumbnail and formatted duration |
| ⚙️ | **Smart Resolution Detection** | Detects available tiers: 4K 2160p, 2K 1440p, 1080p FHD, 720p HD, 480p / 360p SD |
| 🎵 | **Audio Mode** | High-bitrate MP3 (320 / 192 kbps) or native M4A (AAC) |
| 🎨 | **Premium UI** | Glassmorphic vanilla CSS, responsive layout and visual download progress |
| 🧹 | **Automatic Cleanup** | A background thread continuously purges expired temporary downloads |
| 🚀 | **Two-Phase Serving** | Pre-downloads server-side so the browser gets clean byte delivery |

<br>

## 📡 API Endpoints

| Method | Endpoint | Description |
|:---:|---|---|
| `GET` | `/` | Renders the main HTML interface |
| `GET` | `/api/info?url=<URL>` | Fetches metadata, thumbnail, duration, resolutions and audio options |
| `POST` | `/api/prepare?url=<URL>&media_type=<video\|audio>&quality=<QUALITY>` | Prepares the download and returns a single-use token with file size |
| `GET` | `/api/serve/{token}` | Streams the prepared file with clean `Content-Disposition` headers |

<br>

## 📁 Project Structure

```text
tubemint/
├── main.py              # FastAPI server, background cleanup thread & API router
├── utils.py             # yt-dlp integration & FFmpeg post-processing helpers
├── templates/
│   └── index.html       # Single Page Application HTML & interactive JS script
├── static/
│   └── style.css        # Custom glassmorphism dark theme CSS styling
├── requirements.txt     # Python package dependencies
└── README.md            # Project documentation
```

<br>

## 📜 Legal & Usage Disclaimer

This tool is for educational and personal archiving purposes only. Download content only if you own it or have explicit permission from the copyright holder, and always respect YouTube's Terms of Service.

<br>

<div align="center">

*Tubemint: inspect, prepare, download.*

</div>
