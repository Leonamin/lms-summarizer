"""Application-owned job service and desktop result/host adapters (no Flet)."""
import os
from datetime import datetime
from pathlib import Path
import shutil
import threading
from uuid import uuid4

from src.core.models.jobs import Source
from src.core.models.settings import PromptSettings, UserContext
from src.core.repositories.json_store import JsonStore
from src.core.services.jobs import JobService
from src.core.services.settings import snapshot_settings
from src.core.validation import initial_stage
from src.desktop import legacy_storage as storage
from src.desktop.actions import open_chatbot


class DesktopRuntime:
    def __init__(self, root=None, *, service=None, chatbot_action=open_chatbot,
                 folder_action=storage.open_in_file_explorer, history_path=None):
        root = Path(root or (Path(storage.get_app_data_dir()) / 'runtime'))
        self.service = service or JobService(root)
        self.context = UserContext()
        self.state = JsonStore(root / 'desktop.json')
        self.history = JsonStore(history_path or storage.get_settings_path())
        self.chatbot_action, self.folder_action = chatbot_action, folder_action
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.listeners = []
        self._last_states = {}
        self.thread = None
        self.closed = False

    def start(self):
        with self.lock:
            if self.thread is not None:
                return
            self.service.start()
            self.thread = threading.Thread(target=self._observe, name='desktop-events', daemon=True)
            self.thread.start()

    def jobs(self):
        jobs, after = [], 0
        while True:
            page = self.service.list_jobs(self.context, after=after, limit=200)
            jobs.extend(page['jobs'])
            if not page['jobs']:
                return jobs
            after = page['next_cursor']

    def subscribe(self, callback):
        with self.lock:
            self.listeners.append(callback)
        def unsubscribe():
            with self.lock:
                if callback in self.listeners:
                    self.listeners.remove(callback)
        return unsubscribe

    def _emit(self, job=None, message=None):
        with self.lock:
            listeners = tuple(self.listeners)
        for callback in listeners:
            try:
                callback(job, message)
            except Exception:
                # A closed UI session must not stop processing or other subscribers.
                pass

    def submit(self, urls, files, options):
        """Translate legacy UI settings to an immutable, secret-free revision."""
        with self.lock:
            for path in files:
                initial_stage(Path(path).name)
            inputs = options['user_inputs']
            params = dict(options.get('stt_params', {}))
            credentials = {
                'lms_password': inputs.get('password', ''),
                'summary_api_key': inputs.get('api_key', ''),
                'stt_api_key': params.pop('api_key', ''),
                'returnzero_client_id': params.pop('client_id', ''),
                'returnzero_client_secret': params.pop('client_secret', ''),
            }
            for name in ('returnzero_client_id', 'returnzero_client_secret'):
                credentials[name] = params.pop(name, '') or credentials[name]
            settings = {
                'student_id': inputs.get('student_id', ''),
                'ai_engine': options['engine'], 'ai_model': options['model_name'],
                'base_url': options.get('base_url', ''),
                'stt_engine': options['stt_engine'], 'stt_model': options['stt_model'],
                'stt_base_url': params.pop('base_url', ''),
                'stt_compatible_model': params.pop('model_name', ''),
                'stt_params': params, 'keep_source': bool(options.get('save_video_dir')),
                'chrome_path': options.get('chrome_path'), 'headless': options.get('headless', True),
            }
            if settings['stt_engine'] == 'faster-whisper':
                params.setdefault('device', 'auto')
                params.setdefault('compute_type', 'auto')
            state = self.state.read()
            refs = state.setdefault('secrets', {})
            versions = {}
            for name, value in credentials.items():
                if not value:
                    continue
                previous = refs.get(name)
                try:
                    old_value = self.service.secrets.get(self.context.owner_id, previous) if previous else None
                except KeyError:
                    old_value = None
                if old_value != value:
                    previous = self.service.secrets.put(self.context.owner_id, name, value)
                    refs[name] = previous
                versions[name] = previous
            revision = snapshot_settings(self.context.owner_id, settings,
                PromptSettings(mode='custom', custom_prompt=options['summary_prompt']), versions)
            # Persist desktop destinations before a worker can finish the new job.
            state.setdefault('revisions', {})[revision.id] = {
                'downloads_dir': str(Path(options['downloads_dir']).resolve()),
                'auto_open_folder': options.get('auto_open_folder', storage.get_auto_open_folder()),
                'ai_model': options['model_name'],
            }
            self.state.write(state)
            sources = [Source.url(url) for url in urls]
            sources.extend(Source.file(self.service.import_file(self.context, Path(path))) for path in files)
            job_ids = self.service.submit(self.context, sources, revision, idempotency_key=str(uuid4()))
            state.setdefault('jobs', {}).update({job_id: {'url': source.reference if source.kind == 'url' else ''}
                                                 for job_id, source in zip(job_ids, sources)})
            self.state.write(state)
            return job_ids

    def cancel(self, job_id, attempt_id):
        self.service.cancel(self.context, job_id, attempt_id)

    def cancel_all(self):
        self.service.cancel_all(self.context)

    def retry(self, job_id, attempt_id):
        return self.service.retry(self.context, job_id, attempt_id, idempotency_key=str(uuid4()))

    def _observe(self):
        try:
            # Subscribing from zero is safe: completion exports are idempotent by attempt.
            for job in self.jobs():
                self._update(job)
            for event in self.service.subscribe(self.context, stop=self.stop, heartbeat=1):
                if self.stop.is_set():
                    break
                if event.get('job_id'):
                    self._update(self.service.detail(self.context, event['job_id']))
                elif event.get('type') == 'reset':
                    for job in self.jobs():
                        self._update(job)
        except Exception as exc:
            if not self.stop.is_set():
                self._emit(message=f'작업 상태 구독 실패: {type(exc).__name__}')

    def _update(self, job):
        attempt = job['attempts'][-1]
        marker = (job['current_attempt_id'], job['status'], attempt['current_stage'])
        if self._last_states.get(job['id']) != marker:
            self._last_states[job['id']] = marker
            labels = {'queued': '대기', 'running': '실행', 'cancelling': '중지 중',
                      'completed': '완료', 'failed': '실패', 'cancelled': '취소', 'interrupted': '중단'}
            stages = {1: '다운로드', 2: '변환', 3: 'STT', 4: '요약'}
            status = '프롬프트 준비 완료' if job['result_kind'] == 'manual_ready' else labels[job['status']]
            error = attempt.get('safe_message') or attempt.get('error_code') or ''
            self._emit(message=f"{job['display_name']}: {stages[attempt['current_stage']]} · {status}" + (f" ({error})" if error else ''))
        if job['status'] == 'completed':
            try:
                self.export(job)
            except Exception as exc:
                self._emit(message=f"결과 내보내기 실패 ({job['display_name']}): {type(exc).__name__}")
        self._emit(job=job)

    def export(self, job):
        """Copy retained artifacts into a collision-free desktop result directory."""
        with self.lock:
            state = self.state.read()
            attempt_id = job['current_attempt_id']
            exports = state.setdefault('exports', {})
            if attempt_id in exports:
                return Path(exports[attempt_id])
            destination = state.get('revisions', {}).get(job['settings_revision_id'], {})
            base = Path(destination.get('downloads_dir') or storage.ensure_downloads_directory())
            folder = base / f"job-{job['id']}-{attempt_id}"
            folder.mkdir(parents=True, exist_ok=True)
            paths = {}
            for artifact in job['artifacts']:
                if artifact['state'] != 'complete' or artifact['attempt_id'] not in (None, '', attempt_id):
                    continue
                source = self.service.artifact_path(self.context, artifact['id'])
                target = folder / (artifact['kind'] + source.suffix)
                temp = target.with_suffix(target.suffix + '.tmp')
                shutil.copyfile(source, temp)
                os.replace(temp, target)
                paths[artifact['kind']] = target
            attempt = job['attempts'][-1]
            started, ended = attempt.get('started_at'), attempt.get('ended_at')
            duration = max(0, (datetime.fromisoformat(ended) - datetime.fromisoformat(started)).total_seconds()) if started and ended else 0
            lecture_name = next((a['display_name'] for a in job['artifacts'] if a['kind'] == 'video'
                                 and a['attempt_id'] == attempt_id), job['display_name'])
            source_url = state.get('jobs', {}).get(job['id'], {}).get('url', '')
            size = next((a['size'] for a in job['artifacts'] if a['kind'] in ('input', 'video')), 0)
            def history_change(raw):
                history = raw.setdefault('history', [])
                if not any(entry.get('attempt_id') == attempt_id for entry in history):
                    history.append({
                        'job_id': job['id'], 'attempt_id': attempt_id,
                        'url': source_url,
                        'lecture_name': lecture_name, 'file_size_mb': round(size / 1024**2, 2), 'duration_sec': duration,
                        'summary_path': str(paths.get('summary') or paths.get('prompt') or folder),
                        'processed_at': job['attempts'][-1].get('ended_at') or job['created_at'],
                        'result_kind': job['result_kind'],
                    })
            self.history.update(history_change)
            exports[attempt_id] = str(folder)
            self.state.write(state)
        self._emit(message=f"결과 저장: {folder}")
        if 'prompt' in paths:
            self.copy_prompt(job)
        if destination.get('auto_open_folder'):
            try:
                self.folder_action(str(folder))
            except Exception as exc:
                self._emit(message=f'결과 폴더 열기 실패: {type(exc).__name__}')
        return folder

    def copy_prompt(self, job):
        from src.summarize_pipeline.providers.clipboard_provider import CHATBOT_URLS
        destination = self.state.read().get('revisions', {}).get(job['settings_revision_id'], {})
        prompt = next(a for a in job['artifacts'] if a['kind'] == 'prompt'
                      and a['attempt_id'] == job['current_attempt_id'] and a['state'] == 'complete')
        try:
            text = self.service.artifact_path(self.context, prompt['id']).read_text(encoding='utf-8')
            self.chatbot_action(text, CHATBOT_URLS.get(destination.get('ai_model'), CHATBOT_URLS['chatgpt']))
            self._emit(message='프롬프트 복사 및 챗봇 열기 완료')
        except Exception as exc:
            self._emit(message=f'프롬프트는 저장되었습니다. 복사·챗봇 열기 실패: {type(exc).__name__}')

    def open_result(self, job):
        self.folder_action(str(self.export(job)))

    def close(self):
        with self.lock:
            if self.closed:
                return
            self.closed = True
            self.listeners.clear()
            self.stop.set()
        with self.service.changed:
            self.service.changed.notify_all()
        if self.thread:
            self.thread.join()
        self.service.close()
