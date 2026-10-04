"""Editable audio metadata and Mutagen tag writing."""

from dataclasses import dataclass
from pathlib import Path

from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TPE2, TRCK, TALB, TDRC, APIC, PictureType


ORIGINAL_COVER = "<original>"
COVER_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".gif": "image/gif", ".bmp": "image/bmp",
}


@dataclass(frozen=True)
class CoverImage:
    mime: str
    data: bytes


def cover_path(value: str, original: Path | None = None) -> Path:
    if value == ORIGINAL_COVER:
        if original is None:
            raise ValueError("Original cover was not downloaded.")
        path = original
    else:
        path = Path(value).expanduser()
    if path.suffix.lower() not in COVER_TYPES:
        raise ValueError("Cover must be a JPEG, PNG, GIF or BMP file.")
    if not path.is_file():
        raise ValueError(f"Cover file not found: {path}")
    return path.resolve()


def read_cover(path: Path) -> CoverImage:
    try:
        data = path.read_bytes()
    except OSError as error:
        raise ValueError(f"Cannot read cover: {path}") from error
    mime = COVER_TYPES[path.suffix.lower()]
    valid = {
        "image/jpeg": data.startswith(b"\xff\xd8\xff"),
        "image/png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/gif": data.startswith((b"GIF87a", b"GIF89a")),
        "image/bmp": data.startswith(b"BM"),
    }[mime]
    if not valid:
        raise ValueError(f"Cover content does not match its image extension: {path}")
    return CoverImage(mime, data)


@dataclass(frozen=True)
class AudioTags:
    title: str
    artist: str
    track: int
    album: str
    year: str = ""
    album_artist: str = ""
    cover: str = ORIGINAL_COVER

    @property
    def track_text(self) -> str:
        return f"{self.track:02d}"


def write_audio_tags(path: Path, tags: AudioTags, cover: CoverImage | None = None) -> None:
    if path.suffix.lower() != ".mp3":
        raise ValueError(f"Unsupported audio tag format: {path.suffix}")
    try:
        metadata = ID3(path)
    except ID3NoHeaderError:
        metadata = ID3()
    for key, frame, value in [
        ("TIT2", TIT2, tags.title), ("TPE1", TPE1, tags.artist),
        ("TRCK", TRCK, tags.track_text), ("TALB", TALB, tags.album),
        ("TDRC", TDRC, tags.year), ("TPE2", TPE2, tags.album_artist),
    ]:
        metadata.delall(key)
        if value:
            metadata.add(frame(encoding=3, text=[value]))
    if cover is not None:
        metadata.delall("APIC")
        metadata.add(APIC(encoding=3, mime=cover.mime, type=PictureType.COVER_FRONT,
                          desc="Cover", data=cover.data))
    metadata.update_to_v23()
    metadata.save(path, v2_version=3)
