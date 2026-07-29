from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from .models import Event


def load_events(path: Path) -> list[Event]:
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(raw, list):
        return []
    return [Event.from_dict(item) for item in raw if isinstance(item, dict)]


def merge_events(existing: list[Event], incoming: list[Event], history_days: int = 90) -> list[Event]:
    merged = {event.event_id or event.finalize().event_id: event for event in existing}
    for event in incoming:
        merged[event.event_id or event.finalize().event_id] = event

    cutoff = datetime.now() - timedelta(days=history_days)
    kept: list[Event] = []
    for event in merged.values():
        try:
            event_dt = datetime.fromisoformat(event.event_time[:19])
        except (TypeError, ValueError):
            event_dt = datetime.now()
        if event_dt >= cutoff:
            kept.append(event)

    return sorted(
        kept,
        key=lambda item: (item.event_time, item.importance_score),
        reverse=True,
    )


def save_events(path: Path, events: list[Event]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [event.to_dict() for event in events]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
