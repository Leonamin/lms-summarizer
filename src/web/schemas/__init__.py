"""Validated web DTOs; the owner and server paths are never client inputs."""
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.core.prompts import DEFAULT_PROMPT

class DTO(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Settings(DTO):
    ai_engine: Literal['clipboard', 'gemini', 'openai', 'claude', 'grok', 'custom'] = 'clipboard'
    ai_model: str = Field(default='chatgpt', max_length=200)
    base_url: str = Field(default='', max_length=2000)
    stt_engine: Literal['faster-whisper', 'openai-whisper', 'openai-compatible', 'returnzero'] = 'faster-whisper'
    stt_model: str = Field(default='large-v3-turbo', max_length=200)
    stt_base_url: str = Field(default='', max_length=2000)
    stt_compatible_model: str = Field(default='', max_length=200)
    stt_params: dict = Field(default_factory=lambda: {'device': 'cpu', 'compute_type': 'int8'})
    request_timeout: float = Field(default=120, ge=5, le=1800)

    @field_validator('stt_params')
    @classmethod
    def validate_stt_params(cls, value):
        allowed = {'device', 'compute_type', 'language', 'initial_prompt', 'repeat_threshold', 'vad_filter'}
        if set(value) - allowed:
            raise ValueError('Unknown STT parameter')
        if value.get('device', 'cpu') not in ('cpu','auto','cuda'):
            raise ValueError('Invalid device')
        if value.get('compute_type', 'int8') not in ('auto','int8','float16','float32','int8_float16'):
            raise ValueError('Invalid precision')
        for name, limit in (('language', 20), ('initial_prompt', 10000)):
            if name in value and (not isinstance(value[name], str) or len(value[name]) > limit):
                raise ValueError('Invalid text parameter')
        if 'repeat_threshold' in value and (type(value['repeat_threshold']) is not int or not 1 <= value['repeat_threshold'] <= 100):
            raise ValueError('Invalid repeat threshold')
        if 'vad_filter' in value and type(value['vad_filter']) is not bool:
            raise ValueError('Invalid VAD flag')
        return value

    @field_validator('base_url', 'stt_base_url')
    @classmethod
    def validate_endpoint(cls, value):
        from urllib.parse import urlsplit
        if value:
            url = urlsplit(value)
            if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password or url.query or url.fragment:
                raise ValueError('Invalid endpoint')
        return value
    student_id: str = Field(default='', max_length=64)
    prompt_mode: Literal['structured', 'custom'] = 'structured'
    summary_mode: Literal['quick','normal','detailed'] = 'normal'
    subject_category: str = Field(default='자동 감지', max_length=100)
    subject_custom: str = Field(default='', max_length=500)
    custom_prompt: str = Field(default=DEFAULT_PROMPT, min_length=1, max_length=100000)
    keep_source: bool = False
    auto_detect_enabled: bool = False
    auto_detect_interval_minutes: int = Field(default=30, ge=5, le=1440)
    auto_detect_courses: str = Field(default='', max_length=2000)
    auto_save_scope: Literal['download', 'full'] = 'download'

class SettingsPatch(DTO):
    expected_revision: int = Field(ge=1)
    settings: Settings

class SecretPut(DTO):
    value: str = Field(min_length=1, max_length=10000, repr=False)

class UploadCreate(DTO):
    filename: str = Field(min_length=1, max_length=255)
    size: int = Field(gt=0)

class SourceDTO(DTO):
    kind: Literal['file', 'url']
    reference: str = Field(min_length=1, max_length=4000)
    display_name: str | None = Field(default=None, max_length=300)
    course_name: str | None = Field(default=None, max_length=300)
    week_title: str | None = Field(default=None, max_length=200)

class JobCreate(DTO):
    sources: list[SourceDTO] = Field(min_length=1, max_length=50)
    settings_revision: UUID
    end_stage: int = Field(default=4, ge=1, le=4)

class AttemptCommand(DTO):
    attempt_id: UUID

class ContinueCommand(DTO):
    attempt_id: UUID
    end_stage: int = Field(ge=2, le=4)

class CourseRefresh(DTO):
    course_id: str | None = Field(default=None, pattern=r'^\d+$', max_length=30)
