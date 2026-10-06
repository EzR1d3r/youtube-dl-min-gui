import os
import sys
import re
import subprocess
import shutil
from threading import Thread
from io import IOBase
from typing import Type

from tkinter import END
from tkinter import Text

START = "1.0" #start index for text item
LAST_LINE = ("end-1l", END)
PENULTIMATE_LINE = ("end-2l", "end-1l")

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
def program_version(program: str, version_option: str = "--version") -> str:
    executable = shutil.which(program) or program
    try:
        result = subprocess.run(
            [executable, version_option], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", timeout=5,
        )
    except FileNotFoundError:
        return f"{program}: not found"
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"{program}: could not read version ({error})"
    lines = result.stdout.strip().splitlines()
    if result.returncode != 0:
        return f"{program}: could not read version (exit code {result.returncode})"
    version = lines[0] if lines else "unknown version"
    return version


def exec_youtube_dl(youtube_dl_path, *options, js_runtime_path: str = "") -> subprocess.Popen:
    l = list(options)
    if js_runtime_path.strip():
        l[0:0] = ["--js-runtimes", js_runtime_path.strip()]
    l.insert(0, youtube_dl_path)
    return subprocess.Popen(l, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def exec_get_info(youtube_dl_path, link, js_runtime_path: str = "") -> subprocess.Popen:
    return exec_youtube_dl(
        youtube_dl_path, "--skip-download", "--no-playlist", "--encoding", "utf-8",
        "--dump-single-json", "--", link, js_runtime_path=js_runtime_path
    )

def _readline(obj, newline = (b"\n", b"\r")):
    l = []
    while True:
        c = obj.read(1)
        if c:
            l.append(c)
        if not c or c in newline:
            break
    return b"".join(l)

def read_output(stream: Type[IOBase], out_append = print, out_replace = print):
    while True:
        try:
            text = _readline(stream)
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

def load_instructions(language_suffix: str) -> str:
    return _load_document("INSTRUCTIONS", language_suffix)


def load_changelog(language_suffix: str) -> str:
    return _load_document("CHANGELOG", language_suffix)


def _load_document(document: str, language_suffix: str) -> str:
    language = language_suffix.upper()
    if language not in {"EN", "RU"}:
        language = "EN"
    document_path = os.path.join(app_root_dir, "docs", f"{document}.{language}.md")

    try:
        with open(document_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return f"Can't find the {document.lower()} file: {document_path}"
