"""Rap segment detection based on sustained, lexically varied fast delivery."""

import re

from config import RAP_WORD_DENSITY_THRESHOLD


def detect_rap_segments(lines: list[dict]) -> list[dict]:
    """Detect coherent rap sections instead of isolated short, dense lines."""
    for line in lines:
        line["is_rap"] = False

    metrics = [_line_metrics(line) for line in lines]
    seed_indices = [
        index for index, metric in enumerate(metrics)
        if metric["duration"] >= 1.0
        and metric["density"] > RAP_WORD_DENSITY_THRESHOLD
    ]
    if not seed_indices:
        return []

    seed_groups: list[list[int]] = []
    for index in seed_indices:
        previous_index = seed_groups[-1][-1] if seed_groups else None
        if (
            previous_index is None
            or index - previous_index > 6
            or _line_gap(lines[previous_index], lines[index]) > 8
        ):
            seed_groups.append([index])
        else:
            seed_groups[-1].append(index)

    rap_segments = []
    for seeds in seed_groups:
        if len(seeds) < 2:
            continue
        start = seeds[0]
        end = seeds[-1]
        while (
            start > 0
            and metrics[start - 1]["density"] >= 2.0
            and _line_gap(lines[start - 1], lines[start]) <= 5
        ):
            start -= 1
        while (
            end + 1 < len(lines)
            and metrics[end + 1]["density"] >= 2.0
            and _line_gap(lines[end], lines[end + 1]) <= 5
        ):
            end += 1

        section_words = [
            token
            for line in lines[start:end + 1]
            for token in _normalized_words(line.get("text", ""))
        ]
        duration = max(0.0, lines[end].get("end", 0) - lines[start].get("start", 0))
        lexical_diversity = len(set(section_words)) / max(1, len(section_words))
        if len(section_words) < 35 or duration < 8 or lexical_diversity < 0.45:
            continue

        for index in range(start, end + 1):
            lines[index]["is_rap"] = True
            rap_segments.append(lines[index])

    return rap_segments


def _line_metrics(line: dict) -> dict:
    duration = max(0.0, float(line.get("end", 0)) - float(line.get("start", 0)))
    word_count = len(line.get("words") or _normalized_words(line.get("text", "")))
    return {
        "duration": duration,
        "density": word_count / duration if duration > 0 else 0.0,
    }


def _normalized_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)*", text.lower())


def _line_gap(left: dict, right: dict) -> float:
    return max(0.0, float(right.get("start", 0)) - float(left.get("end", 0)))
