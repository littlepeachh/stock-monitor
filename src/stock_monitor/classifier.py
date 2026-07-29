from __future__ import annotations

from dataclasses import dataclass

from .models import Event


@dataclass(frozen=True)
class Rule:
    name: str
    keywords: tuple[str, ...]
    base_score: int
    impact: str


RULES: tuple[Rule, ...] = (
    Rule("控制权/并购重组", ("控制权", "实际控制人", "并购", "重组", "收购", "重大资产"), 88, "可能改变公司资产结构、治理或估值框架"),
    Rule("业绩与财务", ("业绩预告", "业绩快报", "年度报告", "季度报告", "半年度报告", "净利润", "营收"), 78, "可能影响盈利预测和估值水平"),
    Rule("重大合同/订单", ("重大合同", "中标", "订单", "框架协议", "采购协议", "战略合作"), 76, "可能影响未来收入确认和订单能见度"),
    Rule("风险与监管", ("立案", "处罚", "问询函", "监管", "诉讼", "仲裁", "风险提示", "终止"), 82, "可能提高风险溢价或影响经营预期"),
    Rule("股东与资本运作", ("减持", "增持", "回购", "解禁", "质押", "可转债", "定增", "融资"), 67, "可能影响供需结构、治理预期或每股价值"),
    Rule("产能与产品", ("扩产", "产能", "投产", "新产品", "技术突破", "研发", "认证"), 64, "可能影响中期成长性、资本开支和竞争力"),
    Rule("管理层与治理", ("董事长", "总经理", "董事", "高管", "辞职", "聘任"), 62, "可能影响公司治理和战略执行稳定性"),
    Rule("投资者交流", ("投资者关系", "调研", "业绩说明会", "机构调研"), 55, "可用于更新经营趋势和市场预期"),
    Rule("行业/市场新闻", ("行业", "政策", "价格", "需求", "供给", "资本开支", "客户"), 52, "需结合公司产业链位置判断间接影响"),
)

POSITIVE = ("增长", "上调", "中标", "突破", "增持", "回购", "盈利", "扭亏", "创新高", "放量")
NEGATIVE = ("下降", "下调", "亏损", "减持", "处罚", "立案", "诉讼", "终止", "风险", "延期", "辞职")
HIGH_PRIORITY_BONUS = {"high": 6, "medium": 2, "low": 0}


def classify_event(event: Event, thresholds: dict[str, int] | None = None) -> Event:
    text = f"{event.title} {event.content}".lower()
    matched = [rule for rule in RULES if any(keyword.lower() in text for keyword in rule.keywords)]

    if matched:
        best = max(matched, key=lambda rule: rule.base_score)
        event.event_type = best.name
        event.impact = best.impact
        score = best.base_score
    else:
        event.event_type = "一般动态"
        event.impact = "当前未识别出明确财务影响，建议快速浏览原文"
        score = 42 if "公告" in event.source_type else 38

    # Source reliability and user priority adjustments.
    if "公告" in event.source_type:
        score += 6
    elif "新闻" in event.source_type:
        score += 1
    score += HIGH_PRIORITY_BONUS.get(event.priority, 0)

    # Extra weight for especially consequential terms.
    if any(word in text for word in ("重大", "修正", "控制权", "立案", "暂停上市", "退市")):
        score += 5
    event.importance_score = min(100, max(0, score))

    positive_hits = sum(word in text for word in POSITIVE)
    negative_hits = sum(word in text for word in NEGATIVE)
    if positive_hits > negative_hits:
        event.sentiment = "偏正面"
    elif negative_hits > positive_hits:
        event.sentiment = "偏负面"
    else:
        event.sentiment = "中性"

    values = thresholds or {"urgent": 85, "important": 70, "normal": 50}
    if event.importance_score >= values["urgent"]:
        event.importance_level = "紧急"
    elif event.importance_score >= values["important"]:
        event.importance_level = "重大"
    elif event.importance_score >= values["normal"]:
        event.importance_level = "一般"
    else:
        event.importance_level = "低"
    return event


def classify_events(events: list[Event], thresholds: dict[str, int] | None = None) -> list[Event]:
    return [classify_event(event, thresholds) for event in events]
