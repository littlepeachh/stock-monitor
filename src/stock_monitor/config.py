from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .models import Stock


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"


def load_settings(path: Path | None = None) -> dict[str, Any]:
    target = path or CONFIG_DIR / "settings.yaml"
    with target.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_watchlist(path: Path | None = None) -> list[Stock]:
    target = path or CONFIG_DIR / "watchlist.csv"
    if not target.exists():
        return []
    frame = pd.read_csv(target, dtype={"code": str}).fillna("")
    required = {"code", "name"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"自选股文件缺少字段: {', '.join(sorted(missing))}")

    stocks: list[Stock] = []
    for row in frame.to_dict("records"):
        code = str(row.get("code", "")).strip().zfill(6)
        if not code:
            continue
        stocks.append(
            Stock(
                code=code,
                name=str(row.get("name", "")).strip(),
                industry=str(row.get("industry", "")).strip(),
                priority=str(row.get("priority", "medium")).strip().lower() or "medium",
                thesis=str(row.get("thesis", "")).strip(),
            )
        )
    return stocks
