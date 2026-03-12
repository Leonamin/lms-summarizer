import functools
from typing import Callable


def invoke_on_ui(page, fn: Callable) -> Callable:
    """백그라운드 스레드에서 호출해도 Flet 메인 이벤트 루프에서 실행되도록 래핑.

    page.run_task()를 통해 콜백을 메인 루프에 스케줄링하므로,
    창이 비활성 상태여도 UI 갱신이 정상 동작한다.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        async def _task():
            fn(*args, **kwargs)
            page.update()

        page.run_task(_task)

    return wrapper
