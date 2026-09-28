"""Pure helpers for auto-detect: pick new selectable lecture videos from a listing."""
from datetime import datetime, timezone


def lecture_key(lecture: dict) -> str | None:
    """Stable identity for a lecture across listings (URL, else title)."""
    return lecture.get('url') or lecture.get('title') or None


def flatten_lectures(weeks) -> list[dict]:
    rows: list[dict] = []
    for week in weeks or []:
        rows.extend(week.get('lectures', []))
    return rows


def is_selectable(lecture: dict) -> bool:
    return bool(lecture.get('is_video')) and not lecture.get('is_upcoming')


def select_new_videos(seen: dict, lectures) -> list[dict]:
    """Return selectable videos not present in ``seen`` (record keyed by identity)."""
    new: list[dict] = []
    for lecture in lectures:
        if not is_selectable(lecture):
            continue
        key = lecture_key(lecture)
        if not key or key in seen:
            continue
        new.append(lecture)
    return new


def mark_seen(seen: dict, lectures, now=None) -> dict:
    stamp = (now or datetime.now(timezone.utc)).isoformat()
    for lecture in lectures:
        key = lecture_key(lecture)
        if key:
            seen.setdefault(key, stamp)
    return seen
