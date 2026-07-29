# 个股跟踪晨报 MVP

一个可直接运行的 A 股自选股跟踪初级版本：输入股票代码加入自选，自动抓取公告和个股新闻，进行去重、分类、重要性评分，并生成网页晨报。GitHub Actions 默认每天北京时间 08:00 自动运行。

## 已实现

- 自选股 CSV 配置，以及 Streamlit 页面添加自选股
- 东方财富个股公告抓取
- 东方财富个股新闻抓取
- 事件去重与 90 天历史保存
- 规则分类：业绩、合同、并购、风险、减持、产能、管理层等
- 0—100 分重要性评分
- 静态网页 `docs/index.html`
- Markdown 晨报 `data/latest_report.md`
- 可选飞书机器人推送
- GitHub Actions 每日自动运行

## 项目结构

```text
stock_monitor_mvp/
├── app.py                       # Streamlit 可视化与自选股管理
├── run_daily.py                 # 每日任务入口
├── config/
│   ├── watchlist.csv            # 自选股
│   └── settings.yaml            # 运行参数
├── src/stock_monitor/           # 抓取、评分、存储、报告模块
├── data/                        # 事件库和晨报
├── docs/index.html              # GitHub Pages 静态看板
└── .github/workflows/daily.yml  # 08:00 自动任务
```

## 本地运行

建议 Python 3.11。

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
# 中国网络环境安装 AKShare 失败时，可改用：
# pip install akshare -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com --upgrade
python run_daily.py
streamlit run app.py
```

运行后浏览器会打开管理页面。首次抓取依赖外网访问东方财富数据接口。

## 修改自选股

直接编辑 `config/watchlist.csv`：

```csv
code,name,industry,priority,thesis
300502,新易盛,光模块,high,AI算力基础设施带动高速光模块需求
```

字段说明：

- `code`：6 位股票代码
- `name`：公司名称
- `industry`：行业标签
- `priority`：`high`、`medium` 或 `low`
- `thesis`：一句话投资逻辑，后续版本可用于“事件是否改变逻辑”的判断

也可以在 Streamlit 左侧表单加入自选股。本地写入会保存；在 Streamlit Community Cloud 上，建议仍通过 GitHub 修改 CSV，以保证长期保存。

## GitHub 自动更新

1. 新建 GitHub 仓库并上传整个项目。
2. 在仓库 `Settings → Actions → General` 中允许 Actions 写入仓库内容。
3. 打开 `Actions`，手动运行一次 `Daily Stock Monitor` 测试。
4. 工作流中的 `0 0 * * *` 表示每天 00:00 UTC，即北京时间 08:00。
5. 在 `Settings → Pages` 中选择从 `main / docs` 部署，即可获得静态网页地址。

GitHub Actions 的定时任务可能因平台负载出现几分钟延迟，因此它适合晨报，不适合盘中秒级预警。

## 飞书推送

在飞书群中创建自定义机器人，复制 Webhook；然后在 GitHub 仓库：

`Settings → Secrets and variables → Actions → New repository secret`

新增：

```text
Name: FEISHU_WEBHOOK
Value: 你的飞书机器人 Webhook
```

未配置时程序会正常生成网页和晨报，只跳过推送。

## 评分逻辑

初版采用规则而不是大模型，以降低成本和避免无依据判断：

- 并购、控制权、重大资产：高分
- 业绩预告、定期报告：高分
- 重大合同、中标、订单：中高分
- 立案、处罚、诉讼、风险提示：高分
- 减持、回购、定增、解禁：中等分
- 产能、投产、新产品、技术突破：中等分
- 公告来源和 high 优先级会获得额外加分

评分只用于信息筛选，不能代替研究员阅读公告原文。

## 初版尚未覆盖

- 微信公众号自动抓取
- 券商研报全文与一致预期变化
- 公司客户、供应商和竞争对手关系图谱
- AI 自动判断对收入、利润、DCF 的量化影响
- 盘中实时预警
- 多用户账号与数据库

这些模块已经可以沿用当前 Event 数据结构继续开发，不需要推倒重来。
