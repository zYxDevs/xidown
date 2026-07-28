import os
import re
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Literal, Tuple, Optional, overload

from xidown.core.constants import FAVICON_PATH
from xidown.core.types import PathLike

# --------- Simple Utilities ---------- #
def is_windows() -> bool:
    """Returns true if the current system is Windows."""
    return sys.platform == 'win32'

@overload
def sanitize_filename(name: str) -> str: ...
@overload
def sanitize_filename(name: Path) -> Path: ...

def sanitize_filename(name: PathLike) -> PathLike:
    """
    Sanitize filename to be used by system files.
    Strips invalid characters, trailing dots/spaces, and handles Windows reserved filenames.

    Returns a filename with type consistent to the given input type.
    """
    _name = str(name)
    sanitized = re.sub(r'[\\/*?:"<>|]', "", _name).strip(" .")
    
    reserved_names = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }
    stem = sanitized.split(".")[0].upper()
    if stem in reserved_names:
        sanitized = f"_{sanitized}"
        
    if not sanitized:
        sanitized = "unnamed_file"

    return Path(sanitized) if isinstance(name, Path) else sanitized

def hide_directory(path: PathLike) -> bool:
    """Safely set hidden attribute on a Windows directory."""
    try:
        if is_windows() and os.path.exists(str(path)):
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(str(path), 0x02)
            return True
    except Exception:
        pass
    return False

def safe_rm(path: PathLike) -> bool:
    """Safely remove a regular file."""
    try:
        os.remove(str(path))
        return True
    except Exception:
        return False

def safe_rmdir(path: PathLike) -> bool:
    """Safely remove a directory tree recursively."""
    try:
        shutil.rmtree(path)
        return True
    except Exception:
        return False

@overload
def get_rootdir() -> str: ...
@overload
def get_rootdir(as_path: Literal[False]) -> str: ...
@overload
def get_rootdir(as_path: Literal[True]) -> Path: ...
@overload
def get_rootdir(as_path: bool) -> PathLike: ...

def get_rootdir(as_path: bool = False) -> PathLike:
    """Get the project's root directory."""
    base_path: Path
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).absolute().parent.parent.parent
    return base_path if as_path else str(base_path)

@overload
def get_bin_folder() -> str: ...
@overload
def get_bin_folder(as_path: Literal[True]) -> Path: ...
@overload
def get_bin_folder(as_path: Literal[False]) -> str: ...
@overload
def get_bin_folder(as_path: bool) -> PathLike: ...

def get_bin_folder(as_path: bool = False) -> PathLike:
    """Get the project's binary directory, relative to project's root directory."""
    bin_path = get_rootdir(True) / 'bin'
    return bin_path if as_path else str(bin_path)

def check_setup() -> Optional[Tuple[str, str, str]]:
    """
    Verify the existence of external binaries (ffmpeg & yt-dlp).
    Checks system PATH first, then falls back to local bin directory.
    Returns (yt-dlp path, ffmpeg directory, cookies path) or None if missing.
    """
    is_win = is_windows()
    yt_dlp_name = "yt-dlp.exe" if is_win else "yt-dlp"
    ffmpeg_name = "ffmpeg.exe" if is_win else "ffmpeg"

    bin_folder = get_bin_folder(True)

    local_yt = bin_folder / yt_dlp_name
    path_yt_dlp = local_yt if local_yt.is_file() else None

    local_ff = bin_folder / ffmpeg_name
    path_ffmpeg = local_ff if local_ff.is_file() else None

    if not path_yt_dlp:
        _temp = shutil.which(yt_dlp_name)
        path_yt_dlp = Path(_temp) if _temp else None

    if not path_ffmpeg:
        _temp = shutil.which(ffmpeg_name)
        path_ffmpeg = Path(_temp) if _temp else None

    path_cookies = bin_folder / "cookies.txt"

    missing = []
    if not path_yt_dlp: missing.append(yt_dlp_name)
    if not path_ffmpeg: missing.append(ffmpeg_name)

    if missing:
        print(f"[Utils] Searching binaries in System PATH and: {bin_folder}", file=sys.stderr)
        print(f"[Utils] ERROR: Missing: {', '.join(missing)}", file=sys.stderr)
        return None

    ffmpeg_dir = path_ffmpeg.parent if path_ffmpeg else bin_folder
    return str(path_yt_dlp), str(ffmpeg_dir), str(path_cookies)

def format_size(bytes_size: float) -> str:
    if not bytes_size: return "Unknown"
    power = 1024
    n = 0
    power_labels = {0 : '', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while bytes_size > power and n < 4:
        bytes_size /= power
        n += 1
    return f"{bytes_size:.2f} {power_labels[n]}"

def hitung_estimasi_mp3(duration_detik: int) -> str:
    if not duration_detik: return "Unknown"
    try:
        total_bytes = int(duration_detik) * 16 * 1024 
        return format_size(total_bytes)
    except Exception:
        return "Unknown"

def get_icon_path() -> Optional[str]:
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = get_rootdir(True)
        
    favicon_path = base_path.joinpath(*FAVICON_PATH.split('/'))
    if favicon_path.is_file():
        return str(favicon_path)
    return None
