from __future__ import annotations

from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path

from .models import Event, Stock


def _summary(event: Event, limit: int = 160) -> str:
    text = " ".join((event.content or "").split())
    if not text:
        return "暂无正文摘要，请打开原文查看。"
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def generate_markdown(events: list[Event], stocks: list[Stock], minimum_score: int = 40) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    selected = [event for event in events if event.importance_score >= minimum_score]
    urgent = [event for event in selected if event.importance_level in {"紧急", "重大"}]

    lines = [
        f"# 个股跟踪晨报｜{now}",
        "",
        f"> 自选股 {len(stocks)} 只｜本次更新 {len(selected)} 条｜重大及以上 {len(urgent)} 条",
        "",
    ]
    if not selected:
        lines.append("本次未发现达到展示阈值的新事件。")
        return "\n".join(lines)

    for level in ("紧急", "重大", "一般", "低"):
        group = [event for event in selected if event.importance_level == level]
        if not group:
            continue
        lines.extend([f"## {level}更新", ""])
        for event in group:
            link = f"[原文]({event.url})" if event.url else "无链接"
            lines.extend(
                [
                    f"### {event.company_name}（{event.stock_code}）｜{event.importance_score}分",
                    f"- **事件：** {event.title}",
                    f"- **类型：** {event.event_type}｜{event.sentiment}",
                    f"- **影响：** {event.impact}",
                    f"- **摘要：** {_summary(event)}",
                    f"- **时间/来源：** {event.event_time[:16]}｜{event.source_type}｜{link}",
                    "",
                ]
            )
    lines.append("---")
    lines.append("评分由规则模型生成，用于筛选信息，不构成投资建议；重大事项应回到公告原文核实。")
    return "\n".join(lines)


def generate_html(events: list[Event], stocks: list[Stock], minimum_score: int = 40) -> str:
    selected = [event for event in events if event.importance_score >= minimum_score]
    counts = Counter(event.importance_level for event in selected)
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    cards: list[str] = []
    for event in selected:
        url = escape(event.url, quote=True)
        title = escape(event.title)
        content = escape(_summary(event, 220))
        impact = escape(event.impact)
        company = escape(event.company_name)
        source = escape(event.source_type)
        event_type = escape(event.event_type)
        sentiment = escape(event.sentiment)
        level_class = {"紧急": "urgent", "重大": "major", "一般": "normal", "低": "low"}.get(event.importance_level, "low")
        link = f'<a href="{url}" target="_blank" rel="noopener">查看原文 ↗</a>' if url else ""
        cards.append(
            f"""
            <article class="event-card {level_class}" data-company="{company}" data-level="{escape(event.importance_level)}">
              <div class="event-head">
                <div><strong>{company}</strong><span>{escape(event.stock_code)} · {event_type}</span></div>
                <div class="score">{event.importance_score}<small>分</small></div>
              </div>
              <h3>{title}</h3>
              <div class="badges"><b>{escape(event.importance_level)}</b><i>{sentiment}</i><i>{source}</i></div>
              <p>{content}</p>
              <div class="impact"><strong>潜在影响</strong>{impact}</div>
              <footer><time>{escape(event.event_time[:16])}</time>{link}</footer>
            </article>
            """
        )

    empty = '<div class="empty">本次未发现达到展示阈值的新事件。</div>' if not cards else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>个股跟踪晨报</title>
<style>
:root{{--bg:#f4f7fb;--card:#fff;--text:#172033;--muted:#6b7485;--line:#e6eaf0;--shadow:0 14px 35px rgba(20,35,70,.08)}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}}
.container{{max-width:1180px;margin:auto;padding:34px 22px 70px}}
.hero{{background:linear-gradient(135deg,#101d36,#273b67);color:#fff;border-radius:24px;padding:30px;box-shadow:var(--shadow)}}
.hero h1{{margin:0 0 8px;font-size:30px}} .hero p{{margin:0;color:#cbd5e8}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:22px}} .metric{{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.14);border-radius:16px;padding:15px}}
.metric strong{{display:block;font-size:26px}} .metric span{{font-size:13px;color:#cbd5e8}}
.toolbar{{display:flex;gap:12px;margin:22px 0;flex-wrap:wrap}} input,select{{border:1px solid var(--line);border-radius:12px;padding:11px 14px;background:#fff;font-size:14px;min-width:190px}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}
.event-card{{background:var(--card);border-radius:18px;padding:20px;border:1px solid var(--line);box-shadow:0 5px 18px rgba(20,35,70,.04);border-top:4px solid #9ca3af}}
.event-card.urgent{{border-top-color:#c62828}} .event-card.major{{border-top-color:#ef6c00}} .event-card.normal{{border-top-color:#1976d2}}
.event-head{{display:flex;justify-content:space-between;align-items:flex-start;gap:14px}} .event-head strong{{display:block;font-size:17px}} .event-head span{{display:block;color:var(--muted);font-size:12px;margin-top:4px}}
.score{{font-size:24px;font-weight:750}} .score small{{font-size:11px;color:var(--muted);margin-left:2px}}
h3{{font-size:16px;line-height:1.5;margin:16px 0 10px}} .badges{{display:flex;gap:7px;flex-wrap:wrap}} .badges b,.badges i{{font-style:normal;font-size:11px;border-radius:999px;padding:5px 9px;background:#eef2f7;color:#465168}}
.event-card p{{font-size:14px;color:#4e596d;line-height:1.7}} .impact{{font-size:13px;background:#f7f9fc;border-radius:12px;padding:12px;line-height:1.6}} .impact strong{{display:block;color:#222;margin-bottom:3px}}
footer{{display:flex;justify-content:space-between;align-items:center;margin-top:14px;font-size:12px;color:var(--muted)}} a{{color:#2459c4;text-decoration:none;font-weight:600}} .empty{{grid-column:1/-1;text-align:center;padding:70px;color:var(--muted)}}
.note{{text-align:center;color:var(--muted);font-size:12px;margin-top:28px}}
@media(max-width:760px){{.metrics{{grid-template-columns:repeat(2,1fr)}}.grid{{grid-template-columns:1fr}}.hero h1{{font-size:25px}}}}
</style>
</head>
<body><main class="container">
<section class="hero"><h1>个股跟踪晨报</h1><p>最后更新：{generated} · 规则筛选版 MVP</p>
<div class="metrics"><div class="metric"><strong>{len(stocks)}</strong><span>自选股</span></div><div class="metric"><strong>{len(selected)}</strong><span>有效更新</span></div><div class="metric"><strong>{counts.get('紧急',0)+counts.get('重大',0)}</strong><span>重大及以上</span></div><div class="metric"><strong>{len(set(e.company_name for e in selected))}</strong><span>涉及公司</span></div></div></section>
<div class="toolbar"><input id="search" placeholder="搜索公司或事件"><select id="level"><option value="">全部级别</option><option>紧急</option><option>重大</option><option>一般</option><option>低</option></select></div>
<section class="grid" id="grid">{''.join(cards)}{empty}</section>
<p class="note">自动评分仅用于信息筛选，不构成投资建议。请以公告原文和正式研究为准。</p>
</main>
<script>
const search=document.getElementById('search'),level=document.getElementById('level');
function filter(){{const q=search.value.trim().toLowerCase(),lv=level.value;document.querySelectorAll('.event-card').forEach(card=>{{const okQ=!q||card.innerText.toLowerCase().includes(q);const okL=!lv||card.dataset.level===lv;card.style.display=okQ&&okL?'block':'none';}})}}
search.addEventListener('input',filter);level.addEventListener('change',filter);
</script></body></html>"""


def save_reports(markdown_path: Path, html_path: Path, events: list[Event], stocks: list[Stock], minimum_score: int) -> None:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(generate_markdown(events, stocks, minimum_score), encoding="utf-8")
    html_path.write_text(generate_html(events, stocks, minimum_score), encoding="utf-8")
