"""One persistent spawn worker per stage, fresh IPC after every forced stop."""
import contextlib
import errno
import os
from src.core.models.jobs import StageResult, ServiceError
from src.core.runtime.processes import isolate_process, watch_parent

SAFE_ERRORS = {'cancelled', 'credentials_missing', 'input_missing', 'output_missing',
               'download_failed', 'disk_full', 'stage_failed'}

def worker_main(connection, lifetime, cancelled, executor_factory):
    job_handle = isolate_process()  # Keep the Windows handle alive for the worker lifetime.
    watch_parent(lifetime)
    executor = executor_factory()
    try:
        connection.send(('ready', None))
        while True:
            try:
                command = connection.recv()
            except (EOFError, OSError):
                break
            if command is None:
                break
            # Adapter stdout often includes URLs, prompts, or transcript content.
            # Persist only controlled stage events, never raw adapter output/errors.
            try:
                with open(os.devnull, 'w') as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                    result = executor.execute(command, cancelled)
            except Exception as exc:
                code = exc.code if isinstance(exc, ServiceError) and exc.code in SAFE_ERRORS else 'stage_failed'
                if isinstance(exc, OSError) and exc.errno == errno.ENOSPC:
                    code = 'disk_full'
                result = StageResult(command.token, error_code=code)
            try:
                connection.send(('result', result))
            except (EOFError, OSError):
                break
    finally:
        with contextlib.suppress(Exception):
            executor.close()
        connection.close()
