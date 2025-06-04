import whisper


def transcribe_wav_to_text(wav_path: str, txt_path: str):
    _transcribe_wav_to_text_by_whisper(wav_path, txt_path)


def _transcribe_wav_to_text_by_whisper(wav_path: str, txt_path: str):
    model = whisper.load_model("base")
    result = model.transcribe(wav_path)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(result["text"])

def _transcribe_wav_to_text_by_openai(wav_path: str, txt_path: str):
    pass