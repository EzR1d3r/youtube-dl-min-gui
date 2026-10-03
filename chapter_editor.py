"""Scrollable chapter rows with linked boundaries and editable times."""

import math
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass, replace
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
        self._updating = False
        self._maximum = 0.0
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
        self._maximum = maximum
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
            for column, field, variable in [(2, "start", row.start), (3, "end", row.end)]:
                spinbox = ttk.Spinbox(
                    self.body, textvariable=variable, from_=0, to=maximum, increment=1, width=12
                )
                spinbox.grid(row=number, column=column, sticky="ew", padx=8, pady=4)
                index = number - 1
                variable.trace_add("write", lambda *args, i=index, f=field: self._time_changed(i, f))
                spinbox.bind("<FocusOut>", lambda event, i=index, f=field: self._finish_edit(i, f))
                spinbox.bind("<Return>", lambda event, i=index, f=field: self._finish_edit(i, f))
            lock = ttk.Checkbutton(self.body, variable=row.locked, command=lambda i=number - 1: self._lock_changed(i))
            lock.grid(row=number, column=4, padx=8, pady=4)
            if number == len(chapters):
                lock.state(["disabled"])
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
            self._validate_times(start, end, number)
            chapters.append(Chapter(row.chapter.title, start, end))
        return chapters

    def _validate_times(self, start: float, end: float, number: int) -> None:
        if not math.isfinite(start) or not math.isfinite(end) or not 0 <= start < end <= self._maximum:
            raise ValueError(f"Chapter {number}: expected 0 <= start < end <= {self._maximum}")

    def _time_changed(self, index: int, field: str) -> None:
        if self._updating:
            return
        # Allow incomplete input while typing, but never publish invalid times.
        try:
            chapters = self.get_chapters()
            neighbor = None
            if field == "end" and index + 1 < len(self.rows) and self.rows[index].locked.get():
                neighbor = index + 1
                chapters[neighbor] = replace(chapters[neighbor], start_time=chapters[index].end_time)
            elif field == "start" and index > 0 and self.rows[index - 1].locked.get():
                neighbor = index - 1
                chapters[neighbor] = replace(chapters[neighbor], end_time=chapters[index].start_time)
            if neighbor is not None:
                chapter = chapters[neighbor]
                self._validate_times(chapter.start_time, chapter.end_time, neighbor + 1)
        except ValueError:
            return
        self._updating = True
        try:
            if neighbor is not None:
                variable = self.rows[neighbor].start if field == "end" else self.rows[neighbor].end
                value = chapters[neighbor].start_time if field == "end" else chapters[neighbor].end_time
                variable.set(str(value))
            for row, chapter in zip(self.rows, chapters):
                row.chapter = chapter
        finally:
            self._updating = False
        self.on_change(chapters)

    def _finish_edit(self, index: int, field: str) -> None:
        self._time_changed(index, field)
        # Restore the last accepted times when an edit would invalidate a chapter.
        self._updating = True
        try:
            for row in self.rows:
                row.start.set(str(row.chapter.start_time))
                row.end.set(str(row.chapter.end_time))
        finally:
            self._updating = False

    def _lock_changed(self, index: int) -> None:
        if not self.rows[index].locked.get() or index + 1 >= len(self.rows):
            return
        # On relocking, use this chapter's end as the shared boundary.
        self._time_changed(index, "end")
        if self.rows[index].chapter.end_time != self.rows[index + 1].chapter.start_time:
            self.rows[index].locked.set(False)

    def _resize_content(self, event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"), height=min(self.body.winfo_reqheight(), 220))

    def _resize_width(self, event) -> None:
        self.canvas.itemconfigure(self.body_window, width=event.width)

    def _scroll(self, event) -> str:
        if event.delta:
            steps = -max(1, abs(event.delta) // 120) if event.delta > 0 else max(1, abs(event.delta) // 120)
            self.canvas.yview_scroll(steps, "units")
        return "break"
