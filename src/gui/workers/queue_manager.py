"""
작업 큐 매니저

다운로드 스레드(producer)와 처리 스레드(consumer)를 분리하여
한 영상의 다운로드가 끝나면 다음 영상을 다운로드하는 동안
해당 영상의 변환→STT→요약이 진행되도록 한다.

실행 중에도 submit()으로 URL을 추가할 수 있으며, 모든 작업이
완료되면 스레드가 종료(idle)하고 새 제출 시 새 세션으로 기동한다.
"""

import asyncio
import queue
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

from src.video_pipeline.login import LoginFailedError

_STOP = object()  # 스레드 종료 신호

# 세션 설정 키 (실행 중 첫 제출 시 고정, idle 후 새 세션에서 갱신)
_SESSION_SETTING_KEYS = (
    'user_inputs', 'save_video_dir', 'model_name', 'engine', 'base_url',
    'summary_prompt', 'chrome_path', 'headless',
    'stt_engine', 'stt_model', 'stt_params',
)

_ACTIVE_STATUSES = None  # 하단에서 설정 (TaskStatus 정의 후)


class TaskStatus(str, Enum):
    WAITING = "대기"
    DOWNLOADING = "다운로드"
    CONVERTING = "변환"
    STT = "STT"
    SUMMARIZING = "요약"
    DONE = "완료"
    FAILED = "실패"
    CANCELLED = "취소"


_ACTIVE_STATUSES = {
    TaskStatus.WAITING, TaskStatus.DOWNLOADING,
    TaskStatus.CONVERTING, TaskStatus.STT, TaskStatus.SUMMARIZING,
}

_STAGE_STATUS = {
    "변환": TaskStatus.CONVERTING,
    "STT": TaskStatus.STT,
    "요약": TaskStatus.SUMMARIZING,
}


@dataclass
class TaskItem:
    id: int
    url: str
    status: TaskStatus = TaskStatus.WAITING
    title: str = ""
    error: str = ""
    summary_path: str = ""


class QueueManager:
    """다운로드↔처리 오버랩 파이프라인 + 실행 중 URL 추가 지원"""

    def __init__(
        self,
        modules: Dict,
        on_log: Callable[[str], None],
        on_task_updated: Callable[[TaskItem], None],
        on_idle_changed: Callable[[bool], None],
    ):
        self.modules = modules
        self._on_log = on_log or (lambda msg: None)
        self._on_task_updated = on_task_updated or (lambda task: None)
        self._on_idle_changed = on_idle_changed or (lambda running: None)

        self._tasks: Dict[int, TaskItem] = {}
        self._next_task_id = 1
        self._lock = threading.Lock()

        # 현재 실행(run) 상태 — 스레드에 인자로 전달되어 공유 변이 없음
        self._settings: Optional[Dict] = None
        self._run_cancel: Optional[threading.Event] = None
        self._url_q: Optional[queue.Queue] = None
        self._proc_q: Optional[queue.Queue] = None
        self._download_thread: Optional[threading.Thread] = None
        self._process_thread: Optional[threading.Thread] = None
        self._stopped_ids: Set[int] = set()
        self._restarting = False
        self._idle_notified = True
        self._stopping = False  # 현재 실행이 정리 중이면 True (submit이 새 세션을 기동하도록 함)

    def _log(self, msg: str):
        try:
            self._on_log(msg)
        except Exception:
            pass  # 로그 콜백 실패가 워커 스레드를 죽이지 않도록 방어

    # ── Public API ───────────────────────────────────────

    def submit(self, urls: List[str], settings: Dict) -> List[TaskItem]:
        """URL 작업을 큐에 추가. 실행 중이면 현재 세션 설정이 유지된다."""
        if not urls:
            return []

        with self._lock:
            if self._settings is None:
                self._settings = {k: settings.get(k) for k in _SESSION_SETTING_KEYS}
            else:
                changed = [
                    k for k in ('engine', 'model_name', 'stt_engine', 'stt_model')
                    if self._settings.get(k) != settings.get(k)
                ]
                if changed:
                    self._log(
                        f"⚠️ 현재 세션 설정이 유지됩니다 ({', '.join(changed)} 변경 무시). "
                        f"모든 작업 완료 후 다시 시작하면 새 설정이 적용됩니다."
                    )
            tasks: List[TaskItem] = []
            for url in urls:
                task = TaskItem(id=self._next_task_id, url=url)
                self._next_task_id += 1
                self._tasks[task.id] = task
                tasks.append(task)
            self._idle_notified = False

        if self._run_active() and not self._stopping:
            for task in tasks:
                self._url_q.put(task)
        else:
            # 유휴 또는 정리 중: 새 세션으로 기동 (유실 활성 작업도 함께 재등록)
            self._start_run()

        self._log(f"큐에 {len(tasks)}개 작업 추가됨 (대기: {self.pending_count()})")
        return tasks

    def submit_files(self, files: List[str], settings: Dict,
                     start_stage: str) -> List[TaskItem]:
        """로컬 파일 작업을 처리 큐에 직접 추가 (다운로드 불필요).

        start_stage: "변환" | "STT" | "요약" (ItemProcessor.process_full에 전달)
        """
        if not files:
            return []

        with self._lock:
            if self._settings is None:
                self._settings = {k: settings.get(k) for k in _SESSION_SETTING_KEYS}
            tasks: List[TaskItem] = []
            for f in files:
                task = TaskItem(
                    id=self._next_task_id, url="",
                    title=Path(f).name,
                )
                self._next_task_id += 1
                self._tasks[task.id] = task
                tasks.append(task)
            self._idle_notified = False

        self._ensure_process_thread(settings)

        for task in tasks:
            self._proc_q.put((task, (f, start_stage)))
        self._log(f"큐에 {len(tasks)}개 파일 작업 추가됨 ({start_stage}부터)")
        return tasks

    def _ensure_process_thread(self, settings: Dict):
        """처리 스레드만 기동 (파일 소스 전용 — 브라우저 세션 불필요)"""
        with self._lock:
            if self._proc_q is None:
                self._proc_q = queue.Queue()
                self._run_cancel = threading.Event()
            pr = self._process_thread
        if pr is None or not pr.is_alive():
            self._process_thread = threading.Thread(
                target=self._process_loop,
                args=(settings, self._run_cancel, self._proc_q),
                daemon=True, name="queue-process",
            )
            self._process_thread.start()

    def is_running(self) -> bool:
        """스레드 생존 또는 활성 작업 존재 여부 (UI 상태용)"""
        if self._run_active():
            return True
        with self._lock:
            return any(t.status in _ACTIVE_STATUSES for t in self._tasks.values())

    def pending_count(self) -> int:
        with self._lock:
            return sum(1 for t in self._tasks.values()
                       if t.status == TaskStatus.WAITING)

    def request_stop(self):
        """전체 작업 중지 요청"""
        with self._lock:
            self._stopped_ids = {
                t.id for t in self._tasks.values()
                if t.status in (TaskStatus.WAITING, TaskStatus.DOWNLOADING)
            }
            cancel, url_q, proc_q = self._run_cancel, self._url_q, self._proc_q
        if cancel:
            cancel.set()
        if url_q:
            url_q.put(_STOP)
        if proc_q:
            proc_q.put(_STOP)
        self._stopping = True  # 정리 중 제출분이 새 세션으로 기동되도록
        self._log("전체 작업 중지를 요청했습니다...")

    # ── 실행(run) 생명주기 ────────────────────────────────

    def _run_active(self) -> bool:
        dl, pr = self._download_thread, self._process_thread
        return (dl is not None and dl.is_alive()) or (pr is not None and pr.is_alive())

    def _start_run(self):
        """새 실행 기동: 활성 상태 작업을 대기로 되돌려 새 큐에 넣고 스레드 시작"""
        with self._lock:
            cancel = threading.Event()
            self._run_cancel = cancel
            self._url_q = queue.Queue()
            self._proc_q = queue.Queue()
            settings = self._settings
            requeue = []
            for task in self._tasks.values():
                if task.status in _ACTIVE_STATUSES:
                    # 유실된 작업(스레드 종료로 처리 못 함) → 대기로 되돌려 재처리
                    task.status = TaskStatus.WAITING
                    task.error = ""
                    requeue.append(task)
            self._idle_notified = False
            self._restarting = False
            self._stopped_ids = set()
            self._stopping = False

        for task in requeue:
            self._url_q.put(task)
            self._update_task(task, TaskStatus.WAITING)

        self._download_thread = threading.Thread(
            target=self._download_loop,
            args=(settings, cancel, self._url_q, self._proc_q),
            daemon=True, name="queue-download",
        )
        self._process_thread = threading.Thread(
            target=self._process_loop,
            args=(settings, cancel, self._proc_q),
            daemon=True, name="queue-process",
        )
        self._download_thread.start()
        self._process_thread.start()

    def _all_drained(self) -> bool:
        """활성 작업이 하나도 없으면 True (스레드 자연 종료 조건)"""
        with self._lock:
            return not any(t.status in _ACTIVE_STATUSES for t in self._tasks.values())

    def _cleanup_after_thread(self, cancel: threading.Event):
        """스레드 종료 후 처리: 대기 작업 있으면 자동 재시작, 없으면 idle 발화

        마지막에 종료한 스레드만 판단한다. 상대 스레드가 정리 중이면
        짧게 대기해보고, 그래도 살아있으면 상대가 종료하며 판단하도록 넘긴다.
        """
        current = threading.current_thread()

        def _done(t: Optional[threading.Thread]) -> bool:
            return t is None or t is current or not t.is_alive()

        dl, pr = self._download_thread, self._process_thread
        for _ in range(10):  # 상대 스레드 정리 대기 (최대 0.5초)
            if _done(dl) and _done(pr):
                break
            time.sleep(0.05)

        restart = False
        with self._lock:
            # 세대 검증: 이미 새 실행이 기동되었으면 이 정리는 무효
            if self._download_thread is not dl or self._process_thread is not pr:
                return
            self._stopping = True  # 이후 submit이 새 세션을 기동하도록
            both_done = _done(dl) and _done(pr)
            if not both_done:
                return  # 마지막 종료 스레드가 판단함
            # 중지 스냅샷에 없는 활성 작업 = 중지 후 제출되었거나 유실된 작업 → 재시작 대상
            restartable = [
                t for t in self._tasks.values()
                if t.status in _ACTIVE_STATUSES and t.id not in self._stopped_ids
            ]
            if restartable:
                if self._restarting:
                    return
                self._restarting = True
                restart = True

        if restart:
            self._log("대기 중인 작업이 있어 세션을 다시 시작합니다.")
            self._start_run()
            return

        fire_idle = False
        with self._lock:
            if not self._idle_notified:
                self._idle_notified = True
                fire_idle = True
                self._settings = None  # 다음 제출부터 새 설정 적용
        if fire_idle:
            try:
                self._on_idle_changed(False)
            except Exception:
                pass

    # ── 다운로드 스레드 (producer) ────────────────────────

    def _download_loop(self, settings: Dict, cancel: threading.Event,
                       url_q: queue.Queue, proc_q: queue.Queue):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                self._download_async(settings, cancel, url_q, proc_q))
        except LoginFailedError as e:
            self._log(f"로그인 실패로 다운로드를 중단합니다: {e.detail}")
            self._fail_waiting(e.detail)
        except Exception as e:
            self._log(f"[QUEUE] 다운로드 스레드 오류: {type(e).__name__}: {e}")
            self._fail_waiting(f"다운로드 스레드 오류: {e}")
        finally:
            loop.close()
            self._cleanup_after_thread(cancel)

    async def _download_async(self, settings: Dict, cancel: threading.Event,
                              url_q: queue.Queue, proc_q: queue.Queue):
        user_setting = self.modules['UserSetting'](settings['user_inputs'])
        video_pipeline = self.modules['VideoPipeline'](
            user_setting,
            chrome_path=settings.get('chrome_path'),
            log_callback=self._log,
            headless=settings.get('headless', True),
        )
        from src.gui.core.file_manager import ensure_downloads_directory
        video_pipeline.downloads_dir = ensure_downloads_directory()

        self._log("브라우저 세션 시작 (로그인 포함)")
        await video_pipeline.open_session()
        try:
            while not cancel.is_set():
                try:
                    item = await asyncio.to_thread(url_q.get, True, 0.5)
                except queue.Empty:
                    if self._all_drained():
                        break
                    continue
                if item is _STOP:
                    break
                await self._download_one(video_pipeline, item, proc_q)
        finally:
            await video_pipeline.close_session()
            self._log("브라우저 세션 종료")
            self._cancel_stuck_downloads()

    async def _download_one(self, video_pipeline, task: TaskItem,
                            proc_q: queue.Queue):
        self._update_task(task, TaskStatus.DOWNLOADING)
        try:
            filepath = await video_pipeline.process_single_url(task.url)
        except LoginFailedError:
            raise  # 상위에서 일괄 처리
        except Exception as e:
            self._log(f"[ERROR] 다운로드 실패: {task.url} — {e}")
            self._update_task(task, TaskStatus.FAILED, error=str(e))
            return

        if filepath:
            task.title = Path(filepath).parent.name
            proc_q.put((task, filepath))
        else:
            self._update_task(task, TaskStatus.FAILED,
                              error="동영상 링크를 찾지 못했습니다.")

    def _fail_waiting(self, reason: str):
        """대기 중인 모든 작업을 실패 처리 (세션 중단 시)"""
        with self._lock:
            waiting = [t for t in self._tasks.values() if t.status == TaskStatus.WAITING]
        for task in waiting:
            self._update_task(task, TaskStatus.FAILED, error=reason)

    def _cancel_stuck_downloads(self):
        """중지 요청 시점에 대기/다운로드 중이던 항목만 취소 처리"""
        with self._lock:
            stopped_ids = set(self._stopped_ids)
            targets = [t for t in self._tasks.values()
                       if t.id in stopped_ids
                       and t.status in (TaskStatus.WAITING, TaskStatus.DOWNLOADING)]
        for task in targets:
            self._update_task(task, TaskStatus.CANCELLED)

    # ── 처리 스레드 (consumer) ────────────────────────────

    def _process_loop(self, settings: Dict, cancel: threading.Event,
                      proc_q: queue.Queue):
        from src.gui.workers.item_processor import ItemProcessor, CancelledException
        processor = ItemProcessor(
            self.modules, settings,
            on_log=self._log,
            cancel_check=cancel.is_set,
        )
        self._log(
            f"처리 워커 준비 완료 (STT: {processor.stt_engine} / 요약: {processor.engine})")

        while not cancel.is_set():
            try:
                item = proc_q.get(True, 0.5)
            except queue.Empty:
                if self._all_drained():
                    break
                continue
            if item is _STOP:
                break

            task, payload = item
            if isinstance(payload, tuple):
                video_path, start_stage = payload
            else:
                video_path, start_stage = payload, "변환"
            start_time = time.monotonic()
            try:
                summary_path = processor.process_full(
                    video_path,
                    on_stage=lambda stage: self._update_task(
                        task, _STAGE_STATUS[stage]),
                    start_stage=start_stage,
                )
                task.summary_path = summary_path
                self._update_task(task, TaskStatus.DONE)
                processor.finalize(video_path, task.url, summary_path,
                                   time.monotonic() - start_time,
                                   delete_source=(start_stage == "변환"))
            except CancelledException:
                self._update_task(task, TaskStatus.CANCELLED)
                break
            except Exception as e:
                self._log(f"❌ 처리 실패 ({task.title or task.url}): {e}")
                self._update_task(task, TaskStatus.FAILED, error=str(e))

        self._cleanup_after_thread(cancel)

    # ── 상태 갱신 ────────────────────────────────────────

    def _update_task(self, task: TaskItem, status: TaskStatus, error: str = ""):
        task.status = status
        if error:
            task.error = error
        try:
            self._on_task_updated(task)
        except Exception:
            pass
