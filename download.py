"""Download arguments and processing to run after a successful download."""

import os
import json
import math
import tempfile
from dataclasses import dataclass, field
from typing import Callable
from pathlib import Path

from chapters import Chapter
from audio_tags import AudioTags
from media_splitter import split_media


@dataclass
class DownloadPlan:
    options: list[str]
    postprocessors: list[Callable[[], None]] = field(default_factory=list)
    workspace: tempfile.TemporaryDirectory | None = None

    def postprocess(self) -> None:
        for process in self.postprocessors:
            process()

    def cleanup(self) -> None:
        if self.workspace is not None:
            self.workspace.cleanup()


def build_download_plan(
    options_str: str,
    folder: str,
    title_template: str,
    ffmpeg_path: str,
    split_mode: str | None = None,
    chapters: list[Chapter] | None = None,
    log: Callable[[str], None] = print,
    audio_tags: list[AudioTags] | None = None,
) -> DownloadPlan:
    if split_mode not in (None, "Default", "Extended", "Extended Audio"):
        raise ValueError(f"Splitting in {split_mode} mode is not implemented yet.")

    folder = os.path.abspath(os.path.expanduser(folder))
    options = options_str.split()
    options += ["-o", os.path.join(folder, title_template)]
    options += ["--ffmpeg-location", ffmpeg_path]
    if split_mode == "Default":
        options += ["--split-chapters"]

    # Chapter output has its own template, independent of the main file's -o.
    # Also applies when --split-chapters is supplied in an Options preset.
    chapter_template = "%(title)s - %(section_number)03d - %(section_title)s.%(ext)s"
    options += ["-o", "chapter:" + os.path.join(folder, chapter_template)]
    plan = DownloadPlan(options)
    if split_mode in ("Extended", "Extended Audio"):
        selected = tuple(chapters or [])
        selected_tags = tuple(audio_tags or []) if split_mode == "Extended Audio" else None
        if not selected:
            raise ValueError(f"{split_mode}: request Link Info before downloading.")
        if selected_tags is not None:
            if len(selected_tags) != len(selected):
                raise ValueError("Extended Audio requires tags for every chapter.")
        for number, chapter in enumerate(selected, 1):
            if not (math.isfinite(chapter.start_time) and math.isfinite(chapter.end_time)
                    and 0 <= chapter.start_time < chapter.end_time):
                raise ValueError(f"Chapter {number}: invalid time range.")
        # These options change the source timeline used by the editor.
        for option in options:
            if option.split("=", 1)[0] in {
                "--download-sections", "--remove-chapters", "--sponsorblock-remove",
            }:
                raise ValueError(f"Extended cannot be combined with {option}.")
        os.makedirs(folder, exist_ok=True)
        plan.workspace = tempfile.TemporaryDirectory(prefix=".mingui-download-", dir=folder)
        workspace = Path(plan.workspace.name)
        result_file = str(workspace / "downloaded.jsonl")
        original_cover = None
        if selected_tags is not None:
            original_cover = workspace / "cover.jpg"
            options += [
                "--write-thumbnail", "--convert-thumbnails", "jpg",
                "-o", "thumbnail:" + str(workspace / "cover.%(ext)s"),
            ]
        options += [
            "--no-split-chapters", "--no-playlist",
            "--print-to-file", "after_move:%(filepath)j", result_file,
        ]

        def process_chapters() -> None:
            if not os.path.isfile(result_file):
                raise ValueError("yt-dlp did not report a downloaded media file.")
            with open(result_file, encoding="utf-8") as file:
                paths = [json.loads(line) for line in file if line.strip()]
            if len(paths) != 1 or not isinstance(paths[0], str):
                raise ValueError("Extended requires a single downloaded media file.")
            if selected_tags is None:
                split_media(paths[0], folder, selected, ffmpeg_path, log, workspace=workspace)
            else:
                split_media(paths[0], folder, selected, ffmpeg_path, log,
                            workspace=workspace, audio_tags=selected_tags, original_cover=original_cover)

        plan.postprocessors.append(process_chapters)
    return plan
