"""Qwen Omni provider for evidence-bound, line-level pronunciation coaching."""

from __future__ import annotations

import base64
import io
import json
import re
import wave
from pathlib import Path

import httpx

from config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    LYRICFLOW_AUDIO_COACH_MODEL,
    LYRICFLOW_CLOUD_TIMEOUT_SECONDS,
)


SUPPORTED_CUE_TYPES = {
    "linking",
    "weak_form",
    "elision",
    "flap",
    "assimilation",
    "stress",
    "breath",
}


class QwenAudioCoachError(RuntimeError):
    """Raised when Qwen cannot produce a valid, evidence-bound coaching result."""


def is_configured() -> bool:
    return bool(DASHSCOPE_API_KEY and DASHSCOPE_BASE_URL and LYRICFLOW_AUDIO_COACH_MODEL)


def analyze_line(audio_path: str, line: dict, dialect: str = "en-us") -> dict:
    """Analyze the audible realization of one short lyric line."""
    if not is_configured():
        raise QwenAudioCoachError("千问音频教练未配置")

    start = max(0.0, float(line.get("start", 0)))
    end = max(start, float(line.get("end", start)))
    if end - start <= 0:
        raise QwenAudioCoachError("歌词行没有有效的音频时间范围")

    wav_bytes = _extract_wav_segment(audio_path, start, min(end, start + 20), 0.18)
    audio_data = base64.b64encode(wav_bytes).decode("ascii")
    indexed_words = [
        {
            "index": index,
            "word": word.get("word", ""),
            "ipa": word.get("ipa", ""),
            "start": word.get("start", 0),
            "end": word.get("end", 0),
            "asr_word": word.get("asr_word", ""),
        }
        for index, word in enumerate(line.get("words", []))
    ]

    prompt = f"""
你是一位严谨的英语 Rap 语音教练。请只根据所附音频中能听到的证据，分析这一句的真实唱法。

方言目标：{dialect}
书面歌词：{line.get('text', '')}
逐词证据：{json.dumps(indexed_words, ensure_ascii=False)}

任务：
1. 给出紧凑的 performed_text，用 ‿ 表示连读，用 ( ) 表示弱化或可能吞掉的音，用大写表示真正承重的词，用 / 表示换气或节奏分组。
2. 只标注音频中有把握听到的 linking、weak_form、elision、flap、assimilation、stress、breath。
3. 每条 cue 必须绑定有效的 word_index；跨词现象可提供 end_word_index。
4. confidence 低于 0.60 的现象不要输出。不能仅凭英语规则断言原唱确实发生了某现象。
5. 中文解释要能直接指导学习者的口型、气流和落拍，不写空泛鼓励。

只返回一个 JSON 对象，不要 Markdown：
{{
  "performed_text": "string",
  "coach_summary_zh": "string",
  "difficulty": 1,
  "beat_hint": "string",
  "cues": [
    {{
      "word_index": 0,
      "end_word_index": 0,
      "type": "linking",
      "source": "string",
      "heard_as": "string",
      "confidence": 0.8,
      "explanation_zh": "string",
      "mouth_tip_zh": "string",
      "rhythm_tip_zh": "string"
    }}
  ]
}}
""".strip()

    payload = {
        "model": LYRICFLOW_AUDIO_COACH_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": f"data:audio/wav;base64,{audio_data}",
                        "format": "wav",
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
        "modalities": ["text"],
        "temperature": 0.1,
    }

    try:
        response = httpx.post(
            f"{DASHSCOPE_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=LYRICFLOW_CLOUD_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise QwenAudioCoachError("千问音频教练网络请求失败") from exc

    try:
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]
        result = _parse_json_content(content)
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise QwenAudioCoachError("千问音频教练返回了无效结果") from exc

    return _validate_result(result, len(indexed_words))


def _extract_wav_segment(
    audio_path: str,
    start_seconds: float,
    end_seconds: float,
    padding_seconds: float,
) -> bytes:
    path = Path(audio_path)
    if not path.is_file():
        raise QwenAudioCoachError(f"待分析音频不存在：{path.name}")

    try:
        with wave.open(str(path), "rb") as source:
            sample_rate = source.getframerate()
            start_frame = max(0, int((start_seconds - padding_seconds) * sample_rate))
            end_frame = min(
                source.getnframes(),
                int((end_seconds + padding_seconds) * sample_rate),
            )
            source.setpos(start_frame)
            frames = source.readframes(max(0, end_frame - start_frame))

            output = io.BytesIO()
            with wave.open(output, "wb") as target:
                target.setnchannels(source.getnchannels())
                target.setsampwidth(source.getsampwidth())
                target.setframerate(sample_rate)
                target.writeframes(frames)
            return output.getvalue()
    except (wave.Error, OSError) as exc:
        raise QwenAudioCoachError("千问音频教练目前只能分析有效 WAV 人声音频") from exc


def _parse_json_content(content: object) -> dict:
    if isinstance(content, list):
        content = "".join(
            str(part.get("text", ""))
            for part in content
            if isinstance(part, dict)
        )
    if not isinstance(content, str):
        raise ValueError("response content is not text")
    stripped = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL)
    if fenced:
        stripped = fenced.group(1)
    return json.loads(stripped)


def _validate_result(result: dict, word_count: int) -> dict:
    if not isinstance(result, dict):
        raise QwenAudioCoachError("千问音频教练结果不是对象")

    cues = []
    for raw in result.get("cues") or []:
        if not isinstance(raw, dict) or raw.get("type") not in SUPPORTED_CUE_TYPES:
            continue
        try:
            word_index = int(raw.get("word_index"))
            end_word_index = int(raw.get("end_word_index", word_index))
            confidence = float(raw.get("confidence", 0))
        except (TypeError, ValueError):
            continue
        if not (0 <= word_index < word_count) or not (word_index <= end_word_index < word_count):
            continue
        if confidence < 0.6:
            continue
        cues.append({
            "word_index": word_index,
            "end_word_index": end_word_index,
            "type": raw["type"],
            "source": str(raw.get("source") or "").strip(),
            "heard_as": str(raw.get("heard_as") or "").strip(),
            "confidence": round(min(1.0, confidence), 2),
            "explanation_zh": str(raw.get("explanation_zh") or "").strip(),
            "mouth_tip_zh": str(raw.get("mouth_tip_zh") or "").strip(),
            "rhythm_tip_zh": str(raw.get("rhythm_tip_zh") or "").strip(),
        })

    try:
        difficulty = int(result.get("difficulty", 1))
    except (TypeError, ValueError):
        difficulty = 1

    return {
        "performed_text": str(result.get("performed_text") or "").strip(),
        "coach_summary_zh": str(result.get("coach_summary_zh") or "").strip(),
        "difficulty": max(1, min(5, difficulty)),
        "beat_hint": str(result.get("beat_hint") or "").strip(),
        "cues": cues,
        "provider": f"qwen_audio:{LYRICFLOW_AUDIO_COACH_MODEL}",
    }
