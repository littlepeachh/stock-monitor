from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Iterable

import pandas as pd

from .models import Event, Stock

LOGGER = logging.getLogger(__name__)


def _to_iso(value: object) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return str(value)[:19]
    if isinstance(parsed, pd.Timestamp):
        return parsed.to_pydatetime().isoformat(timespec="seconds")
    return str(value)[:19]


def _within_lookback(value: object, lookback_days: int) -> bool:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return True
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=lookback_days)
    if getattr(parsed, "tzinfo", None) is not None:
        parsed = parsed.tz_localize(None)
    return parsed >= cutoff.normalize()


def fetch_announcements(stock: Stock, lookback_days: int = 3) -> list[Event]:
    """Fetch announcements through AKShare's Eastmoney adapter."""
    try:
        import akshare as ak

        end = date.today()
        begin = end - timedelta(days=lookback_days)
        frame = ak.stock_individual_notice_report(
            security=stock.code,
            symbol="全部",
            begin_date=begin.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
        )
    except Exception as exc:  # Network/provider failures should not stop the full run.
        LOGGER.warning("公告抓取失败 %s %s: %s", stock.code, stock.name, exc)
        return []

    if frame is None or frame.empty:
        return []

    events: list[Event] = []
    for row in frame.fillna("").to_dict("records"):
        title = str(row.get("公告标题", "")).strip()
        if not title:
            continue
        events.append(
            Event(
                stock_code=stock.code,
                company_name=stock.name or str(row.get("名称", "")).strip(),
                event_time=_to_iso(row.get("公告日期", "")),
                source_type="公司公告",
                title=title,
                url=str(row.get("网址", "")).strip(),
                content=str(row.get("公告类型", "")).strip(),
                industry=stock.industry,
                priority=stock.priority,
            ).finalize()
        )
    return events


def fetch_news(stock: Stock, lookback_days: int = 3) -> list[Event]:
    """Fetch recent company news through AKShare's Eastmoney adapter."""
    try:
        import akshare as ak

        frame = ak.stock_news_em(symbol=stock.code)
    except Exception as exc:
        LOGGER.warning("新闻抓取失败 %s %s: %s", stock.code, stock.name, exc)
        return []

    if frame is None or frame.empty:
        return []

    events: list[Event] = []
    for row in frame.fillna("").to_dict("records"):
        published = row.get("发布时间", "")
        if not _within_lookback(published, lookback_days):
            continue
        title = str(row.get("新闻标题", "")).strip()
        if not title:
            continue
        content = str(row.get("新闻内容", "")).strip()
        source = str(row.get("文章来源", "")).strip()
        events.append(
            Event(
                stock_code=stock.code,
                company_name=stock.name,
                event_time=_to_iso(published),
                source_type=f"新闻-{source}" if source else "个股新闻",
                title=title,
                url=str(row.get("新闻链接", "")).strip(),
                content=content,
                industry=stock.industry,
                priority=stock.priority,
            ).finalize()
        )
    return events


def fetch_for_stock(
    stock: Stock,
    lookback_days: int,
    announcements: bool = True,
    news: bool = True,
) -> list[Event]:
    events: list[Event] = []
    if announcements:
        events.extend(fetch_announcements(stock, lookback_days))
    if news:
        events.extend(fetch_news(stock, lookback_days))
    return events


def fetch_all(
    stocks: Iterable[Stock],
    lookback_days: int,
    announcements: bool = True,
    news: bool = True,
) -> list[Event]:
    events: list[Event] = []
    for stock in stocks:
        events.extend(fetch_for_stock(stock, lookback_days, announcements, news))
    return events
