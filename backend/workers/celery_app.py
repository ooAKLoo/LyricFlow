from celery import Celery

from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery_app = Celery(
    "lyricflow",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, name="process_song_pipeline")
def process_song_pipeline(
    self,
    task_id: str,
    audio_path: str,
    lyrics_path: str | None,
    title: str,
    artist: str,
    dialect: str,
):
    """Main pipeline: runs all 6 stages sequentially."""
    from pipeline.stage1_preprocess import preprocess_audio
    from pipeline.stage2_lyrics import get_lyrics
    from pipeline.stage3_alignment import forced_alignment
    from pipeline.stage4_phonetics import phonetic_transcription
    from pipeline.stage5_detection import detect_phenomena
    from pipeline.stage6_output import generate_output

    try:
        # Stage 1: Audio preprocessing
        self.update_state(
            state="PROGRESS",
            meta={"stage": "preprocessing", "message": "Separating vocals and preprocessing audio..."},
        )
        preprocess_result = preprocess_audio(task_id, audio_path)

        # Stage 2: Lyrics fetching
        self.update_state(
            state="PROGRESS",
            meta={"stage": "lyrics_fetching", "message": "Detecting embedded lyrics / fetching lyrics..."},
        )
        lyrics_result = get_lyrics(
            task_id,
            preprocess_result,
            lyrics_path=lyrics_path,
            title=title,
            artist=artist,
        )

        # Stage 3: Forced alignment
        self.update_state(
            state="PROGRESS",
            meta={"stage": "aligning", "message": "Aligning words to audio..."},
        )
        alignment_result = forced_alignment(task_id, preprocess_result, lyrics_result)

        # Stage 4: Phonetic transcription
        self.update_state(
            state="PROGRESS",
            meta={"stage": "phonetics", "message": "Converting to IPA phonetics..."},
        )
        phonetics_result = phonetic_transcription(alignment_result, dialect)

        # Stage 5: Phenomenon detection
        self.update_state(
            state="PROGRESS",
            meta={"stage": "detecting", "message": "Detecting linking, weak forms, and elision..."},
        )
        detection_result = detect_phenomena(
            task_id, phonetics_result, preprocess_result, dialect
        )

        # Stage 6: Generate output
        self.update_state(
            state="PROGRESS",
            meta={"stage": "output", "message": "Generating final output..."},
        )
        # Use embedded metadata as fallback for title/artist
        final_title = title or preprocess_result.get("embedded_title", "")
        final_artist = artist or preprocess_result.get("embedded_artist", "")

        output = generate_output(
            task_id=task_id,
            detection_result=detection_result,
            title=final_title,
            artist=final_artist,
            dialect=dialect,
            audio_path=audio_path,
            preprocess_result=preprocess_result,
        )

        return {"song_id": task_id, "status": "completed"}

    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)},
        )
        raise
