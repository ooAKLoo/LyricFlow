"""Stage 6: Result Output
Generate final annotated JSON for frontend rendering.
"""

import json
import shutil
from pathlib import Path

from config import OUTPUT_DIR


def generate_output(
    task_id: str,
    detection_result: dict,
    title: str,
    artist: str,
    dialect: str,
    audio_path: str,
    preprocess_result: dict,
) -> dict:
    """Generate final output JSON and prepare audio files."""
    output_dir = OUTPUT_DIR / task_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build result structure
    lines = detection_result.get("lines", [])
    duration = preprocess_result.get("duration", 0)

    result = {
        "song_id": task_id,
        "song_title": title or "Unknown",
        "artist": artist or "Unknown",
        "dialect": dialect,
        "duration": duration,
        "lines": _clean_lines(lines),
        "audio_url": f"/api/v1/songs/{task_id}/audio?type=original",
        "vocals_url": f"/api/v1/songs/{task_id}/audio?type=vocals",
        "stats": _compute_stats(lines),
    }

    # Save result JSON
    result_path = output_dir / "result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return result


def _clean_lines(lines: list[dict]) -> list[dict]:
    """Clean and format lines for JSON output."""
    cleaned = []
    for line in lines:
        cleaned_words = []
        for word_data in line.get("words", []):
            cleaned_words.append({
                "word": word_data.get("word", ""),
                "start": round(word_data.get("start", 0), 3),
                "end": round(word_data.get("end", 0), 3),
                "ipa": word_data.get("ipa", ""),
                "phones": word_data.get("phones", []),
                "annotations": word_data.get("annotations", []),
            })

        cleaned.append({
            "text": line.get("text", ""),
            "translation": line.get("translation", ""),
            "start": round(line.get("start", 0), 3),
            "end": round(line.get("end", 0), 3),
            "words": cleaned_words,
            "is_rap": line.get("is_rap", False),
        })

    return cleaned


def _compute_stats(lines: list[dict]) -> dict:
    """Compute annotation statistics."""
    total_linking = 0
    total_weak = 0
    total_elision = 0
    total_words = 0

    for line in lines:
        for word in line.get("words", []):
            total_words += 1
            for ann in word.get("annotations", []):
                ann_type = ann.get("type", "")
                if ann_type == "linking":
                    total_linking += 1
                elif ann_type == "weak_form":
                    total_weak += 1
                elif ann_type == "elision":
                    total_elision += 1

    return {
        "total_words": total_words,
        "total_linking": total_linking,
        "total_weak_forms": total_weak,
        "total_elision": total_elision,
        "total_annotations": total_linking + total_weak + total_elision,
    }
