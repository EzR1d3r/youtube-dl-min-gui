from dataclasses import dataclass
import os
from utils import app_root_dir
import platform

current_platform = platform.system()
Windows = "Windows"
Linux = "Linux"
Mac = "Darwin"

std_youtube_dl_dir = os.path.join(app_root_dir, "youtube-dl")
std_ffmpeg_dir = os.path.join(app_root_dir, "ffmpeg", "bin")

rel_dl_dir = os.path.join("~", "Downloads", "youtube-downloads")
std_dl_dir = os.path.expanduser( rel_dl_dir )

if current_platform == Windows:
    std_path_youtube_dl_path = os.path.join( std_youtube_dl_dir, "youtube-dl.exe" )
elif current_platform == Mac:
    std_path_youtube_dl_path = os.path.join( std_youtube_dl_dir, "youtube-dl.app" )
else:
    std_path_youtube_dl_path = os.path.join( std_youtube_dl_dir, "youtube-dl" )

class Settings:
    youtube_dl_path: str = std_path_youtube_dl_path
    ffmpeg_path: str = std_ffmpeg_dir
    download_dir: str = std_dl_dir
    file_title: str = "%(title)s.%(ext)s"
    options: str = "-f 399+140"
    colors: str = "mp4+1080p:cyan, m4a:magenta"