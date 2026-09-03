# StockTest 对话窗口交接文档

> 这是更换对话窗口时的唯一交接入口。新窗口先阅读本文件，再按链接读取完整上下文和最近进度；后续只更新本文件与 `PROJECT_PROGRESS.md`，不要重复生成同类交接/进度文档。

**最后更新：** 2026-09-03
**项目目录：** `C:\Users\i023j\.codex\.chatgpt-projects\g-p-6a914fbe15f881918f3b80c224c6d0e9\StockTest`  
**运行方式：** 本地静态网页，默认 `http://127.0.0.1:8765/index.html`  
**当前阶段：** 网页原型、本地数据质量、异常状态与一键常驻刷新均已完成；板块/行业每日 RSI 历史表、SPY 滚动固定、前十大持仓名单和指数 TradingView 跳转已完成；当前收束为“只展示前十大名单、不展示持仓比例、保留来源异常证据”。本地市场分析 Task 1–4 已完成复审；主题 AI 排名、小程序和 GitHub 上线暂缓。

## 新窗口启动顺序

1. 阅读本文件。
2. 阅读 [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) 的产品口径、数据契约和文件地图。
3. 阅读 [PROJECT_PROGRESS.md](./PROJECT_PROGRESS.md) 最近一条记录，不重复已完成工作。
4. 阅读 [PROJECT_ROADMAP.md](./PROJECT_ROADMAP.md)，从当前首个未完成阶段开始，不跨阶段猜测。
5. 检查 `sources/` 只读状态。
6. 运行测试和语法检查：

   ```powershell
   <PYTHON> -m unittest discover -s StockTest/data_pipeline -p 'test_*.py' -v
   <NODE> --check StockTest/app.js
   ```

7. 运行 `StockTest\status-local.cmd`；若网页或刷新进程未运行，再双击 `StockTest\start-local.cmd`，不要另开重复服务器。

   ```powershell
   StockTest\status-local.cmd
   ```

## 当前不可回退的产品口径

- 网页优先，小程序延期到网页验收和稳定后另立项目。
- 主题 Top 20 暂停，不恢复主题 UI；候选目录和 AI 研究契约保留备用。
- 新闻热度和独立基本面 UI 已删除；基本面只可作为未来后台主题研究输入。
- 主要市场为 SPX、NDX、DJI、RUT、BTC，共 5 张卡片；近一个月迷你 K 线约 21 个交易日。
- 板块 ETF 与权重股为同一模块；板块共 14 个（含 IBIT），SPY 固定首行。
- 产品切换和页面导航已改为页面顶部横向 sticky 导航；搜索框和“查找 ETF”入口已删除。
- 板块表 RSI14、Δ5、Δ20 支持排序，状态使用表头下拉筛选；SPY 状态不可修改。
- 板块模块保留 12 个权重股入口；详情统一使用右侧抽屉查看前十大持仓。
- 行业表支持“强势 15 / 全部 60”、RSI14/Δ5/20 日排序，新增 MA150 趋势列和按 Δ5 映射的状态列；ETF 名称打开 TradingView，每行前十大入口仍打开本地详情。
- 板块和行业表下方各有一个默认收起的“每日 RSI · 近 2 个月”历史面板，可选择 ETF 查看最近 42 个美股交易日 RSI14；历史值从同一份本地日线快照逐日回算。
- 两个榜单的 SPY 固定行采用整行 sticky，并动态遮挡固定行下方被压住的半行内容，滚动时不再漏字或出现空隙。
- 固定行定位已改为读取实际表头高度（`--table-header-height`）；遮挡层不再铺设空白区域，滚动后后续行连续显示。
- 两个每日 RSI 面板已合并到独立“每日 RSI 对比”区块，桌面端两列等宽、行高和日期轴一致；≤780px 自动单列。
- 市场宽度直接使用 Stockbee 原始列折线图；20 日表默认折叠，展开后使用卡片顶部横向滚动条，日期列固定。
- 浏览器只读取本地 JSON，不在页面中直连 Yahoo、Binance 或 Stockbee。
- 指数卡片默认预览：SPX/NDX/DJI/RUT 为 Yahoo 原生 5M 折线面积图（最多 79 点，含收盘时刻记录），BTC 为 2H K 线（最多 12 根，24H）；悬停/键盘聚焦仍打开最多 640px 的近一个月日线 K 线气泡，叠加 EMA9/EMA21 并显示价格。
- 指数卡片数据已接入本地真实日内快照：美股直接读取 Yahoo 原生 5M，不再做本地 5→10M 聚合；BTC 从 Binance 公共 K 线读取 2H；当前页面不直连外部 API，日内数据随本地每小时刷新更新，BTC 当日未收盘根保留 `incomplete` 状态。
- K 线不再绘制容易误解的末端小圆点；若最后一根日内柱为 `incomplete`，卡片显示“未收盘”提示且该柱照常绘制。
- 行情刷新已加入 Yahoo 双域名/短重试、Binance 公共备用域名，以及局部失败时沿用上一次有效标的的保护；Yahoo 当前日临时日线柱保留为 `pendingBar`，不会让单只 ETF 从页面消失。
- 当前真实快照为 `76/76`，COPX 已恢复为 Yahoo Chart 数据（499 根已确认日线，最新确认日 `2026-08-28`），行业 RSI 历史表可正常展示其最近 42 个交易日。
- ETF 前十大持仓已接入公开来源：普通股票 ETF 使用 StockAnalysis（页面列出的源为 Finnhub），IBIT 使用 iShares 官方 CSV，USO 使用 USCF 官方 holdings API；当前真实刷新 `71/71` 成功。IBIT 显示 BTC/现金，USO 显示期货/国债/掉期，不回退到 SPY；24 小时缓存避免每小时重复抓取。
- 持仓解析会保留无代码资产行并将交易所前缀规范化（例如 `!asx/RIO` → `ASX:RIO`）；ARKF/ARKW/BLOK/DTCR 的排名缺口与 SLX 的 RIO 重复告警已通过来源核对和重新刷新消除。
- 每个 ETF 快照新增 `ma150` 与 `trend150`，趋势只比较已确认收盘价；数据不足显示“数据不足”。
- 板块表已移除收盘价并改为 MA150 趋势列；行业表继续使用相同的趋势口径。
- TradingView 交易所映射已修正：DTCR/QTUM/IBIT/QQQ/SOXX 为 `NASDAQ:`，ARKK 为 `CBOE:`，不再统一拼接 `AMEX:`。
- 新增 `data/stockbee_momentum.json` 与 Stockbee 50 纯代码名单区块；已切换到用户指定的公开工作表 `gid=1499398020`，最新日期为 2026-08-25、完整 50 个代码，页面按来源日期显示新鲜度。
- 指数卡片整卡悬停已可打开近一个月日线 K 线气泡，含价格、K 线和 EMA9/EMA21；行业前十大按钮已验证可打开真实 10 行持仓。
- 若用户误以 `file:///.../index.html` 直接打开，`app.js` 会探测本地服务并自动切换到 `http://127.0.0.1:8765/index.html`；本地 HTTP 页面已验证 Stockbee 50 行和指数气泡真实 K 线均可加载。气泡覆盖层级已提升至 101，避免被表格或固定行遮挡。
- Stockbee 50 的代码链接不再猜测 `AMEX:`；现在跳转 `tw.tradingview.com/symbols/{ticker}/`，由 TradingView 自动解析交易所，已验证 DAIC→NASDAQ:DAIC、RFAI→NASDAQ:RFAI。
- 指数气泡已改为 `body` 下的页面级浮层（z-index 101），优先显示最新盘中 5M/2H 价格并标注“盘中价格每小时刷新”；行情快照每小时重绘后会恢复当前悬停卡片，避免被板块表格与分段控件遮挡或消失。
- 气泡锚点二次修正：`positionIndexHoverBubble()` 同时读取卡片保存的浮层引用，脚本版本为 `app.js?v=20260901-hourly-bubble-anchor`；后续浏览器回归需确认气泡始终贴近当前指数/BTC 卡片。
- 气泡近一个月日线包含当前交易日 `pendingBar`，右侧最后一根显示未收盘柱；盘中价格每小时更新，临时柱不参与 RSI、收益或 MA150。当前脚本版本为 `app.js?v=20260901-pending-daily-bubble`。
- 2026-09-01 项目审计与两项优先任务已完成：主项目 89 项测试、Task 4 核心复审 37 项和特性分支运行时 2 项通过；76/76 行情、Stockbee 半年 128 行、Stockbee 50 50 行可用，前十大持仓已达 71/71。刷新器已改为原子写入，持仓完整性校验已纳入 validator，Windows 服务状态误报已修复；下一步默认观察一轮小时刷新日志；完整证据见 [PROJECT_PROGRESS.md](./PROJECT_PROGRESS.md) 最后一节。

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
- 美股交易日历：`us-equity`，当前共同确认收盘日 `2026-08-27`；Yahoo 返回的 `2026-08-28` 日线仍作为未收盘 `pendingBars` 保留。
- BTC 交易日历：`crypto-24x7`，真实最新日线 `2026-08-30`。
- 跨资产共同基准：`comparisonDate = 2026-08-28`。
- 页面显示：以快照中的共同确认收盘日为准（当前 `2026-08-27`），并单独显示 BTC 最新日；美股日内 5M 会话可为 `2026-08-28`，不覆盖收盘指标日期。
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
- [data_pipeline/fetch_holdings.py](./data_pipeline/fetch_holdings.py)：ETF 前十大持仓公开页抓取、解析和来源元数据。
- [data_pipeline/refresh_local_data.py](./data_pipeline/refresh_local_data.py)：一次或每小时刷新行情与 Stockbee。
- [data_pipeline/local_runtime.py](./data_pipeline/local_runtime.py)：后台进程、PID、日志和重复启动保护。
- [start-local.cmd](./start-local.cmd)、[status-local.cmd](./status-local.cmd)、[stop-local.cmd](./stop-local.cmd)：Windows 一键运行入口。
- [data_pipeline/validate_market_snapshot.py](./data_pipeline/validate_market_snapshot.py)：行情质量检查。
- [data_pipeline/stockbee.py](./data_pipeline/stockbee.py)：Stockbee CSV 解析与字段校验。
- [data_pipeline/test_*.py](./data_pipeline/)：数据、UI 和契约测试。

## 下一步（当前执行顺序）

真实日内接入、每日 RSI 历史面板、双表并列对比、SPY 固定行滚动修正、COPX 真实数据补齐、ETF 持仓、交易所映射和 Stockbee 名单区块均已完成：5 张卡片、5M/2H 标签、真实价格、640px 气泡、42 日 RSI 历史、滚动遮挡层、76/76 快照、49 项测试和浏览器交互检查通过。Stockbee 50 已进一步切换并验证用户指定工作表 `gid=1499398020`，当前快照 50 行、最新日期 2026-08-25；后续刷新沿用该导出地址即可。

在用户确认前，不要恢复主题 AI 排名、不接入小程序，也不要重做已有页面交互。GitHub 公开发布与 Pages 部署已按用户后续明确授权完成，当前以本文件最后的“2026-09-04 休息后启动入口”为准。

## 2026-08-31 本地执行交接

- GitHub 远程仓库、推送、PR、Pages 发布与线上授权操作已按用户要求暂停；不要主动恢复。
- 当前本地特性分支：`.worktrees/market-analysis-evidence/StockTest`，分支名 `feature/market-analysis-evidence`。
- Task 1–3 已完成并通过独立审查：来源/证据契约、五因子评分与日期对齐、证据化结论与置信度。
- Task 4 已独立复审完成：刷新成功生成/复用 `market_analysis.json`，市场/Stockbee/分析失败均保留上一份有效快照，分析写入失败不会替换旧分析；Windows 进程探测超时也已安全降级。
- Task 5：首页市场状态卡与证据抽屉尚未开始；Task 6：端到端 QA 和最终本地交付尚未开始。
- 最新本地实现分支提交：`6d315f6`；不要将其视为已合并到 `main` 或已上线。
- 详细证据、提交、测试数量和暂停项见 [PROJECT_PROGRESS.md](./PROJECT_PROGRESS.md) 的 `2026-08-31 本地执行状态（GitHub 暂停后）`。
- 最新 UI 与数据变更和验证证据见 [PROJECT_PROGRESS.md](./PROJECT_PROGRESS.md) 最后一节 `2026-09-01 Stockbee 50 指定工作表接入`；不要回退到此前的 1 分钟/全面积图方案。

## 防重复规则

- 先读本文件和 `PROJECT_PROGRESS.md`，再动手。
- 同类工作日志只更新 `PROJECT_PROGRESS.md`；本文件只更新交接状态和启动入口。
- 新增代码先写失败测试并确认失败，再写最小实现。
- 不修改、移动、删除 `sources/`。
- 不把示例值、未收盘值或候选主题说成最终实时结论。
- 每次完成声明必须附实际测试或浏览器证据。

## 可直接粘贴到新窗口的启动语句

```text
请只在本机继续 StockTest，不进行任何 GitHub 推送、PR、Pages 发布或授权操作。先阅读 StockTest/PROJECT_HANDOFF.md、PROJECT_CONTEXT.md、PROJECT_PROGRESS.md 最后一节和 PROJECT_ROADMAP.md；当前网页指数卡片口径是美股真实 Yahoo 原生 5M、BTC Binance 真实 2H，640px 近月价格气泡，不要重复制作或回退。先运行现有 data_pipeline 测试和 app.js 语法检查，再做刷新异常监控与持仓来源回归；Task 4 已完成独立复审，不要重复复审。不要重复制作已有页面、数据契约或进度文档。主题 AI、小程序、新闻热度、基本面 UI 与线上部署继续暂停。
```

## 2026-09-04 休息后启动入口

当前线上发布已经完成；下一次不要从 UI 或数据管线重做，直接从域名配置与线上监控继续：

1. 先读取本文件最后两节、`PROJECT_PROGRESS.md` 最后一节和 `DATA_RELIABILITY_AUDIT.md`。
2. 快速核验 `https://bravo-189.github.io/StockTest/`、Pages 状态和最近一次 workflow；只有出现失败或数据缺口时才修复。
3. TightPlayer 完整域名已确认并写入 Pages：`www.tightplayer.com`。当前只等待 DNS 生效。
4. 引导用户在 DNS 服务商添加 `www` → `bravo-189.github.io` 的 CNAME；DNS 生效后验证 HTTPS、重定向和线上资源路径，再开启 HTTPS 强制。
5. 检查 Actions 的 Node.js 20 弃用提示，并观察每小时刷新、盘后日更和 `data-state` 快照是否持续成功。
6. 继续遵守：不上传 `.codex/skills/`，不写入或提交任何 API key/密码，不恢复已暂停的主题 AI/新闻功能，除非用户重新明确要求。

本次已完成的 GitHub 公开发布、Pages 上线、数据端点验证和敏感信息扫描均记录在 `PROJECT_PROGRESS.md`，无需重复执行。
