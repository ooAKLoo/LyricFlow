import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from api.schemas import UploadResponse, SongResult, CorrectionRequest
from config import UPLOAD_DIR, OUTPUT_DIR, MAX_UPLOAD_SIZE, ALLOWED_AUDIO_FORMATS
from workers.celery_app import process_song_pipeline

router = APIRouter(tags=["songs"])


@router.post("/songs/upload", response_model=UploadResponse)
async def upload_song(
    audio: UploadFile = File(...),
    lyrics: UploadFile | None = File(None),
    title: str | None = Form(None),
    artist: str | None = Form(None),
    dialect: str = Form("en-us"),
):
    # Validate file extension
    ext = audio.filename.rsplit(".", 1)[-1].lower() if audio.filename else ""
    if ext not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(400, f"Unsupported format: {ext}. Allowed: {ALLOWED_AUDIO_FORMATS}")

    # Generate task ID and save paths
    task_id = str(uuid.uuid4())
    task_dir = UPLOAD_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    # Save audio file
    audio_path = task_dir / f"original.{ext}"
    content = await audio.read()
    if len(content) > MAX_UPLOAD_SIZE:
        shutil.rmtree(task_dir)
        raise HTTPException(413, f"File too large. Max size: {MAX_UPLOAD_SIZE // (1024*1024)}MB")
    audio_path.write_bytes(content)

    # Save lyrics file if provided
    lyrics_path = None
    if lyrics and lyrics.filename:
        lyrics_ext = lyrics.filename.rsplit(".", 1)[-1].lower()
        if lyrics_ext in {"lrc", "qrc", "krc", "txt"}:
            lyrics_path = str(task_dir / f"lyrics.{lyrics_ext}")
            lyrics_content = await lyrics.read()
            Path(lyrics_path).write_bytes(lyrics_content)

    # Dispatch Celery pipeline
    process_song_pipeline.delay(
        task_id=task_id,
        audio_path=str(audio_path),
        lyrics_path=lyrics_path,
        title=title or "",
        artist=artist or "",
        dialect=dialect,
    )

    return UploadResponse(task_id=task_id)


@router.get("/songs/{song_id}/lyrics", response_model=SongResult)
async def get_lyrics(song_id: str):
    result_path = OUTPUT_DIR / song_id / "result.json"
    if not result_path.exists():
        raise HTTPException(404, "Song not found or still processing")

    import json
    data = json.loads(result_path.read_text(encoding="utf-8"))
    return SongResult(**data)


@router.get("/songs/{song_id}/audio")
async def get_audio(song_id: str, type: str = "vocals"):
    if type == "vocals":
        audio_path = OUTPUT_DIR / song_id / "vocals.wav"
    else:
        audio_path = OUTPUT_DIR / song_id / "original.wav"

    if not audio_path.exists():
        raise HTTPException(404, "Audio not found")

    return FileResponse(str(audio_path), media_type="audio/wav")


@router.post("/songs/{song_id}/correct")
async def submit_correction(song_id: str, correction: CorrectionRequest):
    result_path = OUTPUT_DIR / song_id / "result.json"
    if not result_path.exists():
        raise HTTPException(404, "Song not found")

    # Save correction for future model improvement
    corrections_dir = OUTPUT_DIR / song_id / "corrections"
    corrections_dir.mkdir(exist_ok=True)

    import json
    correction_file = corrections_dir / f"{uuid.uuid4()}.json"
    correction_file.write_text(
        json.dumps(correction.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {"message": "Correction saved", "id": correction_file.stem}
