from pydantic import BaseModel
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PREPROCESSING = "preprocessing"
    LYRICS_FETCHING = "lyrics_fetching"
    ALIGNING = "aligning"
    PHONETICS = "phonetics"
    DETECTING = "detecting"
    COMPLETED = "completed"
    ERROR = "error"


class UploadResponse(BaseModel):
    task_id: str
    message: str = "Processing started"


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: int = 0  # 0-100
    current_stage: str = ""
    error_message: str | None = None
    song_id: str | None = None


class PhoneAnnotation(BaseModel):
    phone: str
    start: float
    end: float


class Annotation(BaseModel):
    type: str  # linking, weak_form, elision
    subtype: str
    symbol: str
    target_word: str | None = None
    explanation_zh: str
    confidence: float
    strong_ipa: str | None = None
    weak_ipa: str | None = None


class WordData(BaseModel):
    word: str
    start: float
    end: float
    ipa: str
    phones: list[PhoneAnnotation] = []
    annotations: list[Annotation] = []


class LyricLine(BaseModel):
    text: str
    translation: str = ""
    start: float = 0.0
    end: float = 0.0
    words: list[WordData] = []
    is_rap: bool = False


class SongResult(BaseModel):
    song_id: str
    song_title: str
    artist: str
    dialect: str = "en-us"
    duration: float = 0.0
    lines: list[LyricLine] = []
    audio_url: str = ""
    vocals_url: str = ""


class CorrectionRequest(BaseModel):
    line_index: int
    word_index: int
    annotation_index: int | None = None
    action: str  # "remove", "add", "modify"
    data: dict = {}
