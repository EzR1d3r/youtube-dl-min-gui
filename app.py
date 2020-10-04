import subprocess
import os
from threading import Thread

from tkinter import Tk, Label, Button, Entry, StringVar, Text
from tkinter import LEFT, END

START = "1.0" #start index for text item
LAST_LINE = ("end-1l", END)

title_scheme = "%(title)s.%(ext)s"
youtube_dl_app = "C:\\Program Files (x86)\\youtube-dl\\youtube-dl.exe"
rel_dl_path = os.path.join("~", "Downloads", "youtube-downloads", title_scheme)
dl_path = os.path.expanduser( rel_dl_path )

#tk gui root
root = Tk()
root.title("Youtube-dl")
root.minsize(720,360)
txtConsole = Text(bg="black", fg="#2bfe72")

def _readline(obj, newline = (b"\n", b"\r")):
    l = []
    while True:
        c = obj.read(1)
        if c:
            l.append(c)
        if not c or c in newline:
            break
    return b"".join(l)

def read_output(p: subprocess.Popen):
    proc_stdout = p.stdout
    while True:
        try:
            text = _readline(proc_stdout)
            if text:
                text = text.decode("cp1251")
                if text.endswith("\r"):
                    replace_last_console_line(text)
                elif text.endswith("\n"):
                    append_console_line(text)
            else:
                break
        except ValueError:
            break
    
    append_console_line("---------------END---------------")

def append_console_line(text_line: str):
    _append_text_item_text_line(txtConsole, text_line)

def clear_and_fill_console(text):
    _set_text_item_text(txtConsole, text)

def replace_last_console_line(text_line):
    _replace_text_item_last_line(txtConsole, text_line)

def _append_text_item_text_line(text_item: Text, text_line: str):
    text_item.insert(END, text_line)

def _replace_text_item_last_line(text_item: Text, text_line: str):
    txtConsole.delete(*LAST_LINE)
    text_line = "\n" + text_line
    text_item.insert(END, text_line)

def _set_text_item_text(text_item: Text, text: str):
    text_item.delete(START, END)
    text_item.insert(START, text)

def exec(link, *options):
    l = list(options)
    l.insert(0, youtube_dl_app)
    l.append(link)
    proc = subprocess.Popen(l, stdout=subprocess.PIPE)
    t = Thread(target=read_output, args=(proc,))
    t.start()

def download(link, options_str):
    options = options_str.split(" ") if options_str else []
    options+=["-o", dl_path]
    append_console_line("\n")
    exec(link, *options)

def get_info(link):
    append_console_line("\n")
    exec(link, "-F")

def fill_with_info(link):
    get_info(link)

def start_gui():
    #labels
    lbLink = Label(root, text="Download link: ", justify=LEFT)
    lbLink.grid(row=0,column=0,sticky="W",pady=10, padx=10)

    lbOptions = Label(root, text="Options: ", justify=LEFT)
    lbOptions.grid(row=1,column=0, sticky="W", pady=10, padx=10)

    #entrys
    entDwnLink = Entry(root)
    entDwnLink.grid(row=0, column=1, sticky="WE", columnspan=2, pady=10, padx=10)
    entDwnLink.bind("<Button-3>", lambda x: entDwnLink.insert(0,entDwnLink.selection_get(selection='CLIPBOARD') ))
    entDwnLink.insert(0, "https://www.youtube.com/watch?v=S6ygE226h-0")

    entOptions = Entry(root, width=100)
    entOptions.grid(row=1,column=1, sticky="WE", columnspan=2, pady=10, padx=10)
    entOptions.insert(0, "-f 399+140")

    #buttons
    btnDownload = Button(root, text="Download", width=20, command = lambda: download(entDwnLink.get(), entOptions.get()))
    btnDownload.grid(row=100, column=1, pady=10, padx=10, sticky="E")

    btnInfo = Button(root, text="Info", width=20, command = lambda: fill_with_info(entDwnLink.get()))
    btnInfo.grid(row=100, column=2, pady=10, padx=10, sticky="E")

    # text
    txtConsole.grid(row=102, column=0, columnspan=3, sticky="WNES", pady=10, padx=10)

    #root
    root.columnconfigure(0, weight=0, minsize=100)
    root.columnconfigure(1, weight=10, minsize=300)
    root.rowconfigure(102, weight=100)

    root.mainloop()

if __name__ == "__main__":
    start_gui()