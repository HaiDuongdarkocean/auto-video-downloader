import os
import re
from urllib.parse import urlparse

# Characters invalid on Windows and common filesystems.
_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
_MULTI_SPACE = re.compile(r"  +")


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename.

    Removes characters invalid on common filesystems (\\/:*?"<>|), collapses
    runs of internal whitespace, and strips leading/trailing whitespace.
    Returns "untitled" when the result would be empty.
    """
    if not name:
        return "untitled"
    cleaned = _INVALID_CHARS.sub("", name)
    cleaned = cleaned.strip()
    cleaned = _MULTI_SPACE.sub(" ", cleaned)
    if not cleaned:
        return "untitled"
    return cleaned


def get_website_name(url: str) -> str:
    """Extract the website domain from a URL.

    Returns "unknown" when the URL cannot be parsed.
    """
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc
        if not netloc:
            return "unknown"
        return netloc.rstrip("/")
    except (ValueError, AttributeError):
        return "unknown"


def create_output_path(base_url: str, video_title: str, base_dir: str = "./downloads") -> str:
    """Create the output folder for a video and return its path.

    The folder structure is `<base_dir>/<website_name>/<sanitized_title>/`.
    Directories are created if missing. Safe to call repeatedly (idempotent).

    Args:
        base_url: The source page URL; its domain becomes the website folder.
        video_title: The video title; sanitized into a valid folder name.
        base_dir: Root output directory. Defaults to "./downloads".

    Returns:
        Absolute or relative path to the created video folder.
    """
    website = get_website_name(base_url)
    title = sanitize_filename(video_title)
    path = os.path.join(base_dir, website, title)
    os.makedirs(path, exist_ok=True)
    return path
