"""Utility functions for SkillForge."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


def sanitize_name(name: str) -> str:
    """Sanitize a skill name for use as a filename."""
    name = re.sub(r"[^\w\-]", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-").lower()


def compute_hash(content: str | bytes) -> str:
    """Compute a SHA-256 hash of content."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_file_safe(path: Path, encoding: str = "utf-8") -> str | None:
    """Read a file safely, returning None if it doesn't exist."""
    try:
        return path.read_text(encoding=encoding)
    except OSError:
        return None


def write_file_safe(path: Path, content: str, encoding: str = "utf-8") -> bool:
    """Write a file safely, creating parent directories."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return True
    except OSError:
        return False


def format_version(version: str) -> str:
    """Format a version string with leading v."""
    if not version.startswith("v"):
        return f"v{version}"
    return version


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def parse_tags(tags_str: str) -> list[str]:
    """Parse a comma-separated tags string."""
    return [t.strip().lower() for t in tags_str.split(",") if t.strip()]
