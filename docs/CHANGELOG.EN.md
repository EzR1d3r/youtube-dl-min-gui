# Changelog

## 1.2.0

- Add "S" to split Title into Artist and Title, and "T" to convert selected Title and Artist values to Title Case.
- Clamp the last segment's end to the downloaded file duration when splitting in Extended modes.
- Add optional audio tag columns through "Tag +", including WOAR and WOAF URLs, with bulk editing and MP3 tag writing.
- Add and remove segments in "Extended" and "Extended Audio", and edit chapter names in "Extended".
- Support a cookies file through the "cookies" setting for downloads and information requests.

## 1.1.1

- Fix separate console windows appearing when launching the downloader, FFmpeg and FFprobe on Windows.

## 1.1.0

- Show available formats as a table with "Link Info".
- Add "Split media" with three modes: "Default" splits original chapters; "Extended" trims or splits editable time ranges; "Extended Audio" saves MP3 tracks with editable tags, covers and bulk tag editing.
- Configure a JavaScript runtime through "js_runtime_path" for yt-dlp.
- Handle an empty clipboard when pasting links and extra spaces in Options.
- Remove saved folders and option presets with "−".
- Remember the window size when closing and restore it on startup.
- Save option presets with "+", select them from a dropdown and restore the last used preset.
- Save download folders with "+" and select them from a dropdown.
- Restore the last selected folder on startup.
- Show instructions and change history in English or Russian at startup.

## 1.0.1

- Added "Clear output" to clear the application console.
- Right-clicking "Download link" clears the field before pasting clipboard text.
- Redirected downloader errors to the application console.
