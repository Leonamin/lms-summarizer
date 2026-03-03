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


@dataclass
class ModuleConfig:
    """모듈 설정"""
    name: str
    import_path: str
    required: bool = True


# 입력 필드 설정들
INPUT_FIELD_CONFIGS = {
    'student_id': InputFieldConfig(
        label="📚 학번:",
        placeholder="예: 20201234"
    ),
    'password': InputFieldConfig(
        label="🔒 비밀번호:",
        placeholder="LMS 비밀번호",
        is_password=True
    ),
    'api_key': InputFieldConfig(
        label="🔑 Gemini API 키:",
        placeholder="sk-... (Gemini API 키를 입력하세요)"
    ),
    'urls': InputFieldConfig(
        label="🎬 강의 URL 목록:",
        placeholder="https://canvas.ssu.ac.kr/courses/...\n(여러 URL은 각각 새 줄에 입력)",
        is_multiline=True,
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