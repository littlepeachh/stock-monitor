from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from stock_monitor.config import CONFIG_DIR, DATA_DIR, load_settings, load_watchlist  # noqa: E402
from stock_monitor.pipeline import run  # noqa: E402
from stock_monitor.storage import load_events  # noqa: E402

st.set_page_config(page_title="个股跟踪", page_icon="📡", layout="wide")
st.title("📡 个股跟踪晨报")
st.caption("MVP：公告 + 个股新闻 + 规则评分 + 每日自动更新")

settings = load_settings()
watchlist_path = CONFIG_DIR / "watchlist.csv"

with st.sidebar:
    st.header("自选股管理")
    with st.form("add_stock", clear_on_submit=True):
        code = st.text_input("股票代码", max_chars=6, placeholder="例如 300502")
        name = st.text_input("公司名称", placeholder="例如 新易盛")
        industry = st.text_input("行业", placeholder="例如 光模块")
        priority = st.selectbox("优先级", ["high", "medium", "low"])
        thesis = st.text_area("关注逻辑", placeholder="一句话记录核心投资逻辑")
        submitted = st.form_submit_button("加入自选")
        if submitted:
            normalized = code.strip().zfill(6)
            if len(normalized) != 6 or not normalized.isdigit() or not name.strip():
                st.error("请输入6位股票代码和公司名称。")
            else:
                frame = pd.read_csv(watchlist_path, dtype={"code": str}).fillna("") if watchlist_path.exists() else pd.DataFrame(columns=["code", "name", "industry", "priority", "thesis"])
                frame["code"] = frame["code"].astype(str).str.zfill(6)
                if normalized in set(frame["code"]):
                    st.warning("该股票已在自选股中。")
                else:
                    frame.loc[len(frame)] = [normalized, name.strip(), industry.strip(), priority, thesis.strip()]
                    frame.to_csv(watchlist_path, index=False, encoding="utf-8-sig")
                    st.success("已加入自选股。")
                    st.rerun()

    if st.button("立即更新数据", use_container_width=True):
        with st.spinner("正在抓取和整理…"):
            try:
                stats = run(notify=False)
                st.success(f"完成：抓取 {stats['fetched']} 条，保存 {stats['stored']} 条")
                st.rerun()
            except Exception as exc:
                st.error(f"更新失败：{exc}")

stocks = load_watchlist()
events = load_events(DATA_DIR / "events.json")

metric1, metric2, metric3, metric4 = st.columns(4)
metric1.metric("自选股", len(stocks))
metric2.metric("历史事件", len(events))
metric3.metric("重大及以上", sum(e.importance_level in {"紧急", "重大"} for e in events))
metric4.metric("涉及公司", len({e.company_name for e in events}))

st.subheader("自选股")
watch_frame = pd.DataFrame([s.__dict__ if hasattr(s, "__dict__") else {"code": s.code, "name": s.name, "industry": s.industry, "priority": s.priority, "thesis": s.thesis} for s in stocks])
if not watch_frame.empty:
    st.dataframe(watch_frame, use_container_width=True, hide_index=True)

st.subheader("最新事件")
col1, col2, col3 = st.columns([2, 1, 1])
query = col1.text_input("搜索", placeholder="公司、标题或事件类型")
levels = col2.multiselect("重要性", ["紧急", "重大", "一般", "低"], default=["紧急", "重大", "一般"])
source = col3.selectbox("来源", ["全部", "公司公告", "新闻"])

filtered = []
for event in events:
    haystack = f"{event.company_name} {event.stock_code} {event.title} {event.event_type}".lower()
    if query and query.lower() not in haystack:
        continue
    if levels and event.importance_level not in levels:
        continue
    if source == "公司公告" and "公告" not in event.source_type:
        continue
    if source == "新闻" and "新闻" not in event.source_type:
        continue
    filtered.append(event)

for event in filtered[:100]:
    with st.container(border=True):
        c1, c2 = st.columns([7, 1])
        c1.markdown(f"### {event.company_name}（{event.stock_code}）")
        c1.caption(f"{event.event_time[:16]} · {event.source_type} · {event.event_type} · {event.sentiment}")
        c2.metric(event.importance_level, event.importance_score)
        st.markdown(f"**{event.title}**")
        if event.content:
            st.write(event.content[:260] + ("…" if len(event.content) > 260 else ""))
        st.info(f"潜在影响：{event.impact}")
        if event.url:
            st.link_button("查看原文", event.url)

if not filtered:
    st.info("暂无符合条件的事件。首次使用请点击左侧“立即更新数据”。")
