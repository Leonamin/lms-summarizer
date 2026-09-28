"""Verify existing LMS login and strict CDP extraction without exposing secrets."""
import argparse
import asyncio
from contextlib import redirect_stdout, redirect_stderr
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from src.user_setting import UserSetting
from src.video_pipeline.pipeline import VideoPipeline
from src.video_pipeline.video_parser import extract_video_url


async def run(settings_path, headed):
    result = {"mode": "headed-xvfb" if headed else "headless", "phase": "settings",
              "login": False, "cdp_mp4_captured": False}
    pipeline = None
    try:
        settings = json.loads(Path(settings_path).read_text())
        inputs = settings.get("user_inputs", settings)
        url = settings.get("lecture_url", "")
        parsed = urlparse(url)
        if not inputs.get("student_id") or not inputs.get("password"):
            raise ValueError("Missing credentials")
        if parsed.scheme != "https" or parsed.hostname != "canvas.ssu.ac.kr" or not parsed.path.startswith("/courses/"):
            raise ValueError("Invalid lecture URL")
        captured = []

        def safe_log(message):
            if message.startswith("[CDP] .mp4 요청 감지:"):
                captured.append(True)

        pipeline = VideoPipeline(UserSetting(inputs), chrome_path="/usr/bin/google-chrome",
                                 headless=not headed, log_callback=safe_log)
        result["phase"] = "login"
        await pipeline.open_session()
        result["chrome"] = pipeline._browser.version
        result["login"] = "canvas.ssu.ac.kr" == urlparse(pipeline._session_page.url).hostname and "login" not in pipeline._session_page.url
        if not result["login"]:
            raise RuntimeError("Login not confirmed")
        result["phase"] = "lecture_navigation"
        await pipeline._session_page.goto(url, wait_until="networkidle", timeout=60000)
        result["phase"] = "cdp_extract"
        video_url, title = await extract_video_url(pipeline._session_page, method="cdp", timeout=90, log=safe_log)
        result["cdp_mp4_captured"] = bool(video_url and captured)
        result["title_found"] = bool(title)
        result["captured_count"] = len(captured)
        result["success"] = result["login"] and result["cdp_mp4_captured"]
        result["phase"] = "finished"
    except Exception as error:
        # Exception messages can contain account identifiers, URLs or tokens.
        result["success"] = False
        result["error_type"] = type(error).__name__
    finally:
        if pipeline:
            try:
                await pipeline.close_session()
            except Exception:
                result["cleanup_failed"] = True
    return result


async def bounded_run(args):
    try:
        return await asyncio.wait_for(run(args.settings, args.headed), timeout=240)
    except TimeoutError:
        return {"success": False, "phase": "overall_timeout", "error_type": "TimeoutError"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", default="/run/lms-settings.json")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()
    with open(os.devnull, "w") as sink, redirect_stdout(sink), redirect_stderr(sink):
        result = asyncio.run(bounded_run(args))
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result.get("success") else 1)
