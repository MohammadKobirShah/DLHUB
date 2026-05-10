"""
DLHUB - Filename Sanitizer
===========================
Sanitize filenames and paths for safe file operations.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import re
import os
from pathlib import Path
from typing import Optional


SANITIZE_PATTERN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
CONTROL_CHARS_PATTERN = re.compile(r'[\x00-\x1f\x7f]')


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize filename for safe file system operations.

    Args:
        filename: Original filename
        max_length: Maximum allowed length

    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"

    sanitized = SANITIZE_PATTERN.sub("_", filename)

    sanitized = sanitized.strip(". ")

    sanitized = sanitized[:max_length]

    if not sanitized:
        sanitized = "file"

    return sanitized


def sanitize_path(path: str, base_dir: Optional[str] = None) -> str:
    """
    Sanitize file path and prevent path traversal.

    Args:
        path: File path
        base_dir: Base directory to restrict path within

    Returns:
        Sanitized absolute path
    """
    if not path:
        raise ValueError("Path cannot be empty")

    path = os.path.normpath(path)

    path = re.sub(r'[/\\]+', os.sep, path)

    path = SANITIZE_PATTERN.sub("_", path)

    if base_dir:
        abs_base = os.path.abspath(base_dir)
        abs_path = os.path.abspath(os.path.join(abs_base, path))

        if not abs_path.startswith(abs_base + os.sep) and abs_path != abs_base:
            raise ValueError("Path traversal detected")

        return abs_path

    return os.path.abspath(path)


def get_safe_filename(url: str, title: Optional[str] = None, ext: str = "mp4") -> str:
    """
    Generate safe filename from URL or title.

    Args:
        url: Source URL
        title: Optional video title
        ext: File extension

    Returns:
        Safe filename
    """
    if title:
        base = sanitize_filename(title)
    else:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path or parsed.netloc
        base = sanitize_filename(Path(path).stem)

    if not base:
        base = "download"

    filename = f"{base}.{ext}"
    return filename


def validate_extension(filename: str, allowed_extensions: set) -> bool:
    """
    Validate file extension.

    Args:
        filename: Filename to check
        allowed_extensions: Set of allowed extensions

    Returns:
        True if extension is allowed
    """
    ext = Path(filename).suffix.lower()
    return ext in allowed_extensions


def ensure_unique_filename(filepath: str) -> str:
    """
    Ensure filename is unique by adding counter if needed.

    Args:
        filepath: Desired file path

    Returns:
        Unique file path
    """
    if not os.path.exists(filepath):
        return filepath

    path = Path(filepath)
    stem = path.stem
    ext = path.suffix
    directory = path.parent

    counter = 1
    while True:
        new_path = directory / f"{stem}_{counter}{ext}"
        if not new_path.exists():
            return str(new_path)
        counter += 1