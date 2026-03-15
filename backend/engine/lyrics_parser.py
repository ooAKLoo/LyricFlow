"""Lyrics file parsers for LRC, QRC (QQ Music), and KRC (Kugou) formats."""

import re
import gzip
import zlib
from pathlib import Path


def parse_lrc(file_path: str) -> list[dict]:
    """Parse standard LRC format lyrics."""
    text = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    return _parse_lrc_text(text)


def _parse_lrc_text(text: str) -> list[dict]:
    """Parse LRC text content."""
    pattern = re.compile(r"\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)")
    lines = []

    for raw_line in text.strip().split("\n"):
        match = pattern.match(raw_line.strip())
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            ms_str = match.group(3)
            ms = int(ms_str) * (10 if len(ms_str) == 2 else 1)
            start = minutes * 60 + seconds + ms / 1000
            lyric_text = match.group(4).strip()
            if lyric_text:
                lines.append({
                    "text": lyric_text,
                    "start": start,
                    "end": 0.0,
                    "words": [],
                })

    # Calculate end times from next line's start
    for i in range(len(lines) - 1):
        lines[i]["end"] = lines[i + 1]["start"]
    if lines:
        lines[-1]["end"] = lines[-1]["start"] + 5.0

    return lines


def parse_qrc(file_path: str) -> list[dict]:
    """Parse QQ Music .qrc encrypted lyrics."""
    QRC_KEYS = [
        0x78, 0x6F, 0x6E, 0x67, 0x38, 0x31, 0x36,
        0x5A, 0x4A, 0x59, 0x32, 0x4F, 0x41, 0x53,
    ]

    data = Path(file_path).read_bytes()

    try:
        # Skip header
        encrypted = data[11:]

        # XOR decrypt
        decrypted = bytearray(
            b ^ QRC_KEYS[i % len(QRC_KEYS)]
            for i, b in enumerate(encrypted)
        )

        # Decompress
        xml_text = zlib.decompress(bytes(decrypted)).decode("utf-8", errors="ignore")

        # Parse QRC XML format
        return _parse_qrc_xml(xml_text)
    except Exception:
        # Try as plain text fallback
        try:
            text = data.decode("utf-8", errors="ignore")
            return _parse_qrc_xml(text)
        except Exception:
            return []


def _parse_qrc_xml(xml_text: str) -> list[dict]:
    """Parse QRC XML content with word-level timestamps."""
    lines = []

    # QRC format: <Lyric_1 LyricType="1" LyricContent="..."/>
    # Content uses format: [offset,duration]word(offset,duration)char...
    line_pattern = re.compile(r"\[(\d+),(\d+)\](.*?)(?=\[\d+,\d+\]|$)")

    for match in line_pattern.finditer(xml_text):
        line_start_ms = int(match.group(1))
        line_duration_ms = int(match.group(2))
        content = match.group(3)

        # Parse word-level timestamps within the line
        word_pattern = re.compile(r"(\S+?)\((\d+),(\d+)\)")
        words = []
        full_text_parts = []

        for word_match in word_pattern.finditer(content):
            word_text = word_match.group(1)
            word_start_ms = int(word_match.group(2))
            word_dur_ms = int(word_match.group(3))
            words.append({
                "word": word_text,
                "start": word_start_ms / 1000,
                "end": (word_start_ms + word_dur_ms) / 1000,
            })
            full_text_parts.append(word_text)

        # If no word-level timestamps found, use line text
        if not words:
            clean_text = re.sub(r"\(\d+,\d+\)", "", content).strip()
            if clean_text:
                full_text_parts = [clean_text]

        line_text = " ".join(full_text_parts)
        if line_text.strip():
            lines.append({
                "text": line_text,
                "start": line_start_ms / 1000,
                "end": (line_start_ms + line_duration_ms) / 1000,
                "words": words,
            })

    return lines


def parse_krc(file_path: str) -> list[dict]:
    """Parse Kugou .krc encrypted lyrics."""
    KRC_KEY = [
        64, 71, 97, 119, 94, 50, 116, 71,
        47, 81, 54, 49, 45, 206, 210, 110,
    ]

    data = Path(file_path).read_bytes()

    try:
        # Skip 'krc1' header (4 bytes)
        encrypted = data[4:]

        # XOR decrypt
        decrypted = bytearray(
            b ^ KRC_KEY[i % len(KRC_KEY)]
            for i, b in enumerate(encrypted)
        )

        # Gzip decompress
        text = gzip.decompress(bytes(decrypted)).decode("utf-8", errors="ignore")

        return _parse_krc_text(text)
    except Exception:
        return []


def _parse_krc_text(text: str) -> list[dict]:
    """Parse KRC text content with word-level timestamps."""
    lines = []

    # KRC format: [offset,duration]<offset,duration,0>word<offset,duration,0>word...
    line_pattern = re.compile(r"\[(\d+),(\d+)\](.*?)$", re.MULTILINE)

    for match in line_pattern.finditer(text):
        line_start_ms = int(match.group(1))
        line_duration_ms = int(match.group(2))
        content = match.group(3)

        # Parse word-level timestamps
        word_pattern = re.compile(r"<(\d+),(\d+),\d+>([^<]+)")
        words = []
        full_text_parts = []

        for word_match in word_pattern.finditer(content):
            word_offset_ms = int(word_match.group(1))
            word_dur_ms = int(word_match.group(2))
            word_text = word_match.group(3)
            abs_start = (line_start_ms + word_offset_ms) / 1000
            words.append({
                "word": word_text,
                "start": abs_start,
                "end": abs_start + word_dur_ms / 1000,
            })
            full_text_parts.append(word_text)

        line_text = "".join(full_text_parts)
        if line_text.strip():
            lines.append({
                "text": line_text,
                "start": line_start_ms / 1000,
                "end": (line_start_ms + line_duration_ms) / 1000,
                "words": words,
            })

    return lines
