from threading import Thread
import subprocess
import os

from tkinter import Tk, Label, Button, Entry, StringVar, BooleanVar, Checkbutton, Text, Frame, Scrollbar
from tkinter import LEFT, END, Y, END, FIRST
from tkinter.ttk import Combobox
from tkinter import messagebox, TclError

import utils as ut
from settings import load_settings, save_settings
from link_info import read_link_info
from chapters import Chapter
from chapter_panel import ChapterPanel

app_version = "1.0.1"

title_scheme = "%(title)s.%(ext)s"
rel_dl_dir = os.path.join("~", "Downloads", "youtube-downloads")
dl_dir = os.path.expanduser(rel_dl_dir)
blocks_color = "light grey"


class MainWindow:
    def __init__(self):
        self.settings = load_settings()
        save_settings(self.settings)

        # tk gui root
        self.root = Tk()
        self.root.title("MinGui Youtube-dl")
        self.root.minsize(720, 360)
        if self.settings.window_size:
            self.root.geometry(self.settings.window_size)

        self.chapters: list[Chapter] = []
        self._info_link = ""

        # link block
        self.lbLink = Label(self.root, text="Download link: ", justify=LEFT)
        self.lbLink.grid(row=0, column=0, sticky="W", pady=10, padx=10)

        self.link_var = StringVar(master=self.root)
        self.entDwnLink = Entry(self.root, bg="light green", textvariable=self.link_var)
        self.entDwnLink.grid(row=0, column=1, sticky="WE", pady=10, padx=10)
        # self.entDwnLink.insert(0, "https://www.youtube.com/watch?v=rl9FFZZnWWo")

        # Download block
        # fmt: off
        self.fmDLBlock = Frame(bg=blocks_color)
        self.fmDLBlock.grid(row=1, column=0, sticky="WNES", columnspan=2, pady=10, padx=10)

        self.lbDownloadFolder  = Label(self.fmDLBlock, text="Save folder: ", bg=blocks_color, justify=LEFT)
        self.entDownloadFolder = Combobox(self.fmDLBlock, values=self.settings.download_dir)
        self.fmFolderButtons = Frame(self.fmDLBlock, bg=blocks_color)
        self.btnSaveDownloadFolder = Button(self.fmFolderButtons, text="+", width=2, command=self.save_download_folder)
        self.btnDeleteDownloadFolder = Button(self.fmFolderButtons, text="-", width=2, command=self.delete_download_folder)
        self.lbOptions         = Label(self.fmDLBlock, text="Options: ", bg=blocks_color, justify=LEFT)
        self.fmOptions         = Frame(self.fmDLBlock, bg=blocks_color)
        self.entOptions        = Combobox(self.fmOptions, values=self.settings.options)
        self.btnSaveOptions    = Button(self.fmOptions, text="+", width=2, command=self.save_options)
        self.btnDeleteOptions  = Button(self.fmOptions, text="-", width=2, command=self.delete_options)
        self.btnExec           = Button(self.fmDLBlock, text="Exec", width=5)
        self.lbTitleSheme      = Label(self.fmDLBlock, text="Title sheme: ", bg=blocks_color, justify=LEFT)
        self.entTitleSheme     = Entry(self.fmDLBlock)
        self.btnDownload       = Button(self.fmDLBlock, text="Download", bg="light green", width=20)

        self.lbDownloadFolder .grid(row=0, column=0, sticky="W",  pady=10, padx=10)
        self.entDownloadFolder.grid(row=0, column=1, sticky="WE", pady=10, padx=(10, 2), columnspan=4)
        self.fmFolderButtons.grid(row=0, column=5, sticky="E", pady=10, padx=(2, 10))
        self.btnSaveDownloadFolder.grid(row=0, column=0)
        self.btnDeleteDownloadFolder.grid(row=0, column=1, padx=(2, 0))
        
        self.lbOptions        .grid(row=1, column=0, sticky="W",  pady=10, padx=10)
        self.fmOptions        .grid(row=1, column=1, sticky="WE", pady=10, padx=10)
        self.entOptions       .grid(row=0, column=0, sticky="WE")
        self.btnSaveOptions   .grid(row=0, column=1, padx=(2, 0))
        self.btnDeleteOptions .grid(row=0, column=2, padx=(2, 0))
        self.fmOptions.columnconfigure(0, weight=1)
        self.btnExec          .grid(row=1, column=2, sticky="W",  pady=10, padx=2)
        self.lbTitleSheme     .grid(row=1, column=3, sticky="W",  pady=10, padx=10)
        self.entTitleSheme    .grid(row=1, column=4, sticky="WE", pady=10, padx=10, columnspan=2)
        
        self.btnDownload      .grid(row=2, column=4, sticky="E",  pady=10, padx=10, columnspan=2)

        self.fmDLBlock.columnconfigure(0, weight=0, minsize=50)
        self.fmDLBlock.columnconfigure(1, weight=20, minsize=100)
        self.fmDLBlock.columnconfigure(2, weight=0, minsize=30)
        self.fmDLBlock.columnconfigure(3, weight=0, minsize=50) #
        self.fmDLBlock.columnconfigure(4, weight=10, minsize=50) #
        self.fmDLBlock.columnconfigure(5, weight=0, minsize=30)

        self.entDownloadFolder.set(self.settings.download_dir[0] if self.settings.download_dir else "")
        self.entOptions.set(self.settings.options[0] if self.settings.options else "")
        self.entTitleSheme.insert(0, title_scheme)

        #Link Info block
        self.fmInfoBlock = Frame(bg=blocks_color)
        self.fmInfoBlock.grid(row=1,column=2, sticky="WNES", pady=10, padx=10)
        
        self.lbColors  = Label(self.fmInfoBlock, text="Colors: ", bg=blocks_color, justify=LEFT)
        self.entColors = Entry(self.fmInfoBlock)
        self.btnInfo   = Button(self.fmInfoBlock, text="Link Info", width=20)
        self.show_chapters = BooleanVar(master=self.root, value=False)
        self.chkShowChapters = Checkbutton(
            self.fmInfoBlock, text="Split media", variable=self.show_chapters,
            command=self._toggle_chapters, bg=blocks_color,
        )
        self.btnClearConsole = Button(self.fmInfoBlock, text="Clear output", width=20)

        self.lbColors  .grid(row=0, column=0, sticky="W",  pady=10, padx=10)
        self.entColors .grid(row=0, column=1, sticky="WE", pady=10, padx=10)
        self.btnInfo   .grid(row=1, column=1, pady=10, padx=10, sticky="E")
        self.chkShowChapters.grid(row=1, column=0, pady=10, padx=10, sticky="W")
        self.btnClearConsole   .grid(row=2, column=1, pady=10, padx=10, sticky="E")

        self.fmInfoBlock.columnconfigure(0, weight=0, minsize=50)
        self.fmInfoBlock.columnconfigure(1, weight=20, minsize=150)

        self.entColors.insert(0, self.settings.colors)

        self.chapter_editor = ChapterPanel(self.root, on_change=self._chapters_edited)
        self.chapter_editor.grid(row=2, column=0, columnspan=3, sticky="WE", padx=10, pady=(0, 10))
        self.chapter_editor.grid_remove()

        #Console
        self.fmConsole = Frame(bg=blocks_color)
        self.fmConsole.grid(row=102, column=0, columnspan=3, sticky="WNES", pady=10, padx=10)
        
        self.txtConsole = Text(
            self.fmConsole,
            bg=self.settings.console_bg,
            fg=self.settings.console_fg,
            font=(self.settings.font_name, self.settings.font_size)
        )
        scroll = Scrollbar(self.fmConsole, command=self.txtConsole.yview, activebackground="red")
        
        self.txtConsole .grid(row=102, column=0, sticky="WNES")
        scroll          .grid(row=102, column=1, sticky="WNES")
        self.txtConsole.config(yscrollcommand=scroll.set)

        self.fmConsole.columnconfigure(0, weight=20)
        self.fmConsole.rowconfigure(102, weight=20)

        #Root
        self.root.columnconfigure(0, weight=0, minsize=100)
        self.root.columnconfigure(1, weight=20, minsize=350)
        self.root.columnconfigure(2, weight=10, minsize=250)
        self.root.rowconfigure(102, weight=100)

        # fmt: on

        self.bind_gui()
        self.show_app_info()
        self.append_console_line(ut.load_instructions(self.settings.language))
        self.append_console_line("\n\n" + ut.load_changelog(self.settings.language))

    def show_app_info(self):
        self.append_console_line(f"MinGui Youtube-dl v{app_version} (c) Voronezh Statics\n")

        proc = ut.exec_youtube_dl(self.settings.youtube_dl_path, "--version")
        version, _ = proc.communicate()
        self.append_console_line(f"Youtube-dl version: {version.decode()}\n")

    def bind_gui(self):
        self.link_var.trace_add("write", self._clear_link_info)
        self.entOptions.bind("<<ComboboxSelected>>", lambda event: self.save_options())
        self.entOptions.bind("<Return>", lambda event: self.save_options())
        self.entDownloadFolder.bind("<<ComboboxSelected>>", lambda event: self.save_download_folder())
        self.entDownloadFolder.bind("<Return>", lambda event: self.save_download_folder())
        self.entDwnLink.bind("<Button-3>", self.paste_download_link)
        self.btnDownload.bind("<ButtonRelease>", lambda x: self.download(self.entDwnLink.get(), self.entOptions.get()))
        self.btnInfo.bind("<ButtonRelease>", lambda x: self.get_info(self.entDwnLink.get()))
        self.btnExec.bind("<ButtonRelease>", lambda x: self.exec_options(self.entOptions.get()))
        self.btnClearConsole.bind("<ButtonRelease>", lambda x: self.txtConsole.delete(ut.START, END))

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def paste_download_link(self, event):
        try:
            text = self.entDwnLink.clipboard_get()
        except TclError:
            return "break"
        self.entDwnLink.delete(0, END)
        self.entDwnLink.insert(0, text)
        return "break"

    def mainloop(self):
        self.root.mainloop()

    def save_download_folder(self):
        folder = self.entDownloadFolder.get().strip()
        if not folder:
            return
        # Keep the selected folder first so it is restored on the next launch.
        self.settings.download_dir = [folder] + [
            saved for saved in self.settings.download_dir
            if os.path.normcase(os.path.normpath(saved)) != os.path.normcase(os.path.normpath(folder))
        ]
        self.entDownloadFolder.configure(values=self.settings.download_dir)
        self.entDownloadFolder.set(folder)
        save_settings(self.settings)

    def save_options(self, options_str=None):
        options = (self.entOptions.get() if options_str is None else options_str).strip()
        self.settings.options = [options] + [
            saved for saved in self.settings.options if saved != options
        ]
        self.entOptions.configure(values=self.settings.options)
        self.entOptions.set(options)
        save_settings(self.settings)

    def delete_download_folder(self):
        self._delete_preset("download_dir", self.entDownloadFolder)

    def delete_options(self):
        self._delete_preset("options", self.entOptions)

    def _delete_preset(self, setting_name, combobox):
        selected = combobox.get().strip()
        presets = getattr(self.settings, setting_name)
        if selected not in presets:
            return
        remaining = [preset for preset in presets if preset != selected]
        setattr(self.settings, setting_name, remaining)
        combobox.configure(values=remaining)
        combobox.set(remaining[0] if remaining else "")
        save_settings(self.settings)

    def download(self, link, options_str):
        if not self.entDownloadFolder.get().strip():
            messagebox.showerror("Download", "Choose a save folder first.", parent=self.root)
            return
        self.save_download_folder()
        self.save_options(options_str)
        dl_path = os.path.join(self.entDownloadFolder.get(), self.entTitleSheme.get())
        options = options_str.split(" ") if options_str else []
        options += ["-o", dl_path]
        options += ["--ffmpeg-location", self.settings.ffmpeg_path]
        proc = ut.exec_youtube_dl(
            self.settings.youtube_dl_path, link, *options,
            js_runtime_path=self.settings.js_runtime_path,
        )
        self.__redirect_out(proc)

    def exec_options(self, options_str):
        self.save_options(options_str)
        options = options_str.split(" ") if options_str else []
        proc = ut.exec_youtube_dl(
            self.settings.youtube_dl_path, *options,
            js_runtime_path=self.settings.js_runtime_path,
        )
        self.__redirect_out(proc)

    def get_info(self, link):
        link = link.strip()
        self._clear_link_info()
        proc = ut.exec_get_info(
            self.settings.youtube_dl_path, link, self.settings.js_runtime_path,
        )
        Thread(
            target=read_link_info,
            args=(proc, self.append_console_line),
            kwargs={"on_chapters": lambda chapters: self._receive_chapters(link, chapters)},
        ).start()

    def _clear_link_info(self, *args):
        self._info_link = self.link_var.get().strip()
        self.chapters = []
        self.chapter_editor.set_chapters([])
        self.chapter_editor.grid_remove()

    def _receive_chapters(self, link: str, chapters: list[Chapter]) -> None:
        # Create and update widgets in Tk's main thread, without a polling queue.
        try:
            self.root.after(0, self._set_chapters, link, chapters)
        except (TclError, RuntimeError):
            return

    def _set_chapters(self, link: str, chapters: list[Chapter]) -> None:
        if link != self._info_link:
            return
        self.chapters = chapters
        self.chapter_editor.set_chapters(chapters)
        self._toggle_chapters()

    def _toggle_chapters(self) -> None:
        if self.show_chapters.get() and self.chapters:
            self.chapter_editor.grid()
        else:
            self.chapter_editor.grid_remove()

    def _chapters_edited(self, chapters: list[Chapter]) -> None:
        self.chapters = chapters

    def __redirect_out(self, proc: subprocess.Popen):
        # read youtube-dl output and redirect to the console
        t_out = Thread(
            target=ut.read_output,
            args=(proc.stdout,),
            kwargs={"out_append": self.append_console_line, "out_replace": self.replace_last_console_line},
        )
        t_out.start()

        t_errs = Thread(
            target=ut.read_output,
            args=(proc.stderr,),
            kwargs={"out_append": self.append_console_line, "out_replace": self.replace_last_console_line},
        )
        t_errs.start()

    def on_closing(self):
        self.settings.window_size = f"{self.root.winfo_width()}x{self.root.winfo_height()}"
        save_settings(self.settings)
        self.root.destroy()

    # work with console text
    def append_console_line(self, text_line: str):
        ut._append_text_item_text_line(self.txtConsole, text_line)
        contains = ut.parse_colors(self.entColors.get())
        ut._post_format(self.txtConsole, text_line, contains=contains)

    def clear_and_fill_console(self, text):
        ut._set_text_item_text(self.txtConsole, text)

    def replace_last_console_line(self, text_line):
        ut._replace_text_item_last_line(self.txtConsole, text_line)
