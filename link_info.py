"""Read JSON from Link Info and display its formats as a console table."""

import json
import subprocess
from typing import Any, Callable


def format_formats(metadata: dict[str, Any]) -> str:
    formats = metadata.get("formats") or []
    if not isinstance(formats, list) or any(not isinstance(item, dict) for item in formats):
        raise ValueError("Expected a list of format objects")
    if not formats:
        return "No formats available.\n"

    rows = [["ID", "EXT", "RESOLUTION", "FPS", "VIDEO", "AUDIO", "NOTE"]]
    for item in formats:
        resolution = item.get("resolution")
        if not resolution:
            if item.get("vcodec") == "none":
                resolution = "audio only"
            elif item.get("width") and item.get("height"):
                resolution = f"{item['width']}x{item['height']}"
            elif item.get("height"):
                resolution = f"{item['height']}p"
        rows.append([
            str(item.get("format_id") or "?"),
            str(item.get("ext") or "-"),
            str(resolution or "-"),
            str(item.get("fps") or "-"),
            str(item.get("vcodec") or "-"),
            str(item.get("acodec") or "-"),
            str(item.get("format_note") or ""),
        ])
    widths = [max(len(row[column]) for row in rows) for column in range(len(rows[0]))]
    table = "\n".join(
        "  ".join(value.ljust(width) for value, width in zip(row, widths)).rstrip()
        for row in rows
    )
    title = metadata.get("title") or metadata.get("id") or "video"
    return f"Available formats for {title}:\n{table}\n"


def read_link_info(process: subprocess.Popen[bytes], out_append: Callable[[str], None]) -> None:
    """Read one process in a background thread, using the existing output callback."""
    def output(text: str) -> None:
        for line in text.splitlines(keepends=True):
            out_append(line)

    try:
        stdout, stderr = process.communicate()
        output(stderr.decode("utf-8", errors="replace"))
        if process.returncode:
            output(f"ERROR: Link Info failed (exit code {process.returncode}).\n")
            return
        metadata = json.loads(stdout)
        if not isinstance(metadata, dict) or "entries" in metadata or metadata.get("_type") in {"playlist", "multi_video"}:
            raise ValueError("Expected metadata for a single video")
        output(format_formats(metadata))
    except (OSError, ValueError, UnicodeDecodeError) as error:
        output(f"ERROR: Could not read link information: {error}\n")
