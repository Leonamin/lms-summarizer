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
