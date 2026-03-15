"""Rap segment detection and optimization."""

from config import RAP_WORD_DENSITY_THRESHOLD


def detect_rap_segments(lines: list[dict]) -> list[dict]:
    """Detect rap segments based on word density (words per second)."""
    rap_segments = []

    for line in lines:
        start = line.get("start", 0)
        end = line.get("end", 0)
        duration = end - start

        if duration <= 0:
            continue

        words = line.get("words", [])
        if not words:
            word_count = len(line.get("text", "").split())
        else:
            word_count = len(words)

        word_density = word_count / duration

        if word_density > RAP_WORD_DENSITY_THRESHOLD:
            line["is_rap"] = True
            rap_segments.append(line)
        else:
            line["is_rap"] = False

    return rap_segments
