"""
애플리케이션 설정 데이터 클래스들
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class InputFieldConfig:
    """입력 필드 설정"""
    label: str
    placeholder: str
    is_password: bool = False
    is_multiline: bool = False
    max_height: Optional[int] = None
    icon: Optional[str] = None
    tooltip: Optional[str] = None


@dataclass
class ModuleConfig:
    """모듈 설정"""
    name: str
    import_path: str
    required: bool = True


# 입력 필드 설정들
INPUT_FIELD_CONFIGS = {
    'student_id': InputFieldConfig(
        label="학번:",
        placeholder="예: 20201234",
        icon="school",
        tooltip="숭실대학교 LMS에 로그인할 학번을 입력하세요",
    ),
    'password': InputFieldConfig(
        label="비밀번호:",
        placeholder="LMS 비밀번호",
        is_password=True,
        icon="lock",
        tooltip="숭실대학교 LMS 로그인 비밀번호",
    ),
    'api_key': InputFieldConfig(
        label="AI API 키:",
        placeholder="AI 엔진의 API 키를 입력하세요",
        icon="key",
        tooltip="선택한 AI 엔진(Gemini, OpenAI 등)의 API 키",
    ),
    'urls': InputFieldConfig(
        label="강의 URL 목록:",
        placeholder="https://canvas.ssu.ac.kr/courses/...\n(여러 URL은 각각 새 줄에 입력)",
        is_multiline=True,
        icon="movie",
        tooltip="요약할 강의 영상의 URL을 한 줄에 하나씩 입력하세요",
    )
}

# 모듈 설정들
MODULE_CONFIGS = {
    'UserSetting': ModuleConfig(
        name='UserSetting',
        import_path='src.user_setting.UserSetting'
    ),
    'VideoPipeline': ModuleConfig(
        name='VideoPipeline',
        import_path='src.video_pipeline.pipeline.VideoPipeline'
    ),
    'AudioToTextPipeline': ModuleConfig(
        name='AudioToTextPipeline',
        import_path='src.audio_pipeline.pipeline.AudioToTextPipeline'
    ),
    'SummarizePipeline': ModuleConfig(
        name='SummarizePipeline',
        import_path='src.summarize_pipeline.pipeline.SummarizePipeline'
    )
}