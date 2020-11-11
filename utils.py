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
READ_ME_prefix = "READ_ME"
language_dir_name = "language"
md = "md"

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
    """
    Parse string which contains data for coloring console strings.
    Example 'mp4+1080p:cyan, m4a:magenta' --> {"mp4+1080p":"cyan", "m4a":"magenta"}
    """
    try:
        opt = re.split(", |,| ,", color_config)
        opt = [ part for part in opt if part ]
        opt = dict(tuple( re.split(":| :|: ", part) ) for part in opt)
        opt = { k.strip():v.strip() for k,v in opt.items() }
    except ValueError:
        opt = {}

    return opt

#utils
def exec_youtube_dl(youtube_dl_path, *options) -> subprocess.Popen:
    l = list(options)
    l.insert(0, youtube_dl_path)
    return subprocess.Popen(l, stdout=subprocess.PIPE)

def exec_get_info(youtube_dl_path, link) -> subprocess.Popen:
    return exec_youtube_dl(youtube_dl_path, link, "-F")

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

def load_read_me(language_suffix: str)->str:
    read_me_fname = ".".join([READ_ME_prefix, language_suffix, md])
    read_me_path = os.path.join(app_root_dir, language_dir_name, read_me_fname)

    try:
        with open(read_me_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return f"Can't find the read_me file: {read_me_path}"