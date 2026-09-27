"""Disposable Chrome/CDP probe. Synthetic media only; no LMS account needed."""
import argparse
import asyncio
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import tempfile
import threading

from playwright.async_api import async_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


async def probe(headed: bool) -> dict:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
            "-i", "color=c=black:s=160x90:r=10", "-f", "lavfi",
            "-i", "sine=frequency=440:sample_rate=44100", "-t", "2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-movflags", "+faststart", str(root / "fixture.mp4"),
        ], check=True)
        (root / "index.html").write_text(
            '<video muted autoplay src="/fixture.mp4"></video>', encoding="utf-8")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=directory))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(
                    executable_path="/usr/bin/google-chrome", headless=not headed)
                try:
                    page = await browser.new_page()
                    cdp = await page.context.new_cdp_session(page)
                    requests = []
                    cdp.on("Network.requestWillBeSent", lambda event: requests.append(event["request"]["url"]))
                    await cdp.send("Network.enable")
                    await page.goto(f"http://127.0.0.1:{server.server_port}/index.html")
                    await page.wait_for_function("document.querySelector('video').currentTime > 0", timeout=15000)
                    media = await page.evaluate("""() => {
                        const video = document.querySelector('video');
                        return {h264: video.canPlayType('video/mp4; codecs="avc1.42E01E"'),
                                aac: video.canPlayType('audio/mp4; codecs="mp4a.40.2"'),
                                current_time: video.currentTime, ready_state: video.readyState};
                    }""")
                    captured = any('/fixture.mp4' in url for url in requests)
                    result = {"chrome": browser.version, "mode": "headed-xvfb" if headed else "headless",
                              "cdp_mp4_captured": captured, "media": media,
                              "scope": "synthetic H264/AAC; LMS not verified"}
                    if not captured or media["current_time"] <= 0:
                        raise RuntimeError("Chrome media/CDP probe did not pass")
                    return result
                finally:
                    await browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headed", action="store_true", help="Requires Xvfb or an existing display")
    arguments = parser.parse_args()
    print(json.dumps(asyncio.run(probe(arguments.headed)), ensure_ascii=False))
