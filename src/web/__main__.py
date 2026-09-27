import multiprocessing
import os


def main():
    multiprocessing.freeze_support()
    import uvicorn
    from src.web.app import create_app
    from src.web.config import WebConfig
    config = WebConfig()
    display = None
    try:
        if not config.headless and not os.getenv('DISPLAY'):
            import subprocess
            import time
            display = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1280x900x24', '-nolisten', 'tcp'],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.environ['DISPLAY'] = ':99'
            time.sleep(.3)
            if display.poll() is not None:
                raise RuntimeError('Xvfb startup failed')
        uvicorn.run(create_app(config), host='0.0.0.0', port=int(os.getenv('LMS_PORT', '8000')),
                    workers=1, timeout_graceful_shutdown=15, access_log=False)
    finally:
        if display:
            display.terminate()
            display.wait(timeout=5)


if __name__ == '__main__':
    main()
