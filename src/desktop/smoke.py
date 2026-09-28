"""Offline packaging diagnostic using the production spawned clipboard stage."""
import json
import sys
from pathlib import Path
import tempfile
import time
from src.core.models.jobs import Source
from src.core.models.settings import PromptSettings, UserContext
from src.core.services.jobs import JobService
from src.core.services.settings import snapshot_settings


def run():
    with tempfile.TemporaryDirectory(prefix='lms-smoke-') as directory:
        root = Path(directory)
        source = root / 'lecture.txt'
        source.write_text('패키징 검증 원문', encoding='utf-8')
        context = UserContext()
        revision = snapshot_settings('local', {'ai_engine': 'clipboard', 'ai_model': 'chatgpt'},
                                     PromptSettings(mode='custom', custom_prompt='검증 프롬프트'), {})
        with JobService(root / 'runtime', min_free_bytes=0) as service:
            artifact = service.import_file(context, source)
            job_id = service.submit(context, [Source.file(artifact)], revision, idempotency_key='smoke')[0]
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline:
                detail = service.detail(context, job_id)
                if detail['status'] in ('completed', 'failed', 'interrupted'):
                    break
                time.sleep(.05)
            assert detail['status'] == 'completed', detail
            assert detail['result_kind'] == 'manual_ready', detail
            prompt = next(a for a in detail['artifacts'] if a['kind'] == 'prompt')
            assert '패키징 검증 원문' in service.artifact_path(context, prompt['id']).read_text(encoding='utf-8')
            assert len(service._slots) == 4
        result = json.dumps({'status': 'ok', 'workers': 4, 'result_kind': 'manual_ready'})
        if '--core-smoke-result' in sys.argv:
            destination = Path(sys.argv[sys.argv.index('--core-smoke-result') + 1])
            destination.write_text(result, encoding='utf-8')
        print(result)
