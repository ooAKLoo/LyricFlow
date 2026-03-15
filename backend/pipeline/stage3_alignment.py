"""Stage 3: Forced Alignment using Montreal Forced Aligner (MFA)
Aligns lyrics text to audio at word and phone level.
"""

import subprocess
import shutil
from pathlib import Path

from config import OUTPUT_DIR, MFA_ACOUSTIC_MODEL, MFA_DICTIONARY, MFA_BEAM, MFA_RETRY_BEAM


def forced_alignment(task_id: str, preprocess_result: dict, lyrics_result: dict) -> dict:
    """Run MFA forced alignment. Returns aligned word/phone data."""

    # If lyrics already have word-level timestamps (from QRC/KRC or Musixmatch sync),
    # skip alignment and use existing timestamps
    if lyrics_result.get("has_word_timestamps"):
        return {
            "lines": lyrics_result["lines"],
            "alignment_source": "existing",
        }

    output_dir = Path(preprocess_result["output_dir"])
    processed_path = preprocess_result["processed_path"]

    # Prepare MFA corpus directory
    corpus_dir = output_dir / "mfa_corpus" / "song"
    corpus_dir.mkdir(parents=True, exist_ok=True)

    # Copy processed audio
    audio_dest = corpus_dir / "song.wav"
    shutil.copy2(processed_path, audio_dest)

    # Write lyrics text file (one line per lyric line)
    lyrics_text = "\n".join(
        line["text"] for line in lyrics_result["lines"] if line.get("text")
    )
    txt_dest = corpus_dir / "song.txt"
    txt_dest.write_text(lyrics_text, encoding="utf-8")

    # Run MFA alignment
    mfa_output = output_dir / "mfa_output"
    mfa_output.mkdir(exist_ok=True)

    try:
        subprocess.run(
            [
                "mfa", "align",
                str(corpus_dir.parent),
                MFA_DICTIONARY,
                MFA_ACOUSTIC_MODEL,
                str(mfa_output),
                "--clean",
                "--beam", str(MFA_BEAM),
                "--retry_beam", str(MFA_RETRY_BEAM),
                "--output_format", "short_textgrid",
            ],
            check=True,
            capture_output=True,
            timeout=300,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # MFA not available or failed — fall back to simple estimation
        return _estimate_alignment(lyrics_result, preprocess_result)

    # Parse TextGrid output
    textgrid_path = mfa_output / "song.TextGrid"
    if textgrid_path.exists():
        aligned = _parse_textgrid(textgrid_path, lyrics_result)
        return {
            "lines": aligned,
            "alignment_source": "mfa",
        }

    # Fallback
    return _estimate_alignment(lyrics_result, preprocess_result)


def _parse_textgrid(textgrid_path: Path, lyrics_result: dict) -> list[dict]:
    """Parse Praat TextGrid file into aligned word data."""
    try:
        import textgrid

        tg = textgrid.TextGrid.fromFile(str(textgrid_path))
        words_tier = tg.getFirst("words")
        phones_tier = tg.getFirst("phones")

        aligned_words = []
        for interval in words_tier:
            if interval.mark and interval.mark.strip():
                # Find phones belonging to this word
                phones = [
                    {"phone": p.mark, "start": p.minTime, "end": p.maxTime}
                    for p in phones_tier
                    if p.minTime >= interval.minTime
                    and p.maxTime <= interval.maxTime
                    and p.mark and p.mark.strip()
                ]
                aligned_words.append({
                    "word": interval.mark,
                    "start": interval.minTime,
                    "end": interval.maxTime,
                    "phones": phones,
                })

        # Map aligned words back to lyric lines
        return _map_words_to_lines(aligned_words, lyrics_result["lines"])

    except ImportError:
        return _estimate_alignment(lyrics_result, {"duration": 0})["lines"]


def _map_words_to_lines(aligned_words: list[dict], original_lines: list[dict]) -> list[dict]:
    """Map individually aligned words back to their original lyric lines."""
    result_lines = []
    word_idx = 0

    for line in original_lines:
        text = line.get("text", "")
        line_word_count = len(text.split())
        line_words = []

        for _ in range(line_word_count):
            if word_idx < len(aligned_words):
                line_words.append(aligned_words[word_idx])
                word_idx += 1

        line_start = line_words[0]["start"] if line_words else line.get("start", 0)
        line_end = line_words[-1]["end"] if line_words else line.get("end", 0)

        result_lines.append({
            "text": text,
            "start": line_start,
            "end": line_end,
            "words": line_words,
        })

    return result_lines


def _estimate_alignment(lyrics_result: dict, preprocess_result: dict) -> dict:
    """Simple proportional alignment when MFA is unavailable."""
    lines = lyrics_result.get("lines", [])
    if not lines:
        return {"lines": [], "alignment_source": "estimated"}

    duration = preprocess_result.get("duration", 180.0)

    # If lines have timestamps, use those for word-level estimation
    has_line_timestamps = any(line.get("start", 0) > 0 for line in lines)

    result_lines = []
    for line in lines:
        text = line.get("text", "")
        words_in_line = text.split()
        if not words_in_line:
            result_lines.append(line)
            continue

        line_start = line.get("start", 0.0)
        line_end = line.get("end", 0.0)

        if not has_line_timestamps or line_end <= line_start:
            # Distribute evenly across total duration
            total_words = sum(len(l.get("text", "").split()) for l in lines)
            if total_words > 0:
                word_duration = duration / total_words
            else:
                word_duration = 0.5
            line_start = sum(
                len(l.get("text", "").split()) * word_duration
                for l in lines[:lines.index(line)]
            )
            line_end = line_start + len(words_in_line) * word_duration

        # Distribute time across words proportionally by character count
        total_chars = sum(len(w) for w in words_in_line)
        if total_chars == 0:
            total_chars = 1

        current_time = line_start
        line_words = []
        for word in words_in_line:
            word_duration = (line_end - line_start) * (len(word) / total_chars)
            line_words.append({
                "word": word,
                "start": round(current_time, 3),
                "end": round(current_time + word_duration, 3),
                "phones": [],
            })
            current_time += word_duration

        result_lines.append({
            "text": text,
            "start": line_start,
            "end": line_end,
            "words": line_words,
        })

    return {"lines": result_lines, "alignment_source": "estimated"}
