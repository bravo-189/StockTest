# StockTest 对话窗口交接文档

> 这是更换对话窗口时的唯一交接入口。新窗口先阅读本文件，再按链接读取完整上下文和最近进度；后续只更新本文件与 `PROJECT_PROGRESS.md`，不要重复生成同类交接/进度文档。

**最后更新：** 2026-08-31
**项目目录：** `C:\Users\i023j\.codex\.chatgpt-projects\g-p-6a914fbe15f881918f3b80c224c6d0e9\StockTest`  
**运行方式：** 本地静态网页，默认 `http://127.0.0.1:8765/index.html`  
**当前阶段：** 网页原型、本地数据质量、异常状态与一键常驻刷新均已完成；本地市场分析 Task 1–3 已完成并审查通过，Task 4 已实现但待独立复审；主题 AI 排名、小程序和 GitHub 上线暂缓。

## 新窗口启动顺序

1. 阅读本文件。
2. 阅读 [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) 的产品口径、数据契约和文件地图。
3. 阅读 [PROJECT_PROGRESS.md](./PROJECT_PROGRESS.md) 最近一条记录，不重复已完成工作。
4. 检查 `sources/` 只读状态。
5. 运行测试和语法检查：

   ```powershell
   <PYTHON> -m unittest discover -s StockTest/data_pipeline -p 'test_*.py' -v
   <NODE> --check StockTest/app.js
   ```

6. 运行 `StockTest\status-local.cmd`；若网页或刷新进程未运行，再双击 `StockTest\start-local.cmd`，不要另开重复服务器。

   ```powershell
   StockTest\status-local.cmd
   ```

## 当前不可回退的产品口径

- 网页优先，小程序延期到网页验收和稳定后另立项目。
- 主题 Top 20 暂停，不恢复主题 UI；候选目录和 AI 研究契约保留备用。
- 新闻热度和独立基本面 UI 已删除；基本面只可作为未来后台主题研究输入。
- 主要市场为 SPX、NDX、DJI、RUT、BTC，共 5 张卡片；近一个月迷你 K 线约 21 个交易日。
- 板块 ETF 与权重股为同一模块；板块共 14 个（含 IBIT），SPY 固定首行。
- 板块表 RSI14、Δ5、Δ20 支持排序，状态使用表头下拉筛选；SPY 状态不可修改。
- 板块模块保留 12 个权重股入口；详情统一使用右侧抽屉查看前十大持仓。
- 行业表支持“强势 15 / 全部 60”、RSI14/Δ5/20 日排序和每行前十大入口；删除“动能”列。
- 市场宽度直接使用 Stockbee 原始列折线图；20 日表默认折叠，展开后使用卡片顶部横向滚动条，日期列固定。
- 浏览器只读取本地 JSON，不在页面中直连 Yahoo、Binance 或 Stockbee。

## 最近已完成并验证

### 网页与交互

- 盘后研究简报方向的浅色/深色主题网页原型。
- 苹果式深色模式开关、固定侧边栏、响应式桌面/平板/移动布局。
- 板块、行业、抽屉、状态筛选、排序、SPY 固定、强势 15/全部 60 均已实现。
- 市场宽度图表卡片已重构，含当前指标和最新观察读数。
- Stockbee 原始表顶部独立横向滚动条已实现，支持鼠标拖动和 `←`、`→`、`Home`、`End`。

### 数据与日期口径

- 本地行情快照：76/76 标的，包含 4 个指数、14 个板块 ETF、60 个行业 ETF 和 BTC。
- `pendingBars` 保留 Yahoo 未收盘日线，不参与收盘价、RSI 或多周期收益。
- Stockbee：20 行、15 个指标、20 个唯一日期，最新日期 `2026-08-28`。
- 美股交易日历：`us-equity`，最新确认收盘日 `2026-08-28`。
- BTC 交易日历：`crypto-24x7`，真实最新日线 `2026-08-30`。
- 跨资产共同基准：`comparisonDate = 2026-08-28`。
- 页面显示：`2026-08-28 美股收盘 · BTC 最新 2026-08-30 · 本地快照`。
- `start-local.cmd` 已在后台运行网页和每 60 分钟刷新进程；重复启动会复用现有 PID。
- 刷新状态通过 `data/refresh_status.json` 展示新鲜、过期、局部缺失或失败保留旧数据。
- 日历差异已从质量异常调整为信息说明，不补造美股周末 K 线。

### 验证结果

- Python 测试：50 项通过。
- JavaScript 语法检查：通过。
- 本地 HTTP：200。
- 浏览器日期提示正确，控制台 error/warn 为 0。
- 行情质量报告：0 个高/中风险 finding，1 条交易日历 info note。
- 设计 QA：[design-qa.md](./design-qa.md) 保持 `final result: passed`。

## 关键文件入口

- [index.html](./index.html)：页面结构和本地资源引用。
- [styles.css](./styles.css)：主题、布局、组件和响应式规则。
- [app.js](./app.js)：交互、快照 hydration、指标计算和 Canvas 图表。
- [data/market_snapshot.json](./data/market_snapshot.json)：76 个市场标的本地快照。
- [data/market_snapshot_quality.json](./data/market_snapshot_quality.json)：最近一次行情质量报告。
- [data/stockbee.json](./data/stockbee.json)：Stockbee 最近 20 个交易日快照。
- [data_pipeline/fetch_market_data.py](./data_pipeline/fetch_market_data.py)：Yahoo/Binance 快照生成。
- [data_pipeline/refresh_local_data.py](./data_pipeline/refresh_local_data.py)：一次或每小时刷新行情与 Stockbee。
- [data_pipeline/local_runtime.py](./data_pipeline/local_runtime.py)：后台进程、PID、日志和重复启动保护。
- [start-local.cmd](./start-local.cmd)、[status-local.cmd](./status-local.cmd)、[stop-local.cmd](./stop-local.cmd)：Windows 一键运行入口。
- [data_pipeline/validate_market_snapshot.py](./data_pipeline/validate_market_snapshot.py)：行情质量检查。
- [data_pipeline/stockbee.py](./data_pipeline/stockbee.py)：Stockbee CSV 解析与字段校验。
- [data_pipeline/test_*.py](./data_pipeline/)：数据、UI 和契约测试。

## 下一步（需用户确认后执行）

P0 数据质量、P1 异常状态与备用源评估、P2 本地一键常驻运行均已完成。下一步候选是美股 ETF 备用源适配；Alpaca 需要账号密钥且免费实时仅 IEX，Alpha Vantage 免费额度不足以支持 76 个标的一小时轮询，因此接入前需要用户确认数据源与口径。

在用户确认前，不要恢复主题 AI 排名、不接入小程序、不发布 GitHub Pages，也不要重做已有页面交互。

## 2026-08-31 本地执行交接

- GitHub 远程仓库、推送、PR、Pages 发布与线上授权操作已按用户要求暂停；不要主动恢复。
- 当前本地特性分支：`.worktrees/market-analysis-evidence/StockTest`，分支名 `feature/market-analysis-evidence`。
- Task 1–3 已完成并通过独立审查：来源/证据契约、五因子评分与日期对齐、证据化结论与置信度。
- Task 4 已实现：刷新成功后生成/复用 `market_analysis.json`，失败保留旧分析；但还未完成独立复审。
- Task 5：首页市场状态卡与证据抽屉尚未开始；Task 6：端到端 QA 和最终本地交付尚未开始。
- 最新本地实现分支提交：`6d315f6`；不要将其视为已合并到 `main` 或已上线。
- 详细证据、提交、测试数量和暂停项见 [PROJECT_PROGRESS.md](./PROJECT_PROGRESS.md) 的 `2026-08-31 本地执行状态（GitHub 暂停后）`。

## 防重复规则

- 先读本文件和 `PROJECT_PROGRESS.md`，再动手。
- 同类工作日志只更新 `PROJECT_PROGRESS.md`；本文件只更新交接状态和启动入口。
- 新增代码先写失败测试并确认失败，再写最小实现。
- 不修改、移动、删除 `sources/`。
- 不把示例值、未收盘值或候选主题说成最终实时结论。
- 每次完成声明必须附实际测试或浏览器证据。

## 可直接粘贴到新窗口的启动语句

```text
请只在本机继续 StockTest，不进行任何 GitHub 推送、PR、Pages 发布或授权操作。先阅读 StockTest/PROJECT_HANDOFF.md、PROJECT_CONTEXT.md 和 PROJECT_PROGRESS.md 最近的 2026-08-31 记录；当前本地特性分支 .worktrees/market-analysis-evidence/StockTest 已完成 Task 1–3，Task 4 已实现但待独立复审，Task 5/6 尚未开始。运行现有 data_pipeline 测试和 app.js 语法检查，不重复制作已有页面、数据契约或进度文档；然后等待我的新本地需求。主题 AI、小程序、新闻热度、基本面 UI 与线上部署继续暂停。
```
