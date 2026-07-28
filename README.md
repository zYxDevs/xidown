# xidown

<p align="center">
  <img src="assets/favicon.ico" width="100" alt="xidown Logo" />
</p>

<p align="center">
  <img src="xidownv0.2516.png" alt="xidown GUI Screenshot" />
</p>

**xidown** is a cross-platform GUI media downloader built with Python and CustomTkinter. Powered by `yt-dlp` and `ffmpeg`, it allows you to scan, queue, and download videos and audio with automated cookie syncing, playlist protection, and instant browser extension integration.

---

## Features

- **Modern CustomTkinter GUI:** Fluid dark-themed interface with queue reordering, card pinning, and instant 15-second test play previews.
- **Multi-Platform Downloader:** Download high-quality MP4 video or extract MP3 audio with embedded thumbnails and metadata.
- **Browser Extension Sync:** Built-in local server (port 3000) for one-click download capture from browser extensions.
- **Smart Cookie Management:** Domain-specific cookie auto-detection to bypass login walls, age restrictions, and bot protections.
- **Thread-Safe Architecture:** Full UNDO/REDO list management, playlist guard dialogs, and parallel worker pool.

---

## Quick Start

### Prerequisites
- **Python:** 3.8+ (Python 3.10 recommended)
- **External Tools:** `yt-dlp` and `ffmpeg` (automatically prompted on first run if missing)

### Installation

```bash
git clone https://github.com/indravoyager/xidown.git
cd xidown

python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -e .
```

### Usage

```bash
# Direct Entry Point
python main.py

# Module Mode
python -m xidown

# Package CLI (if installed)
xidown
```

---

## Building Standalone Executable (.exe)

Build native standalone executables using Nuitka:

```bash
pip install nuitka ordered-set
python build.py
```

The output standalone binary and release ZIP will be placed inside `dist/` and `releases/`.

---

## License

[MIT](LICENSE)
