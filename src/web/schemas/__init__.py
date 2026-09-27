"""Validated web DTOs; the owner and server paths are never client inputs."""
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
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
    stt_params: dict = Field(default_factory=dict)
    student_id: str = Field(default='', max_length=64)
    prompt_mode: Literal['structured', 'custom'] = 'structured'
    summary_mode: str = Field(default='normal', max_length=64)
    subject_category: str = Field(default='자동 감지', max_length=100)
    subject_custom: str = Field(default='', max_length=500)
    custom_prompt: str = Field(default=DEFAULT_PROMPT, min_length=1, max_length=100000)
    keep_source: bool = False

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

class JobCreate(DTO):
    sources: list[SourceDTO] = Field(min_length=1, max_length=50)
    settings_revision: UUID
    end_stage: int = Field(default=4, ge=1, le=4)

class AttemptCommand(DTO):
    attempt_id: UUID
