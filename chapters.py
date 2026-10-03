"""Parse yt-dlp chapter JSON without fetching metadata or changing the GUI."""

import json
import math
from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Chapter:
    """A named time interval; timestamps are seconds, including fractions."""

    title: str
    start_time: float
    end_time: float


class ChapterParseError(ValueError):
    """Metadata contains malformed or incomplete chapter information."""


def _timestamp(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ChapterParseError(f"{name} must be a number of seconds")
    try:
        seconds = float(value)
    except OverflowError as error:
        raise ChapterParseError(f"{name} must be finite") from error
    if not math.isfinite(seconds) or seconds < 0:
        raise ChapterParseError(f"{name} must be finite and nonnegative")
    return seconds


def parse_chapters(metadata: Union[str, bytes, dict, list]) -> list[Chapter]:
    """Read full video metadata or a chapters-only array, decoded or as JSON.

    Missing/null/empty chapters return an empty list. Missing end times are
    inferred from the next chapter's start, or video duration for the last one.
    Chapters must have strictly increasing starts and positive durations.
    Explicit gaps and overlaps are preserved. Bad data raises ChapterParseError
    rather than silently dropping chapters. The input is never modified.
    """
    if isinstance(metadata, (str, bytes)):
        try:
            metadata = json.loads(metadata)
        except (ValueError, UnicodeDecodeError) as error:
            raise ChapterParseError("Invalid chapter JSON") from error

    duration = None
    if isinstance(metadata, dict):
        if "entries" in metadata or metadata.get("_type") in {"playlist", "multi_video"}:
            raise ChapterParseError("Expected a single video's metadata, not a playlist")
        raw_chapters = metadata.get("chapters")
        raw_duration = metadata.get("duration")
    elif isinstance(metadata, list):
        raw_chapters = metadata
        raw_duration = None
    else:
        raise ChapterParseError("Expected a metadata object or chapter array")

    if raw_chapters is None:
        return []
    if not isinstance(raw_chapters, list):
        raise ChapterParseError("chapters must be an array")
    if not raw_chapters:
        return []
    if raw_duration is not None:
        duration = _timestamp(raw_duration, "duration")

    starts = []
    for index, item in enumerate(raw_chapters, 1):
        if not isinstance(item, dict):
            raise ChapterParseError(f"Chapter {index} must be an object")
        start = _timestamp(item.get("start_time"), f"Chapter {index} start_time")
        if starts and start <= starts[-1]:
            raise ChapterParseError("Chapter start times must be strictly increasing")
        starts.append(start)

    chapters = []
    for index, item in enumerate(raw_chapters):
        number = index + 1
        title = item.get("title")
        if title is not None and not isinstance(title, str):
            raise ChapterParseError(f"Chapter {number} title must be a string")
        title = (title or "").strip() or f"Chapter {number}"
        end = item.get("end_time")
        if end is None:
            end = starts[index + 1] if number < len(starts) else duration
        if end is None:
            raise ChapterParseError(f"Chapter {number} needs end_time or video duration")
        end = _timestamp(end, f"Chapter {number} end_time")
        if end <= starts[index]:
            raise ChapterParseError(f"Chapter {number} end_time must be after start_time")
        if duration is not None and end > duration:
            raise ChapterParseError(f"Chapter {number} extends beyond video duration")
        chapters.append(Chapter(title, starts[index], end))
    return chapters
