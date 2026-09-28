"""Single API process owns all workers; HTTP sessions never own jobs."""
import asyncio
from contextlib import asynccontextmanager, suppress
import errno
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from src.core.models.jobs import ServiceError
from src.core.services.jobs import JobService
from src.web.api.routes import router
from src.web.autoplay import AutoDetect
from src.web.config import WebConfig
from src.web.settings import WebSettings
from src.web.uploads import Uploads

MESSAGES = {
    'credentials_missing': '필요한 LMS 계정 또는 공급자 자격 증명을 설정해 주세요.',
    'invalid_url': 'https://canvas.ssu.ac.kr/courses/로 시작하는 LMS 강의 URL을 입력해 주세요.',
    'queue_full': '작업 대기열이 가득 찼습니다. 잠시 후 다시 제출해 주세요.',
    'not_found': '항목을 찾을 수 없습니다.', 'settings_conflict': '설정이 변경되었습니다. 새로 불러와 주세요.',
    'invalid_settings': '프롬프트 또는 설정을 확인해 주세요.', 'invalid_file_content': '파일 내용이 지원하는 형식과 맞지 않습니다.',
    'unsupported_file': 'MP4, TS, WAV, MP3, UTF-8 TXT 파일을 지원합니다.',
    'upload_size_mismatch': '파일 크기가 다릅니다. 다시 업로드해 주세요.',
    'upload_not_ready': '업로드 완료 후 작업을 제출해 주세요.', 'disk_full': '서버 저장 공간이 부족합니다.',
    'input_too_large': '파일 또는 요청 크기 한도를 초과했습니다.',
    'input_in_use': '작업이 참조하는 입력은 삭제할 수 없습니다.',
    'secret_in_use': '기존 작업에서 사용하는 자격 증명은 삭제할 수 없습니다.',
    'content_too_large': '열람 한도를 초과했습니다. 파일을 다운로드해 주세요.',
}

def error(code, status, field=None):
    body = {'code': code, 'message': MESSAGES.get(code, '요청을 처리할 수 없습니다. 상태와 입력을 확인해 주세요.')}
    if field:
        body['field'] = field
    return JSONResponse({'error': body}, status_code=status)


def create_app(config=None, *, service_factory=JobService):
    config = config or WebConfig()
    config.data_dir = Path(config.data_dir).resolve()
    config.models_dir = Path(config.models_dir).resolve()

    @asynccontextmanager
    async def lifespan(app):
        service = service_factory(config.data_dir, models_dir=config.models_dir,
                                  min_free_bytes=config.min_free_bytes, max_input_bytes=config.max_upload_bytes)
        app.state.service, app.state.config = service, config
        tasks = []
        try:
            app.state.settings = WebSettings(config, service)
            app.state.uploads = Uploads(config, service)
            app.state.autodetect = AutoDetect(service, app.state.settings)
            await run_in_threadpool(service.start)
            async def clean_uploads():
                while True:
                    await asyncio.sleep(300)
                    try:
                        await run_in_threadpool(app.state.uploads.cleanup)
                    except OSError:
                        pass  # A temporary disk failure must not kill the lifecycle task.
            async def auto_detect_loop():
                while True:
                    await asyncio.sleep(15)
                    try:
                        await run_in_threadpool(app.state.autodetect.tick)
                    except Exception:
                        pass  # Auto-detect must never kill the lifecycle task.
            tasks = [asyncio.create_task(clean_uploads()), asyncio.create_task(auto_detect_loop())]
            yield
        finally:
            for task in tasks:
                task.cancel()
            for task in tasks:
                with suppress(asyncio.CancelledError):
                    await task
            await run_in_threadpool(service.close)

    app = FastAPI(title='LMS Summarizer', lifespan=lifespan)

    @app.middleware('http')
    async def same_origin(request, call_next):
        host = urlsplit(str(request.url)).hostname
        allowed = {value.strip().strip('[]').lower() for value in config.allowed_hosts}
        if not host or host.lower() not in allowed:
            return error('invalid_host', 400)
        origin = request.headers.get('origin')
        if origin and origin not in (str(request.base_url).rstrip('/'), *config.allowed_origins):
            return error('invalid_origin', 403)
        if request.method in ('POST', 'PUT', 'PATCH') and request.url.path.startswith('/api/'):
            raw_upload = request.url.path.startswith('/api/v1/uploads/') and request.url.path.endswith('/content')
            if not raw_upload:
                if request.headers.get('content-type', '').split(';')[0] != 'application/json':
                    return error('invalid_content_type', 415)
                body = bytearray()
                async for chunk in request.stream():
                    body.extend(chunk)
                    if len(body) > 1024 * 1024:
                        return error('input_too_large', 413)
                request._body = bytes(body)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        return response

    @app.exception_handler(ServiceError)
    async def service_error(request, exc):
        code = exc.code
        status = 422
        if code in ('not_found', 'artifact_missing'):
            status = 404
        elif code in ('settings_conflict', 'idempotency_conflict', 'upload_conflict', 'input_in_use', 'secret_in_use', 'attempt_conflict', 'job_not_retryable', 'job_active'):
            status = 409
        elif code in ('input_too_large', 'content_too_large'):
            status = 413
        elif code == 'disk_full':
            status = 507
        elif code == 'service_unavailable':
            status = 503
        return error(code, status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Pydantic errors can include the submitted secret value; never serialize them.
        return error('invalid_request', 422)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error('not_found' if exc.status_code == 404 else 'invalid_request', exc.status_code)

    @app.exception_handler(ValueError)
    async def value_error(request, exc):
        return error('invalid_request', 422)

    @app.exception_handler(OSError)
    async def disk_error(request, exc):
        return error('disk_full' if exc.errno == errno.ENOSPC else 'storage_error', 507 if exc.errno == errno.ENOSPC else 500)

    app.include_router(router)
    static = Path(config.static_dir).resolve()
    if (static / 'assets').is_dir():
        app.mount('/assets', StaticFiles(directory=static / 'assets'), name='assets')

    @app.get('/{path:path}', include_in_schema=False)
    def frontend(path: str):
        if path.startswith('api/'):
            raise ServiceError('not_found')
        target = (static / path).resolve()
        if target.is_relative_to(static) and target.is_file():
            return FileResponse(target)
        if (static / 'index.html').exists():
            return FileResponse(static / 'index.html')
        return error('frontend_not_built', 503)

    return app
