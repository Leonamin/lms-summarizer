"""
UI 스타일시트 정의
"""

from .constants import Colors


class StyleSheet:
    """UI 스타일시트 관리 클래스"""

    @staticmethod
    def title() -> str:
        """제목 스타일"""
        return f"""
            font-size: 24px;
            font-weight: bold;
            margin: 20px;
            color: {Colors.TEXT_DARK};
        """

    @staticmethod
    def subtitle() -> str:
        """부제목 스타일"""
        return f"""
            color: {Colors.TEXT_LIGHT};
            font-size: 12px;
            margin-bottom: 20px;
        """

    @staticmethod
    def label() -> str:
        """라벨 스타일"""
        return f"""
            margin-top: 10px; 
            margin-bottom: 5px; 
            font-weight: bold;
            color: {Colors.TEXT_SECONDARY};
            font-size: 14px;
        """

    @staticmethod
    def input_field() -> str:
        """일반 입력 필드 스타일"""
        return f"""
            QLineEdit {{
                padding: 12px;
                font-size: 14px;
                border: 2px solid {Colors.BORDER};
                border-radius: 8px;
                margin-bottom: 10px;
                background-color: {Colors.WHITE};
            }}
            QLineEdit:focus {{
                border-color: {Colors.BORDER_FOCUS};
            }}
        """

    @staticmethod
    def multiline_input() -> str:
        """멀티라인 입력 필드 스타일"""
        return f"""
            QTextEdit {{
                padding: 12px;
                font-size: 14px;
                border: 2px solid {Colors.BORDER};
                border-radius: 8px;
                margin-bottom: 10px;
                background-color: {Colors.WHITE};
                min-width: 500px;
                min-height: 100px;
            }}
            QTextEdit:focus {{
                border-color: {Colors.BORDER_FOCUS};
            }}
        """

    @staticmethod
    def button() -> str:
        """버튼 스타일"""
        return f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                margin-top: 20px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_PRESSED};
            }}
            QPushButton:disabled {{
                background-color: {Colors.DISABLED_BG};
                color: {Colors.TEXT_LIGHT};
            }}
        """

    @staticmethod
    def log_area() -> str:
        """로그 영역 스타일"""
        return f"""
            QTextEdit {{
                background-color: {Colors.LOG_BG};
                color: {Colors.LOG_TEXT};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #34495e;
            }}
        """

    @staticmethod
    def main_window() -> str:
        """메인 윈도우 스타일"""
        return f"""
            QWidget {{
                background-color: {Colors.BACKGROUND};
            }}
        """