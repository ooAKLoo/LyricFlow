"""Stage 5: Pronunciation Phenomenon Detection
Two-layer: Rule Engine + Audio Verification
"""

from engine.rules.linking import detect_linking
from engine.rules.weak_forms import detect_weak_form
from engine.rules.elision import detect_elision
from engine.audio_verify import verify_annotation
from engine.rap_optimizer import detect_rap_segments


def detect_phenomena(
    task_id: str,
    phonetics_result: dict,
    preprocess_result: dict,
    dialect: str = "en-us",
) -> dict:
    """Detect linking, weak forms, and elision across all lyric lines."""
    lines = phonetics_result.get("lines", [])
    vocals_path = preprocess_result.get("vocals_path", "")

    # Detect rap segments
    detect_rap_segments(lines)

    for line in lines:
        words = line.get("words", [])
        line_word_count = len(words)

        for i, word_data in enumerate(words):
            annotations = []
            word = word_data.get("word", "")
            ipa = word_data.get("ipa", "")

            if not ipa:
                continue

            # 1. Weak form detection
            weak = detect_weak_form(word, i, line_word_count)
            if weak:
                annotations.append(weak)

            # 2. Linking detection (with next word)
            if i < line_word_count - 1:
                next_word = words[i + 1]
                next_ipa = next_word.get("ipa", "")
                if next_ipa:
                    linking = detect_linking(ipa, next_ipa, dialect)
                    if linking:
                        linking["target_word"] = next_word.get("word", "")
                        annotations.append(linking)

            # 3. Elision detection (with next word)
            if i < line_word_count - 1:
                next_word = words[i + 1]
                next_ipa = next_word.get("ipa", "")
                if next_ipa:
                    elisions = detect_elision(
                        word, next_word.get("word", ""),
                        ipa, next_ipa,
                    )
                    annotations.extend(elisions)

            # Audio verification (adjust confidence)
            if vocals_path and annotations:
                for ann in annotations:
                    next_start = words[i + 1]["start"] if i < line_word_count - 1 else None
                    verified = verify_annotation(
                        vocals_path,
                        word_data.get("start", 0),
                        word_data.get("end", 0),
                        next_start,
                        ann,
                    )
                    ann["confidence"] = round(
                        ann["confidence"] * verified["factor"], 2
                    )

            # Filter by confidence threshold
            word_data["annotations"] = [
                a for a in annotations if a["confidence"] > 0.5
            ]

    return {"lines": lines}
