from audio_pipeline.pipeline import AudioToTextPipeline


if __name__ == "__main__":

    pipeline = AudioToTextPipeline()
    pipeline.process(
        "/Users/lsm/dev/project/lms-summarizer/downloads/037_7장_5_PEP8_3.mp4"
    )
