"""Scrollable chapter rows; boundary locking is implemented separately."""

import math
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from typing import Callable

from chapters import Chapter


@dataclass
class ChapterRow:
    chapter: Chapter
    start: tk.StringVar
    end: tk.StringVar
    locked: tk.BooleanVar


class ChapterEditor(ttk.LabelFrame):
    def __init__(self, master, on_change: Callable[[list[Chapter]], None]):
        super().__init__(master, text="Chapters")
        self.on_change = on_change
        self.rows: list[ChapterRow] = []
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, height=1, highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.body = ttk.Frame(self.canvas)
        self.body.columnconfigure(1, weight=1)
        self.body_window = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.body.bind("<Configure>", self._resize_content)
        self.canvas.bind("<Configure>", self._resize_width)
        self.canvas.bind("<MouseWheel>", self._scroll)
        self.body.bind("<MouseWheel>", self._scroll)

    def set_chapters(self, chapters: list[Chapter]) -> None:
        for widget in self.body.winfo_children():
            widget.destroy()
        self.rows.clear()
        for column, heading in enumerate(["#", "Chapter", "Start (s)", "End (s)", "Lock"]):
            ttk.Label(self.body, text=heading).grid(row=0, column=column, sticky="w", padx=8, pady=4)
        maximum = max((chapter.end_time for chapter in chapters), default=1)
        for number, chapter in enumerate(chapters, 1):
            row = ChapterRow(
                chapter,
                tk.StringVar(master=self, value=str(chapter.start_time)),
                tk.StringVar(master=self, value=str(chapter.end_time)),
                tk.BooleanVar(master=self, value=True),
            )
            self.rows.append(row)
            ttk.Label(self.body, text=str(number)).grid(row=number, column=0, sticky="w", padx=8, pady=4)
            ttk.Label(self.body, text=chapter.title).grid(row=number, column=1, sticky="w", padx=8, pady=4)
            for column, variable in [(2, row.start), (3, row.end)]:
                ttk.Spinbox(
                    self.body, textvariable=variable, from_=0, to=maximum, increment=1, width=12
                ).grid(row=number, column=column, sticky="ew", padx=8, pady=4)
                variable.trace_add("write", self._time_changed)
            ttk.Checkbutton(self.body, variable=row.locked).grid(row=number, column=4, padx=8, pady=4)
        for widget in self.body.winfo_children():
            widget.bind("<MouseWheel>", self._scroll)
        self.canvas.yview_moveto(0)

    def get_chapters(self) -> list[Chapter]:
        chapters = []
        for number, row in enumerate(self.rows, 1):
            try:
                start, end = float(row.start.get()), float(row.end.get())
            except ValueError as error:
                raise ValueError(f"Chapter {number}: enter times in seconds") from error
            if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start:
                raise ValueError(f"Chapter {number}: start must be nonnegative and end must follow start")
            chapters.append(Chapter(row.chapter.title, start, end))
        return chapters

    def _time_changed(self, *args) -> None:
        # Incomplete text is allowed while typing; publish only valid intervals.
        try:
            chapters = self.get_chapters()
        except ValueError:
            return
        self.on_change(chapters)

    def _resize_content(self, event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"), height=min(self.body.winfo_reqheight(), 220))

    def _resize_width(self, event) -> None:
        self.canvas.itemconfigure(self.body_window, width=event.width)

    def _scroll(self, event) -> str:
        if event.delta:
            steps = -max(1, abs(event.delta) // 120) if event.delta > 0 else max(1, abs(event.delta) // 120)
            self.canvas.yview_scroll(steps, "units")
        return "break"
