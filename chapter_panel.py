"""Chapter panel with separate read-only and editable views."""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from chapters import Chapter
from chapter_editor import ChapterEditor
from audio_editor import AudioChapterEditor
from audio_tags import AudioTags
from time_spinbox import format_time, seconds_to_milliseconds


class ChapterList(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.table = ttk.Treeview(
            self, columns=("number", "title", "start", "end"),
            show="headings", height=1, selectmode="none",
        )
        for column, heading, width in [
            ("number", "#", 45), ("title", "Chapter", 300),
            ("start", "Start", 130), ("end", "End", 130),
        ]:
            self.table.heading(column, text=heading)
            self.table.column(column, width=width, stretch=column == "title")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

    def set_chapters(self, chapters: list[Chapter]) -> None:
        for item in self.table.get_children():
            self.table.delete(item)
        for number, chapter in enumerate(chapters, 1):
            self.table.insert("", "end", values=(
                number, chapter.title,
                format_time(seconds_to_milliseconds(chapter.start_time)),
                format_time(seconds_to_milliseconds(chapter.end_time)),
            ))
        self.table.configure(height=max(1, min(len(chapters), 8)))
        self.table.yview_moveto(0)


class ChapterPanel(ttk.LabelFrame):
    def __init__(self, master, on_change: Callable[[list[Chapter]], None]):
        super().__init__(master, text="Chapters")
        self.on_change = on_change
        self._original: list[Chapter] = []
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Label(toolbar, text="Mode:").pack(side="left", padx=(0, 8))
        self.mode = tk.StringVar(master=self, value="Default")
        selector = ttk.Combobox(
            toolbar, textvariable=self.mode, values=("Default", "Extended", "Extended Audio"),
            state="readonly", width=18,
        )
        selector.pack(side="left")
        selector.bind("<<ComboboxSelected>>", self._switch_mode)

        self.default = ChapterList(self)
        self.extended = ChapterEditor(self, on_change=self._extended_changed)
        self.audio = AudioChapterEditor(self, on_change=self._audio_changed)
        self.views = {"Default": self.default, "Extended": self.extended, "Extended Audio": self.audio}
        for view in self.views.values():
            view.grid(row=1, column=0, sticky="nsew")
            view.grid_remove()
        self.default.grid()

    def set_chapters(self, chapters: list[Chapter]) -> None:
        self._original = list(chapters)
        self.default.set_chapters(chapters)
        self.extended.set_chapters(chapters)
        self.audio.set_chapters(chapters)
        self._switch_mode()

    def get_chapters(self) -> list[Chapter]:
        if self.mode.get() == "Default":
            return list(self._original)
        return self.views[self.mode.get()].get_chapters()

    def get_audio_tags(self) -> list[AudioTags]:
        return self.audio.get_audio_tags()

    def _audio_changed(self, chapters: list[Chapter]) -> None:
        if self.mode.get() == "Extended Audio":
            self.on_change(chapters)

    def _extended_changed(self, chapters: list[Chapter]) -> None:
        if self.mode.get() == "Extended":
            self.on_change(chapters)

    def _switch_mode(self, event=None) -> None:
        for view in self.views.values():
            view.grid_remove()
        self.views[self.mode.get()].grid()
        # Publish accepted edits only; incomplete input stays in the editor.
        chapters = (list(self._original) if self.mode.get() == "Default"
                    else [row.chapter for row in self.views[self.mode.get()].rows])
        self.on_change(chapters)
