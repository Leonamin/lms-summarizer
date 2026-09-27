import asyncio
import json
import os
from pathlib import Path
import shutil
import time
from uuid import UUID
from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool
from src.core.models.jobs import Source, ServiceError
from src.core.models.settings import UserContext
from src.core.models.stages import PipelineStage
from src.web.schemas import AttemptCommand, JobCreate, SecretPut, SettingsPatch, UploadCreate

router = APIRouter(prefix='/api/v1')
OWNER = UserContext()

@router.get('/me')
def me():
    return {'owner_id': 'local', 'authentication': 'none'}

@router.get('/settings')
def settings(request: Request):
    return request.app.state.settings.public()

@router.patch('/settings')
def patch_settings(body: SettingsPatch, request: Request):
    return request.app.state.settings.patch(body)

@router.put('/secrets/{provider}')
def put_secret(provider: str, body: SecretPut, request: Request):
    return request.app.state.settings.put_secret(provider, body.value)

@router.delete('/secrets/{provider}')
def delete_secret(provider: str, request: Request):
    return request.app.state.settings.delete_secret(provider)

@router.post('/uploads', status_code=201)
def upload_create(body: UploadCreate, request: Request):
    return request.app.state.uploads.reserve(body)

@router.get('/uploads/{upload_id}')
def upload_get(upload_id: UUID, request: Request):
    return request.app.state.uploads.get(upload_id)

@router.delete('/uploads/{upload_id}', status_code=204)
def upload_delete(upload_id: UUID, request: Request):
    request.app.state.uploads.remove(upload_id)

@router.put('/uploads/{upload_id}/content')
async def upload_content(upload_id: UUID, request: Request):
    uploads = request.app.state.uploads
    record, path = await run_in_threadpool(uploads.claim, upload_id)
    partial = path.with_suffix(path.suffix + '.part')
    received = 0
    stream = None
    try:
        stream = await run_in_threadpool(partial.open, 'wb')
        async for chunk in request.stream():
            received += len(chunk)
            if received > record['expected_size'] or received > uploads.config.max_upload_bytes:
                raise ServiceError('input_too_large')
            await run_in_threadpool(uploads.check_disk, len(chunk))
            await run_in_threadpool(stream.write, chunk)
        await run_in_threadpool(stream.flush)
        await run_in_threadpool(os.fsync, stream.fileno())
        await run_in_threadpool(stream.close)
        stream = None
        await run_in_threadpool(os.replace, partial, path)
        return await run_in_threadpool(uploads.finish, upload_id, path, received)
    except BaseException:
        await run_in_threadpool(uploads.fail, str(upload_id))
        raise
    finally:
        if stream:
            await run_in_threadpool(stream.close)
        await run_in_threadpool(shutil.rmtree, path.parent, True)

@router.post('/jobs', status_code=202)
def submit(body: JobCreate, request: Request, idempotency_key: str = Header(min_length=1, max_length=200)):
    state = request.app.state
    sources = [Source.file(state.uploads.source(source.reference)) if source.kind == 'file'
               else Source.url(source.reference) for source in body.sources]
    revision = state.settings.snapshot(body.settings_revision)
    ids = state.service.submit(OWNER, sources, revision, end_stage=PipelineStage(body.end_stage), idempotency_key=idempotency_key)
    return {'job_ids': ids}

@router.get('/jobs')
def jobs(request: Request, cursor: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=200), status: str | None = None):
    return request.app.state.service.list_jobs(OWNER, after=cursor, limit=limit, status=status)

@router.post('/jobs/cancel-all')
def cancel_all(request: Request):
    return {'cancelled': request.app.state.service.cancel_all(OWNER)}

@router.get('/jobs/{job_id}')
def detail(job_id: UUID, request: Request):
    return request.app.state.service.detail(OWNER, str(job_id))

@router.get('/jobs/{job_id}/settings')
def job_settings(job_id: UUID, request: Request):
    state = request.app.state
    job = state.service.detail(OWNER, str(job_id))
    revision = state.settings.snapshot(job['settings_revision_id'])
    public_settings = json.loads(revision.settings_json)
    public_settings.pop('chrome_path', None)
    return {'settings': public_settings, 'resolved_prompt': revision.resolved_prompt}

@router.post('/jobs/{job_id}/cancel')
def cancel(job_id: UUID, body: AttemptCommand, request: Request):
    service = request.app.state.service
    service.cancel(OWNER, str(job_id), str(body.attempt_id))
    return service.detail(OWNER, str(job_id))

@router.post('/jobs/{job_id}/retry', status_code=202)
def retry(job_id: UUID, body: AttemptCommand, request: Request, idempotency_key: str = Header(min_length=1, max_length=200)):
    service = request.app.state.service
    service.retry(OWNER, str(job_id), str(body.attempt_id), idempotency_key=idempotency_key)
    return service.detail(OWNER, str(job_id))

@router.get('/artifacts/{artifact_id}/content')
def content(artifact_id: UUID, request: Request):
    service = request.app.state.service
    path = service.artifact_path(OWNER, str(artifact_id))
    if path.suffix.lower() != '.txt':
        raise ServiceError('not_text')
    if path.stat().st_size > request.app.state.config.content_limit:
        raise ServiceError('content_too_large')
    return {'text': path.read_text(encoding='utf-8-sig')}

@router.get('/artifacts/{artifact_id}/download')
def download(artifact_id: UUID, request: Request):
    service = request.app.state.service
    path = service.artifact_path(OWNER, str(artifact_id))
    return FileResponse(path, filename=path.name, media_type='application/octet-stream', headers={'X-Content-Type-Options': 'nosniff'})

@router.get('/events')
async def events(request: Request, cursor: int = Query(default=0, ge=0), last_event_id: str | None = Header(default=None)):
    if last_event_id is not None:
        try:
            cursor = int(last_event_id)
        except ValueError:
            raise ServiceError('invalid_cursor') from None
    service = request.app.state.service
    async def stream():
        nonlocal cursor
        heartbeat = time.monotonic()
        while not await request.is_disconnected():
            batch = await run_in_threadpool(service.events_since, OWNER, cursor)
            if batch['reset']:
                cursor = batch['cursor']
                yield f'id: {cursor}\nevent: reset\ndata: {{}}\n\n'
            else:
                for event in batch['events']:
                    cursor = event['seq']
                    yield f"id: {cursor}\nevent: {event['type']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            if time.monotonic() - heartbeat > 15:
                yield ': heartbeat\n\n'
                heartbeat = time.monotonic()
            await asyncio.sleep(.25)
    return StreamingResponse(stream(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@router.get('/system')
def system(request: Request):
    import sqlite3
    from src import __version__
    config = request.app.state.config
    return {'version': __version__, 'sqlite_version': sqlite3.sqlite_version,
            'free_bytes': shutil.disk_usage(config.data_dir).free,
            'chrome_available': Path(config.chrome_path).is_file(),
            'limits': {'upload_bytes': config.max_upload_bytes, 'text_bytes': config.max_text_bytes,
                       'batch': 50, 'active_jobs': 200},
            'stage_counts': request.app.state.service.stage_counts(OWNER)}
