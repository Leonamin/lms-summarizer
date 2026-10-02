"""사용자에게 보이는 산출물 파일 이름 규칙.

저장소 내부 파일명(`summary.txt`, `audio.wav` 등)은 그대로 두고, 다운로드·내보내기
시점에만 강의 prefix와 역할 suffix를 붙인 이름을 만든다.
"""
from pathlib import Path
import re

# prefix에 포함할 범위. 값이 커질수록 더 많은 상위 정보를 붙인다.
SCOPES = ('lecture', 'week', 'course')
DEFAULT_SCOPE = 'lecture'

# prefix 뒤에 붙는 역할 접미사.
SUFFIXES = {
    'video': '영상',
    'audio': '음성',
    'transcript': '대본',
    'summary': '요약',
    'prompt': '프롬프트',
}

_INVALID_CHARS = set('<>:"/\\|?*') | {chr(code) for code in range(32)}
_KNOWN_MEDIA_EXTENSIONS = {
    '.mp4', '.ts', '.m4a', '.mkv', '.mov', '.webm', '.avi',
    '.wav', '.mp3', '.flac', '.ogg', '.opus', '.aac',
    '.txt', '.md',
}
_MAX_COMPONENT = 180
_MAX_NAME = 220


def sanitize_component(value) -> str:
    """파일 이름 한 조각에서 경로·예약 문자를 제거하고 공백을 정리한다."""
    if value is None:
        return ''
    text = ''.join(ch for ch in str(value) if ch not in _INVALID_CHARS)
    text = '_'.join(text.split())
    text = re.sub(r'_+', '_', text)
    return text.strip('._')[: _MAX_COMPONENT]


def sanitize_filename(value) -> str:
    """확장자를 보존한 채 파일 이름 전체를 안전하게 정리한다."""
    name = str(value or '').strip()
    if not name:
        return ''
    suffix = Path(name).suffix
    stem = name[: -len(suffix)] if suffix else name
    stem = sanitize_component(stem)
    safe_suffix = ''.join(ch for ch in suffix if ch not in _INVALID_CHARS)
    return (stem + safe_suffix)[:_MAX_NAME]


def lecture_label(display_name) -> str:
    """작업 표시 이름에서 알려진 확장자를 떼어 prefix용 강의명을 만든다."""
    name = str(display_name or '').strip()
    if not name:
        return ''
    suffix = Path(name).suffix.lower()
    if suffix in _KNOWN_MEDIA_EXTENSIONS:
        name = name[: -len(suffix)]
    return sanitize_component(name)


def build_stem(kind: str, *, lecture: str = '', course: str = '', week: str = '',
               scope: str = DEFAULT_SCOPE) -> str:
    """prefix 범위와 종류 접미사로 확장자 없는 파일 이름을 조립한다."""
    suffix = SUFFIXES.get(kind, '')
    if scope == 'course':
        parts = [course, week, lecture]
    elif scope == 'week':
        parts = [week, lecture]
    else:
        parts = [lecture]
    cleaned = [sanitize_component(part) for part in parts]
    if suffix:
        cleaned.append(suffix)
    stem = '_'.join(part for part in cleaned if part)
    return stem[:_MAX_NAME]


def artifact_filename(artifact, job=None, scope: str = DEFAULT_SCOPE) -> str:
    """산출물과 작업 정보로 다운로드·내보내기 파일 이름을 만든다."""
    artifact = artifact or {}
    job = job or {}
    original = artifact.get('display_name') or ''
    kind = artifact.get('kind') or ''
    if kind not in SUFFIXES:
        # 입력 원문 등은 원래 이름을 그대로 살린다.
        return sanitize_filename(original) or kind or 'file'
    extension = Path(original).suffix
    stem = build_stem(
        kind,
        lecture=lecture_label(job.get('display_name')),
        course=job.get('course_name') or '',
        week=job.get('week_title') or '',
        scope=scope,
    )
    if not stem:
        return sanitize_filename(original) or (kind + extension)
    return stem + extension
