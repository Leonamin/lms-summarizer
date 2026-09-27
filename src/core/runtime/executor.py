"""Production stage adapters. Constructed inside each persistent worker only."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
from src.core.models.jobs import StageResult, ServiceError
from src.core.models.stages import PipelineStage

class PipelineExecutor:
    def __init__(self):
        self._transcriber = None
        self._fingerprint = None

    def execute(self, command, cancelled):
        if cancelled.is_set():
            raise ServiceError('cancelled')
        settings = json.loads(command.settings_json)
        if command.catalog_query is not None:
            from src.core.services.courses import execute_query
            return execute_query(command)
        output = Path(command.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        token = command.token
        reused = False
        kind = {1:'video', 2:'audio', 3:'transcript', 4:'summary'}[token.stage]
        if token.stage == PipelineStage.DOWNLOAD:
            from src.video_pipeline.pipeline import VideoPipeline
            from src.core.models.settings import LMSCredentials
            password = command.credentials.get('lms_password')
            if not password or not settings.get('student_id'):
                raise ServiceError('credentials_missing')
            pipeline = VideoPipeline(LMSCredentials(settings['student_id'], password),
                                     chrome_path=settings.get('chrome_path'),
                                     headless=settings.get('headless', True),
                                     output_dir=str(output), log_callback=lambda _: None)
            async def download():
                try:
                    await pipeline.open_session()
                    return await pipeline.process_single_url(command.source)
                finally:
                    await pipeline.close_session()
            path = asyncio.run(download())
            if not path:
                raise ServiceError('download_failed')
        elif token.stage == PipelineStage.CONVERT_AUDIO:
            from src.audio_pipeline.converter import convert_audio_to_wav
            path = str(output / 'audio.wav')
            convert_audio_to_wav(command.source, path, settings.get('sample_rate', 16000))
        elif token.stage == PipelineStage.STT:
            from src.audio_pipeline.transcriber import transcribe_audio_to_text
            params = dict(settings.get('stt_params', {}))
            params['request_timeout'] = settings.get('request_timeout', 120)
            engine = settings.get('stt_engine', 'faster-whisper')
            model = settings.get('stt_model', 'large-v3-turbo')
            if engine == 'openai-whisper' and not command.credentials.get('stt_api_key'):
                raise ServiceError('credentials_missing')
            if engine == 'returnzero' and not all(command.credentials.get(k) for k in ('returnzero_client_id','returnzero_client_secret')):
                raise ServiceError('credentials_missing')
            if engine in ('openai-whisper', 'openai-compatible'):
                params['api_key'] = command.credentials.get('stt_api_key')
            if engine == 'openai-compatible':
                params['base_url'] = settings.get('stt_base_url')
                model = settings.get('stt_compatible_model') or model
            if engine == 'returnzero':
                params['client_id'] = command.credentials.get('returnzero_client_id')
                params['client_secret'] = command.credentials.get('returnzero_client_secret')
            if engine == 'faster-whisper':
                if command.model_cache_dir:
                    params['download_root'] = command.model_cache_dir
                params.setdefault('device', 'cpu')
                params.setdefault('compute_type', 'int8')
            fingerprint = hashlib.sha256(json.dumps([engine, model, params], sort_keys=True).encode()).hexdigest()
            reused = self._transcriber is not None and fingerprint == self._fingerprint
            if not reused:
                self._release_transcriber()  # Release model before allocating the replacement.
                self._fingerprint = None
            path = str(output / 'transcript.txt')
            self._transcriber = transcribe_audio_to_text(command.source, path, engine=engine,
                                                         model_name=model, params=params,
                                                         _reuse_transcriber=self._transcriber)
            self._fingerprint = fingerprint
        else:
            from src.summarize_pipeline.providers import create_provider
            text = Path(command.source).read_text(encoding='utf-8-sig')
            engine = settings.get('ai_engine', 'gemini')
            if engine not in ('clipboard', 'custom') and not command.credentials.get('summary_api_key'):
                raise ServiceError('credentials_missing')
            provider = create_provider(engine, api_key=command.credentials.get('summary_api_key'),
                                       model_name=settings.get('ai_model'), base_url=settings.get('base_url'),
                                       request_timeout=settings.get('request_timeout',120))
            try:
                result = provider.summarize(text, command.resolved_prompt)
            finally:
                client = getattr(provider, 'client', getattr(provider, '_client', None))
                if client and hasattr(client, 'close'):
                    client.close()
            kind = 'prompt' if engine == 'clipboard' else 'summary'
            path = str(output / ('prompt.txt' if kind == 'prompt' else 'summary.txt'))
            Path(path).write_text(result, encoding='utf-8')
        if cancelled.is_set():
            raise ServiceError('cancelled')
        path = Path(path)
        if not path.is_file() or path.stat().st_size == 0:
            raise ServiceError('output_missing')
        with path.open('rb') as stream:
            os.fsync(stream.fileno())
        return StageResult(token, str(path), kind, model_reused=reused)

    def _release_transcriber(self):
        client = getattr(self._transcriber, 'client', None)
        if client and hasattr(client, 'close'):
            client.close()
        self._transcriber = None

    def close(self):
        self._release_transcriber()
