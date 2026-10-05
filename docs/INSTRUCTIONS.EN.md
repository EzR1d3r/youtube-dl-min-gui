# Instructions

[Русская версия](INSTRUCTIONS.RU.md) · [Project overview](../README.md)

## Setup

Install a youtube-dl-compatible downloader and FFmpeg separately. Copy
`.settings.example.json` to `.settings.json` beside `app.py` (or beside the built
EXE), then edit the paths before starting the application.

When running from source, install dependencies with
`python -m pip install -r requirements.txt`. Mutagen is used to write audio tags.

- `youtube_dl_path`: full path to the downloader executable, such as yt-dlp.exe.
- `ffmpeg_path`: path to the directory containing FFmpeg executables.
- `js_runtime_path`: optional JavaScript runtime in yt-dlp's `RUNTIME:PATH`
  format, for example `deno:C:/Tools/deno/deno.exe` or
  `node:C:/Program Files/nodejs/node.exe`. Passed as `--js-runtimes` for
  Download, Link Info and Exec. An empty string keeps yt-dlp's defaults.
- `download_dir`: list of output folders; the first folder is selected
  at startup. Example: `["C:/Downloads/videos", "D:/Music"]`.
- `options`: list of saved option presets; the first is selected at
  startup. Example: `["-f 137+140", "-h", ""]`. An empty string means no extra options.
- `colors`: comma-separated console highlighting rules, such as
  `mp4+1080p:cyan, m4a:magenta, ERROR:red`.
- `font_name`, `font_size`, `console_bg`, `console_fg`: console appearance.
- `window_size`: window dimensions, such as `"1000x650"`. Saved on closing and
  restored at startup; an empty string lets Tkinter choose the initial size.
- `language`: `EN` or `RU` for the startup instructions; interface labels remain
  in English.

JSON paths may use forward slashes (`C:/Downloads`) or escaped backslashes
(`C:\\Downloads`). If an older configuration stores `download_dir` as a string,
replace it with a list manually. Automatic migration is not provided.
Older `options` strings also need to be changed to lists manually.

## Download a video or audio file

For audio tracks, enable **Split media**, request **Link Info** and choose
**Extended Audio** in the chapter panel. Edit Track, Artist, Title, Album,
Year (four digits or empty) and Album Artist,
as well as the time ranges and Lock. Track numbers appear as `01`, `02`, etc.
Cover defaults to `<original>`: the video thumbnail is downloaded with the
media, converted to JPEG and embedded in each selected track. Alternatively,
enter a path to a JPEG, PNG, GIF or BMP file in Cover, or leave it empty for
no cover. Custom paths are checked
before downloading; all cover files are read and checked before splitting.
An invalid or missing cover stops processing with a chapter-specific error.
Use the leftmost checkboxes to select segments for bulk editing; **All** selects
or clears every row. The **…** button beside a column heading opens an editor
that applies its value to the selected rows. Beside the Cover input, **X** clears
the cover, **O** selects `<original>`, and **…** opens a file dialog. Hover over
these buttons for hints. Bulk editing applies to tag columns only;
Start, End and Lock are edited per row. Selection controls editing only; Download
still processes all segments.
Output names are `01 - Artist - Title`; when Artist is empty, `01 - Title`.
Album is saved as a tag and does not appear in the filename.
The mode produces MP3 audio only. All six tags are saved using Mutagen,
including the track number with a leading zero, such as `01`.

1. Paste a URL into **Download link**. Right-clicking this field replaces its
   contents with the clipboard text.
2. Click **Link Info** to list available audio and video formats.
3. Choose a folder from **Save folder**, or type a path. Click the small **+**
   button to save the typed path to the dropdown. Enter also saves it.
4. Enter the desired downloader arguments in **Options**. For example,
   `-f 137+140` combines video format 137 and audio format 140 when those codes
   are available. Format codes depend on the URL; use the actual listed codes.
   Choose a saved preset from the dropdown, or save the current value using
   the **+** button next to Options or Enter.
5. Set the filename template in **Title sheme**. The initial template is
   `%(title)s.%(ext)s`.
6. Click **Download** and watch the console for progress or errors.

The selected folder moves to the top of the saved list and is restored on the
next launch. Downloading also saves a newly typed folder. Repeated paths do not
create duplicate history entries. The **+** button saves a path; it does not
open a folder picker or create the directory.

For audio extraction with yt-dlp, one possible Options value is
`--extract-audio --audio-format mp3 --audio-quality 0`. FFmpeg is needed for
conversion. Consult the downloader's help for its supported options.

## Other controls

- **−** next to Save folder or Options removes the current saved preset and
  saves the updated list. The next remaining preset is selected. Deleting the
  last preset clears the field; enter a folder before downloading.
- **Exec** runs the downloader with only the contents of **Options**. It does
  not automatically add the URL, output folder, filename or FFmpeg path.
  To display help, enter `-h` and click **Exec**.
- **Clear output** clears the application console.
- **Colors** controls highlighting. In a rule such as `mp4+1080p:cyan`, both
  terms must occur in a line for that line to match.

Folder and options histories are saved to `.settings.json`. Selecting an options
preset, **Download** or **Exec** also saves the current options, with duplicates
removed and the last selected preset restored at startup. Empty options can be saved.
Other edited fields affect the current session; edit the configuration file while
the app is closed for persistent startup colors. The `file_title` setting is currently
not applied to the initial filename field.

## Troubleshooting

- If startup reports a missing executable, check `youtube_dl_path`.
- If merging or audio conversion fails, check `ffmpeg_path` and the downloader's
  error output.
- Keep `docs/` beside the executable so startup instructions can be loaded.
- The Options field splits arguments on spaces and does not interpret quoted
  arguments. Use the separate Save folder field for paths with spaces.

Release notes are in [CHANGELOG.EN.md](CHANGELOG.EN.md).
