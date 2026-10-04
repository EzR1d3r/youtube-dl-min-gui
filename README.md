# MinGui Youtube-dl

A small Tkinter desktop interface for youtube-dl-compatible downloaders, including
yt-dlp. Paste a URL, inspect available formats, choose an output folder and start
a download. Downloader output and errors appear in the application console.

## Features

- Video and audio downloads through an external downloader executable.
- Format inspection and editable command-line options with saved presets.
- Editable output-folder dropdown with saved history and **+** / **−** buttons.
- Output filename templates and configurable console colors and fonts.
- English and Russian startup instructions.

## Requirements

- Python 3.9 or newer with Tkinter to run from source. The current development
  environment uses Python 3.14.8 on Windows.
- A [yt-dlp executable](https://github.com/yt-dlp/yt-dlp#installation) or a
  compatible youtube-dl executable.
- [FFmpeg](https://ffmpeg.org/download.html) for merging streams and audio conversion.

The GUI uses the Python standard library. Downloader and FFmpeg binaries are
installed separately and are not included in this repository.

## Quick start on Windows

1. Clone the repository and open its directory.
2. Install the downloader and FFmpeg.
   Install Python dependencies with `python -m pip install -r requirements.txt`.
3. Copy the example configuration:

   ```powershell
   Copy-Item .settings.example.json .settings.json
   ```

4. Edit `.settings.json`: set `youtube_dl_path` to the downloader executable,
   `ffmpeg_path` to FFmpeg's `bin` directory and `download_dir` to a
   list of output folders. Use paths that exist on your computer.
5. Start the application:

   ```powershell
   python app.py
   ```

If `python` resolves to the Microsoft Store shortcut, invoke your installed
interpreter directly, for example `C:\Python3.14.8\python.exe app.py`.

Configure the downloader before the first launch: the application checks its
version during startup. If `.settings.json` is absent, the application creates
defaults that expect `youtube-dl/youtube-dl.exe` and `ffmpeg/bin` beside `app.py`
on Windows. Your local `.settings.json` is ignored by Git.

## Documentation

| Document | English | Русский |
| --- | --- | --- |
| Setup, configuration and usage | [Instructions](docs/INSTRUCTIONS.EN.md) | [Инструкция](docs/INSTRUCTIONS.RU.md) |
| Change history | [Changelog](docs/CHANGELOG.EN.md) | [История изменений](docs/CHANGELOG.RU.md) |

Set `language` to `EN` or `RU` in `.settings.json` to select the instructions
shown at startup. This setting does not translate the interface labels.

## Build a Windows executable

Install [PyInstaller](https://pyinstaller.org/en/stable/usage.html) into the
Python environment used for the build:

```powershell
python -m pip install pyinstaller
.\make_exe.cmd
```

The script uses `python` from PATH. If needed, pass an interpreter explicitly:

```powershell
.\make_exe.cmd C:\Python3.14.8\python.exe
```

The output is `dist/MinGui-youtube-dl.exe`. The script also copies `docs/` and
`.settings.example.json` into `dist/`. Keep `docs/` beside the executable, copy
the example to `.settings.json` there and configure the binary paths before
running it. Python is not required to run the built GUI; the external downloader
and FFmpeg are still required.

## Project layout

```text
app.py                    Application entry point
main_window.py            Tkinter interface and download actions
settings.py               Settings model and JSON persistence
utils.py                  Downloader processes, console output and instructions
make_exe.cmd              Windows build and documentation-copy script
.settings.example.json    Portable configuration example
docs/                     English and Russian instructions and changelogs
```

## Current limitations

- `download_dir` must be a JSON array. Older string values must be
  changed manually, for example from `"C:/Downloads"` to `["C:/Downloads"]`.
- `options` must also be a JSON array, for example `["-f 137+140", "-h"]`.
  Use `[""]` for no extra options; change older string values to lists manually.
- Options are split on spaces; shell-style quoting is not supported in the
  **Options** field. The separate folder field supports paths containing spaces.
- Folder and options histories are saved automatically; edits to **Title sheme**
  and **Colors** apply to the current session. Startup colors come
  from `.settings.json`; the filename field currently starts with
  `%(title)s.%(ext)s`.
