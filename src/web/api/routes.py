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
from src.web.schemas import AttemptCommand, JobCreate, RetryCommand, SecretPut, SettingsPatch, UploadCreate, CourseRefresh, Settings, ContinueCommand

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
    sources = [Source.file(state.uploads.source(source.reference), display_name=source.display_name,
                           course_name=source.course_name, week_title=source.week_title) if source.kind == 'file'
               else Source.url(source.reference, display_name=source.display_name,
                               course_name=source.course_name, week_title=source.week_title)
               for source in body.sources]
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

def _adopted_revision(request: Request, use_current_settings: bool):
    """The current settings revision when a retry/resume opts into current settings."""
    if not use_current_settings:
        return None
    settings = request.app.state.settings
    return settings.snapshot(settings.public()['settings_revision'])

@router.post('/jobs/{job_id}/retry', status_code=202)
def retry(job_id: UUID, body: RetryCommand, request: Request, idempotency_key: str = Header(min_length=1, max_length=200)):
    state = request.app.state
    revision = _adopted_revision(request, body.use_current_settings)
    state.service.retry(OWNER, str(job_id), str(body.attempt_id), idempotency_key=idempotency_key, settings_revision=revision)
    return state.service.detail(OWNER, str(job_id))

@router.post('/jobs/{job_id}/resume', status_code=202)
def resume(job_id: UUID, body: RetryCommand, request: Request, idempotency_key: str = Header(min_length=1, max_length=200)):
    state = request.app.state
    revision = _adopted_revision(request, body.use_current_settings)
    state.service.resume(OWNER, str(job_id), str(body.attempt_id), idempotency_key=idempotency_key, settings_revision=revision)
    return state.service.detail(OWNER, str(job_id))

@router.post('/jobs/{job_id}/continue', status_code=202)
def continue_job(job_id: UUID, body: ContinueCommand, request: Request, idempotency_key: str = Header(min_length=1, max_length=200)):
    service = request.app.state.service
    service.continue_job(OWNER, str(job_id), str(body.attempt_id), body.end_stage, idempotency_key=idempotency_key)
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
            'stage_counts': request.app.state.service.stage_counts(OWNER),
            'health': request.app.state.service.health(),
            'runtime': {'local_stt_device': 'CPU 기본', 'chrome_mode': 'headless' if config.headless else 'headed/Xvfb', 'data_storage': '서버 데이터 볼륨',
                        'models_storage': '서버 모델 볼륨'},
            'retention': {'input': '성공 후 원본 보관 설정 적용; 실패·취소·중단은 재시도용 보존',
                          'audio': '성공 후 변환 오디오 보관 설정 적용; 미보관 시 정리',
                          'results': '원문·요약·프롬프트·이력 자동 삭제 없음', 'logs_days': 7},
            'update_instructions': ['docker compose up -d --build', '업데이트 전에 데이터·모델 볼륨 백업']}


@router.get('/catalog')
def get_catalog():
    from src.core.catalog import catalog
    return catalog()

@router.post('/prompt-preview')
def preview(body: Settings):
    from src.core.models.settings import PromptSettings
    return {'text': PromptSettings(mode=body.prompt_mode, summary_mode=body.summary_mode,
                                  subject_category=body.subject_category, subject_custom=body.subject_custom,
                                  custom_prompt=body.custom_prompt).resolve()}

@router.get('/courses')
def courses(request: Request):
    state = request.app.state
    revision = state.settings.snapshot(state.settings.public()['settings_revision'])
    with state.service.lock:
        return state.service.courses.cached(revision)

@router.get('/courses/{course_id}/lectures')
def lectures(course_id: str, request: Request):
    state = request.app.state
    revision = state.settings.snapshot(state.settings.public()['settings_revision'])
    with state.service.lock:
        return state.service.courses.cached(revision, course_id)

@router.post('/course-refreshes', status_code=202)
def refresh_courses(body: CourseRefresh, request: Request):
    state = request.app.state
    revision = state.settings.snapshot(state.settings.public()['settings_revision'])
    with state.service.lock:
        state.service._ensure_open()
        return state.service.courses.submit(OWNER, revision, body.course_id)

@router.get('/course-refreshes/{query_id}')
def refresh_status(query_id: UUID, request: Request):
    with request.app.state.service.lock:
        return request.app.state.service.courses.get(OWNER, str(query_id))

@router.get('/auto-detect')
def auto_detect(request: Request):
    return request.app.state.autodetect.status()

@router.post('/auto-detect/check')
def auto_detect_check(request: Request):
    return request.app.state.autodetect.tick(force=True)

@router.post('/auto-detect/resume')
def auto_detect_resume(request: Request):
    return request.app.state.autodetect.resume()

@router.get('/playback')
def playback(request: Request):
    return {'records': request.app.state.service.playback.list(OWNER, limit=50)}

@router.get('/jobs/{job_id}/logs')
def job_logs(job_id: UUID, request: Request, cursor: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=200)):
    return request.app.state.service.logs(OWNER, str(job_id), cursor, limit)

@router.post('/system/update-check')
def update_check():
    import requests
    from src import __version__
    import re
    try:
        response = requests.get('https://api.github.com/repos/Leonamin/lms-summarizer/releases/latest', timeout=5)
        response.raise_for_status()
        data = response.json()
        tag = data['tag_name']
        if not re.fullmatch(r'v?\d+\.\d+\.\d+', tag):
            raise ValueError()
        url = data['html_url']
        if not url.startswith('https://github.com/Leonamin/lms-summarizer/releases/'):
            raise ValueError()
        return {'status': 'ok', 'latest': tag, 'url': url,
                'newer': tuple(map(int, tag.lstrip('v').split('.'))) > tuple(map(int, __version__.lstrip('v').split('.')))}
    except (requests.RequestException, KeyError, ValueError):
        return {'status': 'unavailable'}
