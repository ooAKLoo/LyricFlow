from __future__ import annotations

from pydantic import BaseModel, Field
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
    type: str  # linking, weak_form, elision, flap, assimilation, stress, breath
    subtype: str
    symbol: str
    target_word: str | None = None
    explanation_zh: str
    confidence: float
    strong_ipa: str | None = None
    weak_ipa: str | None = None
    source: str | None = None
    heard_as: str | None = None
    mouth_tip_zh: str | None = None
    rhythm_tip_zh: str | None = None
    end_word_index: int | None = None
    evidence: str | None = None


class WordData(BaseModel):
    word: str
    start: float
    end: float
    ipa: str
    phones: list[PhoneAnnotation] = Field(default_factory=list)
    annotations: list[Annotation] = Field(default_factory=list)
    asr_word: str = ""
    asr_confidence: float | None = None
    timing_source: str = "unknown"


class LyricLine(BaseModel):
    text: str
    translation: str = ""
    start: float = 0.0
    end: float = 0.0
    words: list[WordData] = Field(default_factory=list)
    is_rap: bool = False
    performed_text: str = ""
    coach_summary_zh: str = ""
    difficulty: int = 0
    beat_hint: str = ""
    analysis_source: str = "rule_engine"


class SongStats(BaseModel):
    total_words: int = 0
    total_linking: int = 0
    total_weak_forms: int = 0
    total_elision: int = 0
    total_stress: int = 0
    total_other: int = 0
    total_annotations: int = 0


class AnalysisMeta(BaseModel):
    alignment_source: str = "unknown"
    alignment_quality: float = 0.0
    coaching_provider: str = "rule_engine"
    cloud_enabled: bool = False
    warnings: list[str] = Field(default_factory=list)


class SongResult(BaseModel):
    song_id: str
    song_title: str
    artist: str
    dialect: str = "en-us"
    duration: float = 0.0
    lines: list[LyricLine] = Field(default_factory=list)
    audio_url: str = ""
    vocals_url: str = ""
    stats: SongStats = Field(default_factory=SongStats)
    analysis: AnalysisMeta | None = None


class CorrectionRequest(BaseModel):
    line_index: int
    word_index: int
    annotation_index: int | None = None
    action: str  # "remove", "add", "modify"
    data: dict = Field(default_factory=dict)
