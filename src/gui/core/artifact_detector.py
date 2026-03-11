"""
기존 파이프라인 산출물 감지 모듈

다운로드 디렉토리를 스캔하여 이전 실행에서 생성된 산출물(MP4, WAV, TXT 등)을
감지하고, 파이프라인을 이어서 실행할 수 있는 시작 단계를 추천한다.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple

from src.pipeline_stage import PipelineStage, ARTIFACT_EXTENSIONS


class ArtifactDetector:
    """다운로드 디렉토리의 기존 산출물을 감지"""

    def __init__(self, directory: str):
        self.directory = directory

    def scan(self) -> Dict[PipelineStage, List[str]]:
        """디렉토리를 재귀적으로 스캔하여 단계별 산출물 분류

        Returns:
            각 PipelineStage에 해당하는 파일 경로 목록
        """
        result: Dict[PipelineStage, List[str]] = {stage: [] for stage in PipelineStage}

        if not os.path.isdir(self.directory):
            return result

        for root, _dirs, files in os.walk(self.directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                stage = self._classify_file(filename)
                if stage is not None:
                    result[stage].append(filepath)

        return result

    def recommend_start_stage(self) -> Tuple[PipelineStage, List[str]]:
        """산출물 기반으로 다음 실행 단계를 추천

        Returns:
            (추천 시작 단계, 해당 단계의 입력 파일 목록)
        """
        artifacts = self.scan()

        # 가장 진행된 단계부터 역순으로 확인
        # .txt (요약되지 않은) 파일이 있으면 → SUMMARIZE 단계부터
        if artifacts[PipelineStage.STT]:
            return PipelineStage.SUMMARIZE, artifacts[PipelineStage.STT]

        # .wav/.mp3 파일이 있으면 → STT 단계부터
        if artifacts[PipelineStage.CONVERT_AUDIO]:
            return PipelineStage.STT, artifacts[PipelineStage.CONVERT_AUDIO]

        # .mp4/.ts 파일이 있으면 → CONVERT_AUDIO 단계부터
        if artifacts[PipelineStage.DOWNLOAD]:
            return PipelineStage.CONVERT_AUDIO, artifacts[PipelineStage.DOWNLOAD]

        # 아무것도 없으면 처음부터
        return PipelineStage.DOWNLOAD, []

    @staticmethod
    def _classify_file(filename: str) -> "PipelineStage | None":
        """파일명을 기반으로 파이프라인 단계를 분류"""
        lower = filename.lower()

        # *_summarized.txt → SUMMARIZE 단계의 산출물 (이미 완료)
        if lower.endswith("_summarized.txt"):
            return PipelineStage.SUMMARIZE

        # .txt (요약 아닌 것) → STT 단계의 산출물
        if lower.endswith(".txt"):
            return PipelineStage.STT

        # .wav, .mp3 → CONVERT_AUDIO 단계의 산출물
        for ext in ARTIFACT_EXTENSIONS[PipelineStage.CONVERT_AUDIO]:
            if lower.endswith(ext):
                return PipelineStage.CONVERT_AUDIO

        # .mp4, .ts → DOWNLOAD 단계의 산출물
        for ext in ARTIFACT_EXTENSIONS[PipelineStage.DOWNLOAD]:
            if lower.endswith(ext):
                return PipelineStage.DOWNLOAD

        return None
