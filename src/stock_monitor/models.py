from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha1
from typing import Any


@dataclass(slots=True)
class Stock:
    code: str
    name: str
    industry: str = ""
    priority: str = "medium"
    thesis: str = ""


@dataclass(slots=True)
class Event:
    stock_code: str
    company_name: str
    event_time: str
    source_type: str
    title: str
    url: str = ""
    content: str = ""
    event_type: str = "其他"
    importance_score: int = 0
    importance_level: str = "低"
    sentiment: str = "中性"
    impact: str = "需人工判断"
    industry: str = ""
    priority: str = "medium"
    event_id: str = ""
    fetched_at: str = ""

    def finalize(self) -> "Event":
        normalized = "|".join(
            [
                self.stock_code.strip(),
                self.title.strip(),
                self.event_time[:10],
                self.url.strip(),
            ]
        )
        self.event_id = sha1(normalized.encode("utf-8")).hexdigest()[:20]
        if not self.fetched_at:
            self.fetched_at = datetime.now().isoformat(timespec="seconds")
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Event":
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: value.get(key) for key in allowed})
