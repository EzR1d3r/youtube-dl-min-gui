"""Editable audio metadata and Mutagen tag writing."""

from dataclasses import dataclass
from pathlib import Path

from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TRCK, TALB


@dataclass(frozen=True)
class AudioTags:
    title: str
    artist: str
    track: int
    album: str

    @property
    def track_text(self) -> str:
        return f"{self.track:02d}"


def write_audio_tags(path: Path, tags: AudioTags) -> None:
    if path.suffix.lower() != ".mp3":
        raise ValueError(f"Unsupported audio tag format: {path.suffix}")
    try:
        metadata = ID3(path)
    except ID3NoHeaderError:
        metadata = ID3()
    for key, frame, value in [
        ("TIT2", TIT2, tags.title), ("TPE1", TPE1, tags.artist),
        ("TRCK", TRCK, tags.track_text), ("TALB", TALB, tags.album),
    ]:
        metadata.delall(key)
        if value:
            metadata.add(frame(encoding=3, text=[value]))
    metadata.save(path, v2_version=3)
