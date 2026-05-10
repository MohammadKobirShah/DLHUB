<!--
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                         🟢 DLHUB - High Performance                         ║
║                    Open Media Downloading Platform                           ║
║                                                                              ║
║              Powered by yt-dlp + FFmpeg + FastAPI + PostgreSQL              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

      ██████╗ ██╗     ██╗  ██╗██╗   ██╗██████╗
      ██╔══██╗██║     ██║  ██║██║   ██║██╔══██╗
      ██║  ██║██║     ███████║██║   ██║██████╔╝
      ██║  ██║██║     ██╔══██║██║   ██║██╔══██╗
      ██████╔╝███████╗██║  ██║╚██████╔╝██████╔╝
      ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝

-->

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0.0-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.12+-green?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-00a859?style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Docker-Ready-blue?style=flat-square" alt="Docker">
  <img src="https://img.shields.io/badge/100+-API%20Endpoints-green?style=flat-square" alt="Endpoints">
</p>

<p align="center">
  <a href="https://github.com/MohammadKobirShah/DLHUB">
    <img src="https://komarev.com/ghpvc/?username=MohammadKobirShah&repo=DLHUB&label=Views&color=0e75b6&style=flat" alt="Profile Views">
  </a>
  <a href="https://github.com/MohammadKobirShah/DLHUB/stargazers">
    <img src="https://img.shields.io/github/stars/MohammadKobirShah/DLHUB?style=flat-square&color=ffcb2b" alt="Stars">
  </a>
  <a href="https://github.com/MohammadKobirShah/DLHUB/forks">
    <img src="https://img.shields.io/github/forks/MohammadKobirShah/DLHUB?style=flat-square&color=ff6b6b" alt="Forks">
  </a>
</p>

---

<h2 align="center">🚀 Quick Start</h2>

```bash
# Clone the repository
git clone https://github.com/MohammadKobirShah/DLHUB.git
cd DLHUB

# Start the stack
docker compose -f compose/docker-compose.yml up -d

# Access the API
curl http://localhost:8000
```

<p align="center">
  <a href="https://localhost:8000/api/v1/docs">
    <img src="https://img.shields.io/badge/Swagger-UI-orange?style=for-the-badge" alt="Swagger">
  </a>
  <a href="https://localhost:8000/api/v1/redoc">
    <img src="https://img.shields.io/badge/ReDoc-purple?style=for-the-badge" alt="ReDoc">
  </a>
  <a href="http://localhost:8000/health">
    <img src="https://img.shields.io/badge/Health-Check-green?style=for-the-badge" alt="Health">
  </a>
</p>

---

<h2 align="center">📋 Table of Contents</h2>

- [About](#about)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Usage Examples](#usage-examples)
- [YouTube Optimization](#youtube-optimization)
- [Quality Presets](#quality-presets)
- [Media Processing](#media-processing)
- [WebSocket Real-Time](#websocket-real-time)
- [Development](#development)
- [Environment Variables](#environment-variables)
- [License](#license)
- [Credits](#credits)
- [Connect](#connect)

---

<h2 id="about">📖 About</h2>

**DLHUB** is a production-grade, enterprise-ready open media downloading platform powered by **yt-dlp** and **FFmpeg**. It provides a robust REST API for downloading videos, audio, and playlists from YouTube and 1000+ other websites.

Built with modern technologies including **FastAPI**, **PostgreSQL**, **Redis**, and **Docker**, DLHUB offers high performance, scalability, and reliability for self-hosted media processing.

<p align="center">
  <img src="https://img.shields.io/badge/1000+-Sites-orange?style=flat" alt="Sites">
  <img src="https://img.shields.io/badge/100+-Endpoints-blue?style=flat" alt="Endpoints">
  <img src="https://img.shields.io/badge/Production-Ready-green?style=flat" alt="Ready">
</p>

---

<h2 id="features">✨ Features</h2>

| Category | Features |
|----------|----------|
| **Downloads** | Video, Audio, Playlist, Channel, Custom Format |
| **Quality** | 144p, 240p, 360p, 480p, 720p, 1080p, 1440p, 2160p, Best |
| **Formats** | MP4, MKV, WEBM, MP3, M4A, FLAC, WAV, AAC, OGG |
| **Embedding** | Thumbnails, Metadata, Chapters, Subtitles, Tags |
| **Processing** | Transcode, Merge, Trim, Normalize, Extract Audio |
| **Queue** | Priority Queue, Retry Logic, Job Management |
| **API** | REST API, Swagger UI, ReDoc, OpenAPI Schema |
| **Real-Time** | WebSocket Progress, Event Streaming |
| **Monitoring** | Prometheus Metrics, Health Checks, Analytics |
| **Security** | SSRF Protection, Rate Limiting, Path Traversal Prevention |
| **Storage** | PostgreSQL Jobs, Redis Cache, Local/S3 Storage |
| **Deployment** | Docker, Docker Compose, Nginx, Non-root Container |

---

<h2 id="technology-stack">🛠 Technology Stack</h2>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/yt--dlp-FF0000?style=for-the-badge&logo=yt-dlp&logoColor=white" alt="yt-dlp">
  <img src="img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white" alt="FFmpeg">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white" alt="Nginx">
</p>

---

<h2 id="architecture">🏗 Architecture</h2>

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   DLHUB ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │   Client    │────▶│   Nginx     │────▶│  FastAPI   │────▶│   Redis     │   │
│  │  (cURL/UI)  │     │    Proxy    │     │    API      │     │    Queue    │   │
│  └─────────────┘     └─────────────┘     └──────┬──────┘     └─────────────┘   │
│                                                  │                               │
│                            ┌──────────────────────┴──────────────────────┐     │
│                            │                                              │     │
│                    ┌──────▼──────┐                              ┌──────▼──────┐ │
│                    │ PostgreSQL   │                              │  Workers    │ │
│                    │   (Jobs)     │                              │ (yt-dlp)   │ │
│                    └─────────────┘                              └─────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                        MEDIA PROCESSING                                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │  │
│  │  │ FFmpeg   │  │ Transcode│  │  Merge   │  │  Trim    │  │ Normalize│    │  │
│  │  │Process   │  │          │  │          │  │          │  │          │    │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

<h2 id="installation">📦 Installation</h2>

### Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Docker | 20.10+ | 24.0+ |
| Docker Compose | 2.0+ | 2.20+ |
| RAM | 2 GB | 4 GB |
| Disk | 10 GB | 50 GB |

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/MohammadKobirShah/DLHUB.git
cd DLHUB

# 2. Start all services
docker compose -f compose/docker-compose.yml up -d

# 3. Check service status
docker compose -f compose/docker-compose.yml ps

# 4. View logs
docker compose -f compose/docker-compose.yml logs -f api
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| 🌐 API | http://localhost:8000 | Main API endpoint |
| 📚 Swagger | http://localhost:8000/api/v1/docs | Interactive API docs |
| 📖 ReDoc | http://localhost:8000/api/v1/redoc | Alternative API docs |
| ❤️ Health | http://localhost:8000/health | Health check |
| 📊 Metrics | http://localhost:8000/api/v1/system/metrics | Prometheus metrics |

---

<h2 id="configuration">⚙️ Configuration</h2>

Copy `.env.example` to `.env` and customize:

```bash
# Database
DATABASE_URL=postgresql://dlhub:dlhub123@postgres:5432/dlhub

# Redis
REDIS_URL=redis://redis:6379/0

# Download Settings
DOWNLOAD_DIR=/downloads
MAX_CONCURRENT_DOWNLOADS=50
MAX_DOWNLOAD_SIZE=5GB
MAX_DURATION=7200

# yt-dlp Settings
YTDLP_FORMAT=bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best
YTDLP_EMBED_THUMBNAIL=true
YTDLP_ADD_METADATA=true

# Security
ENABLE_RATE_LIMIT=false
ENABLE_SSRF_PROTECTION=true
```

---

<h2 id="api-documentation">📡 API Documentation</h2>

### 100+ Endpoints Available

| Category | Endpoints | Description |
|----------|------------|-------------|
| **Download** | 10 | Video, Audio, Playlist, Custom |
| **System** | 18 | Health, Version, Stats, Storage |
| **Files** | 8 | List, Download, Stream, Delete |
| **Queue** | 12 | Add, Status, Pause, Resume |
| **Media** | 15 | Transcode, Merge, Trim |
| **YouTube** | 12 | Video, Playlist, Channel Info |
| **Admin** | 15 | Overview, Analytics, Cleanup |
| **WebSocket** | 4 | Progress, Events, Jobs |
| **Total** | **100+** | Full-featured API |

---

<h2 id="usage-examples">💡 Usage Examples</h2>

### Download Video (Best Quality)

```bash
curl -X POST "http://localhost:8000/api/v1/download/video" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "best",
    "format": "mp4"
  }'
```

### Download Video (1080p)

```bash
curl -X POST "http://localhost:8000/api/v1/download/video" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "1080p",
    "format": "mp4"
  }'
```

### Download Audio (MP3)

```bash
curl -X POST "http://localhost:8000/api/v1/download/audio" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "format": "mp3"
  }'
```

### Download Playlist

```bash
curl -X POST "http://localhost:8000/api/v1/download/playlist" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/playlist?list=PL123456789",
    "quality": "720p",
    "max_items": 50
  }'
```

### Get Job Status

```bash
curl "http://localhost:8000/api/v1/download/{job_id}"
```

### List Downloaded Files

```bash
curl "http://localhost:8000/api/v1/files"
```

### System Health Check

```bash
curl "http://localhost:8000/api/v1/system/health"
```

---

<h2 id="youtube-optimization">🎯 YouTube Optimization</h2>

DLHUB includes enterprise-grade YouTube optimizations:

- ✅ **DASH Merging** - Combine video + audio for best quality
- ✅ **Fragment Concurrency** - Faster downloads with parallel fragments
- ✅ **Anti-Throttling** - Smart rate limiting bypass
- ✅ **Subtitle Auto-Download** - Multi-language subtitles
- ✅ **Chapter Embedding** - Preserve video chapters
- ✅ **SponsorBlock Support** - Remove sponsored segments
- ✅ **Live Stream Support** - Capture live broadcasts
- ✅ **Cookie Support** - Age-restricted video access
- ✅ **Resume Support** - Continue interrupted downloads

---

<h2 id="quality-presets">📺 Quality Presets</h2>

| Quality | Resolution | Use Case |
|---------|------------|----------|
| `best` | Any | Highest available quality |
| `2160p` | 4K UHD | Ultra HD content |
| `1440p` | 2K QHD | High resolution |
| `1080p` | Full HD | Standard HD |
| `720p` | HD | High quality |
| `480p` | SD | Standard definition |
| `360p` | Low | Mobile devices |
| `240p` | Very Low | Slow connections |
| `144p` | Minimal | Minimal bandwidth |

---

<h2 id="media-processing">🎬 Media Processing</h2>

DLHUB provides powerful FFmpeg-based media processing:

| Operation | Endpoint | Description |
|-----------|----------|-------------|
| **Transcode** | `/api/v1/media/transcode` | Convert to different format |
| **Extract Audio** | `/api/v1/media/extract-audio` | Pull audio from video |
| **Merge** | `/api/v1/media/merge` | Combine multiple videos |
| **Trim** | `/api/v1/media/trim` | Cut specific segment |
| **Normalize** | `/api/v1/media/normalize` | Audio loudness normalization |
| **Waveform** | `/api/v1/media/waveform` | Generate audio visualization |
| **Preview** | `/api/v1/media/preview` | Create short preview clip |
| **GIF** | `/api/v1/media/gif` | Convert video to GIF |
| **Screenshot** | `/api/v1/media/screenshot` | Capture frame at timestamp |

---

<h2 id="websocket-real-time">🔄 WebSocket Real-Time</h2>

Connect for live progress updates:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/progress');

// Listen for progress updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.data.progress}%`);
};

// Subscribe to specific job
ws.send(JSON.stringify({
  action: 'subscribe',
  job_id: 'your-job-id'
}));
```

---

<h2 id="development">👨‍💻 Development</h2>

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Build

```bash
# Build the image
docker build -t dlhub/api -f docker/Dockerfile .

# Run the container
docker run -d -p 8000:8000 --name dlhub dlhub/api
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | DLHUB | Application name |
| `API_PORT` | 8000 | API server port |
| `DATABASE_URL` | postgresql://... | PostgreSQL connection |
| `REDIS_URL` | redis://... | Redis connection |
| `DOWNLOAD_DIR` | /downloads | Download storage path |
| `MAX_CONCURRENT_DOWNLOADS` | 50 | Maximum parallel downloads |
| `WORKER_COUNT` | 4 | Background worker count |

---

<h2 id="license">📄 License</h2>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License">
</p>

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

<h2 id="credits">💎 Credits</h2>

<p align="center">
  Built with ❤️ by <a href="https://github.com/MohammadKobirShah">Md Kobir Shah</a>
</p>

<p align="center">
  <a href="https://github.com/MohammadKobirShah">
    <img src="https://img.shields.io/github/followers/MohammadKobirShah?style=flat-square&logo=github" alt="Follow">
  </a>
  <a href="https://twitter.com">
    <img src="https://img.shields.io/twitter/follow/?style=flat-square&logo=twitter" alt="Twitter">
  </a>
</p>

### Powered By

| Technology | Description |
|------------|-------------|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | YouTube/media downloader |
| [FastAPI](https://fastapi.tiangolo.com/) | Modern Python web framework |
| [FFmpeg](https://ffmpeg.org/) | Media processing |
| [PostgreSQL](https://www.postgresql.org/) | Database |
| [Redis](https://redis.io/) | Queue & Cache |
| [Nginx](https://nginx.org/) | Reverse proxy |

---

<h2 id="connect">🔗 Connect</h2>

<p align="center">
  <a href="https://github.com/MohammadKobirShah">
    <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
  </a>
  <a href="https://twitter.com">
    <img src="https://img.shields.io/badge/Twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white" alt="Twitter">
  </a>
  <a href="mailto:kobirshah@example.com">
    <img src="https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Email">
  </a>
</p>

---

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-❤️-red?style=flat" alt="Made with love">
  <img src="https://img.shields.io/badge/Open-Source-yes-green?style=flat" alt="Open Source">
  <img src="https://img.shields.io/badge/Production-Ready-blue?style=flat" alt="Production Ready">
</p>

<p align="center">
  <sub>DLHUB © 2024 - High-Performance Open Media Downloading Platform</sub>
</p>

<!--
╔══════════════════════════════════════════════════════════════════════════════╗
║                              END OF README                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
-->