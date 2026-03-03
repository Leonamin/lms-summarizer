"""
처리 과정을 단계별로 표시하는 모달 다이얼로그
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal

from src.gui.config.styles import StyleSheet

# 처리 단계 정의: (단계번호, 표시 이름)
_STEPS = [
    (1, "영상 다운로드"),
    (2, "음성 → 텍스트 변환"),
    (3, "AI 요약 생성"),
]


class ProcessingModal(QDialog):
    """처리 진행 상황을 표시하는 모달 다이얼로그"""

    stop_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._log_visible = False
        self._is_finished = False

        self.setWindowTitle("처리 중...")
        self.setModal(True)
        # X 버튼과 ESC 키로 닫기 방지
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setMinimumWidth(460)
        self.setStyleSheet(StyleSheet.modal_window())

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        # 모달 제목
        title = QLabel("강의 처리 중...")
        title.setStyleSheet(StyleSheet.modal_title())
        layout.addWidget(title)

        # 구분선
        layout.addWidget(self._make_divider())

        # 단계 인디케이터
        self._step_labels = []
        steps_frame = QFrame()
        steps_layout = QVBoxLayout(steps_frame)
        steps_layout.setSpacing(4)
        steps_layout.setContentsMargins(0, 4, 0, 4)
        for num, name in _STEPS:
            lbl = QLabel(f"○  {num}단계: {name}")
            lbl.setStyleSheet(StyleSheet.step_label_pending())
            steps_layout.addWidget(lbl)
            self._step_labels.append(lbl)
        layout.addWidget(steps_frame)

        # 구분선
        layout.addWidget(self._make_divider())

        # 현재 상태 텍스트
        self._status_label = QLabel("작업을 시작하는 중...")
        self._status_label.setStyleSheet(f"color: #555; font-size: 12px;")
        layout.addWidget(self._status_label)

        # 진행 바
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setStyleSheet(StyleSheet.progress_bar())
        self._progress_bar.setFixedHeight(16)
        layout.addWidget(self._progress_bar)

        # 로그 토글 버튼
        self._log_toggle_btn = QPushButton("▼ 상세 로그 보기")
        self._log_toggle_btn.setStyleSheet(StyleSheet.modal_log_toggle())
        self._log_toggle_btn.setCursor(Qt.PointingHandCursor)
        self._log_toggle_btn.clicked.connect(self._toggle_log)
        layout.addWidget(self._log_toggle_btn)

        # 로그 영역 (기본 숨김)
        self._log_area = QTextEdit()
        self._log_area.setReadOnly(True)
        self._log_area.setStyleSheet(StyleSheet.modal_log_area())
        self._log_area.setFixedHeight(130)
        self._log_area.setVisible(False)
        layout.addWidget(self._log_area)

        # 하단 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._stop_btn = QPushButton("■ 중지")
        self._stop_btn.setStyleSheet(StyleSheet.modal_stop_button())
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        btn_layout.addWidget(self._stop_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _make_divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(StyleSheet.divider())
        return line

    def _toggle_log(self):
        self._log_visible = not self._log_visible
        self._log_area.setVisible(self._log_visible)
        self._log_toggle_btn.setText(
            "▲ 상세 로그 숨기기" if self._log_visible else "▼ 상세 로그 보기"
        )
        self.adjustSize()

    def _on_stop_clicked(self):
        self._stop_btn.setEnabled(False)
        self._stop_btn.setText("중지 중...")
        self.stop_requested.emit()

    # ── 외부에서 호출하는 업데이트 메서드 ──────────────────────────

    def update_step(self, step_num: int, step_name: str):
        """현재 단계 업데이트 (step_num: 1-indexed)"""
        for i, (num, name) in enumerate(_STEPS):
            lbl = self._step_labels[i]
            if i + 1 < step_num:
                lbl.setText(f"✓  {num}단계: {name}")
                lbl.setStyleSheet(StyleSheet.step_label_done())
            elif i + 1 == step_num:
                lbl.setText(f"●  {num}단계: {name}")
                lbl.setStyleSheet(StyleSheet.step_label_active())
            else:
                lbl.setText(f"○  {num}단계: {name}")
                lbl.setStyleSheet(StyleSheet.step_label_pending())

        self._progress_bar.setValue(0)
        self._status_label.setText(f"{step_name} 중...")

    def update_progress(self, current: int, total: int):
        """다운로드 진행도 업데이트"""
        if total > 0:
            pct = int(current / total * 100)
            self._progress_bar.setValue(pct)
            mb_cur = current / (1024 * 1024)
            mb_tot = total / (1024 * 1024)
            self._status_label.setText(
                f"다운로드 중... {pct}%  ({mb_cur:.1f} / {mb_tot:.1f} MB)"
            )

    def append_log(self, message: str):
        """로그 메시지 추가"""
        self._log_area.append(message)
        sb = self._log_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def mark_complete(self):
        """모든 단계 완료 상태로 전환"""
        self._is_finished = True
        for i, (num, name) in enumerate(_STEPS):
            lbl = self._step_labels[i]
            lbl.setText(f"✓  {num}단계: {name}")
            lbl.setStyleSheet(StyleSheet.step_label_done())
        self._progress_bar.setValue(100)
        self._status_label.setText("모든 작업이 완료되었습니다!")
        self._stop_btn.setEnabled(False)
        self._stop_btn.setText("완료")

    def mark_cancelled(self):
        """취소/오류 상태로 전환"""
        self._is_finished = True
        self._stop_btn.setEnabled(False)
        self._stop_btn.setText("닫기")
        # 닫기 가능하도록 설정
        self._stop_btn.setEnabled(True)
        self._stop_btn.clicked.disconnect()
        self._stop_btn.clicked.connect(self.accept)

    def closeEvent(self, event):
        """처리 중 강제 닫기 방지"""
        if not self._is_finished and self._stop_btn.isEnabled():
            event.ignore()
        else:
            event.accept()
