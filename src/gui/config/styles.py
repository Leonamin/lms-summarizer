"""
UI 스타일시트 정의 (밝은 테마)
"""

from .constants import Colors


class StyleSheet:
    """UI 스타일시트 관리 클래스"""

    @staticmethod
    def main_window() -> str:
        return f"""
            QWidget {{
                background-color: {Colors.BACKGROUND};
            }}
            QSplitter::handle {{
                background-color: {Colors.BORDER};
                height: 1px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #C1C9D4;
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #9AA3AF;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: transparent;
                height: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: #C1C9D4;
                border-radius: 4px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: #9AA3AF;
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """

    @staticmethod
    def title() -> str:
        return f"""
            font-size: 20px;
            font-weight: bold;
            color: {Colors.TEXT_DARK};
            padding: 12px 0 4px 0;
        """

    @staticmethod
    def subtitle() -> str:
        return f"""
            color: {Colors.TEXT_LIGHT};
            font-size: 12px;
            padding-bottom: 8px;
        """

    @staticmethod
    def card() -> str:
        return f"""
            QFrame {{
                background-color: {Colors.CARD_BG};
                border-radius: 8px;
                border: 1px solid {Colors.BORDER};
            }}
        """

    @staticmethod
    def label() -> str:
        return f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: 13px;
            font-weight: 600;
            margin-top: 10px;
        """

    @staticmethod
    def input_field() -> str:
        return f"""
            QLineEdit {{
                padding: 9px 12px;
                font-size: 13px;
                border: 1.5px solid {Colors.BORDER};
                border-radius: 6px;
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_DARK};
            }}
            QLineEdit:focus {{
                border-color: {Colors.BORDER_FOCUS};
            }}
            QLineEdit:disabled {{
                background-color: #F5F5F5;
                color: {Colors.TEXT_LIGHT};
            }}
        """

    @staticmethod
    def multiline_input() -> str:
        return f"""
            QTextEdit {{
                padding: 9px 12px;
                font-size: 13px;
                border: 1.5px solid {Colors.BORDER};
                border-radius: 6px;
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_DARK};
            }}
            QTextEdit:focus {{
                border-color: {Colors.BORDER_FOCUS};
            }}
            QTextEdit:disabled {{
                background-color: #F5F5F5;
                color: {Colors.TEXT_LIGHT};
            }}
        """

    @staticmethod
    def button() -> str:
        return f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_PRESSED};
            }}
            QPushButton:disabled {{
                background-color: {Colors.DISABLED_BG};
                color: white;
            }}
        """

    @staticmethod
    def outline_button() -> str:
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.PRIMARY};
                border: 1.5px solid {Colors.PRIMARY};
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #E3F2FD;
            }}
            QPushButton:pressed {{
                background-color: #BBDEFB;
            }}
            QPushButton:disabled {{
                color: {Colors.DISABLED_BG};
                border-color: {Colors.DISABLED_BG};
            }}
        """

    @staticmethod
    def log_area() -> str:
        return f"""
            QTextEdit {{
                background-color: {Colors.LOG_BG};
                color: {Colors.LOG_TEXT};
                font-family: 'Consolas', 'Monaco', 'Menlo', monospace;
                font-size: 12px;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid {Colors.BORDER};
            }}
        """

    @staticmethod
    def caps_lock_warning() -> str:
        return f"""
            QLabel {{
                color: {Colors.WARNING};
                font-size: 11px;
                padding-left: 4px;
            }}
        """

    @staticmethod
    def stop_button() -> str:
        return f"""
            QPushButton {{
                background-color: {Colors.ERROR};
                color: white;
                border: none;
                padding: 9px 20px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #B71C1C;
            }}
            QPushButton:pressed {{
                background-color: #7F0000;
            }}
            QPushButton:disabled {{
                background-color: {Colors.DISABLED_BG};
            }}
        """

    @staticmethod
    def path_value() -> str:
        return f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                padding: 6px 10px;
                background: {Colors.WHITE};
                border: 1px solid {Colors.BORDER};
                border-radius: 5px;
                font-size: 12px;
            }}
        """

    @staticmethod
    def checkbox() -> str:
        return f"""
            QCheckBox {{
                color: {Colors.TEXT_SECONDARY};
                font-size: 13px;
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1.5px solid {Colors.BORDER};
                background-color: {Colors.WHITE};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
            }}
        """

    # ── 모달 전용 스타일 ──────────────────────────────────────────

    @staticmethod
    def modal_window() -> str:
        return f"QDialog {{ background-color: {Colors.WHITE}; }}"

    @staticmethod
    def modal_title() -> str:
        return f"font-size: 15px; font-weight: bold; color: {Colors.TEXT_DARK};"

    @staticmethod
    def step_label_pending() -> str:
        return f"color: {Colors.TEXT_LIGHT}; font-size: 13px;"

    @staticmethod
    def step_label_active() -> str:
        return f"color: {Colors.PRIMARY}; font-size: 13px; font-weight: bold;"

    @staticmethod
    def step_label_done() -> str:
        return f"color: {Colors.SUCCESS}; font-size: 13px;"

    @staticmethod
    def progress_bar() -> str:
        return f"""
            QProgressBar {{
                border: 1px solid {Colors.BORDER};
                border-radius: 5px;
                height: 14px;
                text-align: center;
                font-size: 11px;
                color: {Colors.TEXT_DARK};
                background-color: #E3F2FD;
            }}
            QProgressBar::chunk {{
                background-color: {Colors.PRIMARY};
                border-radius: 4px;
            }}
        """

    @staticmethod
    def modal_log_toggle() -> str:
        return f"""
            QPushButton {{
                background: none;
                border: none;
                color: {Colors.PRIMARY};
                font-size: 12px;
                text-align: left;
                padding: 2px 0;
            }}
            QPushButton:hover {{ color: {Colors.PRIMARY_HOVER}; }}
        """

    @staticmethod
    def modal_log_area() -> str:
        return f"""
            QTextEdit {{
                background-color: {Colors.LOG_BG};
                color: {Colors.LOG_TEXT};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 8px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """

    @staticmethod
    def modal_stop_button() -> str:
        return f"""
            QPushButton {{
                background-color: {Colors.ERROR};
                color: white;
                border: none;
                padding: 7px 18px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #B71C1C; }}
            QPushButton:disabled {{ background-color: {Colors.DISABLED_BG}; }}
        """

    @staticmethod
    def divider() -> str:
        return f"QFrame {{ color: {Colors.BORDER}; }}"

    @staticmethod
    def app_button(variant: str = "filled") -> str:
        """범용 버튼 스타일 - filled/outline/text/danger 변형"""
        common = "border-radius: 6px; font-size: 13px; font-weight: 600; padding: 8px 16px;"
        if variant == "filled":
            return f"""
                QPushButton {{
                    {common}
                    border: none;
                    background-color: {Colors.PRIMARY};
                    color: white;
                }}
                QPushButton:hover {{ background-color: {Colors.PRIMARY_HOVER}; }}
                QPushButton:pressed {{ background-color: {Colors.PRIMARY_PRESSED}; }}
                QPushButton:disabled {{ background-color: {Colors.DISABLED_BG}; color: white; }}
            """
        elif variant == "outline":
            return f"""
                QPushButton {{
                    {common}
                    background-color: transparent;
                    color: {Colors.PRIMARY};
                    border: 1.5px solid {Colors.PRIMARY};
                }}
                QPushButton:hover {{ background-color: #E3F2FD; }}
                QPushButton:pressed {{ background-color: #BBDEFB; }}
                QPushButton:disabled {{
                    color: {Colors.DISABLED_BG};
                    border-color: {Colors.DISABLED_BG};
                }}
            """
        elif variant == "text":
            return f"""
                QPushButton {{
                    {common}
                    border: none;
                    background-color: transparent;
                    color: {Colors.PRIMARY};
                }}
                QPushButton:hover {{ background-color: #E3F2FD; }}
                QPushButton:disabled {{ color: {Colors.DISABLED_BG}; }}
            """
        elif variant == "danger":
            return f"""
                QPushButton {{
                    {common}
                    border: none;
                    background-color: {Colors.ERROR};
                    color: white;
                }}
                QPushButton:hover {{ background-color: #B71C1C; }}
                QPushButton:pressed {{ background-color: #7F0000; }}
                QPushButton:disabled {{ background-color: {Colors.DISABLED_BG}; color: white; }}
            """
        return f"QPushButton {{ {common} border: none; }}"
