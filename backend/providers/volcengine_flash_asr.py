"""Volcengine flash ASR provider with word-level timing evidence."""

from __future__ import annotations

import base64
import time
import uuid
from pathlib import Path

import httpx

from config import (
    LYRICFLOW_CLOUD_TIMEOUT_SECONDS,
    VOLC_ACCESS_TOKEN,
    VOLC_API_KEY,
    VOLC_APP_ID,
    VOLC_FLASH_ASR_RESOURCE_ID,
    VOLC_FLASH_ASR_URL,
    VOLC_STANDARD_ASR_POLL_SECONDS,
    VOLC_STANDARD_ASR_QUERY_URL,
    VOLC_STANDARD_ASR_RESOURCE_ID,
    VOLC_STANDARD_ASR_SUBMIT_URL,
)


class VolcengineAsrError(RuntimeError):
    """Raised when the configured ASR provider cannot return trustworthy data."""

    def __init__(self, message: str, status_code: str = ""):
        super().__init__(message)
        self.status_code = status_code


def is_configured() -> bool:
    return bool(VOLC_API_KEY or (VOLC_APP_ID and VOLC_ACCESS_TOKEN))


def transcribe_file(audio_path: str) -> dict:
    """Transcribe one local audio file and normalize its word timing response."""
    if not is_configured():
        raise VolcengineAsrError("火山极速 ASR 未配置")

    path = Path(audio_path)
    if not path.is_file():
        raise VolcengineAsrError(f"待识别音频不存在：{path.name}")
    if path.stat().st_size > 100 * 1024 * 1024:
        raise VolcengineAsrError("待识别音频超过火山极速 ASR 的 100MB 限制")

    encoded_audio = base64.b64encode(path.read_bytes()).decode("ascii")
    payload = {
        "user": {"uid": "lyricflow"},
        "audio": {
            "data": encoded_audio,
            "format": _audio_format(path),
            "rate": 16000,
            "channel": 1,
        },
        "request": {
            "model_name": "bigmodel",
            "language": "en-US",
            "enable_itn": True,
            "enable_punc": True,
            "enable_ddc": True,
            "show_utterances": True,
        },
    }

    try:
        return _transcribe_flash(payload)
    except VolcengineAsrError as exc:
        if exc.status_code != "45000030":
            raise
    return _transcribe_standard(payload)


def _transcribe_flash(payload: dict) -> dict:
    headers = _auth_headers(
        request_id=str(uuid.uuid4()),
        resource_id=VOLC_FLASH_ASR_RESOURCE_ID,
        sequence=True,
    )

    try:
        response = httpx.post(
            VOLC_FLASH_ASR_URL,
            headers=headers,
            json=payload,
            timeout=LYRICFLOW_CLOUD_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise VolcengineAsrError("火山极速 ASR 网络请求失败") from exc

    _ensure_success(response, "火山极速 ASR")
    normalized = _normalize_response(_response_json(response), "volcengine_flash_asr")
    if not normalized["words"]:
        raise VolcengineAsrError("火山极速 ASR 未返回逐词时间戳")
    return normalized


def _transcribe_standard(payload: dict) -> dict:
    task_id = str(uuid.uuid4())
    submit_headers = _auth_headers(
        request_id=task_id,
        resource_id=VOLC_STANDARD_ASR_RESOURCE_ID,
        sequence=True,
    )
    try:
        response = httpx.post(
            VOLC_STANDARD_ASR_SUBMIT_URL,
            headers=submit_headers,
            json=payload,
            timeout=LYRICFLOW_CLOUD_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise VolcengineAsrError("火山标准 ASR 提交请求失败") from exc

    _ensure_success(response, "火山标准 ASR 提交")
    deadline = time.monotonic() + LYRICFLOW_CLOUD_TIMEOUT_SECONDS
    query_headers = _auth_headers(
        request_id=task_id,
        resource_id=VOLC_STANDARD_ASR_RESOURCE_ID,
    )

    while time.monotonic() < deadline:
        time.sleep(VOLC_STANDARD_ASR_POLL_SECONDS)
        try:
            response = httpx.post(
                VOLC_STANDARD_ASR_QUERY_URL,
                headers=query_headers,
                json={},
                timeout=min(60, LYRICFLOW_CLOUD_TIMEOUT_SECONDS),
            )
        except httpx.HTTPError as exc:
            raise VolcengineAsrError("火山标准 ASR 查询请求失败") from exc

        status = response.headers.get("X-Api-Status-Code", "")
        if status in {"20000001", "20000002"}:
            continue
        _ensure_success(response, "火山标准 ASR 查询")
        normalized = _normalize_response(
            _response_json(response),
            "volcengine_standard_asr",
        )
        if not normalized["words"]:
            raise VolcengineAsrError("火山标准 ASR 未返回逐词时间戳")
        return normalized

    raise VolcengineAsrError("火山标准 ASR 查询超时")


def _auth_headers(request_id: str, resource_id: str, sequence: bool = False) -> dict:
    headers = {
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": request_id,
    }
    if sequence:
        headers["X-Api-Sequence"] = "-1"
    if VOLC_API_KEY:
        headers["X-Api-Key"] = VOLC_API_KEY
    else:
        headers["X-Api-App-Key"] = VOLC_APP_ID
        headers["X-Api-Access-Key"] = VOLC_ACCESS_TOKEN
    return headers


def _ensure_success(response: httpx.Response, label: str) -> None:
    status = response.headers.get("X-Api-Status-Code", "")
    if response.is_success and (not status or status == "20000000"):
        return
    message = response.headers.get("X-Api-Message", "服务拒绝了请求")
    safe_status = status or str(response.status_code)
    raise VolcengineAsrError(f"{label} 失败（{safe_status}）：{message}", safe_status)


def _response_json(response: httpx.Response) -> dict:
    try:
        value = response.json()
    except ValueError as exc:
        raise VolcengineAsrError("火山 ASR 返回了无效 JSON") from exc
    if not isinstance(value, dict):
        raise VolcengineAsrError("火山 ASR 返回格式不正确")
    return value


def _audio_format(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return "ogg" if suffix in {"opus", "ogg_opus"} else (suffix or "wav")


def _normalize_response(raw: dict, provider: str = "volcengine_flash_asr") -> dict:
    raw_result = raw.get("result") or {}
    results = raw_result if isinstance(raw_result, list) else [raw_result]
    utterances = []
    flat_words = []
    texts = []

    for result in results:
        if not isinstance(result, dict):
            continue
        result_text = str(result.get("text") or "").strip()
        if result_text:
            texts.append(result_text)
        for raw_utterance in result.get("utterances") or []:
            words = []
            for raw_word in raw_utterance.get("words") or []:
                text = str(raw_word.get("text") or "").strip()
                if not text:
                    continue
                word = {
                    "word": text,
                    "start": _milliseconds_to_seconds(raw_word.get("start_time")),
                    "end": _milliseconds_to_seconds(raw_word.get("end_time")),
                    "confidence": _normalize_confidence(raw_word.get("confidence")),
                }
                words.append(word)
                flat_words.append(word)

            utterances.append({
                "text": str(raw_utterance.get("text") or "").strip(),
                "start": _milliseconds_to_seconds(raw_utterance.get("start_time")),
                "end": _milliseconds_to_seconds(raw_utterance.get("end_time")),
                "words": words,
            })

    return {
        "provider": provider,
        "text": "\n".join(texts),
        "duration": _milliseconds_to_seconds(
            (raw.get("audio_info") or {}).get("duration")
        ),
        "utterances": utterances,
        "words": flat_words,
    }


def _milliseconds_to_seconds(value: object) -> float:
    try:
        return round(float(value or 0) / 1000, 3)
    except (TypeError, ValueError):
        return 0.0


def _normalize_confidence(value: object) -> float | None:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return None
    if confidence <= 0:
        return None
    if confidence > 1:
        confidence /= 100
    return round(min(1.0, confidence), 3)
