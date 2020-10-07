import os
import sys
import re
import subprocess
from threading import Thread

from tkinter import END
from tkinter import Text

START = "1.0" #start index for text item
LAST_LINE = ("end-1l", END)
PENULTIMATE_LINE = ("end-2l", "end-1l")

youtube_dl_app = "C:\\Program Files (x86)\\youtube-dl\\youtube-dl.exe"
enter_point_fname = os.path.realpath(sys.argv[0])
app_root_dir = os.path.dirname(enter_point_fname)

#gui utils
def _post_format(text_item: Text, text_line, contains=None):
    contains = contains if contains else {}
    for sub_str, color in contains.items():
        if _check_substrings(text_line, sub_str):
            text_item.tag_add(sub_str, *PENULTIMATE_LINE)
            text_item.tag_config(sub_str, foreground=color)

def _check_substrings(inspected_str: str, subs):
    subs = subs.split("+")
    return all( [(s in inspected_str) for s in subs] )

def _append_text_item_text_line(text_item: Text, text_line: str):
    text_item.insert(END, text_line)

def _replace_text_item_last_line(text_item: Text, text_line: str):
    text_item.delete(*LAST_LINE)
    text_line = "\n" + text_line
    text_item.insert(END, text_line)

def _set_text_item_text(text_item: Text, text: str):
    text_item.delete(START, END)
    text_item.insert(START, text)

def parse_colors(color_config: str):
    try:
        opt = re.split(", |,| ", color_config)
        opt = [ part for part in opt if part ]
        opt = dict(tuple( re.split(":| :|: ", part) ) for part in opt)
    except ValueError:
        opt = {}

    return opt

#utils
def exec_youtube_dl(link, *options) -> subprocess.Popen:
    l = list(options)
    l.insert(0, youtube_dl_app)
    l.append(link)
    return subprocess.Popen(l, stdout=subprocess.PIPE)

def exec_get_info(link) -> subprocess.Popen:
    return exec_youtube_dl(link, "-F")

def _readline(obj, newline = (b"\n", b"\r")):
    l = []
    while True:
        c = obj.read(1)
        if c:
            l.append(c)
        if not c or c in newline:
            break
    return b"".join(l)

def read_output(p: subprocess.Popen, out_append = print, out_replace = print):
    proc_stdout = p.stdout
    while True:
        try:
            text = _readline(proc_stdout)
            if text:
                text = text.decode("cp1251")
                if text.endswith("\r"):
                    out_replace(text)
                elif text.endswith("\n"):
                    out_append(text)
            else:
                break
        except ValueError:
            break
