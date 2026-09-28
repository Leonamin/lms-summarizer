"""Exclusive data ownership and process-tree isolation on Unix and Windows."""
import os
from pathlib import Path
import signal
import threading

class DataLock:
    def __init__(self, root: Path):
        root.mkdir(parents=True, exist_ok=True)
        self.stream = open(root / 'supervisor.lock', 'a+b')
        try:
            if os.name == 'nt':
                import msvcrt
                self.stream.seek(0)
                self.stream.write(b'0')
                self.stream.flush()
                self.stream.seek(0)
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.stream.close()
            raise RuntimeError('Data directory already has a supervisor') from None

    def close(self):
        self.stream.close()


def isolate_process():
    if os.name != 'nt':
        os.setsid()
        return None
    # A non-inheritable Job Object handle in the worker closes on forced death,
    # killing descendants even if they outlive the Python worker.
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    class Basic(ctypes.Structure):
        _fields_ = [('PerProcessUserTimeLimit', ctypes.c_longlong), ('PerJobUserTimeLimit', ctypes.c_longlong),
                    ('LimitFlags', wintypes.DWORD), ('MinimumWorkingSetSize', ctypes.c_size_t),
                    ('MaximumWorkingSetSize', ctypes.c_size_t), ('ActiveProcessLimit', wintypes.DWORD),
                    ('Affinity', ctypes.c_size_t), ('PriorityClass', wintypes.DWORD), ('SchedulingClass', wintypes.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
    class Extended(ctypes.Structure):
        _fields_ = [('BasicLimitInformation', Basic), ('IoInfo', IO),
                    ('ProcessMemoryLimit', ctypes.c_size_t), ('JobMemoryLimit', ctypes.c_size_t),
                    ('PeakProcessMemoryUsed', ctypes.c_size_t), ('PeakJobMemoryUsed', ctypes.c_size_t)]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    handle = kernel.CreateJobObjectW(None, None)
    info = Extended()
    info.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE
    if not handle or not kernel.SetInformationJobObject(handle, 9, ctypes.byref(info), ctypes.sizeof(info)) or not kernel.AssignProcessToJobObject(handle, kernel.GetCurrentProcess()):
        raise RuntimeError('Worker process isolation failed')
    return handle


def watch_parent(lifetime):
    def monitor():
        try:
            lifetime.recv_bytes()
        except (EOFError, OSError):
            if os.name != 'nt':
                kill_descendants(os.getpid())
                os.killpg(os.getpid(), signal.SIGKILL)
            os._exit(1)
    threading.Thread(target=monitor, daemon=True).start()


def reap(process, descendants=()):
    if os.name != 'nt' and process.pid:
        kill_descendants(process.pid, descendants, suspend_root=True)
    if os.name != 'nt' and process.pid:
        # Also removes descendants after a worker exits unexpectedly.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.is_alive():
        process.terminate()
    process.join(timeout=3)
    if process.is_alive():
        process.kill()
        process.join(timeout=3)
    if process.is_alive():
        raise RuntimeError('Worker tree could not be reaped')

class CancellationFlag:
    """Single-byte shared flag without named semaphore leaks after server crashes."""
    def __init__(self, context):
        self.value = context.RawValue('b', 0)

    def set(self):
        self.value.value = 1

    def clear(self):
        self.value.value = 0

    def is_set(self):
        return bool(self.value.value)


def descendant_snapshot(pid):
    import psutil
    try:
        return psutil.Process(pid).children(recursive=True)
    except psutil.Error:
        return []


def kill_descendants(pid, known=(), *, suspend_root=False):
    """Includes detached groups (e.g. Chromium), with PID-reuse-safe handles."""
    import psutil
    descendants = {process.pid:process for process in known}
    try:
        root = psutil.Process(pid)
        if suspend_root:
            root.suspend()
        # Freeze descendants from their parents down so they cannot keep spawning.
        while True:
            discovered = root.children(recursive=True)
            fresh = [process for process in discovered if process.pid not in descendants]
            for process in fresh:
                descendants[process.pid] = process
                try:
                    process.suspend()
                except psutil.NoSuchProcess:
                    pass
            if not fresh:
                break
    except psutil.NoSuchProcess:
        pass
    for process in reversed(list(descendants.values())):
        try:
            process.kill()  # psutil verifies process identity before signalling.
        except psutil.NoSuchProcess:
            pass
