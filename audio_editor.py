"""Chapter time editor with editable audio tags."""

import tkinter as tk
from tkinter import ttk

from audio_tags import AudioTags
from chapter_editor import ChapterEditor, ChapterRow
from chapters import Chapter


class AudioChapterEditor(ChapterEditor):
    headings = ("Track", "Artist", "Title", "Album", "Start", "End", "Lock")
    time_columns = (4, 5)
    lock_column = 6

    def __init__(self, master, on_change):
        self.fields: list[dict[str, tk.StringVar]] = []
        super().__init__(master, on_change)
        self.body.columnconfigure(2, weight=2)
        self.body.columnconfigure(3, weight=1)

    def set_chapters(self, chapters: list[Chapter]) -> None:
        self.fields.clear()
        super().set_chapters(chapters)

    def _add_identity_widgets(self, number: int, row: ChapterRow) -> None:
        fields = {
            "track": tk.StringVar(master=self, value=f"{number:02d}"),
            "artist": tk.StringVar(master=self),
            "title": tk.StringVar(master=self, value=row.chapter.title),
            "album": tk.StringVar(master=self),
        }
        self.fields.append(fields)
        for column, (name, width) in enumerate([("track", 5), ("artist", 20), ("title", 30), ("album", 20)]):
            entry = ttk.Entry(self.body, textvariable=fields[name], width=width)
            entry.grid(row=number, column=column, sticky="ew", padx=8, pady=4)
            if name == "track":
                entry.bind("<FocusOut>", lambda event, i=number - 1: self._format_track(i))
                entry.bind("<Return>", lambda event, i=number - 1: self._format_track(i))

    def _chapter_title(self, index: int, row: ChapterRow) -> str:
        return self.fields[index]["title"].get().strip()

    def _format_track(self, index: int) -> None:
        variable = self.fields[index]["track"]
        value = variable.get().strip()
        if value.isascii() and value.isdigit() and 1 <= int(value) <= 65535:
            variable.set(f"{int(value):02d}")

    def get_audio_tags(self) -> list[AudioTags]:
        result = []
        for number, fields in enumerate(self.fields, 1):
            title = fields["title"].get().strip()
            track = fields["track"].get().strip()
            if not title:
                raise ValueError(f"Chapter {number}: enter a Title.")
            if not (track.isascii() and track.isdigit() and 1 <= int(track) <= 65535):
                raise ValueError(f"Chapter {number}: Track must be an integer from 1 to 65535.")
            self._format_track(number - 1)
            result.append(AudioTags(title, fields["artist"].get().strip(), int(track),
                                    fields["album"].get().strip()))
        return result
