from __future__ import annotations

import logging
from pathlib import Path

from .classifier import classify_events
from .config import DATA_DIR, DOCS_DIR, load_settings, load_watchlist
from .fetchers import fetch_all
from .notifications import send_feishu
from .report import save_reports
from .storage import load_events, merge_events, save_events

LOGGER = logging.getLogger(__name__)


def run(root: Path | None = None, notify: bool = True) -> dict[str, int]:
    settings = load_settings()
    stocks = load_watchlist()
    if not stocks:
        raise RuntimeError("自选股为空，请先编辑 config/watchlist.csv")

    sources = settings.get("sources", {})
    raw = fetch_all(
        stocks,
        lookback_days=int(settings.get("lookback_days", 3)),
        announcements=bool(sources.get("announcements", True)),
        news=bool(sources.get("news", True)),
    )
    thresholds = {
        "urgent": int(settings.get("urgent_score", 85)),
        "important": int(settings.get("important_score", 70)),
        "normal": int(settings.get("normal_score", 50)),
    }
    classified = classify_events(raw, thresholds)

    event_path = DATA_DIR / "events.json"
    existing = load_events(event_path)
    merged = merge_events(existing, classified, int(settings.get("history_days", 90)))
    save_events(event_path, merged)

    markdown_path = DATA_DIR / "latest_report.md"
    html_path = DOCS_DIR / "index.html"
    minimum_score = int(settings.get("minimum_display_score", 40))
    save_reports(markdown_path, html_path, merged, stocks, minimum_score)

    if notify and bool(settings.get("notifications", {}).get("feishu_enabled", True)):
        send_feishu(markdown_path.read_text(encoding="utf-8"))

    stats = {
        "stocks": len(stocks),
        "fetched": len(raw),
        "stored": len(merged),
        "important": sum(event.importance_score >= thresholds["important"] for event in classified),
    }
    LOGGER.info("运行完成: %s", stats)
    return stats
