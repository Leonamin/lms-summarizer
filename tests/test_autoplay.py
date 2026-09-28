import json
from pathlib import Path
import tempfile
import threading
import unittest
from types import SimpleNamespace
from src.core.models.stages import PipelineStage
from src.core.services.detection import (
    flatten_lectures,
    is_selectable,
    is_watched,
    mark_seen,
    select_new_videos,
    select_playback_videos,
)
from src.web.autoplay import AutoDetect, parse_courses


def lecture(url, is_video=True, is_upcoming=False):
    return {"title": url, "url": url, "is_video": is_video, "is_upcoming": is_upcoming}


class FakeCourses:
    def __init__(self):
        self.list_data = []
        self.list_expired = True
        self.detail = {}
        self.refreshes = []

    def cached(self, revision, course_id=None):
        if course_id is None:
            return {"data": self.list_data, "expired": self.list_expired}
        present = course_id in self.detail
        return {"data": self.detail.get(course_id), "expired": not present}

    def submit(self, context, revision, course_id=None):
        self.refreshes.append(course_id)
        return {"id": "query", "course_id": course_id, "status": "queued"}


class FakePlayback:
    def __init__(self):
        self.records = []
        self.popup_failed = False

    def submit(self, context, revision, url, title, scope):
        record = {"id": "pb-%d" % (len(self.records) + 1), "url": url, "scope": scope, "title": title}
        self.records.append(record)
        return record

    def active(self, context):
        return []

    def popup_repeat_failed(self, context):
        return self.popup_failed


class FakeService:
    def __init__(self, root):
        self.paths = SimpleNamespace(file=lambda rel: Path(root) / rel)
        self.lock = threading.RLock()
        self.courses = FakeCourses()
        self.playback = FakePlayback()
        self.submitted = []

    def _ensure_open(self):
        pass

    def submit(self, context, sources, revision, end_stage=None, idempotency_key=None):
        self.submitted.append(
            {
                "reference": sources[0].reference,
                "end_stage": int(end_stage),
                "key": idempotency_key,
            }
        )
        return ["job-" + str(len(self.submitted))]


class FakeSettings:
    def __init__(self, settings):
        self.settings = settings

    def public(self):
        return {"settings": self.settings, "settings_revision": "rev-1"}

    def snapshot(self, revision_id):
        return SimpleNamespace(
            owner_id="local",
            settings_json=json.dumps(self.settings),
            secret_versions={},
        )


def base_settings(**overrides):
    values = {
        "auto_detect_enabled": True,
        "auto_detect_interval_minutes": 30,
        "auto_detect_courses": "123",
        "auto_save_scope": "download",
    }
    values.update(overrides)
    return values


class DetectionHelpersTests(unittest.TestCase):
    def test_parse_courses_accepts_commas_and_spaces(self):
        self.assertEqual(parse_courses("123, 456 789"), ["123", "456", "789"])
        self.assertEqual(parse_courses("abc, 12"), ["12"])
        self.assertEqual(parse_courses(""), [])

    def test_select_new_videos_excludes_upcoming_and_non_video(self):
        seen = {}
        lectures = [
            lecture("u1"),
            lecture("u2", is_upcoming=True),
            lecture("u3", is_video=False),
            lecture("u4"),
        ]
        self.assertEqual([row["url"] for row in select_new_videos(seen, lectures)], ["u1", "u4"])
        self.assertFalse(is_selectable(lectures[1]))
        # marking seen hides them on the next pass
        mark_seen(seen, lectures)
        self.assertEqual(select_new_videos(seen, lectures), [])
        self.assertEqual(len(flatten_lectures([{"lectures": lectures}])), 4)


    def test_select_playback_skips_already_watched(self):
        seen = {}
        lectures = [
            {**lecture("u1"), "completion": "completed"},
            {**lecture("u2"), "attendance": "attendance", "completion": "incomplete"},
            {**lecture("u3"), "attendance": "none", "completion": "incomplete"},
        ]
        self.assertTrue(is_watched(lectures[0]))
        self.assertTrue(is_watched(lectures[1]))
        self.assertFalse(is_watched(lectures[2]))
        self.assertEqual([row["url"] for row in select_playback_videos(seen, lectures)], ["u3"])


class AutoDetectTests(unittest.TestCase):
    def engine(self, root, **overrides):
        service = FakeService(root)
        engine = AutoDetect(service, FakeSettings(base_settings(**overrides)))
        return engine, service

    def test_disabled_and_missing_courses_are_noops(self):
        with tempfile.TemporaryDirectory() as directory:
            engine, service = self.engine(directory, auto_detect_enabled=False)
            self.assertEqual(engine.tick()["status"], "disabled")
            self.assertEqual(service.courses.refreshes, [])
            engine, service = self.engine(directory, auto_detect_courses="")
            self.assertEqual(engine.tick(force=True)["status"], "error")
            self.assertEqual(engine.status()["last_error"], "no_courses")

    def test_stepwise_refresh_submits_and_dedupes(self):
        with tempfile.TemporaryDirectory() as directory:
            engine, service = self.engine(directory)
            # 1) course list must refresh first
            self.assertEqual(engine.tick(force=True)["status"], "refreshing_courses")
            self.assertEqual(service.courses.refreshes, [None])
            # 2) then the selected course detail
            service.courses.list_data = [{"id": "123", "long_name": "과목"}]
            service.courses.list_expired = False
            self.assertEqual(engine.tick(force=True)["status"], "refreshing_course")
            self.assertEqual(service.courses.refreshes[-1], "123")
            # 3) detection submits only the selectable video
            service.courses.detail["123"] = {
                "weeks": [
                    {
                        "lectures": [
                            lecture("u1"),
                            lecture("u2", is_upcoming=True),
                            lecture("u3", is_video=False),
                        ]
                    }
                ]
            }
            result = engine.tick(force=True)
            self.assertEqual(result["status"], "ok")
            self.assertEqual([row["url"] for row in service.playback.records], ["u1"])
            self.assertEqual(service.playback.records[0]["scope"], "download")
            self.assertTrue(engine.status()["last_run"])
            # 4) rerun does not enqueue known lectures again
            engine.tick(force=True)
            self.assertEqual(len(service.playback.records), 1)
            # 5) a genuinely new lecture is enqueued
            service.courses.detail["123"]["weeks"][0]["lectures"].append(lecture("u4"))
            engine.tick(force=True)
            self.assertEqual([row["url"] for row in service.playback.records], ["u1", "u4"])

    def test_full_scope_uses_summarize_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            engine, service = self.engine(directory, auto_save_scope="full")
            service.courses.list_expired = False
            service.courses.list_data = [{"id": "123"}]
            service.courses.detail["123"] = {"weeks": [{"lectures": [lecture("u1")]}]}
            engine.tick(force=True)
            self.assertEqual(service.playback.records[0]["scope"], "full")

    def test_engine_skips_already_watched_lectures(self):
        with tempfile.TemporaryDirectory() as directory:
            engine, service = self.engine(directory)
            service.courses.list_expired = False
            service.courses.list_data = [{"id": "123"}]
            service.courses.detail["123"] = {
                "weeks": [{"lectures": [
                    {**lecture("u1"), "completion": "completed"},
                    {**lecture("u2"), "attendance": "none", "completion": "incomplete"},
                ]}]
            }
            engine.tick(force=True)
            self.assertEqual([row["url"] for row in service.playback.records], ["u2"])

    def test_popup_repeat_pauses_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            engine, service = self.engine(directory)
            service.playback.popup_failed = True
            result = engine.tick()
            self.assertEqual(result["status"], "paused")
            self.assertEqual(result["reason"], "popup_repeat")
            self.assertTrue(engine.status()["paused"])

    def test_pause_blocks_until_resumed(self):
        with tempfile.TemporaryDirectory() as directory:
            engine, service = self.engine(directory)
            state = engine.store.read()
            state["paused"] = True
            engine.store.write(state)
            self.assertEqual(engine.tick()["status"], "paused")
            self.assertEqual(service.courses.refreshes, [])
            engine.resume()
            engine.tick(force=True)
            self.assertFalse(engine.status()["paused"])


if __name__ == "__main__":
    unittest.main()
