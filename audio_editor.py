"""Chapter time editor with editable audio tags."""

import tkinter as tk
from dataclasses import replace
from tkinter import ttk
from tkinter import filedialog, messagebox

from audio_tags import AudioTags, ORIGINAL_COVER, EXTRA_TAGS, cover_path, validate_extra_tags
from chapter_editor import ChapterEditor, ChapterRow
from chapters import Chapter
from tooltips import ToolTip
from time_spinbox import format_time, parse_time


class AudioChapterEditor(ChapterEditor):
    headings = ("Track", "Artist", "Title", "Album", "Year", "Album Artist", "Cover", "Tag", "Start", "End", "Lock", "Segments")
    field_names = ("track", "artist", "title", "album", "year", "album_artist", "cover")
    time_columns = (9, 10)
    lock_column = 11
    tag_column = 8
    segments_column = 12

    def __init__(self, master, on_change):
        self.fields: list[dict[str, tk.StringVar]] = []
        self.selected: list[tk.BooleanVar] = []
        self.extra_tags: list[str] = []
        super().__init__(master, on_change)
        self.tag_menu = tk.Menu(self, tearoff=False)
        self.select_all = tk.BooleanVar(master=self, value=False)
        self.body.columnconfigure(1, weight=0)
        self.body.columnconfigure(2, weight=1)
        self.body.columnconfigure(3, weight=2)
        self.body.columnconfigure(4, weight=1)
        self.body.columnconfigure(6, weight=1)
        self.body.columnconfigure(7, weight=1)

    def set_chapters(self, chapters: list[Chapter]) -> None:
        self.fields.clear()
        self.selected.clear()
        self.select_all.set(False)
        super().set_chapters(chapters)

    def _add_headers(self) -> None:
        self.select_all_button = ttk.Checkbutton(
            self.body, text="All", variable=self.select_all, command=self._select_all,
        )
        self.select_all_button.grid(row=0, column=0, padx=8, pady=4)
        fields = (*self.field_names, *self.extra_tags)
        headings = (*self.headings[:7], *(f"{EXTRA_TAGS[key][0]} ({key})" for key in self.extra_tags), *self.headings[7:])
        for column, heading in enumerate(headings, 1):
            header = ttk.Frame(self.body)
            header.grid(row=0, column=column, sticky="w", padx=8, pady=4)
            ttk.Label(header, text=heading).pack(side="left")
            if column <= len(fields):
                field = fields[column - 1]
                ttk.Button(header, text="…", width=2,
                           command=lambda f=field, h=heading: self._edit_selected(f, h)).pack(side="left", padx=(4, 0))
            elif column == self.tag_column:
                button = ttk.Button(header, text="+", width=2)
                button.configure(command=lambda b=button: self._show_tag_menu(b))
                button.pack(side="left", padx=(4, 0))
                ToolTip(button, "Add an audio tag column")
            elif column == self.segments_column:
                button = ttk.Button(header, text="−", width=2, command=self._remove_selected)
                button.pack(side="left", padx=(4, 0))
                ToolTip(button, "Remove selected segments")

    def _show_tag_menu(self, button) -> None:
        menu = self.tag_menu
        menu.delete(0, "end")
        for key, (label, _) in EXTRA_TAGS.items():
            menu.add_command(label=f"{label} ({key})", command=lambda k=key: self._add_tag(k),
                             state="disabled" if key in self.extra_tags else "normal")
        try:
            menu.tk_popup(button.winfo_rootx(), button.winfo_rooty() + button.winfo_height())
        finally:
            menu.grab_release()

    def _add_tag(self, key: str) -> None:
        if key in self.extra_tags:
            return
        column = self.tag_column
        for widget in self.body.winfo_children():
            info = widget.grid_info()
            if int(info["row"]) == 0:
                widget.destroy()
            elif int(info["column"]) >= column:
                widget.grid_configure(column=int(info["column"]) + 1)
        self.extra_tags.append(key)
        self.tag_column += 1
        self.time_columns = tuple(value + 1 for value in self.time_columns)
        self.lock_column += 1
        self.segments_column += 1
        for number, fields in enumerate(self.fields, 1):
            fields[key] = tk.StringVar(master=self)
            entry = ttk.Entry(self.body, textvariable=fields[key], width=24)
            entry.grid(row=number, column=column, sticky="ew", padx=8, pady=4)
            entry.bind("<MouseWheel>", self._scroll)
        self.body.columnconfigure(column, weight=1)
        self._add_headers()
        self._selection_changed()

    def _select_all(self) -> None:
        for variable in self.selected:
            variable.set(self.select_all.get())
        self._selection_changed()

    def _selection_changed(self) -> None:
        count = sum(variable.get() for variable in self.selected)
        self.select_all.set(bool(self.selected) and count == len(self.selected))
        self.select_all_button.state(["alternate"] if 0 < count < len(self.selected) else ["!alternate"])

    def _add_identity_widgets(self, number: int, row: ChapterRow) -> None:
        selected = tk.BooleanVar(master=self, value=False)
        self.selected.append(selected)
        ttk.Checkbutton(self.body, variable=selected, command=self._selection_changed).grid(
            row=number, column=0, padx=8, pady=4,
        )
        fields = {
            "track": tk.StringVar(master=self, value=f"{number:02d}"),
            "artist": tk.StringVar(master=self),
            "title": tk.StringVar(master=self, value=row.chapter.title),
            "album": tk.StringVar(master=self),
            "year": tk.StringVar(master=self),
            "album_artist": tk.StringVar(master=self),
            "cover": tk.StringVar(master=self, value=ORIGINAL_COVER),
        }
        fields.update({key: tk.StringVar(master=self) for key in self.extra_tags})
        self.fields.append(fields)
        for column, (name, width) in enumerate([
            ("track", 5), ("artist", 20), ("title", 30), ("album", 20),
            ("year", 6), ("album_artist", 20), ("cover", 28),
            *((key, 24) for key in self.extra_tags),
        ], 1):
            entry = ttk.Entry(self.body, textvariable=fields[name], width=width)
            entry.grid(row=number, column=column, sticky="ew", padx=8, pady=4)
            if name == "track":
                entry.bind("<FocusOut>", lambda event, f=fields: self._format_track(self.fields.index(f)))
                entry.bind("<Return>", lambda event, f=fields: self._format_track(self.fields.index(f)))
        actions = ttk.Frame(self.body)
        actions.grid(row=number, column=self.segments_column, padx=8, pady=4)
        ttk.Button(actions, text="−", width=2, command=lambda r=row: self._remove_segment(r)).pack(side="left")
        ttk.Button(actions, text="+", width=2, command=lambda r=row: self._insert_segment(r)).pack(side="left", padx=(3, 0))

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
        self.fields.pop(index)
        self.selected.pop(index)
        self._segments_changed()

    def _insert_segment(self, row: ChapterRow | None) -> None:
        index = self.rows.index(row) + 1 if row is not None else 0
        try:
            start_ms = parse_time(row.end.get()) if row is not None else 0
            end_ms = parse_time(self.rows[index].start.get()) if index < len(self.rows) else start_ms
        except ValueError:
            messagebox.showerror("Add segment", "Enter valid times before adding a segment.", parent=self)
            return
        track = max((int(fields["track"].get()) for fields in self.fields
                     if fields["track"].get().isascii() and fields["track"].get().isdigit()), default=0) + 1
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
        fields = self.fields.pop()
        fields["track"].set(f"{track:02d}")
        self.fields.insert(index, fields)
        self.selected.insert(index, self.selected.pop())
        self._segments_changed()

    def _segments_changed(self) -> None:
        self._update_locks()
        self._selection_changed()
        for widget in self.body.winfo_children():
            widget.bind("<MouseWheel>", self._scroll)
        self.on_change([replace(row.chapter, title=self.fields[index]["title"].get().strip())
                        for index, row in enumerate(self.rows)])

    def _edit_selected(self, field: str, heading: str) -> None:
        indexes = [index for index, selected in enumerate(self.selected) if selected.get()]
        if not indexes:
            messagebox.showinfo("Edit segments", "Select at least one segment first.", parent=self)
            return
        first = indexes[0]
        dialog = tk.Toplevel(self)
        dialog.withdraw()
        dialog.title(f"Edit {heading}")
        dialog.transient(self.winfo_toplevel())
        dialog.resizable(False, False)
        ttk.Label(dialog, text=f"{heading} for {len(indexes)} selected segments:").grid(
            row=0, column=0, columnspan=3, sticky="w", padx=12, pady=10,
        )
        value = tk.StringVar(master=dialog, value=self.fields[first][field].get())
        input_row = ttk.Frame(dialog)
        input_row.grid(row=1, column=0, columnspan=3, sticky="ew", padx=12, pady=4)
        control = ttk.Entry(input_row, textvariable=value, width=55)
        control.selection_range(0, "end")
        control.pack(side="left", fill="x", expand=True)
        if field == "cover":
            def browse():
                path = filedialog.askopenfilename(
                    parent=dialog, title="Choose cover", filetypes=[
                        ("Images", "*.jpg *.jpeg *.png *.gif *.bmp"),
                        ("JPEG", "*.jpg *.jpeg"), ("PNG", "*.png"),
                        ("GIF", "*.gif"), ("BMP", "*.bmp"),
                    ],
                )
                if path:
                    value.set(path)
            for label, command, hint in [
                ("X", lambda: value.set(""), "Clear cover: no cover image"),
                ("O", lambda: value.set(ORIGINAL_COVER), "Use original video thumbnail"),
                ("…", browse, "Browse for a cover image"),
            ]:
                button = ttk.Button(input_row, text=label, width=2, command=command)
                button.pack(side="left", padx=(3, 0))
                ToolTip(button, hint)

        def apply():
            try:
                self._apply_selected(field, indexes, value.get())
            except ValueError as error:
                messagebox.showerror(f"Edit {heading}", str(error), parent=dialog)
                return
            dialog.destroy()

        buttons = ttk.Frame(dialog)
        buttons.grid(row=2, column=0, columnspan=3, sticky="e", padx=12, pady=12)
        ttk.Button(buttons, text="Apply", command=apply).pack(side="left", padx=4)
        ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(side="left")
        dialog.bind("<Return>", lambda event: apply())
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        dialog.update_idletasks()
        parent = self.winfo_toplevel()
        x = parent.winfo_rootx() + (parent.winfo_width() - dialog.winfo_reqwidth()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - dialog.winfo_reqheight()) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.deiconify()
        dialog.grab_set()
        control.focus_set()

    def _apply_selected(self, field: str, indexes: list[int], value: str) -> None:
        value = value.strip()
        if field == "track":
            if not (value.isascii() and value.isdigit() and 1 <= int(value) <= 65535):
                raise ValueError("Track must be an integer from 1 to 65535.")
            value = f"{int(value):02d}"
        elif field == "title" and not value:
            raise ValueError("Enter a Title.")
        elif field == "year" and value and not (len(value) == 4 and value.isascii() and value.isdigit() and int(value) > 0):
            raise ValueError("Year must be four digits or empty.")
        elif field == "cover" and value and value != ORIGINAL_COVER:
            value = str(cover_path(value))
        elif field in EXTRA_TAGS:
            validate_extra_tags({field: value})
        for index in indexes:
            self.fields[index][field].set(value)

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
            year = fields["year"].get().strip()
            cover = fields["cover"].get().strip()
            if not title:
                raise ValueError(f"Chapter {number}: enter a Title.")
            if not (track.isascii() and track.isdigit() and 1 <= int(track) <= 65535):
                raise ValueError(f"Chapter {number}: Track must be an integer from 1 to 65535.")
            if year and not (len(year) == 4 and year.isascii() and year.isdigit() and int(year) > 0):
                raise ValueError(f"Chapter {number}: Year must be four digits or empty.")
            if cover and cover != ORIGINAL_COVER:
                try:
                    cover = str(cover_path(cover))
                except ValueError as error:
                    raise ValueError(f"Chapter {number}: {error}") from error
            self._format_track(number - 1)
            extra = {key: fields[key].get().strip() for key in self.extra_tags}
            try:
                validate_extra_tags(extra)
            except ValueError as error:
                raise ValueError(f"Chapter {number}: {error}") from error
            result.append(AudioTags(title, fields["artist"].get().strip(), int(track),
                                    fields["album"].get().strip(), year,
                                    fields["album_artist"].get().strip(), cover, extra=extra))
        return result
