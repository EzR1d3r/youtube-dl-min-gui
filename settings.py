import os
import json
from dataclasses import dataclass, asdict
import platform

from utils import app_root_dir

current_platform = platform.system()
Windows = "Windows"
Linux = "Linux"
Mac = "Darwin"

std_youtube_dl_dir = os.path.join(app_root_dir, "youtube-dl")
std_ffmpeg_dir = os.path.join(app_root_dir, "ffmpeg", "bin")
settings_fname = os.path.join(app_root_dir, ".settings.json")

rel_dl_dir = os.path.join("~", "Downloads", "youtube-downloads")
std_dl_dir = os.path.expanduser( rel_dl_dir )

if current_platform == Windows:
    std_path_youtube_dl_path = os.path.join( std_youtube_dl_dir, "youtube-dl.exe" )
elif current_platform == Mac:
    std_path_youtube_dl_path = os.path.join( std_youtube_dl_dir, "youtube-dl.app" )
else:
    std_path_youtube_dl_path = os.path.join( std_youtube_dl_dir, "youtube-dl" )

@dataclass
class Settings:
    youtube_dl_path: str = std_path_youtube_dl_path
    ffmpeg_path: str = std_ffmpeg_dir
    download_dir: str = std_dl_dir
    file_title: str = "%(title)s.%(ext)s"
    options: str = "-f 399+140"
    colors: str = "mp4+1080p:cyan, m4a:magenta"

def save_settings(settings_obj: Settings, fname: str) -> None:
    _json = asdict(settings_obj)
    with open(fname, "w") as file:
        json.dump(_json, file, indent=4)

def load_settings(fname: str = settings_fname) -> None:
    try:
        with open(fname, "r") as file:
            _json = json.load(file)
        settings_obj = Settings(**_json)
    except (FileNotFoundError, json.JSONDecodeError):
        settings_obj = Settings()
        save_settings(settings_obj, fname)

    return settings_obj