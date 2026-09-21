# 🍃 Tubemint

**Tubemint** is a high-performance, self-hosted YouTube Video Inspector & Downloader web application built with **FastAPI**, **yt-dlp**, and **FFmpeg**. It features a modern, glassmorphic dark-mode UI with emerald accent highlights, real-time video resolution detection, and audio conversion options (MP3/M4A).

---

## ✨ Key Features

- 🎥 **Video Metadata Extraction**: Instantly inspect video title, high-resolution thumbnail, and formatted duration.
- ⚙️ **Smart Resolution Detection**: Automatically detects and presents available video quality tiers (e.g. 4K 2160p, 2K 1440p, 1080p FHD, 720p HD, 480p/360p SD).
- 🎵 **Audio Mode Extraction**: Download audio directly in high-bitrate MP3 (320 kbps / 192 kbps) or native M4A (AAC).
- 🎨 **Premium UI**: Glassmorphic UI styled with vanilla CSS, dynamic responsive layout, and visual download progress indicators.
- 🧹 **Automatic Cleanup**: Server-side background thread continuously purges expired temporary downloads.
- 🚀 **Two-Phase Prepared Serving**: Pre-downloads content server-side to guarantee clean byte delivery to browser clients.

---

## 🛠️ Requirements

- **Python 3.10+**
- **FFmpeg**: Must be installed and available on your system `PATH`.
  - *Windows*: Download from [FFmpeg.org](https://ffmpeg.org/download.html) or install via `winget install Gyan.FFmpeg` / `choco install ffmpeg`.

---
## 📡 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Renders the primary HTML user interface |
| `/api/info?url=<URL>` | `GET` | Fetches video metadata, thumbnail, duration, available video resolutions, and audio format options |
| `/api/prepare?url=<URL>&media_type=<video\|audio>&quality=<QUALITY>` | `POST` | Prepares the download on the server and returns a single-use token with file size |
| `/api/serve/{token}` | `GET` | Streams the prepared media file to the browser with clean `Content-Disposition` headers |

---

## 📁 Project Structure

```
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

---

## 📜 Legal & Usage Disclaimer

This tool is created for educational and personal archiving purposes only. Download content only if you hold ownership or explicit permission from the copyright holder. Always respect YouTube's Terms of Service.

