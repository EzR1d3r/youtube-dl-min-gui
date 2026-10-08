"""Scrollable chapter rows with linked boundaries and editable times."""

import math
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from dataclasses import dataclass, field, replace
from typing import Callable

from chapters import Chapter
from time_spinbox import TimeSpinbox, format_time, parse_time, seconds_to_milliseconds
from tooltips import ToolTip


@dataclass
class ChapterRow:
    chapter: Chapter
    start: tk.StringVar
    end: tk.StringVar
    locked: tk.BooleanVar
    title: tk.StringVar | None = None
    lock_control: ttk.Checkbutton | None = field(default=None, compare=False, repr=False)


class ChapterEditor(ttk.Frame):
    headings = ("All", "Chapter", "Start", "End", "Lock", "Segments")
    time_columns = (2, 3)
    lock_column = 4
    segments_column = 5

    def __init__(self, master, on_change: Callable[[list[Chapter]], None]):
        super().__init__(master)
        self.on_change = on_change
        self.rows: list[ChapterRow] = []
        self.selected: list[tk.BooleanVar] = []
        self.select_all = tk.BooleanVar(master=self, value=False)
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
        self.selected.clear()
        self.select_all.set(False)
        self._add_headers()
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
            self._add_row_widgets(number, row)
        self._update_locks()
        for widget in self.body.winfo_children():
            widget.bind("<MouseWheel>", self._scroll)
        self.canvas.yview_moveto(0)
        self.on_change([row.chapter for row in self.rows])

    def _add_row_widgets(self, number: int, row: ChapterRow) -> None:
        self._add_identity_widgets(number, row)
        for column, field, variable in [(self.time_columns[0], "start", row.start),
                                         (self.time_columns[1], "end", row.end)]:
            spinbox = TimeSpinbox(
                self.body, textvariable=variable,
                maximum_ms=seconds_to_milliseconds(self._maximum),
            )
            spinbox.grid(row=number, column=column, sticky="ew", padx=8, pady=4)
            variable.trace_add("write", lambda *args, r=row, f=field: self._time_changed(self.rows.index(r), f))
            spinbox.bind("<FocusOut>", lambda event, r=row, f=field: self._finish_edit(self.rows.index(r), f), add="+")
            spinbox.bind("<Return>", lambda event, r=row, f=field: self._finish_edit(self.rows.index(r), f), add="+")
        lock = ttk.Checkbutton(self.body, variable=row.locked,
                               command=lambda r=row: self._lock_changed(self.rows.index(r)))
        lock.grid(row=number, column=self.lock_column, padx=8, pady=4)
        row.lock_control = lock
        lock.configure(state="disabled" if row is self.rows[-1] else "normal")
        actions = ttk.Frame(self.body)
        actions.grid(row=number, column=self.segments_column, padx=8, pady=4)
        ttk.Button(actions, text="−", width=2, command=lambda r=row: self._remove_segment(r)).pack(side="left")
        ttk.Button(actions, text="+", width=2, command=lambda r=row: self._insert_segment(r)).pack(side="left", padx=(3, 0))

    def _update_locks(self) -> None:
        for index, row in enumerate(self.rows):
            last = index == len(self.rows) - 1
            if last:
                row.locked.set(True)
            if row.lock_control is not None:
                row.lock_control.configure(state="disabled" if last else "normal")

    def get_chapters(self) -> list[Chapter]:
        chapters = []
        for number, row in enumerate(self.rows, 1):
            try:
                start, end = parse_time(row.start.get()) / 1000, parse_time(row.end.get()) / 1000
            except ValueError as error:
                raise ValueError(f"Chapter {number}: enter HH:MM:SS:CC") from error
            self._validate_times(start, end, number)
            title = self._chapter_title(number - 1, row)
            if not title:
                raise ValueError(f"Chapter {number}: enter a Title.")
            chapters.append(Chapter(title, start, end))
        return chapters

    def _add_identity_widgets(self, number: int, row: ChapterRow) -> None:
        self._add_selection_widget(number)
        row.title = tk.StringVar(master=self, value=row.chapter.title)
        ttk.Entry(self.body, textvariable=row.title, width=40).grid(row=number, column=1, sticky="ew", padx=8, pady=4)
        row.title.trace_add("write", lambda *args, r=row: self._title_changed(r))

    def _add_headers(self) -> None:
        self._add_selection_header()
        for column, heading in enumerate(self.headings):
            if column == 0:
                continue
            header = ttk.Frame(self.body)
            header.grid(row=0, column=column, sticky="w", padx=8, pady=4)
            ttk.Label(header, text=heading).pack(side="left")
            if column == self.segments_column:
                self._add_segment_header_button(header)

    def _chapter_title(self, index: int, row: ChapterRow) -> str:
        return row.title.get().strip() if row.title is not None else row.chapter.title

    def _title_changed(self, row: ChapterRow) -> None:
        row.chapter = replace(row.chapter, title=row.title.get().strip())
        self.on_change([item.chapter for item in self.rows])

    def _add_selection_header(self) -> None:
        self.select_all_button = ttk.Checkbutton(
            self.body, text="All", variable=self.select_all, command=self._select_all,
        )
        self.select_all_button.grid(row=0, column=0, padx=8, pady=4)

    def _add_selection_widget(self, number: int) -> None:
        selected = tk.BooleanVar(master=self, value=False)
        self.selected.append(selected)
        ttk.Checkbutton(self.body, variable=selected, command=self._selection_changed).grid(
            row=number, column=0, padx=8, pady=4,
        )

    def _add_segment_header_button(self, header) -> None:
        button = ttk.Button(header, text="−", width=2, command=self._remove_selected)
        button.pack(side="left", padx=(4, 0))
        ToolTip(button, "Remove selected segments")

    def _select_all(self) -> None:
        for variable in self.selected:
            variable.set(self.select_all.get())
        self._selection_changed()

    def _selection_changed(self) -> None:
        count = sum(variable.get() for variable in self.selected)
        self.select_all.set(bool(self.selected) and count == len(self.selected))
        self.select_all_button.state(["alternate"] if 0 < count < len(self.selected) else ["!alternate"])

    def _remove_selected(self) -> None:
        rows = [row for row, selected in zip(self.rows, self.selected) if selected.get()]
        for row in reversed(rows):
            self._remove_segment(row)

    def _remove_segment(self, row: ChapterRow) -> None:
        index = self.rows.index(row)
        for widget in self.body.winfo_children():
            number = int(widget.grid_info()["row"])
            if number == index + 1:
                widget.destroy()
            elif number > index + 1:
                widget.grid_configure(row=number - 1)
        self.rows.pop(index)
        self.selected.pop(index)
        self._row_removed(index)
        self._segments_changed()

    def _insert_segment(self, row: ChapterRow | None) -> None:
        index = self.rows.index(row) + 1 if row is not None else 0
        try:
            start_ms = parse_time(row.end.get()) if row is not None else 0
            end_ms = parse_time(self.rows[index].start.get()) if index < len(self.rows) else start_ms
        except ValueError:
            messagebox.showerror("Add segment", "Enter valid times before adding a segment.", parent=self)
            return
        chapter = Chapter("New segment", start_ms / 1000, end_ms / 1000)
        new_row = ChapterRow(
            chapter, tk.StringVar(master=self, value=format_time(start_ms)),
            tk.StringVar(master=self, value=format_time(end_ms)),
            tk.BooleanVar(master=self, value=False),
        )
        for widget in self.body.winfo_children():
            number = int(widget.grid_info()["row"])
            if number >= index + 1:
                widget.grid_configure(row=number + 1)
        self.rows.insert(index, new_row)
        self._add_row_widgets(index + 1, new_row)
        self.selected.insert(index, self.selected.pop())
        self._row_inserted(index)
        self._segments_changed()

    def _row_removed(self, index: int) -> None:
        pass

    def _row_inserted(self, index: int) -> None:
        pass

    def _segments_changed(self) -> None:
        self._update_locks()
        self._selection_changed()
        for widget in self.body.winfo_children():
            widget.bind("<MouseWheel>", self._scroll)
        for index, row in enumerate(self.rows):
            row.chapter = replace(row.chapter, title=self._chapter_title(index, row))
        self.on_change([row.chapter for row in self.rows])

    def _validate_times(self, start: float, end: float, number: int) -> None:
        if not math.isfinite(start) or not math.isfinite(end) or not 0 <= start < end <= self._maximum:
            raise ValueError(f"Chapter {number}: expected 0 <= start < end <= {self._maximum}")

    def _time_changed(self, index: int, field: str) -> None:
        if self._updating:
            return
        # Allow incomplete input while typing, but never publish invalid times.
        try:
            chapters = [row.chapter for row in self.rows]
            row = self.rows[index]
            start, end = parse_time(row.start.get()) / 1000, parse_time(row.end.get()) / 1000
            self._validate_times(start, end, index + 1)
            chapters[index] = Chapter(self._chapter_title(index, row), start, end)
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
