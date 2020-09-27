import subprocess
import os
from threading import Thread

from tkinter import Tk, Label, Button, Entry, StringVar, LEFT

title_scheme = "%(title)s.%(ext)s"
youtube_dl_app = "C:\\Program Files (x86)\\youtube-dl\\youtube-dl.exe"
rel_dl_path = os.path.join("~", "Downloads", "youtube-downloads", title_scheme)
dl_path = os.path.expanduser( rel_dl_path )

#tk gui root
root = Tk()
root.title("Youtube-dl")
root.minsize(720,360)
console_text = StringVar(value="")

def exec(link, *options):
    l = list(options)
    l.insert(0, youtube_dl_app)
    l.append(link)
    proc = subprocess.Popen(l, stdout=subprocess.PIPE)
    outs, errs = proc.communicate()
    return outs, errs

def download(link, options_str):
    options = options_str.split(" ") if options_str else []
    options+=["-o", dl_path]
    outs, errs = exec(link, *options)

def get_info(link):
    outs, errs = exec(link, "-F")
    return outs, errs

def fill_console(text):
    console_text.set(text)

def fill_with_info(link):
    outs, _ = get_info(link)
    if outs:
        fill_console(outs.decode())

def start_gui():
    #labels
    lbLink = Label(root, text="Download link: ", justify=LEFT)
    lbLink.grid(row=0,column=0,sticky="W",pady=10, padx=10)

    lbOptions = Label(root, text="Options: ", justify=LEFT)
    lbOptions.grid(row=1,column=0,sticky="W",pady=10, padx=10)

    lbInfo = Label(textvariable=console_text, bg="black", fg="#2bfe72", justify=LEFT, width=100)
    lbInfo.grid(row=101, column=0, columnspan=2, sticky="W", pady=10, padx=10)

    #entrys
    entDwnLink = Entry(root, width=100)
    entDwnLink.grid(row=0,column=1, sticky="W")
    entDwnLink.bind("<Button-3>", lambda x: entDwnLink.insert(0,entDwnLink.selection_get(selection='CLIPBOARD') ))
    entDwnLink.insert(0, "https://www.youtube.com/watch?v=S6ygE226h-0")

    entOptions = Entry(root, width=100)
    entOptions.grid(row=1,column=1, sticky="W")
    
    #buttons
    btnDownload = Button(root, text="Download", command = lambda: download(entDwnLink.get(), entOptions.get()))
    btnDownload.grid(row=100,column=0)

    btnInfo = Button(root, text="Info", command = lambda: fill_with_info(entDwnLink.get()))
    btnInfo.grid(row=100,column=1)

    #loop
    root.mainloop()

if __name__ == "__main__":
    start_gui()