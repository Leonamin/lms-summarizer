"""Reserved raw uploads, bounded streaming and validation before core import."""
import codecs
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
from uuid import uuid4
from src.core.models.jobs import ServiceError
from src.core.models.settings import UserContext
from src.core.repositories.json_store import JsonStore
from src.core.repositories.jobs import utcnow
from src.core.validation import initial_stage

class Uploads:
    def __init__(self, config, service):
        self.config, self.service = config, service
        self.context = UserContext()
        self.store = JsonStore(Path(config.data_dir) / 'uploads.json')
        self.root = Path(config.data_dir) / 'incoming'
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = self.store.lock
        with self.lock:
            state = self.store.read()
            for record in state.values():
                if record['status'] == 'uploading':
                    record.update(status='failed', received_size=0)
            self.store.write(state)
        for folder in self.root.iterdir():
            if folder.is_dir():
                shutil.rmtree(folder)
        self.cleanup()

    def reserve(self, request):
        filename = request.filename
        if Path(filename).name != filename or '\\' in filename or filename in ('.', '..') or any(ord(char) < 32 for char in filename):
            raise ServiceError('invalid_filename')
        try:
            initial_stage(filename)
        except ValueError:
            raise ServiceError('unsupported_file') from None
        limit = min(self.config.max_upload_bytes, self.config.max_text_bytes) if filename.lower().endswith('.txt') else self.config.max_upload_bytes
        if request.size > limit:
            raise ServiceError('input_too_large')
        with self.lock:
            state = self.store.read()
            pending = sum(r['expected_size'] for r in state.values() if r['status'] in ('pending', 'uploading'))
            if shutil.disk_usage(self.root).free < self.config.min_free_bytes + 2 * (pending + request.size):
                raise ServiceError('disk_full')
            record = {'id': str(uuid4()), 'filename': filename, 'expected_size': request.size,
                      'received_size': 0, 'status': 'pending', 'artifact_id': None, 'created_at': utcnow()}
            state[record['id']] = record
            self.store.write(state)
            return record

    def get(self, upload_id):
        record = self.store.read().get(str(upload_id))
        if not record:
            raise ServiceError('not_found')
        return record

    def claim(self, upload_id):
        with self.lock:
            record = self.get(upload_id)
            if record['status'] not in ('pending', 'failed'):
                raise ServiceError('upload_conflict')
            self._update(str(upload_id), status='uploading', received_size=0)
            folder = self.root / str(upload_id)
            folder.mkdir(exist_ok=True)
            return record, folder / record['filename']

    def _update(self, upload_id, **values):
        self.store.update(lambda state: state[upload_id].update(values))

    def check_disk(self, size):
        if shutil.disk_usage(self.root).free < self.config.min_free_bytes + size:
            raise ServiceError('disk_full')

    def finish(self, upload_id, path, received):
        record = self.get(upload_id)
        if received != record['expected_size']:
            raise ServiceError('upload_size_mismatch')
        try:
            if path.suffix.lower() == '.txt':
                decoder = codecs.getincrementaldecoder('utf-8-sig')()
                with path.open('rb') as stream:
                    while chunk := stream.read(1024 * 1024):
                        if '\x00' in decoder.decode(chunk):
                            raise ValueError('binary text')
                    decoder.decode(b'', final=True)
            else:
                import av
                with av.open(str(path)) as media:
                    expected = media.streams.video if path.suffix.lower() in ('.mp4', '.ts') else media.streams.audio
                    if not expected or not any(packet.size for packet in media.demux(expected[0])):
                        raise ValueError('no media stream')
        except Exception:
            raise ServiceError('invalid_file_content') from None
        self.check_disk(received)
        artifact = self.service.import_file(self.context, path)
        self._update(str(upload_id), status='ready', received_size=received, artifact_id=artifact)
        return self.get(upload_id)

    def fail(self, upload_id):
        self._update(str(upload_id), status='failed', received_size=0)

    def remove(self, upload_id):
        with self.lock:
            record = self.get(upload_id)
            if record['status'] == 'uploading':
                raise ServiceError('upload_conflict')
            if record['artifact_id']:
                self.service.delete_input(self.context, record['artifact_id'])
            self.store.update(lambda state: state.pop(str(upload_id)))
            shutil.rmtree(self.root / str(upload_id), ignore_errors=True)

    def source(self, upload_id):
        record = self.get(upload_id)
        if record['status'] != 'ready':
            raise ServiceError('upload_not_ready')
        return record['artifact_id']

    def cleanup(self):
        now = datetime.now(timezone.utc)
        for record in self.store.read().values():
            if record['status'] != 'uploading' and (now - datetime.fromisoformat(record['created_at'])).total_seconds() > 86400:
                try:
                    self.remove(record['id'])
                except ServiceError:
                    pass  # Referenced inputs are retained for attempts/history.
