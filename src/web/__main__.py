import multiprocessing
import os


def main():
    multiprocessing.freeze_support()
    import uvicorn
    from src.web.app import create_app
    uvicorn.run(create_app(), host='0.0.0.0', port=int(os.getenv('LMS_PORT', '8000')),
                workers=1, timeout_graceful_shutdown=15, access_log=False)


if __name__ == '__main__':
    main()
