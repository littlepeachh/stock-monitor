from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stock_monitor.classifier import classify_event
from stock_monitor.models import Event


def test_major_contract_is_important():
    event = Event(
        stock_code="300502",
        company_name="测试公司",
        event_time="2026-07-29T08:00:00",
        source_type="公司公告",
        title="关于签署重大合同的公告",
        priority="high",
    ).finalize()
    result = classify_event(event)
    assert result.event_type == "重大合同/订单"
    assert result.importance_score >= 70
    assert result.importance_level in {"重大", "紧急"}
