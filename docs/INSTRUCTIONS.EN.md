## Download

1. Paste a URL into "Download link" and click "Link Info" to see available formats.
2. Enter parameters in "Options": for example "-f 137+140", where 137 and 140 are
   video and audio IDs from the table. For MP3: "--extract-audio --audio-format mp3 --audio-quality 0".
3. Click "Download".

## Overview and setup

Amanita Downloader is a graphical interface (GUI) for the yt-dlp downloader.
It uses FFmpeg for media processing and a JavaScript runtime such as Deno
for downloader support. Their versions appear in the console at startup.
Keep these tools updated yourself for reliable operation.

Install yt-dlp, FFmpeg and a JavaScript runtime such as Deno.
When running from source: "python -m pip install -r requirements.txt".

Copy ".settings.example.json" to ".settings.json" beside "app.py" or the EXE.
Set paths for your computer; use forward slashes in JSON, such as C:/Tools.
Downloader, FFmpeg and runtime paths may be absolute or relative to the folder
containing "app.py" (when running from source) or the EXE (in a build).
Examples: "./yt-dlp.exe", "./ffmpeg/bin", "deno:./deno.exe".

- "youtube_dl_path": downloader executable.
- "ffmpeg_path": folder containing FFmpeg and FFprobe.
- "js_runtime_path": runtime and path, for example "deno:C:/Tools/deno/deno.exe".
  An empty string keeps yt-dlp's defaults.
- "download_dir" and "options": lists of saved folders and option presets.
- "cookies": a Netscape cookies file, for example "./cookies.txt".
  Use an absolute path or one relative to the application folder; leave empty to disable.
  One file can contain cookies for multiple sites. yt-dlp may update it.
- "colors": highlighting rules, for example "mp4+1080p:cyan, ERROR:red".
- "font_name", "font_size", "console_bg", "console_fg": console appearance.
- "language": "EN" or "RU". "window_size" is saved automatically on closing.

## Split media

Enable "Split media" and click "Link Info", then choose a mode:

- "Default": split the original chapters into the selected folder.
- "Extended": edit time ranges, then trim or split the downloaded file.
- "Extended Audio": save MP3 tracks with editable tags and covers.

Files without chapters get one full-length segment.
Times use "HH:MM:SS:CC". Arrows change seconds, Shift changes minutes,
Ctrl changes tenths of a second. "Lock" links adjacent chapter boundaries.
Extended modes keep the original file and show FFmpeg processing logs.

## Audio tags and covers

The "+" button in the "Tag" heading adds an optional tag column:
Artist URL (WOAR), Audio URL (WOAF), Genre, Composer, Comment, Disc, BPM,
Copyright, Publisher or Language. Use "…" to apply a value to selected rows.
Additional tags are written to MP3; an empty field removes the corresponding tag.

In "Extended Audio", "−" removes a segment and "+" inserts one after it,
from its end to the next segment's start. Adding after the last segment creates
a zero-length range; adjust it before downloading. Other tracks are not renumbered.
The "−" button in the "Segments" heading removes all selected rows.

Edit Title, Artist, Track, Album, Year and Album Artist.
Track is displayed and tagged as "01"; Year is four digits or empty.
Filenames are "01 - Artist - Title", or "01 - Title" when Artist is empty.

Select rows on the left, or use "All". The "…" button beside a tag heading
applies one value to selected rows. Selection affects editing only;
all segments are processed when downloading.

Cover accepts "<original>", a JPEG/PNG/GIF/BMP path, or an empty value.
In the Cover dialog: "X" removes the cover, "O" selects the original thumbnail,
"…" opens a file picker. Invalid or missing covers stop processing.

## Other controls and troubleshooting

- "Exec": run only the arguments in "Options"; "-h" displays downloader help.
- "Clear output": clear the console.
- "Colors": edit highlighting rules for this session.
- If a tool is not found, check its path in ".settings.json".
- "Options" splits arguments on spaces and does not interpret quotes.
  Use "Save folder" for folder paths containing spaces.
- Keep "docs/" beside the EXE for startup help.

Russian instructions: INSTRUCTIONS.RU.md. Release notes: CHANGELOG.EN.md.
