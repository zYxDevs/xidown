import os
import subprocess
import sys
import time
import zipfile
from urllib import request
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Union, Optional, Tuple
from threading import Event

from xidown.core.constants import MAX_CHUNK_SIZE, DEFAULT_USER_AGENT, YT_DLP_DOWNLOAD_URL
from xidown.core.types import AnyCallable
from xidown.core.utils import get_bin_folder, safe_rm, safe_rmdir

def download_binary(url: str, dest_path: str,
                    progress_callback: Optional[AnyCallable] = None,
                    cancel_event: Optional[Event] = None) -> bool:
    """
    Downloads a file with progress reporting and cancellation support.
    """
    # Ensure destination directory exists
    dest_dir = Path(dest_path).absolute().parent if dest_path else None
    if dest_dir and not dest_dir.exists():
        dest_dir.mkdir(parents=True)

    req = request.Request(url, headers={ 'User-Agent': DEFAULT_USER_AGENT })
    try:
        with request.urlopen(req) as response:
            total_size = int(response.info().get('Content-Length', 0))
            block_size = MAX_CHUNK_SIZE
            downloaded = 0

            with open(dest_path, 'wb') as f:
                while True:
                    if cancel_event and cancel_event.is_set():
                        return False

                    block = response.read(block_size)
                    if not block: break

                    f.write(block)
                    downloaded += len(block)
                    if total_size > 0 and progress_callback:
                        percent = downloaded / total_size
                        progress_callback(percent, downloaded, total_size)
            return True
    except Exception as e:
        print(f"[SetupBinaries] Error downloading {url}: {e}", file=sys.stderr)
        return False

def extract_ffmpeg_binaries(zip_path: str, bin_dir: Optional[Union[str, Path]] = None,
                            cancel_event: Optional[Event] = None) -> bool:
    """
    Extracts ffmpeg.exe and ffprobe.exe from the downloaded zip file and places them in bin_dir.
    """
    try:
        if cancel_event and cancel_event.is_set():
            return False

        extracted_members: Dict[str, Union[str, None]] = {
            'ffmpeg': None,
            'ffprobe': None
        }

        # Fallback if bin directory is not provided
        bin_dir = Path(bin_dir) if bin_dir else get_bin_folder(True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Look for ffmpeg.exe and ffprobe.exe inside the zip file
            for member in zip_ref.namelist():
                if member.endswith("ffmpeg.exe"):
                    extracted_members['ffmpeg'] = member
                elif member.endswith("ffprobe.exe"):
                    extracted_members['ffprobe'] = member

                # Break once both ffmpeg and ffprobe has been found
                if extracted_members['ffmpeg'] and extracted_members['ffprobe']:
                    break

            # If the ffmpeg binary file does not exist, then also for ffprobe is not exist
            if not extracted_members['ffmpeg']:
                print("[SetupBinaries] ffmpeg.exe not found in zip archive.", file=sys.stderr)
                return False

            # Extract to temporary directory and move to bin_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_p = Path(tmpdir)
                if cancel_event and cancel_event.is_set():
                    return False

                # Extract ffmpeg.exe
                zip_ref.extract(extracted_members['ffmpeg'], tmpdir)
                extracted_path = tmpdir_p / extracted_members['ffmpeg']
                dest_path = bin_dir / "ffmpeg.exe"

                if not bin_dir.exists():
                    bin_dir.mkdir(parents=True)

                # Remove any existing ffmpeg file
                if dest_path.exists():
                    safe_rm(dest_path)

                shutil.move(extracted_path, dest_path)

                # Extract ffprobe.exe if available
                ffprobe_path = extracted_members['ffprobe']
                if ffprobe_path:
                    zip_ref.extract(ffprobe_path, tmpdir)
                    extracted_probe_path = tmpdir_p / ffprobe_path
                    dest_probe_path = bin_dir / "ffprobe.exe"

                    if dest_probe_path.exists():
                        safe_rm(dest_probe_path)

                    shutil.move(extracted_probe_path, dest_probe_path)

                # Python <3.11 support, remove the temp directory manually
                safe_rmdir(tmpdir)
        return True
    except Exception as e:
        print(f"[SetupBinaries] Error extracting ffmpeg: {e}", file=sys.stderr)
        return False

def get_ytdlp_version(yt_dlp_path: Optional[str] = None) -> Optional[str]:
    """Check currently installed yt-dlp version."""
    if not yt_dlp_path:
        bin_dir = Path(get_bin_folder(True))
        candidate = bin_dir / ("yt-dlp.exe" if sys.platform == "win32" else "yt-dlp")
        if candidate.is_file():
            yt_dlp_path = str(candidate)
        else:
            yt_dlp_path = shutil.which("yt-dlp.exe" if sys.platform == "win32" else "yt-dlp")
            
    if not yt_dlp_path or not os.path.exists(yt_dlp_path):
        return None
        
    try:
        flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
        proc = subprocess.run(
            [yt_dlp_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            **flags
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    except Exception as e:
        print(f"[SetupBinaries] Error getting yt-dlp version: {e}", file=sys.stderr)
    return None

def flush_ytdlp_cache(yt_dlp_path: Optional[str] = None) -> bool:
    """Flush yt-dlp extractor cache directory to clear stale session tokens."""
    if not yt_dlp_path:
        bin_dir = Path(get_bin_folder(True))
        candidate = bin_dir / ("yt-dlp.exe" if sys.platform == "win32" else "yt-dlp")
        yt_dlp_path = str(candidate) if candidate.is_file() else "yt-dlp"
        
    try:
        flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
        proc = subprocess.run(
            [yt_dlp_path, "--rm-cache-dir"],
            capture_output=True,
            text=True,
            timeout=15,
            **flags
        )
        return proc.returncode == 0
    except Exception as e:
        print(f"[SetupBinaries] Error clearing yt-dlp cache: {e}", file=sys.stderr)
        return False

def update_ytdlp(channel: str = "stable",
                 yt_dlp_path: Optional[str] = None,
                 progress_callback: Optional[AnyCallable] = None) -> Tuple[bool, str]:
    """
    Updates yt-dlp to latest version.
    Supports channel: 'stable' or 'nightly'.
    First tries in-place update (yt-dlp --update-to <target>).
    If in-place update fails, falls back to direct GitHub binary download.
    Also clears extractor cache after update.
    """
    if not yt_dlp_path:
        bin_dir = Path(get_bin_folder(True))
        candidate = bin_dir / ("yt-dlp.exe" if sys.platform == "win32" else "yt-dlp")
        yt_dlp_path = str(candidate) if candidate.is_file() else "yt-dlp"

    kill_running_ytdlp()

    target_channel = "nightly" if channel.lower() == "nightly" else "stable@latest"
    target_name = "Nightly" if channel.lower() == "nightly" else "Stable"

    if progress_callback:
        progress_callback(0.2, f"Checking {target_name} updates for yt-dlp...")
        
    flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
    try:
        proc = subprocess.run(
            [yt_dlp_path, "--update-to", target_channel],
            capture_output=True,
            text=True,
            timeout=60,
            **flags
        )
        combined_out = (proc.stdout + "\n" + proc.stderr).strip()
        if proc.returncode == 0:
            flush_ytdlp_cache(yt_dlp_path)
            new_ver = get_ytdlp_version(yt_dlp_path) or "latest"
            if "is up to date" in combined_out.lower():
                return True, f"yt-dlp is already up to date ({new_ver})."
            return True, f"Successfully updated yt-dlp to {new_ver}!"
    except Exception as e:
        print(f"[SetupBinaries] yt-dlp update error: {e}. Falling back to GitHub download...", file=sys.stderr)

    # Fallback to direct binary download if on Windows (for stable channel)
    if sys.platform == "win32" and channel.lower() != "nightly":
        if progress_callback:
            progress_callback(0.4, "Downloading latest yt-dlp from GitHub...")
        return reinstall_ytdlp(progress_callback)
        
    return False, "Failed to update yt-dlp. Please check internet connection."

def kill_running_ytdlp():
    """Terminates any active yt-dlp.exe processes to ensure file handles are released."""
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "yt-dlp.exe"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception:
            pass

def safe_replace_binary(src_path: Union[str, Path], dest_path: Union[str, Path], max_retries: int = 5) -> bool:
    """
    Safely replaces an executable binary with retry, process termination,
    and backup rename to prevent [Errno 13] Permission denied on Windows.
    """
    src = Path(src_path)
    dest = Path(dest_path)
    if not src.exists():
        return False

    kill_running_ytdlp()

    old_bak = dest.with_name(dest.stem + "_old" + dest.suffix)
    if old_bak.exists():
        try:
            old_bak.unlink()
        except Exception:
            pass

    for attempt in range(max_retries):
        try:
            if dest.exists():
                try:
                    dest.unlink()
                except (PermissionError, OSError):
                    try:
                        dest.rename(old_bak)
                    except Exception:
                        pass

            shutil.move(str(src), str(dest))

            if old_bak.exists():
                try:
                    old_bak.unlink()
                except Exception:
                    pass
            return True
        except (PermissionError, OSError):
            kill_running_ytdlp()
            time.sleep(0.5 * (attempt + 1))

    return False

def reinstall_ytdlp(progress_callback: Optional[AnyCallable] = None,
                    cancel_event: Optional[Event] = None) -> Tuple[bool, str]:
    """
    Directly downloads fresh yt-dlp.exe from GitHub releases into local bin directory.
    """
    if sys.platform != "win32":
        return False, "Direct binary reinstall is only supported on Windows. Use package manager on Linux/macOS."

    bin_dir = Path(get_bin_folder(True))
    if not bin_dir.exists():
        bin_dir.mkdir(parents=True, exist_ok=True)
        
    dest_path = str(bin_dir / "yt-dlp.exe")
    temp_path = str(bin_dir / "yt-dlp_download_temp.exe")

    if progress_callback:
        progress_callback(0.1, "Downloading yt-dlp.exe...")

    def dl_cb(percent, dl, total):
        if progress_callback:
            progress_callback(percent, f"Downloading yt-dlp.exe ({int(percent * 100)}%)...")

    success = download_binary(YT_DLP_DOWNLOAD_URL, temp_path, progress_callback=dl_cb, cancel_event=cancel_event)
    if not success:
        safe_rm(temp_path)
        return False, "Failed to download yt-dlp.exe from GitHub."

    try:
        success_replace = safe_replace_binary(temp_path, dest_path)
        if not success_replace:
            safe_rm(temp_path)
            return False, "File is locked by Windows/antivirus. Please wait a moment and retry."

        flush_ytdlp_cache(dest_path)
        new_ver = get_ytdlp_version(dest_path) or "latest"
        return True, f"Successfully reinstalled yt-dlp ({new_ver})!"
    except Exception as e:
        safe_rm(temp_path)
        return False, f"Failed to replace yt-dlp: {e}"


