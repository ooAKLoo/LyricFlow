"""Stage 1: Audio Upload & Preprocessing
- Format conversion
- Vocal isolation (Spleeter)
- Noise reduction & normalization
- Rap tempo detection & slowdown
"""

import subprocess
from pathlib import Path

import librosa
import numpy as np
import noisereduce as nr
import soundfile as sf

from config import UPLOAD_DIR, OUTPUT_DIR, SAMPLE_RATE, RAP_BPM_THRESHOLD


def preprocess_audio(task_id: str, audio_path: str) -> dict:
    """Main preprocessing pipeline. Returns paths and metadata."""
    task_dir = UPLOAD_DIR / task_id
    output_dir = OUTPUT_DIR / task_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Convert to WAV if needed
    wav_path = _convert_to_wav(audio_path, output_dir / "original.wav")

    # Step 2: Vocal isolation
    prepared_vocals = _find_prepared_vocals(audio_path)
    if prepared_vocals:
        import shutil
        vocals_path = output_dir / "vocals.wav"
        shutil.copy2(prepared_vocals, vocals_path)
    else:
        vocals_path = _separate_vocals(wav_path, output_dir)

    # Step 3: Preprocess vocals (resample, denoise, normalize)
    processed_path = output_dir / "vocals_processed.wav"
    metadata = _preprocess_vocals(vocals_path, processed_path)

    # Step 4: Extract embedded lyrics & metadata from original audio
    embedded = _extract_embedded_data(audio_path)

    return {
        "task_id": task_id,
        "original_audio": audio_path,
        "original_wav": str(wav_path),
        "vocals_path": str(vocals_path),
        "processed_path": str(processed_path),
        "output_dir": str(output_dir),
        "sample_rate": SAMPLE_RATE,
        "duration": metadata["duration"],
        "is_fast_tempo": metadata["is_fast_tempo"],
        "bpm": metadata["bpm"],
        "embedded_lyrics": embedded.get("lyrics"),
        "embedded_synced_lyrics": embedded.get("synced_lyrics"),
        "embedded_title": embedded.get("title", ""),
        "embedded_artist": embedded.get("artist", ""),
    }


def _convert_to_wav(audio_path: str, output_path: Path) -> Path:
    """Convert any supported format to WAV using ffmpeg."""
    if Path(audio_path).suffix.lower() == ".wav":
        # Copy as-is
        import shutil
        shutil.copy2(audio_path, output_path)
        return output_path

    subprocess.run(
        [
            "ffmpeg", "-i", str(audio_path),
            "-acodec", "pcm_s16le",
            "-ar", str(SAMPLE_RATE),
            "-ac", "1",
            "-y", str(output_path),
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def _find_prepared_vocals(audio_path: str) -> Path | None:
    """Reuse an explicit sibling vocals.wav instead of separating the mix again."""
    source = Path(audio_path)
    if source.name.lower() != "original.wav":
        return None
    candidate = source.with_name("vocals.wav")
    if candidate.is_file() and candidate.resolve() != source.resolve():
        return candidate
    return None


def _separate_vocals(wav_path: Path, output_dir: Path) -> Path:
    """Separate vocals using Spleeter."""
    vocals_path = output_dir / "vocals.wav"

    try:
        from spleeter.separator import Separator
        separator = Separator("spleeter:2stems")
        separator.separate_to_file(
            str(wav_path),
            str(output_dir / "spleeter_out"),
            codec="wav",
            bitrate="320k",
        )
        # Spleeter outputs to subdirectory
        spleeter_vocals = output_dir / "spleeter_out" / Path(wav_path).stem / "vocals.wav"
        if spleeter_vocals.exists():
            import shutil
            shutil.move(str(spleeter_vocals), str(vocals_path))
            return vocals_path
    except ImportError:
        pass

    # Fallback: use original audio if spleeter not available
    import shutil
    shutil.copy2(str(wav_path), str(vocals_path))
    return vocals_path


def _preprocess_vocals(vocals_path: Path, output_path: Path) -> dict:
    """Resample to 16kHz mono, denoise, normalize. Returns metadata."""
    # Load and resample
    y, sr = librosa.load(str(vocals_path), sr=SAMPLE_RATE, mono=True)

    # Noise reduction
    y_clean = nr.reduce_noise(y=y, sr=sr, prop_decrease=0.8)

    # Normalize
    y_norm = librosa.util.normalize(y_clean)

    # Tempo detection
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        tempo = librosa.beat.tempo(y=y_norm, sr=sr)[0]
    is_fast = float(tempo) > RAP_BPM_THRESHOLD

    # Keep analysis audio on the original clock. Slow practice playback belongs
    # in the player; stretching here invalidates every downstream timestamp.
    sf.write(str(output_path), y_norm, sr)

    duration = float(len(y)) / sr  # Use original length for duration

    return {
        "duration": duration,
        "bpm": float(tempo),
        "is_fast_tempo": is_fast,
    }


def _extract_embedded_data(audio_path: str) -> dict:
    """Extract embedded lyrics and metadata from audio file using mutagen.

    Supports:
    - MP3: ID3 USLT (unsynchronized), SYLT (synchronized) tags
    - FLAC: Vorbis comments (LYRICS, UNSYNCEDLYRICS)
    - M4A/AAC: MP4 ©lyr tag
    - OGG: Vorbis comments
    """
    from pathlib import Path

    result: dict = {}
    ext = Path(audio_path).suffix.lower()

    try:
        import mutagen

        audio = mutagen.File(audio_path)
        if audio is None:
            return result

        # --- MP3 (ID3) ---
        if ext in (".mp3",):
            from mutagen.id3 import ID3

            tags = ID3(audio_path)

            # SYLT: synchronized lyrics (word/line-level timestamps)
            for key in tags:
                if key.startswith("SYLT"):
                    frame = tags[key]
                    # frame.text is list of (text, timestamp_ms) tuples
                    if hasattr(frame, "text") and frame.text:
                        synced_lines = []
                        for syllable, ts_ms in frame.text:
                            text = syllable.strip("\x00").strip()
                            if text:
                                synced_lines.append({
                                    "text": text,
                                    "timestamp_ms": ts_ms,
                                })
                        if synced_lines:
                            result["synced_lyrics"] = synced_lines

            # USLT: unsynchronized lyrics (plain text, may contain LRC timestamps)
            for key in tags:
                if key.startswith("USLT"):
                    frame = tags[key]
                    text = str(frame)
                    if text.strip():
                        result["lyrics"] = text.strip()
                    break

            # Title / Artist
            result["title"] = str(tags.get("TIT2", ""))
            result["artist"] = str(tags.get("TPE1", ""))

        # --- FLAC ---
        elif ext in (".flac",):
            from mutagen.flac import FLAC

            flac = FLAC(audio_path)
            tags = flac.tags or {}

            for tag_key in ("LYRICS", "UNSYNCEDLYRICS", "lyrics", "unsyncedlyrics"):
                vals = tags.get(tag_key)
                if vals:
                    text = vals[0] if isinstance(vals, list) else str(vals)
                    if text.strip():
                        result["lyrics"] = text.strip()
                        break

            result["title"] = (tags.get("TITLE") or tags.get("title") or [""])[0]
            result["artist"] = (tags.get("ARTIST") or tags.get("artist") or [""])[0]

        # --- M4A / AAC (MP4 container) ---
        elif ext in (".m4a", ".aac", ".mp4"):
            from mutagen.mp4 import MP4

            mp4 = MP4(audio_path)
            tags = mp4.tags or {}

            lyrics_val = tags.get("\xa9lyr")
            if lyrics_val:
                text = lyrics_val[0] if isinstance(lyrics_val, list) else str(lyrics_val)
                if text.strip():
                    result["lyrics"] = text.strip()

            title_val = tags.get("\xa9nam")
            artist_val = tags.get("\xa9ART")
            result["title"] = (title_val[0] if title_val else "")
            result["artist"] = (artist_val[0] if artist_val else "")

        # --- OGG Vorbis ---
        elif ext in (".ogg",):
            from mutagen.oggvorbis import OggVorbis

            ogg = OggVorbis(audio_path)
            tags = ogg.tags or {}

            for tag_key in ("LYRICS", "UNSYNCEDLYRICS", "lyrics"):
                vals = tags.get(tag_key)
                if vals:
                    text = vals[0] if isinstance(vals, list) else str(vals)
                    if text.strip():
                        result["lyrics"] = text.strip()
                        break

            result["title"] = (tags.get("TITLE") or tags.get("title") or [""])[0]
            result["artist"] = (tags.get("ARTIST") or tags.get("artist") or [""])[0]

    except Exception:
        pass

    return result
