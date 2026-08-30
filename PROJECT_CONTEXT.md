# StockTest 项目启动上下文

> 这是 StockTest 的持续工作上下文。更换对话窗口时先阅读 [PROJECT_HANDOFF.md](./PROJECT_HANDOFF.md)，再阅读本文件和 [PROJECT_PROGRESS.md](./PROJECT_PROGRESS.md) 的最近记录，最后执行“启动检查清单”。

## 1. 项目一句话目标

StockTest 是面向个人美股研究者的盘后市场雷达网页：用户打开后，应在约 5 秒内看懂市场状态、四大指数、板块/行业动能、主题候选和市场宽度。

当前优先级是网页原型和免费数据接入；小程序延期到网页验收后再单独设计。

## 2. 已确认的产品口径

### 主题生成

60 个行业 ETF 必须先经过后台 AI 研究流程，再整理成 20 个主题名单。AI 研究需要综合：

- 多周期价格动能与 RSI；
- 市场宽度和 ETF 内部扩散；
- 最新市场热点、概念和催化剂；
- 领先成分股的基本面和公司叙事；
- 未来 1–2 年上涨可能性与 swing trade 机会；
- 风险、失效条件、时间周期和来源网址。

基本面不单独做成网页模块，但保留为后台主题研究输入。新闻数量不作为评分因子，也不展示“新闻热度”。

### 页面结构

- “板块 ETF”和“权重股”属于同一个页面研究模块；
- 侧边栏使用“板块与权重股”，不再提供独立的“权重股”导航；
- 板块区域内展示 14 个板块 ETF（含 IBIT 加密货币），SPY 固定首行，下面嵌入 12 个 ETF 权重股入口；
- 主要市场区域展示 SPX、NDX、DJI、RUT 四大指数以及 BTC 卡片，共 5 个主要市场基准；
- 主要市场卡片迷你 K 线使用近 1 个月约 21 个交易日；ETF 详情抽屉继续展示 60 日走势；
- RSI14、Δ5、Δ20 表头支持升降序排序，状态列使用紧凑表头筛选菜单与只读标签，SPY 状态锁定；
- 行业区域展示强势 15 和全部 60；
- 行业表删除“动能”数据列，RSI14、Δ5、20日支持升降序排序；每行提供前十大权重股入口；
- 板块与行业表均使用独立内部滚动容器，表头和首行 SPY sticky 固定，便于逐行对照；
- 20 个主题模块当前暂停，不出现在主动导航和页面中；其目录与 AI 契约保留备用；
- 市场宽度区域直接使用 Stockbee 原始列绘制折线图，不放左侧解释卡；
- 折线指标包括 4% 上涨、4% 下跌、5 日比率、10 日比率、T2108、S&P 500；
- 原始 Stockbee 20 日数据默认折叠，用户主动展开查看；展开后使用独立横向滚动条，日期列固定，键盘方向键支持移动。

### 数据与范围

- 页面默认示例日期：`2026-08-27 收盘`；
- 页面使用本地 JSON，不在浏览器中直连行情 API；
- `sources/` 目录只读，绝不编辑、移动、重命名或删除；
- 任何真实数据接入都要保存来源、抓取时间、数据日期和缺失状态；
- 当前网页仍是研究原型，不构成投资建议。

## 3. 当前完成状态

### 已完成

- 高保真网页原型、深浅主题和苹果式主题按钮；
- 固定侧边栏和响应式桌面/平板/移动布局；
- 四大指数 + BTC、14 个板块 ETF、60 个行业、前十大持仓、市场宽度；主题 Top 20 资产保留但主动 UI 暂停；
- ETF 详情抽屉，支持打开、关闭和 Escape 键退出；
- 板块周期排序：当日、5 日、20 日；
- 板块 RSI14、Δ5、Δ20 独立排序，SPY 固定首行，状态筛选菜单可操作；
- 12 个板块 ETF 权重股入口统一放在板块模块内；
- 行业“强势 15 / 全部 60”真正切换可见行数，排序状态保持在当前页面；
- 行业切换：强势 15、全部 60；
- Stockbee 公开 Google Sheet CSV 导入和 20 日本地快照；
- 20 个主题候选目录已覆盖 60 个唯一 ETF，并作为后续恢复时的输入资产保存；
- 后台 AI 研究请求/结果校验契约；
- 新闻热度和独立基本面 UI 已移除；
- 主题模块已从主动网页暂停，其他核心区块保持可用；
- 45 项 Python 测试、JavaScript 语法、HTTP 浏览器交互和 `file://` 回退测试均通过。
- 本地行情快照已扩展：4 个指数、14 个板块 ETF（含 IBIT）、60 个行业 ETF 和 BTC，共 76 个唯一标的；网页从 `data/market_snapshot.json` hydration，不在浏览器直连供应商。
- Yahoo 尚未收盘的最新日线保存在 `pendingBars`，网页显示“未收盘日线”提示，但收盘价、RSI 和多周期收益只使用完整日线。
- `data_pipeline/refresh_local_data.py` 支持一次刷新或每小时循环刷新行情与 Stockbee；网页每小时重新读取本地快照。

### 当前仍是占位或样例

- 主题模块当前暂停；目录是“候选输入集合”，不是最终 AI 排名；
- 主题卡片的动能数值仍是原型示例数据；
- 60 个行业 ETF 已接入真实行情快照；下一步需要做跨源核对和异常监控；
- Yahoo Chart 是免密钥的非官方接口，未来仍需备用适配器；已评估 Alpaca、Alpha Vantage 与 CoinGecko，当前仅 CoinGecko 适合作为 BTC 的低频免密钥备用，美股备用源尚未接入；Binance K 线是公开只读接口；
- AI agent 尚未基于最新网络资料生成可引用的最终 20 主题排名；
- SEC 基本面试点文件保留作后台输入备用，未接入网页展示。

## 4. 关键文件地图

```text
StockTest/
├─ index.html                         网页结构和页面区块
├─ styles.css                         主题、布局、响应式和组件样式
├─ app.js                             交互、示例数据、JSON hydration、Canvas 折线图
├─ start-local.cmd                    一键启动网页与每小时刷新进程
├─ status-local.cmd                   查看项目后台进程状态
├─ stop-local.cmd                     安全停止本项目记录的后台进程
├─ PROJECT_CONTEXT.md                 本文件：项目持续上下文和启动手册
├─ PROJECT_HANDOFF.md                 对话窗口交接唯一入口
├─ README.md                          项目说明和运行方式
├─ design-qa.md                       设计 QA 与验收记录
├─ DESIGN.md                          项目内设计规范（基于 awesome-design-md / Linear 参考）
├─ .codex/skills/awesome-design-md/   项目内设计技能（源自 awesome-design-md）
├─ data/
│  ├─ market_snapshot.json             指数、板块 ETF、行业 ETF、BTC 本地行情快照
│  ├─ stockbee.json                   Stockbee 20 日本地快照
│  ├─ refresh_status.json              最近一次本地刷新结果、来源状态和成功时间
│  ├─ theme_catalog.json              60 ETF → 20 主题候选输入目录
│  ├─ fundamentals.json               SEC 基本面试点（后台备用，不展示）
│  └─ market_snapshot_quality.json    最近一次行情快照质量报告
└─ data_pipeline/
   ├─ market_data.py                   Yahoo/Binance 数据规范化与质量校验
   ├─ fetch_market_data.py             首批市场行情抓取和 JSON 快照生成
   ├─ refresh_local_data.py             行情与 Stockbee 半实时本地刷新器
   ├─ local_runtime.py                  本地服务生命周期、PID、日志和重复启动保护
   ├─ validate_market_snapshot.py       行情快照质量分析与报告生成
   ├─ stockbee.py                     Stockbee CSV 解析与校验
   ├─ fetch_stockbee.py               Stockbee 抓取和 JSON 快照
   ├─ theme_catalog.py                20/60 覆盖、唯一性和输入契约校验
   ├─ theme_agent.py                  AI 研究请求与结果校验
   ├─ sec_fundamentals.py             SEC Company Facts 规范化
   ├─ fetch_sec_fundamentals.py       SEC 基本面抓取
   ├─ validate_fundamentals.py        基本面数据质量检查
   └─ test_*.py                       数据和页面契约测试
```

## 5. 数据契约

### 市场行情快照

`data/market_snapshot.json` 的每个 `instruments[*]` 都保留真实供应商日期，并写入交易日历：

```text
instrument: symbol, provider, calendar, bars[], latest, latestDate, pendingBar?
metadata: latestDate, comparisonDate, calendarLatestDates, calendars,
          requiredCount, loadedCount, pendingCount, missing
```

- `us-equity` 使用美股交易日历；`crypto-24x7` 使用 UTC 7×24 日历。
- `comparisonDate` 为各日历已确认最新日期的共同基准，当前为 `2026-08-27`。
- BTC 保留原生最新日期 `2026-08-29`，不补造美股周末 K 线；页面同时显示美股收盘日和 BTC 最新日。
- Yahoo 未收盘记录继续进入 `pendingBars`，不参与收盘价、RSI 或多周期收益计算。

### Stockbee 快照

`data/stockbee.json` 的核心结构：

```text
metadata: rowCount, latestDate, sourceStatus, fetchedAt
source: name, pageUrl, url, format
schema[]: key, source, label, group, type
rows[]: date, up, down, ratio5, ratio10,
  up25Quarter, down25Quarter, up25Month, down25Month,
  up50Month, down50Month, up13_34d, down13_34d,
  wordenUniverse, t2108, sp500
```

网页按 Stockbee 原始结构展示 15 个指标：Primary 6 列、Secondary 6 列和 Reference 3 列；表格默认折叠并支持横向滚动，折线图按同一字段切换，时间轴从旧到新绘制。

当前来源页面：

`https://stockbee.blogspot.com/p/mm.html`

浏览器只读取本地 `data/stockbee.json`，不直接访问 Stockbee。

### 本地刷新状态

`data/refresh_status.json` 不替代数据快照，只记录最近一次刷新尝试：

```text
schemaVersion, status, attemptedAt, lastCompletedAt, lastFullSuccessAt
sources.market: status, latestDate, loadedCount, requiredCount, missingCount
sources.stockbee: status, latestDate, rowCount
errors[]: source, message
```

- `ok`：本次行情与 Stockbee 均完成且无缺失；
- `partial`：本次完成但市场标的存在缺失；
- `failed`：本次未完成，浏览器继续使用上一份快照；
- 页面将最后完成时间超过 90 分钟的 `ok` 状态显示为“数据过期”。

### 主题候选目录

`data/theme_catalog.json` 的核心结构：

```text
metadata: version, asOf, sourceStatus, method, agentPrompt, sourceUrls
industryUniverse[60]: [ticker, name, group]
themes[20]:
  id, name, memberEtfs[], analysisStatus, researchInputs[]
```

每个主题的 `researchInputs` 必须包含：

```text
momentum, breadth, catalysts, fundamentals, narrative
```

### AI 研究请求

`data_pipeline/theme_agent.py` 提供：

- `build_agent_request(catalog, etf_metrics, as_of)`：把 60 个 ETF 和指标包装为 AI 输入；
- `validate_agent_output(output, expected_count=20)`：拒绝缺少排名、来源、领先股票或催化剂的结果。

AI 结果进入网页前必须满足：

- 20 条主题；
- 排名连续且唯一；
- 分数在 0–100；
- 每个主题至少有领先股票、催化剂和来源 URL。

## 6. 下次启动清单

### 启动时先做

1. 阅读本文件和 [README.md](./README.md)。
2. 确认 `sources/` 仍保持只读。
3. 用工作区依赖工具获取当前 Python、Node.js 和 Playwright 路径。
4. 运行 `status-local.cmd` 查看后台网页和刷新进程；未运行时双击 `start-local.cmd`，不要另开重复的 `http.server`。
5. 运行数据管线测试和 JavaScript 语法检查。
6. 打开 `StockTest/index.html`，检查总览、板块与权重股、行业和 Stockbee 图表；主题模块当前跳过。

### 推荐验证命令

在项目根目录执行；Python/Node 路径以当前工作区依赖工具返回的路径为准：

```powershell
<PYTHON> -m unittest discover -s StockTest/data_pipeline -p 'test_*.py' -v
<NODE> --check StockTest/app.js
<PYTHON> StockTest/data_pipeline/theme_catalog.py StockTest/data/theme_catalog.json
StockTest\status-local.cmd
```

浏览器检查至少覆盖：

- SPY 固定首行、RSI14/Δ5/Δ20 排序和状态表头筛选；
- 12 个板块 ETF 权重股入口；
- 全部 60 个行业 ETF；
- “板块与权重股”同一区块；
- 6 个 Stockbee 指标切换；
- ETF 抽屉打开/关闭；
- 390px 宽度无横向溢出；
- 控制台错误为 0。

## 7. 下一阶段执行顺序

### 第一步：免费行情源验证（指数、板块和行业已完成）

已验证并接入 4 个指数、14 个板块 ETF（含 IBIT）、60 个行业 ETF 和 BTC；后续跨源校验与备用源仍沿用同一管线，不直接修改页面组件。每次输出都检查：

- 日期统一性；
- 缺失率；
- 重复记录；
- 多周期收益；
- RSI14；
- 异常值和停牌情况；
- 来源与抓取时间。

数据质量通过后，再进入下一步。

### 第二步：生成 AI 主题排名

把行情、Stockbee、ETF 持仓、成分股基本面和最新网络资料送入研究 agent，生成 20 个主题排名。每个主题保存：

- 总分和排名；
- 领先 ETF；
- 领先股票；
- 技术动能证据；
- 催化剂和日期；
- 基本面证据；
- 叙事；
- 风险和失效条件；
- 来源 URL。

### 第三步：接入网页与最终 QA

把候选主题替换为真实 AI 排名，保持页面只展示研究结论，不增加独立基本面页面。然后重新完成设计 QA、数据 QA、响应式 QA 和交互回归。

### 第四步：发布与小程序

网页验收通过后，再讨论 GitHub Pages 自动发布和“小程序项目”。小程序复用 `DashboardData`，但移动交互需要重新设计。

## 8. 必须遵守的工作原则

- 不把人工候选目录说成 AI 最终排名；
- 不把旧示例数据说成实时行情；
- 不在浏览器中直连网络行情 API；
- 不把新闻数量直接当成催化剂评分；
- 不删除基本面管线，除非用户明确要求彻底删除；
- 不修改 `sources/`；
- 新功能先写失败测试，再写最小实现；
- 完成前必须运行实际测试和浏览器验证；
- 每个需要最新事实的投资判断都要记录来源和日期；
- 发现数据不准确时，先暂停下一阶段并汇报，不用猜测填补。

## 9. 推荐使用的 skill / plugin 顺序

根据任务类型调用，不要无目的安装新插件：

1. `superpowers:using-superpowers`：每次新会话的技能路由；
2. `superpowers:brainstorming`：新增功能或改变页面逻辑前；
3. `superpowers:writing-plans` / `superpowers:executing-plans`：多步骤实现；
4. `superpowers:test-driven-development`：先写失败测试；
5. `public-equity-investing`：主题、成分股、催化剂和投资研究框架；
6. `data-analytics:analyze-data-quality`：数据源、缺失、重复、过期和异常检查；
7. `data-analytics:validate-data`：指标计算、结论和来源复核；
8. `build-web-apps:frontend-testing-debugging`：本地服务器、浏览器交互、响应式和控制台 QA；
9. `superpowers:verification-before-completion`：最终交付前的证据检查。

当前没有必要安装新的 GitHub 依赖。只有当免费数据源验证明确需要额外能力时，才在 `StockTest/` 范围内增加依赖或脚本。
