import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src.core.models.jobs import Source, StageCommand, WorkToken
from src.core.models.settings import UserContext
from src.core.models.stages import PipelineStage
from src.core.runtime.executor import PipelineExecutor
from src.core.runtime.processes import CancellationFlag
from src.core.services.jobs import JobService
from src.core.services.settings import snapshot_settings
from src.core.models.settings import PromptSettings

class PipelineRuntimeTests(unittest.TestCase):
    def token(self, stage):
        return WorkToken('job','attempt','run','generation',stage)

    def test_real_manual_prompt_and_no_host_actions(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'source.txt'
            path.write_text('\ufefflecture body')
            command = StageCommand(self.token(PipelineStage.SUMMARIZE),str(path),str(Path(root)/'output'),
                                   json.dumps({'ai_engine':'clipboard'}),'fixed prompt')
            executor = PipelineExecutor()
            result = executor.execute(command,threading.Event())
            self.assertEqual(result.kind,'prompt')
            self.assertEqual(Path(result.output).read_text(),'fixed prompt\n\n다음 텍스트를 요약해줘:\n\nlecture body')
            executor.close()

    def test_actual_executor_model_reuse_and_change(self):
        instances = []
        closed = []
        def transcribe(source, output, _reuse_transcriber=None, **kwargs):
            model = _reuse_transcriber
            if model is None:
                model = types.SimpleNamespace(client=types.SimpleNamespace(close=lambda:closed.append(1)))
                instances.append(model)
            Path(output).write_text('text')
            return model
        fake = types.ModuleType('src.audio_pipeline.transcriber')
        fake.transcribe_audio_to_text = transcribe
        with tempfile.TemporaryDirectory() as root, patch.dict('sys.modules',{'src.audio_pipeline.transcriber':fake}):
            source = Path(root)/'source.wav'
            source.write_bytes(b'input')
            executor = PipelineExecutor()
            def run(model, number):
                command = StageCommand(self.token(PipelineStage.STT),str(source),str(Path(root)/str(number)),json.dumps({'stt_model':model}),'prompt')
                return executor.execute(command,threading.Event())
            self.assertFalse(run('model-a',1).model_reused)
            self.assertTrue(run('model-a',2).model_reused)
            self.assertFalse(run('model-b',3).model_reused)
            self.assertEqual(len(instances),2)
            self.assertEqual(len(closed),1)
            executor.close()
            self.assertEqual(len(closed),2)

    def test_custom_fallback_does_not_duplicate_uncertain_requests(self):
        from src.summarize_pipeline.providers.custom_provider import CustomProvider
        provider = CustomProvider.__new__(CustomProvider)
        provider._use_responses = None
        calls = []
        def fail():
            calls.append('responses')
            raise TimeoutError('ambiguous result')
        with patch.object(provider,'_summarize_via_responses',side_effect=lambda _:fail()), patch.object(provider,'_summarize_via_chat_completions',return_value='fallback') as chat:
            with self.assertRaises(TimeoutError):
                provider.summarize('text','prompt')
            chat.assert_not_called()
        error = RuntimeError('unsupported endpoint')
        error.status_code = 405
        with patch.object(provider,'_summarize_via_responses',side_effect=error), patch.object(provider,'_summarize_via_chat_completions',return_value='fallback') as chat:
            self.assertEqual(provider.summarize('text','prompt'),'fallback')
            chat.assert_called_once()

    @unittest.skipUnless(importlib.util.find_spec('av'),'PyAV not installed')
    def test_real_audio_conversion(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root)/'source.wav'
            with wave.open(str(source),'wb') as stream:
                stream.setnchannels(1)
                stream.setsampwidth(2)
                stream.setframerate(16000)
                stream.writeframes(b'\0\0'*1600)
            original = source.read_bytes()
            command = StageCommand(self.token(PipelineStage.CONVERT_AUDIO),str(source),str(Path(root)/'output'),'{}','prompt')
            executor = PipelineExecutor()
            result = executor.execute(command,threading.Event())
            self.assertEqual(result.kind,'audio')
            self.assertGreater(Path(result.output).stat().st_size,44)
            self.assertEqual(source.read_bytes(),original)
            executor.close()

    @unittest.skipUnless(importlib.util.find_spec('openai'),'OpenAI SDK not installed')
    def test_real_stt_http_adapter_then_manual_summary(self):
        calls = []
        failures = [0]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                calls.append((self.path,self.headers.get('Authorization')))
                self.rfile.read(int(self.headers['Content-Length']))
                failing = self.path.startswith('/fail') and failures[0] > 0
                if failing:
                    failures[0] -= 1
                body = b'{"error":{"message":"fixture error"}}' if failing else b'{"text":"local STT fixture"}'
                self.send_response(500 if failing else 200)
                self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self,*args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as root:
                with JobService(Path(root)/'data', min_free_bytes=0,shutdown_grace=0.2) as service:
                    path = Path(root)/'input.wav'
                    with wave.open(str(path),'wb') as stream:
                        stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(16000)
                        stream.writeframes(b'\0\0'*1600)
                    owner = UserContext()
                    key = service.secrets.put(owner.owner_id,'stt','fixture-key')
                    settings = snapshot_settings(owner.owner_id,{'ai_engine':'clipboard','stt_engine':'openai-compatible',
                        'stt_base_url':f'http://127.0.0.1:{server.server_port}/v1','stt_compatible_model':'fixture'},
                        PromptSettings(mode='custom',custom_prompt='fixed'),{'stt_api_key':key})
                    job = service.submit(owner,[Source.file(service.import_file(owner,path))],settings,idempotency_key='real')[0]
                    deadline=time.monotonic()+8
                    while time.monotonic()<deadline:
                        detail=service.detail(owner,job)
                        if detail['status'] not in ('queued','running'):
                            break
                        time.sleep(0.02)
                    self.assertEqual(detail['status'],'completed',detail)
                    self.assertEqual(detail['result_kind'],'manual_ready')
                    transcript=next(a for a in detail['artifacts'] if a['kind']=='transcript')
                    self.assertEqual(service.artifact_path(owner,transcript['id']).read_text(),'local STT fixture')
                    self.assertEqual(calls,[('/v1/audio/transcriptions','Bearer fixture-key')])
                    self.assertTrue(path.exists())
                    failures[0] = 1
                    failing_settings = snapshot_settings(owner.owner_id,{'ai_engine':'clipboard','stt_engine':'openai-compatible',
                        'stt_base_url':f'http://127.0.0.1:{server.server_port}/fail/v1','stt_compatible_model':'fixture'},
                        PromptSettings(mode='custom',custom_prompt='fixed'),{'stt_api_key':key})
                    failed = service.submit(owner,[Source.file(service.import_file(owner,path))],failing_settings,idempotency_key='http-fail')[0]
                    deadline=time.monotonic()+8
                    while time.monotonic()<deadline:
                        failed_detail=service.detail(owner,failed)
                        if failed_detail['status']=='failed':
                            break
                        time.sleep(0.02)
                    self.assertEqual(failed_detail['status'],'failed')
                    self.assertEqual(len(calls),2)  # 500 did not trigger any SDK retry.
                    service.retry(owner,failed,failed_detail['current_attempt_id'],idempotency_key='user-retry')
                    deadline=time.monotonic()+8
                    while time.monotonic()<deadline:
                        if service.detail(owner,failed)['status']=='completed':
                            break
                        time.sleep(0.02)
                    self.assertEqual(service.detail(owner,failed)['status'],'completed')
                    self.assertEqual(len(calls),3)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(2)

if __name__ == '__main__':
    unittest.main()
