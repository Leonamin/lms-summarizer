import os
import av


def convert_audio_to_wav(input_path: str, wav_path: str, sample_rate: int = 16000):
    """오디오/비디오 파일을 mono WAV로 변환.

    PyAV를 사용하므로 MP4, MP3, MKV, WebM 등 PyAV가 지원하는 모든 포맷을 처리합니다.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"입력 파일이 존재하지 않음: {input_path}")

    os.makedirs(os.path.dirname(wav_path), exist_ok=True)

    try:
        input_container = av.open(input_path)
        output_container = av.open(wav_path, mode='w')

        if not input_container.streams.audio:
            raise RuntimeError(f"오디오 스트림이 없음: {input_path}")

        output_stream = output_container.add_stream('pcm_s16le', rate=sample_rate)
        output_stream.layout = 'mono'

        resampler = av.AudioResampler(format='s16', layout='mono', rate=sample_rate)

        for frame in input_container.decode(audio=0):
            for resampled in resampler.resample(frame):
                for packet in output_stream.encode(resampled):
                    output_container.mux(packet)

        # 인코더 버퍼 플러시
        for packet in output_stream.encode(None):
            output_container.mux(packet)

        output_container.close()
        input_container.close()
    except av.AVError as e:
        raise RuntimeError(f"오디오 변환 오류: {e}")


# 하위 호환성 유지
convert_mp4_to_wav = convert_audio_to_wav
