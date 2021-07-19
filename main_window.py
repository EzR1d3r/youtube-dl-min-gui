from threading import Thread
import subprocess
import os

from tkinter import Tk, Label, Button, Entry, StringVar, Text, Frame, Scrollbar
from tkinter import LEFT, END, Y, END, FIRST
from tkinter import messagebox

import utils as ut
from settings import load_settings, save_settings

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

        # link block
        self.lbLink = Label(self.root, text="Download link: ", justify=LEFT)
        self.lbLink.grid(row=0, column=0, sticky="W", pady=10, padx=10)

        self.entDwnLink = Entry(self.root, bg="light green")
        self.entDwnLink.grid(row=0, column=1, sticky="WE", pady=10, padx=10)
        # self.entDwnLink.insert(0, "https://www.youtube.com/watch?v=rl9FFZZnWWo")

        # Download block
        # fmt: off
        self.fmDLBlock = Frame(bg=blocks_color)
        self.fmDLBlock.grid(row=1, column=0, sticky="WNES", columnspan=2, pady=10, padx=10)

        self.lbDownloadFolder  = Label(self.fmDLBlock, text="Save folder: ", bg=blocks_color, justify=LEFT)
        self.entDownloadFolder = Entry(self.fmDLBlock)
        self.lbOptions         = Label(self.fmDLBlock, text="Options: ", bg=blocks_color, justify=LEFT)
        self.entOptions        = Entry(self.fmDLBlock)
        self.btnExec           = Button(self.fmDLBlock, text="Exec", width=5)
        self.lbTitleSheme      = Label(self.fmDLBlock, text="Title sheme: ", bg=blocks_color, justify=LEFT)
        self.entTitleSheme     = Entry(self.fmDLBlock)
        self.btnDownload       = Button(self.fmDLBlock, text="Download", bg="light green", width=20)

        self.lbDownloadFolder .grid(row=0, column=0, sticky="W",  pady=10, padx=10)
        self.entDownloadFolder.grid(row=0, column=1, sticky="WE", pady=10, padx=10, columnspan=5)
        
        self.lbOptions        .grid(row=1, column=0, sticky="W",  pady=10, padx=10)
        self.entOptions       .grid(row=1, column=1, sticky="WE", pady=10, padx=10)
        self.btnExec          .grid(row=1, column=2, sticky="W",  pady=10, padx=2)
        self.lbTitleSheme     .grid(row=1, column=3, sticky="W",  pady=10, padx=10)
        self.entTitleSheme    .grid(row=1, column=4, sticky="WE", pady=10, padx=10, columnspan=2)
        
        self.btnDownload      .grid(row=2, column=4, sticky="E",  pady=10, padx=10, columnspan=2)

        self.fmDLBlock.columnconfigure(0, weight=0, minsize=50)
        self.fmDLBlock.columnconfigure(1, weight=20, minsize=100)
        self.fmDLBlock.columnconfigure(2, weight=0, minsize=30)
        self.fmDLBlock.columnconfigure(3, weight=0, minsize=50) #
        self.fmDLBlock.columnconfigure(4, weight=10, minsize=50) #
        self.fmDLBlock.columnconfigure(5, weight=10, minsize=50)

        self.entDownloadFolder.insert(0, self.settings.download_dir)
        self.entOptions.insert(0, self.settings.options)
        self.entTitleSheme.insert(0, title_scheme)

        #Link Info block
        self.fmInfoBlock = Frame(bg=blocks_color)
        self.fmInfoBlock.grid(row=1,column=2, sticky="WNES", pady=10, padx=10)
        
        self.lbColors  = Label(self.fmInfoBlock, text="Colors: ", bg=blocks_color, justify=LEFT)
        self.entColors = Entry(self.fmInfoBlock)
        self.btnInfo   = Button(self.fmInfoBlock, text="Link Info", width=20)
        self.btnClearConsole = Button(self.fmInfoBlock, text="Clear output", width=20)

        self.lbColors  .grid(row=0, column=0, sticky="W",  pady=10, padx=10)
        self.entColors .grid(row=0, column=1, sticky="WE", pady=10, padx=10)
        self.btnInfo   .grid(row=1, column=1, pady=10, padx=10, sticky="E")
        self.btnClearConsole   .grid(row=2, column=1, pady=10, padx=10, sticky="E")

        self.fmInfoBlock.columnconfigure(0, weight=0, minsize=50)
        self.fmInfoBlock.columnconfigure(1, weight=20, minsize=150)

        self.entColors.insert(0, self.settings.colors)

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
        self.append_console_line(ut.load_read_me(self.settings.language))

    def show_app_info(self):
        self.append_console_line(f"MinGui Youtube-dl v{app_version} (c) Voronezh Statics\n")

        proc = ut.exec_youtube_dl(self.settings.youtube_dl_path, "--version")
        version, _ = proc.communicate()
        self.append_console_line(f"Youtube-dl version: {version.decode()}\n")

    def bind_gui(self):
        self.entDwnLink.bind(
            "<Button-3>",
            lambda x: (
                self.entDwnLink.delete(0, END),
                self.entDwnLink.insert(0, self.entDwnLink.selection_get(selection="CLIPBOARD")),
            )
        )
        self.btnDownload.bind("<ButtonRelease>", lambda x: self.download(self.entDwnLink.get(), self.entOptions.get()))
        self.btnInfo.bind("<ButtonRelease>", lambda x: self.get_info(self.entDwnLink.get()))
        self.btnExec.bind("<ButtonRelease>", lambda x: self.exec_options(self.entOptions.get()))
        self.btnClearConsole.bind("<ButtonRelease>", lambda x: self.txtConsole.delete(ut.START, END))

        # self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def mainloop(self):
        self.root.mainloop()

    def download(self, link, options_str):
        dl_path = os.path.join(self.entDownloadFolder.get(), self.entTitleSheme.get())
        options = options_str.split(" ") if options_str else []
        options += ["-o", dl_path]
        options += ["--ffmpeg-location", self.settings.ffmpeg_path]
        proc = ut.exec_youtube_dl(self.settings.youtube_dl_path, link, *options)
        self.__redirect_out(proc)

    def exec_options(self, options_str):
        options = options_str.split(" ") if options_str else []
        proc = ut.exec_youtube_dl(self.settings.youtube_dl_path, *options)
        self.__redirect_out(proc)

    def get_info(self, link):
        proc = ut.exec_get_info(self.settings.youtube_dl_path, link)
        self.__redirect_out(proc)

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
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
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
