# StockTest 网页 UI 原型

新会话恢复项目时，请先阅读对话窗口交接入口 [PROJECT_HANDOFF.md](./PROJECT_HANDOFF.md)，再阅读 [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) 和唯一滚动工作日志 [PROJECT_PROGRESS.md](./PROJECT_PROGRESS.md)。交接文档只做启动索引，不复制完整进度内容。

这是 StockTest 第一阶段的静态网页原型，采用已选择的「盘后研究简报」方向，并完成了一轮审美重构：编辑式市场摘要、克制的蓝色层级、蜡烛走势预览和轻量状态色。浏览器只读取本地 JSON 快照，不直接访问行情网络；`sources/` 目录保持只读。

网页设计规范记录在 [DESIGN.md](./DESIGN.md)，项目内 `awesome-design-md` 技能目录保存了本次采用的设计参考与工作流。

## 预览

直接打开 [index.html](./index.html) 即可预览。若使用本地静态服务器，将 `StockTest/` 作为站点根目录即可。

### Windows 一键本地运行

双击 `start-local.cmd` 会在后台启动网页服务和每 60 分钟刷新一次的数据进程；重复双击不会创建重复进程。运行状态和日志只写入项目内的 `.runtime/`：

```text
start-local.cmd    启动或确认已运行
status-local.cmd   查看网页与刷新进程状态
stop-local.cmd     只停止由本项目记录并验证过的两个进程
```

启动后访问 `http://127.0.0.1:8765/index.html`。关闭命令窗口不会停止后台进程；需要停止时双击 `stop-local.cmd`。该方式不会注册 Windows 计划任务，电脑重启后需要重新运行 `start-local.cmd`。

## 已实现的原型交互

- 固定导航定位：总览、板块与权重股、行业动能、市场宽度；主题模块暂时隐藏，目录保留备用。
- 深浅主题切换，选择保存到浏览器本地；`Ctrl/⌘ + K` 聚焦搜索。
- 四大指数 + BTC 共 5 个主要市场卡片，展示近 1 个月约 21 个交易日的迷你 K 线；详情抽屉保留 60 日走势。
- 14 个板块 ETF（含 IBIT 加密货币）支持多周期排序。
- 板块表将 SPY 固定在首行，RSI14、Δ5、Δ20 支持升降序排序，状态通过紧凑表头菜单筛选，行内标签只读。
- 12 个板块 ETF 权重股入口集中在同一模块；点击 ETF 打开详情抽屉，查看走势和前十大权重股；支持 Escape、关闭按钮和遮罩关闭。
- 行业表支持强势 15 / 全部 60 真正切换、RSI14/Δ5/20日排序，并提供每行“前十大”权重股入口。
- 板块与行业表均为独立内部滚动区域，表头和首行 SPY 固定，方便逐行对照其他 ETF。
- 市场宽度 20 日原始数据默认折叠，可展开查看；展开后表格采用数据卡片顶部的独立横向滚动条，日期列固定，键盘方向键也可移动视窗。
- 搜索框可以筛选板块与行业；Stockbee 区域支持按原始数据列切换折线图。

当本地快照不可用或直接以 `file://` 打开时，页面会使用按未来 `DashboardData` 结构生成的确定性回退数据；静态服务器下则优先加载本地行情快照。主题目录单独保存在 `data/theme_catalog.json`，由后台 AI 研究契约接收 60 个 ETF 并输出 20 个主题；当前主题模块暂停，不把候选集误标为最终投资排名。板块与权重股已合并为同一页面模块。

## 免费数据管线

`data_pipeline/fetch_market_data.py` 会在本地生成 4 个美股指数、14 个板块 ETF（含 IBIT）、60 个行业 ETF 和 BTC 的 OHLCV 快照。Yahoo Chart 为免密钥的非官方接口，Binance 为公开只读 K 线接口；每条记录均保存 provider、来源 URL、抓取时间、最新日期和缺失状态。Yahoo 尚未收盘的当前日线会保留在 `pendingBars`，但不会混入收盘价、RSI 或多周期收益计算。网页只加载生成后的 `data/market_snapshot.json`，不会把行情请求放进浏览器。

快照区分 `us-equity` 和 `crypto-24x7` 两种交易日历：页面以美股最新确认收盘日作为跨资产 `comparisonDate`，BTC 仍显示自己的原生最新日，不补造美股周末 K 线。

快照质量可用 `data_pipeline/validate_market_snapshot.py` 重复检查，并将结果保存到 `data/market_snapshot_quality.json`。检查覆盖标的覆盖率、日期唯一性与顺序、OHLCV 合法性、最新日期指针、未收盘记录数量和供应商交易日历差异。

```text
python StockTest/data_pipeline/fetch_market_data.py --output StockTest/data/market_snapshot.json
```

需要同时刷新行情和 Stockbee 时，使用本地半实时刷新器；默认每 60 分钟运行一次，也可以用 `--once` 做单次刷新：

```text
python StockTest/data_pipeline/refresh_local_data.py --output-dir StockTest/data --interval-minutes 60
python StockTest/data_pipeline/refresh_local_data.py --output-dir StockTest/data --once
```

刷新器会在每次尝试后写入 `data/refresh_status.json`。抓取失败时保留上一份行情与 Stockbee 快照，并记录失败来源；完整刷新、局部缺失和失败分别标记为 `ok`、`partial`、`failed`。网页每小时重新读取本地快照与刷新状态，并以 90 分钟为过期阈值显示“数据新鲜”“数据过期”“局部缺失”或“刷新失败 · 保留上次数据”。

当前快照已通过结构、日期顺序、重复记录、OHLC 边界、成交量非负、行业覆盖和最少 21 根日线检查。美股最近交易日与 BTC 7×24 日历可能不同，页面会保留日期提示。

`data_pipeline/fetch_stockbee.py` 使用 Stockbee 页面公开的 Google Sheet CSV 导出，保留来源 URL、抓取时间、最新日期和规范化后的 20 日完整 Market Monitor 数据。完整字段按 Primary / Secondary / Reference 分组写入 `schema`，网页表格与折线图共用同一批字段：

```text
up, down, ratio5, ratio10,
up25Quarter, down25Quarter, up25Month, down25Month,
up50Month, down50Month, up13_34d, down13_34d,
wordenUniverse, t2108, sp500
```

```text
python StockTest/data_pipeline/fetch_stockbee.py --output StockTest/data/stockbee.json --limit 20
```

网页不会在浏览器中抓取该地址，避免把外部网络不稳定性带入 UI。后续 GitHub Actions 可以运行同一脚本，再把 JSON 作为静态数据发布。

通过静态服务器或 GitHub Pages 打开时，页面会读取 `data/stockbee.json`；直接双击 `index.html` 时浏览器会使用示例回退，避免 `file://` 的 CORS 控制台错误。

### SEC 基本面试点

`data_pipeline/fetch_sec_fundamentals.py` 使用 SEC EDGAR Company Facts 的免费接口抓取 MSFT、NVDA、AAPL、AMZN、META 五家公司。输出保留每个指标的报告期、表单、提交日期和 accession；缺失字段不会被填成 0，必要时只使用同一报告期的明确派生公式。质量检查命令：

```text
python StockTest/data_pipeline/validate_fundamentals.py StockTest/data/fundamentals.json
```

当前试点已通过结构、来源、期间、重复代码、缺失字段和基本数值范围检查。它只准备基本面事实输入，尚未让 AI agent 自动改变主题排名。

## 第二阶段待办

小程序页面暂不启动。网页原型验收后，再复用 `DashboardData` 接口单独设计移动端体验。
