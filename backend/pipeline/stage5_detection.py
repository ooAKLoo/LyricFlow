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
    """Detect candidates locally, then verify rap lines with an audio model."""
    lines = phonetics_result.get("lines", [])
    vocals_path = preprocess_result.get("vocals_path", "")
    cloud_warnings = list(phonetics_result.get("cloud_warnings") or [])

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

    coaching_provider = "rule_engine"
    if preprocess_result.get("cloud_enabled"):
        try:
            from providers.qwen_audio_coach import analyze_line, is_configured

            if not is_configured():
                cloud_warnings.append("已选择云分析，但千问音频教练未配置，语流解释已降级")
            else:
                coached_lines = 0
                for line_index, line in enumerate(lines):
                    if not line.get("is_rap") or not line.get("words"):
                        continue
                    try:
                        coaching = analyze_line(vocals_path, line, dialect)
                        _merge_audio_coaching(line, coaching)
                        coached_lines += 1
                    except Exception as exc:
                        cloud_warnings.append(
                            f"Rap 行 {line_index + 1} 音频复核失败：{exc}"
                        )
                if coached_lines:
                    coaching_provider = "qwen_audio"
        except Exception as exc:
            cloud_warnings.append(f"音频教练初始化失败，已降级：{exc}")

    return {
        **phonetics_result,
        "lines": lines,
        "coaching_provider": coaching_provider,
        "cloud_warnings": cloud_warnings,
    }


def _merge_audio_coaching(line: dict, coaching: dict) -> None:
    line["performed_text"] = coaching.get("performed_text", "")
    line["coach_summary_zh"] = coaching.get("coach_summary_zh", "")
    line["difficulty"] = coaching.get("difficulty", 1)
    line["beat_hint"] = coaching.get("beat_hint", "")
    line["analysis_source"] = coaching.get("provider", "qwen_audio")

    words = line.get("words", [])
    for cue in coaching.get("cues") or []:
        word_index = cue.get("word_index", -1)
        if not isinstance(word_index, int) or not (0 <= word_index < len(words)):
            continue
        annotation = {
            "type": cue.get("type", ""),
            "subtype": "audio_verified",
            "symbol": _cue_symbol(cue.get("type", "")),
            "target_word": words[cue.get("end_word_index", word_index)].get("word", ""),
            "explanation_zh": cue.get("explanation_zh", ""),
            "confidence": cue.get("confidence", 0),
            "source": cue.get("source", ""),
            "heard_as": cue.get("heard_as", ""),
            "mouth_tip_zh": cue.get("mouth_tip_zh", ""),
            "rhythm_tip_zh": cue.get("rhythm_tip_zh", ""),
            "end_word_index": cue.get("end_word_index", word_index),
            "evidence": "audio_model",
        }
        existing = words[word_index].setdefault("annotations", [])
        existing[:] = [
            item for item in existing
            if item.get("type") != annotation["type"]
        ]
        existing.append(annotation)


def _cue_symbol(cue_type: str) -> str:
    return {
        "linking": "‿",
        "weak_form": "( )",
        "elision": "◌̸",
        "flap": "ɾ",
        "assimilation": "→",
        "stress": "•",
        "breath": "/",
    }.get(cue_type, "•")
