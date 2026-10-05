"""Chapter time editor with editable audio tags."""

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

from audio_tags import AudioTags, ORIGINAL_COVER, cover_path
from chapter_editor import ChapterEditor, ChapterRow
from chapters import Chapter
from tooltips import ToolTip


class AudioChapterEditor(ChapterEditor):
    headings = ("Track", "Artist", "Title", "Album", "Year", "Album Artist", "Cover", "Start", "End", "Lock")
    field_names = ("track", "artist", "title", "album", "year", "album_artist", "cover")
    time_columns = (8, 9)
    lock_column = 10

    def __init__(self, master, on_change):
        self.fields: list[dict[str, tk.StringVar]] = []
        self.selected: list[tk.BooleanVar] = []
        super().__init__(master, on_change)
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
        for column, heading in enumerate(self.headings, 1):
            header = ttk.Frame(self.body)
            header.grid(row=0, column=column, sticky="w", padx=8, pady=4)
            ttk.Label(header, text=heading).pack(side="left")
            if column <= len(self.field_names):
                field = self.field_names[column - 1]
                ttk.Button(header, text="…", width=2,
                           command=lambda f=field, h=heading: self._edit_selected(f, h)).pack(side="left", padx=(4, 0))

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
        self.fields.append(fields)
        for column, (name, width) in enumerate([
            ("track", 5), ("artist", 20), ("title", 30), ("album", 20),
            ("year", 6), ("album_artist", 20), ("cover", 28),
        ], 1):
            entry = ttk.Entry(self.body, textvariable=fields[name], width=width)
            entry.grid(row=number, column=column, sticky="ew", padx=8, pady=4)
            if name == "track":
                entry.bind("<FocusOut>", lambda event, i=number - 1: self._format_track(i))
                entry.bind("<Return>", lambda event, i=number - 1: self._format_track(i))

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
            result.append(AudioTags(title, fields["artist"].get().strip(), int(track),
                                    fields["album"].get().strip(), year,
                                    fields["album_artist"].get().strip(), cover))
        return result
