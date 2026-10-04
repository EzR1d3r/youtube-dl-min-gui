"""Scrollable chapter rows with linked boundaries and editable times."""

import math
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass, replace
from typing import Callable

from chapters import Chapter
from time_spinbox import TimeSpinbox, format_time, parse_time, seconds_to_milliseconds


@dataclass
class ChapterRow:
    chapter: Chapter
    start: tk.StringVar
    end: tk.StringVar
    locked: tk.BooleanVar


class ChapterEditor(ttk.Frame):
    headings = ("#", "Chapter", "Start", "End", "Lock")
    time_columns = (2, 3)
    lock_column = 4

    def __init__(self, master, on_change: Callable[[list[Chapter]], None]):
        super().__init__(master)
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
        horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=horizontal.set)
        horizontal.grid(row=1, column=0, sticky="ew")
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
        for column, heading in enumerate(self.headings):
            ttk.Label(self.body, text=heading).grid(row=0, column=column, sticky="w", padx=8, pady=4)
        maximum = max((chapter.end_time for chapter in chapters), default=1)
        maximum_ms = seconds_to_milliseconds(maximum)
        self._maximum = maximum_ms / 1000
        for number, chapter in enumerate(chapters, 1):
            start_ms = seconds_to_milliseconds(chapter.start_time)
            end_ms = seconds_to_milliseconds(chapter.end_time)
            chapter = replace(chapter, start_time=start_ms / 1000, end_time=end_ms / 1000)
            row = ChapterRow(
                chapter,
                tk.StringVar(master=self, value=format_time(start_ms)),
                tk.StringVar(master=self, value=format_time(end_ms)),
                tk.BooleanVar(master=self, value=True),
            )
            self.rows.append(row)
            self._add_identity_widgets(number, row)
            for column, field, variable in [(self.time_columns[0], "start", row.start),
                                             (self.time_columns[1], "end", row.end)]:
                spinbox = TimeSpinbox(
                    self.body, textvariable=variable, maximum_ms=maximum_ms
                )
                spinbox.grid(row=number, column=column, sticky="ew", padx=8, pady=4)
                index = number - 1
                variable.trace_add("write", lambda *args, i=index, f=field: self._time_changed(i, f))
                spinbox.bind("<FocusOut>", lambda event, i=index, f=field: self._finish_edit(i, f), add="+")
                spinbox.bind("<Return>", lambda event, i=index, f=field: self._finish_edit(i, f), add="+")
            lock = ttk.Checkbutton(self.body, variable=row.locked, command=lambda i=number - 1: self._lock_changed(i))
            lock.grid(row=number, column=self.lock_column, padx=8, pady=4)
            if number == len(chapters):
                lock.state(["disabled"])
        for widget in self.body.winfo_children():
            widget.bind("<MouseWheel>", self._scroll)
        self.canvas.yview_moveto(0)
        self.on_change([row.chapter for row in self.rows])

    def get_chapters(self) -> list[Chapter]:
        chapters = []
        for number, row in enumerate(self.rows, 1):
            try:
                start, end = parse_time(row.start.get()) / 1000, parse_time(row.end.get()) / 1000
            except ValueError as error:
                raise ValueError(f"Chapter {number}: enter HH:MM:SS:CC") from error
            self._validate_times(start, end, number)
            chapters.append(Chapter(self._chapter_title(number - 1, row), start, end))
        return chapters

    def _add_identity_widgets(self, number: int, row: ChapterRow) -> None:
        ttk.Label(self.body, text=str(number)).grid(row=number, column=0, sticky="w", padx=8, pady=4)
        ttk.Label(self.body, text=row.chapter.title).grid(row=number, column=1, sticky="w", padx=8, pady=4)

    def _chapter_title(self, index: int, row: ChapterRow) -> str:
        return row.chapter.title

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
                variable.set(format_time(seconds_to_milliseconds(value)))
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
                row.start.set(format_time(seconds_to_milliseconds(row.chapter.start_time)))
                row.end.set(format_time(seconds_to_milliseconds(row.chapter.end_time)))
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
        self.canvas.itemconfigure(self.body_window, width=max(event.width, self.body.winfo_reqwidth()))

    def _scroll(self, event) -> str:
        if event.delta:
            steps = -max(1, abs(event.delta) // 120) if event.delta > 0 else max(1, abs(event.delta) // 120)
            self.canvas.yview_scroll(steps, "units")
        return "break"
