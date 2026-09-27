from enum import Enum

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    CANCELLING = "cancelling"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"

class ResultKind(str, Enum):
    SUMMARY = "summary"
    MANUAL_READY = "manual_ready"
    STAGE_ARTIFACT = "stage_artifact"

RETRYABLE_STATUSES = frozenset({JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.INTERRUPTED})

from dataclasses import dataclass, field
from typing import Optional
from src.core.models.stages import PipelineStage

@dataclass(frozen=True)
class Source:
    kind: str
    reference: str = field(repr=False)

    @classmethod
    def file(cls, artifact_id: str):
        return cls("file", artifact_id)

    @classmethod
    def url(cls, url: str):
        return cls("url", url)

@dataclass(frozen=True)
class WorkToken:
    job_id: str
    attempt_id: str
    run_id: str
    generation: str
    stage: PipelineStage

@dataclass(frozen=True)
class StageCommand:
    token: WorkToken
    source: str = field(repr=False)
    output_dir: str = field(repr=False)
    settings_json: str = field(repr=False)
    resolved_prompt: str = field(repr=False)
    credentials: dict[str, str] = field(default_factory=dict, repr=False)
    model_cache_dir: Optional[str] = field(default=None, repr=False)
    catalog_query: Optional[dict] = field(default=None, repr=False)

@dataclass(frozen=True)
class StageResult:
    token: WorkToken
    output: Optional[str] = field(default=None, repr=False)
    kind: str = ""
    error_code: str = ""
    model_reused: bool = False
    data: Optional[dict | list] = field(default=None, repr=False)

class ServiceError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)
