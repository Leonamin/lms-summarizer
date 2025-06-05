from audio_pipeline.pipeline import AudioToTextPipeline
from summarize_pipeline.pipeline import SummarizePipeline
from user_setting import UserSetting
from video_pipeline.pipeline import VideoPipeline


def get_video_urls(user_setting: UserSetting) -> list[str]:
    result = user_setting.get_video_urls()
    if result:
        return result
    return user_setting.input_video_urls()


def main():
    user_setting = UserSetting()
    print("[INFO] 비디오 다운로드 파이프라인 시작")

    # 비디오 다운로드 파이프라인
    video_pipeline = VideoPipeline(user_setting)
    urls = get_video_urls(user_setting)
    print(f"[INFO] 다운로드할 링크: {len(urls)}개")
    downloaded_videos_path = video_pipeline.process_sync(urls)

    # 오디오 파이프라인 처리
    audio_pipeline = AudioToTextPipeline()
    txt_paths = []
    for filepath in downloaded_videos_path:
        try:
            print(f"[INFO] 동영상 텍스트 변환 시작: {filepath}")
            txt_path = audio_pipeline.process(filepath)
            txt_paths.append(txt_path)
        except Exception as e:
            print(f"[ERROR] 동영상 텍스트 변환 실패: {e}")

    # 요약 파이프라인 처리
    summarized_txt_paths = []
    summarize_pipeline = SummarizePipeline()
    for txt_path in txt_paths:
        try:
            summarized_txt_path = summarize_pipeline.process(txt_path)
            summarized_txt_paths.append(summarized_txt_path)
        except Exception as e:
            print(f"[ERROR] 요약 파이프라인 처리 실패: {e}")

    print("[INFO] 모든 동영상 요약 완료. 저장된 파일 경로를 출력합니다.")
    for path in summarized_txt_paths:
        print(f"[INFO] 요약 파일 경로: {path}")

    print("\n[INFO] 모든 작업이 완료되었습니다.")


# 진입점
if __name__ == "__main__":
    main()
