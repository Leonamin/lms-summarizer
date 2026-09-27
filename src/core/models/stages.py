from enum import IntEnum


class PipelineStage(IntEnum):
    DOWNLOAD = 1        # 영상 다운로드
    CONVERT_AUDIO = 2   # MP4 → WAV 변환
    STT = 3             # STT 텍스트 변환
    SUMMARIZE = 4       # AI 요약


STAGE_LABELS = {
    PipelineStage.DOWNLOAD: "영상 다운로드",
    PipelineStage.CONVERT_AUDIO: "MP3/WAV 변환",
    PipelineStage.STT: "음성 → 텍스트 변환",
    PipelineStage.SUMMARIZE: "AI 요약 생성",
}

ARTIFACT_EXTENSIONS = {
    PipelineStage.DOWNLOAD: [".mp4", ".ts"],
    PipelineStage.CONVERT_AUDIO: [".wav", ".mp3"],
    PipelineStage.STT: [".txt"],  # excluding *_summarized.txt
    PipelineStage.SUMMARIZE: ["_summarized.txt"],
}
