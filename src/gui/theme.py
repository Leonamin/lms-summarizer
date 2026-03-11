"""
LMS Summarizer 디자인 시스템
- Style: Modern Minimalism (Swiss Style)
- Color: Primary Blue (#3B82F6) + Accent Orange (#F97316)
- Typography: System sans-serif (Noto Sans KR 호환)
- Spacing: 8px grid system
- Layout: 2-panel (left 270px + right expand)
"""

import flet as ft


# ── 색상 팔레트 ──────────────────────────────────────────────

class Colors:
    # Primary (Blue)
    PRIMARY = "#3B82F6"          # blue-500
    PRIMARY_LIGHT = "#60A5FA"    # blue-400
    PRIMARY_DARK = "#2563EB"     # blue-600
    PRIMARY_BG = "#EFF6FF"       # 아주 연한 블루 배경

    # Accent (Orange - CTA)
    ACCENT = "#F97316"           # orange-500
    ACCENT_LIGHT = "#FB923C"     # orange-400

    # Neutral
    BG = "#F8FAFC"               # 페이지 배경 (slate-50)
    CARD = "#FFFFFF"             # 카드 배경
    SURFACE = "#F1F5F9"          # 입력 필드 배경 등 (slate-100)
    LEFT_PANEL_BG = "#F8FAFC"    # 왼쪽 패널 배경 (slate-50)

    # Text
    TEXT = "#1E293B"             # 기본 텍스트 (slate-800)
    TEXT_SECONDARY = "#475569"   # 보조 텍스트 (slate-600)
    TEXT_MUTED = "#94A3B8"       # 희미한 텍스트 (slate-400)

    # Border
    BORDER = "#E2E8F0"          # 기본 테두리 (slate-200)
    BORDER_FOCUS = "#3B82F6"    # 포커스 테두리

    # Semantic
    SUCCESS = "#16A34A"          # green-600
    WARNING = "#EA580C"          # orange-600
    ERROR = "#EF4444"            # red-500
    INFO = "#3B82F6"             # primary

    # Misc
    DISABLED = "#CBD5E1"         # slate-300
    SHADOW = "#0F172A"           # shadow color base


# ── 로그 드로어 다크 테마 색상 ──────────────────────────────────

class LogDarkColors:
    BG = "#1E1E2E"               # 다크 배경
    SURFACE = "#252535"          # 표면
    TEXT = "#CDD6F4"             # 밝은 텍스트
    TEXT_DIM = "#6C7086"         # 흐린 텍스트
    BORDER = "#313244"           # 테두리
    TIMESTAMP = "#A6E3A1"        # 타임스탬프 (green)
    HEADER_BG = "#181825"        # 헤더 배경


# ── 타이포그래피 ──────────────────────────────────────────────

class Typography:
    # Flet에서는 시스템 폰트를 기본 사용
    FAMILY = "Noto Sans KR, -apple-system, BlinkMacSystemFont, sans-serif"

    # 크기 스케일
    TITLE = 22
    HEADING = 16
    BODY = 14
    CAPTION = 12
    SMALL = 11

    # 무게
    BOLD = ft.FontWeight.W_700
    SEMI_BOLD = ft.FontWeight.W_600
    MEDIUM = ft.FontWeight.W_500
    REGULAR = ft.FontWeight.W_400


# ── 간격 시스템 (8px 그리드) ─────────────────────────────────

class Spacing:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


# ── 라운딩 ───────────────────────────────────────────────────

class Radius:
    SM = 6
    MD = 8
    LG = 12
    XL = 16
    FULL = 999


# ── 그림자 ───────────────────────────────────────────────────

CARD_SHADOW = ft.BoxShadow(
    spread_radius=0,
    blur_radius=8,
    color=ft.Colors.with_opacity(0.06, Colors.SHADOW),
    offset=ft.Offset(0, 2),
)

CARD_SHADOW_HOVER = ft.BoxShadow(
    spread_radius=0,
    blur_radius=16,
    color=ft.Colors.with_opacity(0.1, Colors.SHADOW),
    offset=ft.Offset(0, 4),
)


# ── 컴포넌트 팩토리 ─────────────────────────────────────────

def card_container(content: ft.Control, padding: int = Spacing.LG, **kwargs) -> ft.Container:
    """카드 스타일 컨테이너"""
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=Radius.LG,
        bgcolor=Colors.CARD,
        border=ft.border.all(1, Colors.BORDER),
        shadow=CARD_SHADOW,
        **kwargs,
    )


def section_title(text: str, icon: ft.Icons = None) -> ft.Row:
    """섹션 제목"""
    controls = []
    if icon:
        controls.append(ft.Icon(icon, size=18, color=Colors.PRIMARY))
    controls.append(
        ft.Text(
            text,
            size=Typography.HEADING,
            weight=Typography.SEMI_BOLD,
            color=Colors.TEXT,
        )
    )
    return ft.Row(controls=controls, spacing=Spacing.SM)


def caption_text(text: str) -> ft.Text:
    """보조 설명 텍스트"""
    return ft.Text(
        text,
        size=Typography.CAPTION,
        color=Colors.TEXT_MUTED,
    )


def divider() -> ft.Divider:
    """구분선"""
    return ft.Divider(height=1, color=Colors.BORDER)


def primary_button(text: str, icon: ft.Icons = None, on_click=None, **kwargs) -> ft.ElevatedButton:
    """Primary 버튼"""
    return ft.ElevatedButton(
        content=ft.Text(text),
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=Colors.PRIMARY,
            shape=ft.RoundedRectangleBorder(radius=Radius.SM),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=13),
            overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        ),
        **kwargs,
    )


def outline_button(text: str, icon: ft.Icons = None, on_click=None, **kwargs) -> ft.OutlinedButton:
    """Outline 버튼"""
    return ft.OutlinedButton(
        content=ft.Text(text),
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=Colors.PRIMARY,
            shape=ft.RoundedRectangleBorder(radius=Radius.SM),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=13),
            side=ft.BorderSide(width=1.5, color=Colors.PRIMARY),
        ),
        **kwargs,
    )


def text_button(text: str, icon: ft.Icons = None, on_click=None, **kwargs) -> ft.TextButton:
    """Text 버튼"""
    return ft.TextButton(
        content=ft.Text(text),
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=Colors.PRIMARY,
            shape=ft.RoundedRectangleBorder(radius=Radius.SM),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=13),
        ),
        **kwargs,
    )


def danger_button(text: str, icon: ft.Icons = None, on_click=None, **kwargs) -> ft.ElevatedButton:
    """Danger 버튼"""
    return ft.ElevatedButton(
        content=ft.Text(text),
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=Colors.ERROR,
            shape=ft.RoundedRectangleBorder(radius=Radius.SM),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            text_style=ft.TextStyle(weight=Typography.SEMI_BOLD, size=13),
            overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        ),
        **kwargs,
    )


def styled_textfield(
    label: str = None,
    hint_text: str = None,
    password: bool = False,
    multiline: bool = False,
    prefix_icon: ft.Icons = None,
    on_change=None,
    **kwargs,
) -> ft.TextField:
    """통일된 스타일의 TextField"""
    return ft.TextField(
        label=label,
        hint_text=hint_text,
        password=password,
        can_reveal_password=password,
        multiline=multiline,
        prefix_icon=prefix_icon,
        on_change=on_change,
        border_radius=Radius.SM,
        border_color=Colors.BORDER,
        focused_border_color=Colors.PRIMARY,
        cursor_color=Colors.PRIMARY,
        text_size=Typography.BODY,
        label_style=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
        **kwargs,
    )


def setup_page_theme(page: ft.Page):
    """페이지 기본 테마 설정"""
    page.title = "LMS 강의 다운로드 & 요약"
    page.bgcolor = Colors.BG
    page.padding = 0
    page.window.width = 820
    page.window.height = 640
    page.window.min_width = 700
    page.window.min_height = 500

    page.theme = ft.Theme(
        color_scheme_seed=Colors.PRIMARY,
        color_scheme=ft.ColorScheme(
            primary=Colors.PRIMARY,
            on_primary=ft.Colors.WHITE,
            surface=Colors.CARD,
            on_surface=Colors.TEXT,
            error=Colors.ERROR,
        ),
        text_theme=ft.TextTheme(
            body_medium=ft.TextStyle(size=Typography.BODY, color=Colors.TEXT),
            body_small=ft.TextStyle(size=Typography.CAPTION, color=Colors.TEXT_SECONDARY),
            title_large=ft.TextStyle(size=Typography.TITLE, weight=Typography.BOLD, color=Colors.TEXT),
        ),
    )
