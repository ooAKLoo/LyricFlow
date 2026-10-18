"""Stage 2: Lyrics Fetching
Priority: Embedded lyrics > User uploaded file > API matching > Whisper fallback
"""

import re
from pathlib import Path

from engine.lyrics_parser import parse_lrc, parse_qrc, parse_krc


def get_lyrics(
    task_id: str,
    preprocess_result: dict,
    lyrics_path: str | None = None,
    title: str = "",
    artist: str = "",
) -> dict:
    """Get lyrics using priority strategy. Returns structured lyrics data."""

    # Use embedded metadata to fill in missing title/artist
    if not title:
        title = preprocess_result.get("embedded_title", "")
    if not artist:
        artist = preprocess_result.get("embedded_artist", "")

    # Priority 1: Embedded lyrics from audio file (ID3/FLAC/M4A tags)
    embedded = _parse_embedded_lyrics(preprocess_result)
    if embedded:
        lines = embedded["lines"]
        # Validate: check if lyrics timeline matches audio duration
        # (e.g., "Acoustic" version lyrics embedded in original audio)
        audio_duration = preprocess_result.get("duration", 0)
        if audio_duration > 0 and lines:
            last_line_end = max(l.get("end", 0) for l in lines)
            # If lyrics end > 15% shorter or longer than audio, they're likely mismatched
            if last_line_end > 0 and abs(last_line_end - audio_duration) / audio_duration > 0.15:
                pass  # Skip embedded lyrics, fall through to next priority
            else:
                return {
                    "source": "embedded",
                    "has_word_timestamps": embedded.get("has_word_timestamps", False),
                    "lines": lines,
                }
        else:
            return {
                "source": "embedded",
                "has_word_timestamps": embedded.get("has_word_timestamps", False),
                "lines": lines,
            }

    # Priority 2: User uploaded lyrics file
    if lyrics_path:
        parsed = _parse_lyrics_file(lyrics_path)
        if parsed:
            return {
                "source": "file",
                "has_word_timestamps": parsed.get("has_word_timestamps", False),
                "lines": parsed["lines"],
            }

    # Priority 3: API matching (LRCLIB, Musixmatch)
    if title or artist:
        api_result = _fetch_from_api(title, artist)
        if api_result:
            return {
                "source": "api",
                "has_word_timestamps": api_result.get("has_word_timestamps", False),
                "lines": api_result["lines"],
            }

    # Priority 4: Whisper fallback
    vocals_path = preprocess_result["processed_path"]
    whisper_result = _whisper_transcribe(vocals_path)
    return {
        "source": "whisper",
        "has_word_timestamps": True,
        "lines": whisper_result["lines"],
        "warning": "Auto-transcribed lyrics may contain errors",
    }


def _parse_embedded_lyrics(preprocess_result: dict) -> dict | None:
    """Parse lyrics embedded in the audio file's metadata tags.

    Handles three cases:
    1. SYLT synchronized lyrics (ID3) → word/line-level timestamps
    2. USLT/Vorbis/MP4 text containing LRC timestamps → parse as LRC
    3. USLT/Vorbis/MP4 plain text → plain lyrics lines
    """
    # Case 1: ID3 SYLT synchronized lyrics
    synced = preprocess_result.get("embedded_synced_lyrics")
    if synced:
        lines = _parse_sylt_data(synced)
        if lines:
            return {"lines": lines, "has_word_timestamps": False}

    # Case 2 & 3: Plain text (may contain LRC timestamps)
    lyrics_text = preprocess_result.get("embedded_lyrics")
    if not lyrics_text:
        return None

    # Check if it looks like LRC format (contains [mm:ss.xx] timestamps)
    if re.search(r"\[\d{2}:\d{2}\.\d{2,3}\]", lyrics_text):
        lines = parse_lrc_text(lyrics_text)
        if lines:
            return {"lines": lines, "has_word_timestamps": False}

    # Plain text lyrics
    plain_lines = [
        {"text": line.strip(), "start": 0.0, "end": 0.0, "words": []}
        for line in lyrics_text.strip().split("\n")
        if line.strip()
    ]
    if plain_lines:
        return {"lines": plain_lines, "has_word_timestamps": False}

    return None


def _parse_sylt_data(synced: list[dict]) -> list[dict]:
    """Convert ID3 SYLT synchronized lyrics into lyric lines.

    SYLT stores (text, timestamp_ms) per syllable/line.
    We group consecutive entries into lines using newline markers.
    """
    if not synced:
        return []

    lines = []
    current_text_parts: list[str] = []
    current_start_ms: int | None = None

    for entry in synced:
        text = entry.get("text", "")
        ts_ms = entry.get("timestamp_ms", 0)

        # Newline or line break → flush current line
        if text in ("\n", "\r", "\r\n", ""):
            if current_text_parts and current_start_ms is not None:
                full_text = " ".join(current_text_parts).strip()
                if full_text:
                    lines.append({
                        "text": full_text,
                        "start": current_start_ms / 1000,
                        "end": ts_ms / 1000,
                        "words": [],
                    })
            current_text_parts = []
            current_start_ms = None
            continue

        if current_start_ms is None:
            current_start_ms = ts_ms
        current_text_parts.append(text)

    # Flush last line
    if current_text_parts and current_start_ms is not None:
        full_text = " ".join(current_text_parts).strip()
        if full_text:
            lines.append({
                "text": full_text,
                "start": current_start_ms / 1000,
                "end": (current_start_ms / 1000) + 5.0,
                "words": [],
            })

    # Fix end times: each line ends when the next begins
    for i in range(len(lines) - 1):
        lines[i]["end"] = lines[i + 1]["start"]

    return lines


def _parse_lyrics_file(lyrics_path: str) -> dict | None:
    """Parse .lrc/.qrc/.krc file."""
    path = Path(lyrics_path)
    ext = path.suffix.lower()

    try:
        if ext == ".lrc":
            lines = parse_lrc(lyrics_path)
        elif ext == ".qrc":
            lines = parse_qrc(lyrics_path)
        elif ext == ".krc":
            lines = parse_krc(lyrics_path)
        elif ext == ".txt":
            # Plain text, one line per lyric line
            text = path.read_text(encoding="utf-8")
            lines = [
                {"text": line.strip(), "start": 0.0, "end": 0.0, "words": []}
                for line in text.strip().split("\n")
                if line.strip()
            ]
        else:
            return None

        if lines:
            has_word_ts = any(
                len(line.get("words", [])) > 0 for line in lines
            )
            return {"lines": lines, "has_word_timestamps": has_word_ts}
    except Exception:
        pass

    return None


def _fetch_from_api(title: str, artist: str) -> dict | None:
    """Fetch lyrics from external APIs."""
    # Try LRCLIB (free, no API key needed)
    result = _fetch_lrclib(title, artist)
    if result:
        return result

    # Try Musixmatch if API key available
    from config import MUSIXMATCH_API_KEY
    if MUSIXMATCH_API_KEY:
        result = _fetch_musixmatch(title, artist, MUSIXMATCH_API_KEY)
        if result:
            return result

    return None


def _fetch_lrclib(title: str, artist: str) -> dict | None:
    """Fetch from LRCLIB (free lyrics API)."""
    import httpx

    try:
        resp = httpx.get(
            "https://lrclib.net/api/get",
            params={"track_name": title, "artist_name": artist},
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        synced = data.get("syncedLyrics")
        plain = data.get("plainLyrics")

        if synced:
            lines = parse_lrc_text(synced)
            return {"lines": lines, "has_word_timestamps": False}
        elif plain:
            lines = [
                {"text": line.strip(), "start": 0.0, "end": 0.0, "words": []}
                for line in plain.strip().split("\n")
                if line.strip()
            ]
            return {"lines": lines, "has_word_timestamps": False}
    except Exception:
        pass

    return None


def _fetch_musixmatch(title: str, artist: str, api_key: str) -> dict | None:
    """Fetch from Musixmatch API."""
    import httpx

    try:
        # Search for track
        resp = httpx.get(
            "https://api.musixmatch.com/ws/1.1/track.search",
            params={
                "q_track": title,
                "q_artist": artist,
                "apikey": api_key,
                "page_size": 1,
                "s_track_rating": "desc",
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        tracks = (
            data.get("message", {})
            .get("body", {})
            .get("track_list", [])
        )
        if not tracks:
            return None

        track_id = tracks[0]["track"]["track_id"]

        # Get lyrics
        resp = httpx.get(
            "https://api.musixmatch.com/ws/1.1/track.lyrics.get",
            params={"track_id": track_id, "apikey": api_key},
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        lyrics_body = (
            resp.json()
            .get("message", {})
            .get("body", {})
            .get("lyrics", {})
            .get("lyrics_body", "")
        )
        if lyrics_body:
            lines = [
                {"text": line.strip(), "start": 0.0, "end": 0.0, "words": []}
                for line in lyrics_body.strip().split("\n")
                if line.strip() and not line.startswith("****")
            ]
            return {"lines": lines, "has_word_timestamps": False}
    except Exception:
        pass

    return None


def _whisper_transcribe(vocals_path: str) -> dict:
    """Fallback: use Whisper to transcribe lyrics."""
    try:
        import whisper

        model = whisper.load_model("base")  # Use 'large-v3' in production
        result = model.transcribe(
            vocals_path,
            language="en",
            word_timestamps=True,
            condition_on_previous_text=False,
        )

        lines = []
        for seg in result.get("segments", []):
            words = []
            for w in seg.get("words", []):
                words.append({
                    "word": w["word"].strip(),
                    "start": w["start"],
                    "end": w["end"],
                })
            lines.append({
                "text": seg["text"].strip(),
                "start": seg["start"],
                "end": seg["end"],
                "words": words,
            })

        return {"lines": lines}
    except ImportError:
        # Whisper not installed, return empty
        return {"lines": []}


# LRC metadata prefixes to filter out (title, artist, album, composer, etc.)
_LRC_META_PREFIXES = (
    "lyrics by", "composed by", "produced by", "arranged by",
    "written by", "作词", "作曲", "编曲",
)


def _is_lrc_metadata(text: str) -> bool:
    """Check if a lyric line is actually metadata (title, credits, etc.)."""
    lower = text.lower().strip()
    # Lines starting with known metadata prefixes
    if any(lower.startswith(p) for p in _LRC_META_PREFIXES):
        return True
    # Lines that are just "SongTitle - ArtistName" pattern at timestamp 0-3s
    if " - " in text and ("(" in text or "）" in text or "·" in text):
        return True
    return False


def parse_lrc_text(lrc_text: str) -> list[dict]:
    """Parse LRC format text into lyric lines, filtering out metadata."""
    import re

    pattern = re.compile(r"\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)")
    lines = []

    for line in lrc_text.strip().split("\n"):
        # Skip LRC metadata tags like [ti:...], [ar:...], [al:...]
        if re.match(r"\[(ti|ar|al|by|offset|re|ve):", line.strip(), re.IGNORECASE):
            continue

        match = pattern.match(line.strip())
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            ms_str = match.group(3)
            ms = int(ms_str) * (10 if len(ms_str) == 2 else 1)
            start = minutes * 60 + seconds + ms / 1000
            text = match.group(4).strip()
            if text and not _is_lrc_metadata(text):
                lines.append({
                    "text": text,
                    "start": start,
                    "end": 0.0,
                    "words": [],
                })

    # Calculate end times
    for i in range(len(lines) - 1):
        lines[i]["end"] = lines[i + 1]["start"]
    if lines:
        lines[-1]["end"] = lines[-1]["start"] + 5.0

    return lines
