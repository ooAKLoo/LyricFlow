"""Align canonical lyric words with cloud ASR word-timing evidence."""

from __future__ import annotations

import re
from difflib import SequenceMatcher


def align_lyrics_with_asr(lyrics_result: dict, asr_result: dict, duration: float) -> dict:
    lines = lyrics_result.get("lines") or []
    canonical = []
    for line_index, line in enumerate(lines):
        for word_index, word in enumerate(_split_words(line.get("text", ""))):
            canonical.append({
                "line_index": line_index,
                "word_index": word_index,
                "word": word,
                "normalized": _normalize_word(word),
            })

    asr_words = [
        {**word, "normalized": _normalize_word(str(word.get("word", "")))}
        for word in asr_result.get("words") or []
        if _normalize_word(str(word.get("word", "")))
    ]
    mapping = _sequence_mapping(canonical, asr_words)

    matched = 0
    result_lines = []
    canonical_offset = 0
    for line_index, line in enumerate(lines):
        words = _split_words(line.get("text", ""))
        line_items = []
        for word_index, word in enumerate(words):
            global_index = canonical_offset + word_index
            asr_index = mapping.get(global_index)
            evidence = asr_words[asr_index] if asr_index is not None else None
            if evidence:
                matched += 1
            line_items.append({
                "word": word,
                "start": float(evidence.get("start", 0)) if evidence else None,
                "end": float(evidence.get("end", 0)) if evidence else None,
                "phones": [],
                "asr_word": evidence.get("word", "") if evidence else "",
                "asr_confidence": evidence.get("confidence") if evidence else None,
                "timing_source": "asr_match" if evidence else "interpolated",
            })
        canonical_offset += len(words)

        line_start, line_end = _line_bounds(line, line_items, duration)
        normalize_word_times(line_items, line_start, line_end)
        result_lines.append({
            **line,
            "start": round(line_start, 3),
            "end": round(line_end, 3),
            "words": line_items,
        })

    total = len(canonical)
    return {
        "lines": result_lines,
        "alignment_source": asr_result.get("provider", "cloud_asr"),
        "alignment_quality": round(matched / total, 3) if total else 0,
        "matched_words": matched,
        "total_words": total,
        "asr_provider": asr_result.get("provider", "cloud_asr"),
    }


def _split_words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*", text)


def _normalize_word(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower().replace("’", "'"))


def _sequence_mapping(canonical: list[dict], asr_words: list[dict]) -> dict[int, int]:
    left = [item["normalized"] for item in canonical]
    right = [item["normalized"] for item in asr_words]
    matcher = SequenceMatcher(a=left, b=right, autojunk=False)
    mapping: dict[int, int] = {}

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                mapping[i1 + offset] = j1 + offset
            continue
        if tag != "replace":
            continue

        left_block = canonical[i1:i2]
        right_block = asr_words[j1:j2]
        available = set(range(len(right_block)))
        for local_left, item in enumerate(left_block):
            best_index = None
            best_ratio = 0.0
            for local_right in available:
                ratio = SequenceMatcher(
                    a=item["normalized"],
                    b=right_block[local_right]["normalized"],
                ).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_index = local_right
            if best_index is not None and best_ratio >= 0.56:
                mapping[i1 + local_left] = j1 + best_index
                available.remove(best_index)

    return mapping


def _line_bounds(line: dict, words: list[dict], duration: float) -> tuple[float, float]:
    explicit_start = float(line.get("start", 0) or 0)
    explicit_end = float(line.get("end", 0) or 0)
    matched_starts = [float(word["start"]) for word in words if word["start"] is not None]
    matched_ends = [float(word["end"]) for word in words if word["end"] is not None]

    start = explicit_start if explicit_end > explicit_start else (min(matched_starts) if matched_starts else 0)
    end = explicit_end if explicit_end > explicit_start else (max(matched_ends) if matched_ends else start)
    if end <= start:
        end = min(duration or start + max(1.0, len(words) * 0.35), start + max(1.0, len(words) * 0.35))
    return max(0.0, start), max(start + 0.05, end)


def normalize_word_times(words: list[dict], line_start: float, line_end: float) -> None:
    """Keep ASR anchors inside a lyric line and interpolate every unmatched run."""
    if not words:
        return
    span = max(0.05, line_end - line_start)
    minimum = min(0.03, span / max(2, len(words) * 2))
    cursor = line_start
    previous_anchor_index = -1
    anchored_indices: set[int] = set()

    for index, word in enumerate(words):
        if word.get("timing_source") == "interpolated":
            continue
        try:
            raw_start = float(word.get("start"))
            raw_end = float(word.get("end"))
        except (TypeError, ValueError):
            continue
        if raw_end <= raw_start or raw_end <= line_start or raw_start >= line_end:
            word["timing_source"] = "interpolated"
            continue

        remaining_count = len(words) - index - 1
        latest_end = line_end - minimum * remaining_count
        start = max(line_start, raw_start)
        end = min(line_end, raw_end, latest_end)
        run_count = index - previous_anchor_index - 1
        earliest_start = cursor + minimum * run_count
        if start < earliest_start:
            start = earliest_start
        if end < start + minimum:
            word["timing_source"] = "interpolated"
            continue

        _assign_proportional(
            words,
            previous_anchor_index + 1,
            index,
            cursor,
            start,
        )
        word["start"] = start
        word["end"] = end
        anchored_indices.add(index)
        cursor = end
        previous_anchor_index = index

    _assign_proportional(
        words,
        previous_anchor_index + 1,
        len(words),
        cursor,
        line_end,
    )

    for index, word in enumerate(words):
        word["start"] = round(max(line_start, float(word["start"])), 3)
        word["end"] = round(min(line_end, float(word["end"])), 3)
        if index not in anchored_indices:
            word["timing_source"] = "interpolated"


def _assign_proportional(
    words: list[dict],
    start_index: int,
    end_index: int,
    start_time: float,
    end_time: float,
) -> None:
    if end_index <= start_index:
        return
    selected = words[start_index:end_index]
    weights = [max(1, len(str(word.get("word", "")))) for word in selected]
    total_weight = sum(weights)
    cursor = start_time
    available = max(0.0, end_time - start_time)
    for offset, word in enumerate(selected):
        duration = available * weights[offset] / total_weight
        word["start"] = cursor
        word["end"] = end_time if offset == len(selected) - 1 else cursor + duration
        cursor = float(word["end"])
