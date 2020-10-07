from threading import Thread
import subprocess
import os

from tkinter import Tk, Label, Button, Entry, StringVar, Text
from tkinter import LEFT, END
from tkinter import messagebox

import utils as ut
from settings import Settings

title_scheme = "%(title)s.%(ext)s"
rel_dl_dir = os.path.join("~", "Downloads", "youtube-downloads")
dl_dir = os.path.expanduser( rel_dl_dir )

class MainWindow:
    def __init__(self):
        #tk gui root
        self.root = Tk()
        self.root.title("Youtube-dl")
        self.root.minsize(720,360)
        self.txtConsole = Text(bg="black", fg="#2bfe72")

        #labels
        self.lbLink = Label(self.root, text="Download link: ", justify=LEFT)
        self.lbLink.grid(row=0,column=0,sticky="W",pady=10, padx=10)

        self.lbOptions = Label(self.root, text="Options: ", justify=LEFT)
        self.lbOptions.grid(row=1,column=0, sticky="W", pady=10, padx=10)

        self.lbDownloadFolder = Label(self.root, text="Save folder: ", justify=LEFT)
        self.lbDownloadFolder.grid(row=2,column=0, sticky="W", pady=10, padx=10)

        self.lbTitleSheme = Label(self.root, text="Title sheme: ", justify=LEFT)
        self.lbTitleSheme.grid(row=2,column=2, sticky="W", pady=10, padx=10)

        #entrys
        self.entDwnLink = Entry(self.root)
        self.entDwnLink.grid(row=0, column=1, sticky="WE", columnspan=4, pady=10, padx=10)
        self.entDwnLink.insert(0, "https://www.youtube.com/watch?v=S6ygE226h-0")

        self.entOptions = Entry(self.root, width=100)
        self.entOptions.grid(row=1,column=1, sticky="WE", columnspan=4, pady=10, padx=10)
        self.entOptions.insert(0, "-f 399+140")

        self.entDownloadFolder = Entry(self.root, width=100)
        self.entDownloadFolder.grid(row=2,column=1, sticky="WE", columnspan=1, pady=10, padx=10)
        self.entDownloadFolder.insert(0, dl_dir)

        self.entTitleSheme = Entry(self.root, width=100)
        self.entTitleSheme.grid(row=2,column=3, sticky="WE", columnspan=2, pady=10, padx=10)
        self.entTitleSheme.insert(0, title_scheme)

        #buttons
        self.btnDownload = Button(self.root, text="Download", width=20)
        self.btnDownload.grid(row=100, column=3, pady=10, padx=10, sticky="E")

        self.btnInfo = Button(self.root, text="Info", width=20)
        self.btnInfo.grid(row=100, column=4, pady=10, padx=10, sticky="E")

        # text
        self.txtConsole.grid(row=102, column=0, columnspan=5, sticky="WNES", pady=10, padx=10)

        #root
        self.root.columnconfigure(0, weight=0, minsize=100)
        self.root.columnconfigure(1, weight=20, minsize=200)
        self.root.columnconfigure(2, weight=0, minsize=50)
        self.root.columnconfigure(3, weight=10, minsize=100)
        # self.root.columnconfigure(4, weight=10, minsize=100)
        self.root.rowconfigure(102, weight=100)

        self.bind_gui()

    def bind_gui(self):
        self.entDwnLink.bind("<Button-3>", lambda x: self.entDwnLink.insert(0, self.entDwnLink.selection_get(selection='CLIPBOARD') ))
        self.btnDownload.bind("<ButtonRelease>", lambda x: self.download(self.entDwnLink.get(), self.entOptions.get()))
        self.btnInfo.bind("<ButtonRelease>", lambda x: self.get_info(self.entDwnLink.get()))
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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