import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
_runtime_dir_value = os.getenv("LYRICFLOW_RUNTIME_DIR", "").strip()
RUNTIME_DIR = Path(_runtime_dir_value).expanduser() if _runtime_dir_value else BASE_DIR
UPLOAD_DIR = RUNTIME_DIR / "uploads"
OUTPUT_DIR = RUNTIME_DIR / "outputs"
DATA_DIR = BASE_DIR / "data"


def _load_env_file(path: Path) -> None:
    """Load a local env file without overriding values supplied by the caller."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value


# Load the small local/runtime bootstrap first. It may point at an existing
# secret store through LYRICFLOW_ENV_FILE, so credentials do not need copying.
_load_env_file(PROJECT_DIR / ".env")
if RUNTIME_DIR != BASE_DIR:
    _load_env_file(RUNTIME_DIR / ".env")
_explicit_env = os.getenv("LYRICFLOW_ENV_FILE", "").strip()
if _explicit_env:
    _load_env_file(Path(_explicit_env).expanduser())

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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

# Cloud intelligence providers. Audio leaves the device only when the user
# explicitly enables cloud analysis for a run; configuration alone is not consent.
VOLC_API_KEY = os.getenv("VOLC_API_KEY", "")
VOLC_APP_ID = os.getenv("VOLC_APP_ID", "")
VOLC_ACCESS_TOKEN = os.getenv("VOLC_ACCESS_TOKEN", "")
VOLC_FLASH_ASR_URL = os.getenv(
    "VOLC_FLASH_ASR_URL",
    "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash",
)
VOLC_FLASH_ASR_RESOURCE_ID = os.getenv(
    "VOLC_FLASH_ASR_RESOURCE_ID",
    "volc.bigasr.auc_turbo",
)
VOLC_STANDARD_ASR_SUBMIT_URL = os.getenv(
    "VOLC_STANDARD_ASR_SUBMIT_URL",
    "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit",
)
VOLC_STANDARD_ASR_QUERY_URL = os.getenv(
    "VOLC_STANDARD_ASR_QUERY_URL",
    "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query",
)
VOLC_STANDARD_ASR_RESOURCE_ID = os.getenv(
    "VOLC_STANDARD_ASR_RESOURCE_ID",
    "volc.bigasr.auc",
)
VOLC_STANDARD_ASR_POLL_SECONDS = float(
    os.getenv("VOLC_STANDARD_ASR_POLL_SECONDS", "3")
)

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
).rstrip("/")
LYRICFLOW_AUDIO_COACH_MODEL = os.getenv(
    "LYRICFLOW_AUDIO_COACH_MODEL",
    "qwen3.5-omni-plus",
)
LYRICFLOW_CLOUD_TIMEOUT_SECONDS = float(
    os.getenv("LYRICFLOW_CLOUD_TIMEOUT_SECONDS", "180")
)

# Rap detection
RAP_WORD_DENSITY_THRESHOLD = 3.5  # words per second
RAP_BPM_THRESHOLD = 140
RAP_SLOWDOWN_RATE = 0.85
