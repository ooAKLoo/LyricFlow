#!/usr/bin/env python3
"""LyricFlow Sidecar — NDJSON stdin/stdout protocol.

Replaces FastAPI + Celery for local desktop execution.
Receives commands via stdin, sends progress/results via stdout.

Protocol:
  → {"type":"ping"}
  ← {"type":"pong","version":"0.1.0"}

  → {"type":"analyze","audioPath":"/path/to/song.mp3","lyricsPath":null,"dialect":"en-us"}
  ← {"type":"progress","stage":"preprocessing","percent":10,"message":"..."}
  ← {"type":"progress","stage":"lyrics","percent":30,"message":"..."}
  ← ...
  ← {"type":"result","data":{...}}   // SongResult JSON

  → {"type":"quit"}
  (process exits)
"""

import json
import sys
import os
import traceback

# Add parent backend directory to path for engine imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "backend")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, SCRIPT_DIR)

VERSION = "0.1.0"


def send(msg: dict):
    """Send NDJSON message to stdout."""
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def send_progress(stage: str, percent: int, message: str = ""):
    send({"type": "progress", "stage": stage, "percent": percent, "message": message})


def handle_ping():
    send({"type": "pong", "version": VERSION})


def handle_analyze(data: dict):
    """Run the full 6-stage pipeline locally."""
    audio_path = data.get("audioPath", "")
    lyrics_path = data.get("lyricsPath")
    dialect = data.get("dialect", "en-us")
    skip_embedded = data.get("skipEmbedded", False)
    cloud_enabled = bool(data.get("cloudEnabled", False))
    requested_title = str(data.get("title") or "").strip()
    requested_artist = str(data.get("artist") or "").strip()

    if not audio_path or not os.path.exists(audio_path):
        send({"type": "error", "message": f"Audio file not found: {audio_path}"})
        return

    import uuid
    task_id = str(uuid.uuid4())[:8]

    try:
        # Stage 1: Preprocess
        send_progress("preprocessing", 5, "Separating vocals and preprocessing audio...")
        from pipeline.stage1_preprocess import preprocess_audio
        preprocess_result = preprocess_audio(task_id, audio_path)
        preprocess_result["cloud_enabled"] = cloud_enabled
        send_progress("preprocessing", 15, "Audio preprocessing complete")

        # Extract title/artist from embedded metadata
        title = requested_title or preprocess_result.get("embedded_title", "")
        artist = requested_artist or preprocess_result.get("embedded_artist", "")
        if not title:
            # Derive from filename
            basename = os.path.splitext(os.path.basename(audio_path))[0]
            if " - " in basename:
                parts = basename.split(" - ", 1)
                artist = artist or parts[0].strip()
                title = parts[1].strip()
            else:
                title = basename

        # Stage 2: Lyrics
        send_progress("lyrics", 20, "Detecting embedded lyrics / fetching lyrics...")
        from pipeline.stage2_lyrics import get_lyrics
        # If user requested skipping embedded lyrics, clear them
        if skip_embedded:
            preprocess_result["embedded_lyrics"] = None
            preprocess_result["embedded_synced_lyrics"] = None

        lyrics_result = get_lyrics(
            task_id, preprocess_result,
            lyrics_path=lyrics_path, title=title, artist=artist,
        )
        lyrics_source = lyrics_result.get("source", "unknown")
        send_progress("lyrics", 30, f"Lyrics obtained from: {lyrics_source}")

        # Stage 3: Alignment
        send_progress("aligning", 35, "Aligning words to audio timeline...")
        from pipeline.stage3_alignment import forced_alignment
        alignment_result = forced_alignment(task_id, preprocess_result, lyrics_result)
        send_progress("aligning", 50, "Word alignment complete")

        # Stage 4: Phonetics
        send_progress("phonetics", 55, "Converting to IPA phonetics...")
        from pipeline.stage4_phonetics import phonetic_transcription
        phonetics_result = phonetic_transcription(alignment_result, dialect)
        send_progress("phonetics", 65, "Phonetic transcription complete")

        # Stage 5: Detection
        send_progress("detecting", 70, "Detecting linking, weak forms, and elision...")
        from pipeline.stage5_detection import detect_phenomena
        detection_result = detect_phenomena(
            task_id, phonetics_result, preprocess_result, dialect,
        )
        send_progress("detecting", 85, "Pronunciation annotation complete")

        # Stage 6: Output
        send_progress("output", 90, "Generating final output...")
        from pipeline.stage6_output import generate_output
        result = generate_output(
            task_id=task_id,
            detection_result=detection_result,
            title=title,
            artist=artist,
            dialect=dialect,
            audio_path=audio_path,
            preprocess_result=preprocess_result,
        )
        send_progress("done", 100, "Complete")

        # Send vocals path for audio playback
        result["vocals_path"] = preprocess_result.get("vocals_path", "")
        result["original_path"] = audio_path

        send({"type": "result", "data": result})

    except Exception as e:
        send({"type": "error", "message": str(e), "traceback": traceback.format_exc()})


# ── Command dispatcher ──
HANDLERS = {
    "ping": lambda _: handle_ping(),
    "analyze": handle_analyze,
}


def main():
    try:
        from providers.volcengine_flash_asr import is_configured as asr_configured
        from providers.qwen_audio_coach import is_configured as coach_configured
        capabilities = {
            "cloudAsrConfigured": asr_configured(),
            "audioCoachConfigured": coach_configured(),
        }
    except Exception:
        capabilities = {
            "cloudAsrConfigured": False,
            "audioCoachConfigured": False,
        }
    send({"type": "ready", "capabilities": capabilities})

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            send({"type": "error", "message": f"Invalid JSON: {line}"})
            continue

        msg_type = msg.get("type", "")

        if msg_type == "quit":
            break

        handler = HANDLERS.get(msg_type)
        if handler:
            try:
                handler(msg)
            except Exception as e:
                send({"type": "error", "message": str(e), "traceback": traceback.format_exc()})
        else:
            send({"type": "error", "message": f"Unknown command: {msg_type}"})


if __name__ == "__main__":
    main()
