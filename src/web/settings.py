"""Persistent web settings with optimistic edits and immutable submission snapshots."""
from dataclasses import asdict
import json
from pathlib import Path
from src.core.models.jobs import ServiceError
from src.core.models.settings import PromptSettings, SettingsRevision, UserContext
from src.core.repositories.json_store import JsonStore
from src.core.services.settings import snapshot_settings
from src.web.schemas import Settings

SECRET_NAMES = ('lms_password', 'returnzero_client_id', 'returnzero_client_secret',
                'summary:gemini', 'summary:openai', 'summary:claude', 'summary:grok', 'summary:custom',
                'stt:openai-whisper', 'stt:openai-compatible')

class WebSettings:
    def __init__(self, config, service):
        self.config, self.service = config, service
        self.owner = UserContext()
        self.store = JsonStore(Path(config.data_dir) / 'web-settings.json')
        self.lock = self.store.lock
        with self.lock:
            state = self.store.read()
            if not state:
                self._save({'revision': 1, 'settings': Settings().model_dump(), 'secrets': {}, 'snapshots': {}})
            else:
                fixed = state['snapshots'][state['settings_revision']]
                values = json.loads(fixed['settings_json'])
                if values.get('chrome_path') != config.chrome_path or values.get('headless') != config.headless:
                    state['revision'] += 1
                    self._save(state)

    def _save(self, state):
        values = dict(state['settings'])
        prompt = PromptSettings(mode=values.pop('prompt_mode'), summary_mode=values.pop('summary_mode'),
            subject_category=values.pop('subject_category'), subject_custom=values.pop('subject_custom'),
            custom_prompt=values.pop('custom_prompt'))
        values.update(chrome_path=self.config.chrome_path, headless=self.config.headless)
        refs = state['secrets']
        selected = {
            'lms_password': refs.get('lms_password'),
            'summary_api_key': refs.get('summary:' + values['ai_engine']),
            'stt_api_key': refs.get('stt:' + values['stt_engine']),
            'returnzero_client_id': refs.get('returnzero_client_id'),
            'returnzero_client_secret': refs.get('returnzero_client_secret'),
        }
        try:
            revision = snapshot_settings('local', values, prompt, {k: v for k, v in selected.items() if v})
        except ValueError:
            raise ServiceError('invalid_settings') from None
        state['settings_revision'] = revision.id
        state['snapshots'][revision.id] = asdict(revision)
        self.store.write(state)

    def public(self):
        state = self.store.read()
        return {k: (Settings(**state[k]).model_dump() if k == 'settings' else state[k]) for k in ('revision', 'settings', 'settings_revision')} | {
            'secrets': {name: {'configured': bool(state['secrets'].get(name))} for name in SECRET_NAMES}}

    def patch(self, request):
        with self.lock:
            state = self.store.read()
            if state['revision'] != request.expected_revision:
                raise ServiceError('settings_conflict')
            state['settings'] = request.settings.model_dump()
            state['revision'] += 1
            self._save(state)
            return self.public()

    def put_secret(self, name, value):
        if name not in SECRET_NAMES:
            raise ServiceError('not_found')
        with self.lock:
            state = self.store.read()
            state['secrets'][name] = self.service.secrets.put('local', name, value)
            state['revision'] += 1
            self._save(state)
        return {'configured': True}

    def delete_secret(self, name):
        if name not in SECRET_NAMES:
            raise ServiceError('not_found')
        with self.lock:
            state = self.store.read()
            version = state['secrets'].get(name)
            if version:
                self.service.delete_secret(self.owner, version)
                del state['secrets'][name]
                state['revision'] += 1
                self._save(state)
        return {'configured': False}

    def snapshot(self, revision_id):
        state = self.store.read()
        raw = state['snapshots'].get(str(revision_id))
        if not raw:
            raise ServiceError('settings_conflict')
        return SettingsRevision(**raw)
