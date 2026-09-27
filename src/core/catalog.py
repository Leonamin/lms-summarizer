"""Expose the application's existing provider/model registry without constructing clients."""
from src.core.prompts import SUBJECT_CATEGORIES, SUMMARY_MODE_LABELS, DEFAULT_PROMPT
from src.audio_pipeline.model_manager import FW_MODEL_REGISTRY

def catalog():
    from src.summarize_pipeline.providers import ENGINE_REGISTRY, ClipboardProvider
    summary = {name: {'default_model': cls.default_model(), 'models': [{'id': model, 'label': label} for model, label in cls.available_models()]}
               for name, cls in {'clipboard': ClipboardProvider, **ENGINE_REGISTRY}.items()}
    return {'summary': summary,
            'stt': {'faster-whisper': {'default_model': 'large-v3-turbo', 'models': [{'id': name, 'label': item['label'], 'size_mb': item['size_mb']} for name,item in FW_MODEL_REGISTRY.items()]},
                    'openai-whisper': {'default_model': 'whisper-1', 'models': [{'id':'whisper-1','label':'Whisper API'}]},
                    'openai-compatible': {'default_model': 'faster-whisper-small', 'models': []},
                    'returnzero': {'default_model': '', 'models': []}},
            'summary_modes': SUMMARY_MODE_LABELS, 'subject_categories': list(SUBJECT_CATEGORIES),
            'default_prompt': DEFAULT_PROMPT, 'input_extensions': ['mp4','ts','wav','mp3','txt']}
