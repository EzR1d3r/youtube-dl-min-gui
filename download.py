"""Download arguments and processing to run after a successful download."""

import os
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class DownloadPlan:
    options: list[str]
    postprocessors: list[Callable[[], None]] = field(default_factory=list)

    def postprocess(self) -> None:
        for process in self.postprocessors:
            process()


def build_download_plan(
    options_str: str,
    folder: str,
    title_template: str,
    ffmpeg_path: str,
    split_mode: str | None = None,
) -> DownloadPlan:
    if split_mode not in (None, "Default"):
        raise ValueError(f"Splitting in {split_mode} mode is not implemented yet.")

    folder = os.path.abspath(os.path.expanduser(folder))
    options = options_str.split(" ") if options_str else []
    options += ["-o", os.path.join(folder, title_template)]
    options += ["--ffmpeg-location", ffmpeg_path]
    if split_mode == "Default":
        options += ["--split-chapters"]

    # Chapter output has its own template, independent of the main file's -o.
    # Also applies when --split-chapters is supplied in an Options preset.
    chapter_template = "%(title)s - %(section_number)03d - %(section_title)s.%(ext)s"
    options += ["-o", "chapter:" + os.path.join(folder, chapter_template)]
    return DownloadPlan(options)
