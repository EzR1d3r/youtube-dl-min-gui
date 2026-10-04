"""Accurate local chapter splitting with FFmpeg re-encoding."""

import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Callable, Sequence

from chapters import Chapter
from audio_tags import AudioTags, CoverImage, cover_path, read_cover, write_audio_tags


def _executable(location: str, name: str) -> str:
    location = os.path.expanduser(location)
    suffix = ".exe" if os.name == "nt" else ""
    if os.path.isdir(location):
        candidate = os.path.join(location, name + suffix)
    elif os.path.isfile(location):
        candidate = location if name == "ffmpeg" else os.path.join(
            os.path.dirname(location), name + suffix,
        )
    else:
        candidate = shutil.which(name) if not location else None
    if not candidate or not os.path.isfile(candidate):
        raise ValueError(f"Cannot find {name}; check ffmpeg_path.")
    return candidate


def _safe_title(title: str) -> str:
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip(" .")
    return title[:80].rstrip(" .") or "Chapter"


def split_media(
    source: str,
    folder: str,
    chapters: Sequence[Chapter],
    ffmpeg_path: str,
    log: Callable[[str], None],
    *, audio_tags: Sequence[AudioTags] | None = None,
    original_cover: Path | None = None,
) -> None:
    if audio_tags is not None and len(audio_tags) != len(chapters):
        raise ValueError("Each audio chapter needs its own tags.")
    covers: list[CoverImage] = []
    if audio_tags is not None:
        log("[Split media] Validating chapter covers\n")
        cached: dict[Path, CoverImage] = {}
        for number, tags in enumerate(audio_tags, 1):
            try:
                image_path = cover_path(tags.cover, original_cover)
                if image_path not in cached:
                    cached[image_path] = read_cover(image_path)
                covers.append(cached[image_path])
            except ValueError as error:
                raise ValueError(f"Chapter {number}: {error}") from error
    source_path = Path(source).resolve(strict=True)
    ffmpeg = _executable(ffmpeg_path, "ffmpeg")
    ffprobe = _executable(ffmpeg_path, "ffprobe")
    log(f"[Split media] Inspecting {source_path.name}\n")
    probe = subprocess.run(
        [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(source_path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
    )
    if probe.returncode != 0:
        raise ValueError(f"FFprobe failed: {probe.stderr.strip()}")
    metadata = json.loads(probe.stdout)
    streams = metadata.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"
                  and not stream.get("disposition", {}).get("attached_pic")), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    if audio_tags is not None:
        if audio is None:
            raise ValueError("Extended Audio requires an audio stream.")
        video = None
    if video is None and audio is None:
        raise ValueError("The downloaded file has no video or audio stream.")
    duration = metadata.get("format", {}).get("duration")
    if duration is not None:
        duration = float(duration)
        if math.isfinite(duration):
            for number, chapter in enumerate(chapters, 1):
                # Allow small differences between reported and encoded durations.
                if chapter.end_time > duration + 0.25:
                    raise ValueError(f"Chapter {number} ends beyond the downloaded file "
                                     f"({duration:.2f} s).")

    extension = ".mp4" if video else ".mp3"
    audio_encoding = ["-c:a", "aac", "-b:a", "192k"]
    if extension == ".mp3":
        try:
            source_bitrate = int(audio.get("bit_rate", 0))
        except (TypeError, ValueError):
            source_bitrate = 0
        if source_bitrate > 0:
            # MP3 needs a supported bitrate; VBR sources report an average.
            supported = (8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320)
            bitrate = min(supported, key=lambda value: abs(value * 1000 - source_bitrate))
            audio_encoding = ["-c:a", "libmp3lame", "-b:a", f"{bitrate}k"]
            log(f"[Split media] Source audio bitrate: {source_bitrate / 1000:.1f} kbps; "
                f"MP3 target: {bitrate} kbps\n")
        else:
            audio_encoding = ["-c:a", "libmp3lame", "-q:a", "2"]
            log("[Split media] Source audio bitrate is unknown; using MP3 VBR quality 2\n")
    outputs = []
    for number, chapter in enumerate(chapters, 1):
        if audio_tags is None:
            filename = f"{source_path.stem[:100]} - {number:03d} - {_safe_title(chapter.title)}"
        else:
            tags = audio_tags[number - 1]
            parts = [tags.track_text]
            if tags.artist:
                parts.append(_safe_title(tags.artist))
            parts.append(_safe_title(tags.title))
            filename = " - ".join(parts)
        outputs.append(Path(folder) / (filename + extension))
    if len(set(outputs)) != len(outputs):
        raise ValueError("Chapter filenames must be unique; check Track, Artist and Title.")
    for output in outputs:
        if output.exists():
            raise ValueError(f"Chapter output already exists: {output}")

    os.makedirs(folder, exist_ok=True)
    log(f"[Split media] Re-encoding {len(chapters)} chapters\n")
    # Only completed files receive their final names; failures leave no partial chapter.
    with tempfile.TemporaryDirectory(prefix=".mingui-chapters-", dir=folder) as workspace:
        for number, (chapter, output) in enumerate(zip(chapters, outputs), 1):
            temporary = Path(workspace) / f"{number:03d}{extension}"
            command = [
                ffmpeg, "-hide_banner", "-nostdin", "-y", "-nostats",
                "-abort_on", "empty_output", "-accurate_seek",
                "-ss", f"{chapter.start_time:.3f}", "-i", str(source_path),
                "-t", f"{chapter.end_time - chapter.start_time:.3f}",
                "-map_metadata", "0", "-map_chapters", "-1",
            ]
            if video:
                command += [
                    "-map", f"0:{video['index']}", "-c:v", "libx264",
                    "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                ]
            if audio:
                command += ["-map", f"0:{audio['index']}"]
                command += audio_encoding
            if extension == ".mp4":
                command += ["-movflags", "+faststart"]
            command += [str(temporary)]
            log(f"[Split media] Chapter {number}/{len(chapters)}: {chapter.title} "
                f"({chapter.start_time:.2f}–{chapter.end_time:.2f} s)\n")
            with subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
            ) as process:
                for line in process.stdout:
                    log(line)
                if process.wait() != 0:
                    raise ValueError(f"FFmpeg failed while processing chapter {number}.")
            if not temporary.is_file() or temporary.stat().st_size == 0:
                raise ValueError(f"FFmpeg produced an empty chapter {number}.")
            if audio_tags is not None:
                log(f"[Split media] Writing audio tags for track {audio_tags[number - 1].track_text}\n")
                write_audio_tags(temporary, audio_tags[number - 1], covers[number - 1])
            if output.exists():
                raise ValueError(f"Chapter output already exists: {output}")
            temporary.rename(output)
            log(f"[Split media] Saved {output}\n")
    log("[Split media] Finished. The original file was kept.\n")
