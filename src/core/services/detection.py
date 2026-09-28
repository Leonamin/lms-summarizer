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


ATTENDED_TOKENS = frozenset({'attendance', 'attended', 'excused'})


def is_watched(lecture: dict) -> bool:
    """True when the lecture is already completed or attendance is granted."""
    return (lecture.get('completion') == 'completed'
            or lecture.get('attendance') in ATTENDED_TOKENS)


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


def select_playback_videos(seen: dict, lectures) -> list[dict]:
    """New selectable videos that still need attendance playback.

    Already completed / attended lectures are skipped: playing them again does
    not change attendance and would needlessly occupy the single Chrome slot.
    """
    return [lecture for lecture in select_new_videos(seen, lectures)
            if not is_watched(lecture)]


def mark_seen(seen: dict, lectures, now=None) -> dict:
    stamp = (now or datetime.now(timezone.utc)).isoformat()
    for lecture in lectures:
        key = lecture_key(lecture)
        if key:
            seen.setdefault(key, stamp)
    return seen
