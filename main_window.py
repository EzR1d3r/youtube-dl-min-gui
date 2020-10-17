from threading import Thread
import subprocess
import os

from tkinter import Tk, Label, Button, Entry, StringVar, Text, Frame
from tkinter import LEFT, END
from tkinter import messagebox

import utils as ut
from settings import load_settings, save_settings

title_scheme = "%(title)s.%(ext)s"
rel_dl_dir = os.path.join("~", "Downloads", "youtube-downloads")
dl_dir = os.path.expanduser( rel_dl_dir )
blocks_color = "light grey"

class MainWindow:
    def __init__(self):
        self.settings = load_settings()

        #tk gui root
        self.root = Tk()
        self.root.title("MinGui Youtube-dl")
        self.root.minsize(720,360)
        self.txtConsole = Text(bg="black", fg="#2bfe72")

        #link block
        self.lbLink = Label(self.root, text="Download link: ", justify=LEFT)
        self.lbLink.grid(row=0,column=0,sticky="W",pady=10, padx=10)

        self.entDwnLink = Entry(self.root)
        self.entDwnLink.grid(row=0, column=1, sticky="WE", pady=10, padx=10)
        self.entDwnLink.insert(0, "https://www.youtube.com/watch?v=S6ygE226h-0")

        #Download block
        self.fmDLBlock = Frame(bg=blocks_color)
        self.fmDLBlock.grid(row=1, column=0, sticky="WNES", columnspan=2, pady=10, padx=10)

        self.lbDownloadFolder  = Label(self.fmDLBlock, text="Save folder: ", bg=blocks_color, justify=LEFT)
        self.entDownloadFolder = Entry(self.fmDLBlock)
        self.lbOptions         = Label(self.fmDLBlock, text="Options: ", bg=blocks_color, justify=LEFT)
        self.entOptions        = Entry(self.fmDLBlock)
        self.lbTitleSheme      = Label(self.fmDLBlock, text="Title sheme: ", bg=blocks_color, justify=LEFT)
        self.entTitleSheme     = Entry(self.fmDLBlock)
        self.btnDownload       = Button(self.fmDLBlock, text="Download", bg="light green", width=20)

        self.lbDownloadFolder .grid(row=0, column=0, sticky="W",  pady=10, padx=10)
        self.entDownloadFolder.grid(row=0, column=1, sticky="WE", pady=10, padx=10, columnspan=4)
        
        self.lbOptions        .grid(row=1, column=0, sticky="W",  pady=10, padx=10)
        self.entOptions       .grid(row=1, column=1, sticky="WE", pady=10, padx=10)
        self.lbTitleSheme     .grid(row=1, column=2, sticky="W",  pady=10, padx=10)
        self.entTitleSheme    .grid(row=1, column=4, sticky="WE", pady=10, padx=10)
        
        self.btnDownload      .grid(row=2, column=4, sticky="E",  pady=10, padx=10)

        self.fmDLBlock.columnconfigure(0, weight=0, minsize=50)
        self.fmDLBlock.columnconfigure(1, weight=20, minsize=100)
        self.fmDLBlock.columnconfigure(2, weight=0, minsize=50)
        self.fmDLBlock.columnconfigure(4, weight=20, minsize=100)

        self.entDownloadFolder.insert(0, self.settings.download_dir)
        self.entOptions.insert(0, self.settings.options)
        self.entTitleSheme.insert(0, title_scheme)

        #Link Info block
        self.fmInfoBlock = Frame(bg=blocks_color)
        self.fmInfoBlock.grid(row=1,column=2, sticky="WNES", pady=10, padx=10)
        
        self.lbColors  = Label(self.fmInfoBlock, text="Colors: ", bg=blocks_color, justify=LEFT)
        self.entColors = Entry(self.fmInfoBlock)
        self.btnInfo   = Button(self.fmInfoBlock, text="Link Info", width=20)

        self.lbColors  .grid(row=0, column=0, sticky="W",  pady=10, padx=10)
        self.entColors .grid(row=0, column=1, sticky="WE", pady=10, padx=10)
        self.btnInfo   .grid(row=1, column=1, pady=10, padx=10, sticky="E")

        self.fmInfoBlock.columnconfigure(0, weight=0, minsize=50)
        self.fmInfoBlock.columnconfigure(1, weight=20, minsize=150)

        self.entColors.insert(0, self.settings.colors)

        #Console
        self.txtConsole.grid(row=102, column=0, columnspan=3, sticky="WNES", pady=10, padx=10)

        #Root
        self.root.columnconfigure(0, weight=0, minsize=100)
        self.root.columnconfigure(1, weight=20, minsize=350)
        self.root.columnconfigure(2, weight=10, minsize=250)
        # self.root.columnconfigure(3, weight=10, minsize=100)
        # self.root.columnconfigure(4, weight=10, minsize=100)
        self.root.rowconfigure(102, weight=100)

        self.bind_gui()

    def bind_gui(self):
        self.entDwnLink.bind("<Button-3>", lambda x: self.entDwnLink.insert(0, self.entDwnLink.selection_get(selection='CLIPBOARD') ))
        self.btnDownload.bind("<ButtonRelease>", lambda x: self.download(self.entDwnLink.get(), self.entOptions.get()))
        self.btnInfo.bind("<ButtonRelease>", lambda x: self.get_info(self.entDwnLink.get()))
        
        # self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def mainloop(self):
        self.root.mainloop()

    def download(self, link, options_str):
        dl_path = os.path.join(self.entDownloadFolder.get(), self.entTitleSheme.get())
        options = options_str.split(" ") if options_str else []
        options+=["-o", dl_path]
        proc = ut.exec_youtube_dl(link, *options)
        self.__redirect_out(proc)

    def get_info(self, link):
        proc = ut.exec_get_info(link)
        self.__redirect_out(proc)
        
    def __redirect_out(self, proc: subprocess.Popen):
        #read youtube-dl output and redirect to the console
        t = Thread(target=ut.read_output, args=(proc,), kwargs={"out_append":self.append_console_line, "out_replace":self.replace_last_console_line})
        t.start()

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()

    #work with console text
    def append_console_line(self, text_line: str):
        ut._append_text_item_text_line(self.txtConsole, text_line)
        ut._post_format(self.txtConsole, text_line, contains={"mp4+1080p":"cyan", "m4a":"magenta"})

    def clear_and_fill_console(self, text):
        ut._set_text_item_text(self.txtConsole, text)

    def replace_last_console_line(self, text_line):
        ut._replace_text_item_last_line(self.txtConsole, text_line)