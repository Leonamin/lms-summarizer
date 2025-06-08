"""
백그라운드에서 LMS 처리 작업을 수행하는 워커 스레드
"""

import traceback
from pathlib import Path
from typing import Dict, List
from PyQt5.QtCore import QThread, pyqtSignal

from src.gui.config.constants import Messages
from src.gui.core.file_manager import (
    create_config_files, extract_urls_from_input,
    ensure_downloads_directory
)
from src.gui.core.module_loader import check_required_modules


class ProcessingWorker(QThread):
    """백그라운드에서 LMS 처리 작업을 수행하는 워커 스레드"""

    # 시그널 정의
    log_message = pyqtSignal(str)
    processing_finished = pyqtSignal(bool, str)

    def __init__(self, user_inputs: Dict[str, str], modules: Dict):
        super().__init__()
        self.user_inputs = user_inputs
        self.modules = modules
        self.downloads_dir = ensure_downloads_directory()

    def run(self):
        """실제 처리 작업 실행"""
        try:
            self._emit_log(Messages.PROCESSING_START)

            # 모듈 검증
            if not self._validate_modules():
                return

            # 설정 파일 생성
            self._create_configuration()

            # 메인 처리 파이프라인 실행
            self._execute_processing_pipeline()

            # 완료 메시지
            self._emit_log(Messages.PROCESSING_COMPLETE)
            self.processing_finished.emit(True, "작업이 성공적으로 완료되었습니다.")

        except Exception as e:
            error_msg = f"작업 중 오류 발생: {str(e)}"
            self._emit_log(f"{Messages.MODULE_LOAD_ERROR.split()[0]} {error_msg}")
            self._emit_log(f"상세 오류:\n{traceback.format_exc()}")
            self.processing_finished.emit(False, error_msg)

    def _emit_log(self, message: str):
        """로그 메시지 출력"""
        self.log_message.emit(message)

    def _validate_modules(self) -> bool:
        """필수 모듈들이 모두 로드되었는지 확인"""
        all_loaded, missing_modules = check_required_modules(self.modules)

        if not all_loaded:
            self._emit_log(f"{Messages.MODULE_LOAD_ERROR}: {', '.join(missing_modules)}")
            self._emit_log(Messages.INSTALL_REQUIREMENTS)
            self.processing_finished.emit(False, f"필수 모듈 누락: {', '.join(missing_modules)}")
            return False

        return True

    def _create_configuration(self):
        """설정 파일들 생성"""
        self._emit_log(Messages.CONFIG_CREATING)
        create_config_files(self.user_inputs)

    def _execute_processing_pipeline(self):
        """메인 처리 파이프라인 실행"""
        # URL 목록 추출
        urls = extract_urls_from_input(self.user_inputs.get('urls', ''))

        if not urls:
            raise ValueError("처리할 URL이 없습니다.")

        # 사용자 설정 초기화
        user_setting = self.modules['UserSetting']()

        # 1. 비디오 다운로드 파이프라인
        video_paths = self._download_videos(urls, user_setting)

        # 2. 오디오를 텍스트로 변환
        text_paths = self._convert_audio_to_text(video_paths)

        # 3. 텍스트 요약
        self._summarize_texts(text_paths)

        # 결과 정리
        self._display_results(video_paths, text_paths)

    def _download_videos(self, urls: List[str], user_setting) -> List[str]:
        """비디오 다운로드"""
        self._emit_log(f"{Messages.VIDEO_DOWNLOADING}")
        self._emit_log(f"📋 다운로드할 링크: {len(urls)}개")

        video_pipeline = self.modules['VideoPipeline'](user_setting)
        video_pipeline.downloads_dir = self.downloads_dir  # 다운로드 경로 설정

        for i, url in enumerate(urls, 1):
            self._emit_log(f"📥 ({i}/{len(urls)}) 다운로드 시작: {url}")

        video_paths = video_pipeline.process_sync(urls)
        self._emit_log(f"{Messages.DOWNLOAD_COMPLETE}: {len(video_paths)}개 파일")

        # 다운로드된 파일 목록 출력
        self._emit_log("📁 다운로드된 파일들:")
        for i, filepath in enumerate(video_paths, 1):
            self._emit_log(f"   📹 ({i}) {filepath}")

        return video_paths

    def _convert_audio_to_text(self, video_paths: List[str]) -> List[str]:
        """오디오를 텍스트로 변환"""
        self._emit_log(Messages.AUDIO_CONVERTING)

        audio_pipeline = self.modules['AudioToTextPipeline']()
        audio_pipeline.downloads_dir = self.downloads_dir  # 다운로드 경로 설정

        text_paths = []
        for i, video_path in enumerate(video_paths, 1):
            self._emit_log(f"🎤 ({i}/{len(video_paths)}) 텍스트 변환 중: {Path(video_path).name}")
            text_path = audio_pipeline.process(video_path)
            text_paths.append(text_path)

        self._emit_log(f"{Messages.CONVERSION_COMPLETE}: {len(text_paths)}개 파일")
        self._emit_log("📄 변환된 텍스트 파일들:")
        for i, filepath in enumerate(text_paths, 1):
            self._emit_log(f"   📝 ({i}) {filepath}")

        return text_paths

    def _summarize_texts(self, text_paths: List[str]) -> List[str]:
        """텍스트 요약"""
        self._emit_log(Messages.TEXT_SUMMARIZING)

        summarize_pipeline = self.modules['SummarizePipeline']()
        summarize_pipeline.downloads_dir = self.downloads_dir  # 다운로드 경로 설정

        summarized_paths = []
        for i, text_path in enumerate(text_paths, 1):
            self._emit_log(f"📝 ({i}/{len(text_paths)}) 요약 생성 중: {Path(text_path).name}")
            summarized_path = summarize_pipeline.process(text_path)
            summarized_paths.append(summarized_path)

        self._emit_log(f"{Messages.SUMMARY_COMPLETE}: {len(summarized_paths)}개 파일")
        return summarized_paths

    def _display_results(self, video_paths: List[str], text_paths: List[str]):
        """결과 요약 표시"""
        self._emit_log("\n" + "="*50)

        if video_paths:
            self._emit_log("📹 다운로드된 동영상:")
            for path in video_paths:
                self._emit_log(f"   📄 {path}")

        if text_paths:
            self._emit_log("📝 변환된 텍스트:")
            for path in text_paths:
                self._emit_log(f"   📄 {path}")

        # 저장 위치 안내
        if video_paths or text_paths:
            self._emit_log(f"\n📁 모든 파일이 저장된 위치: {self.downloads_dir}")
            self._emit_log("💡 Finder에서 확인: open downloads/")

        self._emit_log("="*50)