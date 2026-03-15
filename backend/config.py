import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
DATA_DIR = BASE_DIR / "data"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lyricflow:lyricflow@localhost:5432/lyricflow")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Audio
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_AUDIO_FORMATS = {"mp3", "wav", "flac", "aac", "ogg", "m4a"}
SAMPLE_RATE = 16000  # MFA requirement

# MFA
MFA_ACOUSTIC_MODEL = "english_mfa"
MFA_DICTIONARY = "english_mfa"
MFA_BEAM = 400
MFA_RETRY_BEAM = 1000

# API Keys (from env)
MUSIXMATCH_API_KEY = os.getenv("MUSIXMATCH_API_KEY", "")
GENIUS_API_KEY = os.getenv("GENIUS_API_KEY", "")

# Rap detection
RAP_WORD_DENSITY_THRESHOLD = 3.5  # words per second
RAP_BPM_THRESHOLD = 140
RAP_SLOWDOWN_RATE = 0.85
