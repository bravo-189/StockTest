# StockTest 项目进度与工作日志

> 这是 StockTest 唯一的滚动进度文档。后续工作直接更新本文件，不再为同一阶段重复创建“进度报告”“明日计划”或相近名称的文档。

## 文档用途

- 新会话启动时先阅读 [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md)，再阅读本文件最近一条记录。
- 本文件记录已完成事项、验证证据、明确暂停项和下一步入口。
- 需求口径以用户最新确认内容为准；旧截图、旧计划和旧示例不能覆盖最新确认。
- `sources/` 始终只读，任何数据或页面改动都限定在 `StockTest/` 内。

## 今日记录：2026-08-30

### 本次目标

重构“市场宽度”页面区域，使其更像高密度但可读的研究终端，并解决 Stockbee 20 日原始数据必须滚动到表格底部才能横向查看的问题。

### 已完成

1. **市场宽度图表卡片重构**
   - 将图表标题、说明、当前指标和指标切换器分层排列。
   - 增加“最新观察”读数和最新日期，读数随指标切换同步更新。
   - 保留 Stockbee 原始列切换，不新增新闻热度或基本面展示。
   - 保留浅色/深色主题、克制边框和单一蓝色强调，避免大面积红绿卡片。

2. **Stockbee 原始数据查看体验重构**
   - 20 日原始表默认折叠，展开后在数据卡片顶部提供独立横向滚动条。
   - 日期列保持 sticky 固定，表格纵向区域独立滚动。
   - 横向滚动条与表格视窗双向同步。
   - 支持鼠标拖动，以及 `←`、`→`、`Home`、`End` 键盘操作。
   - 当前表格保持完整结构：20 行、日期 + 15 个指标，共 16 个数据单元格。

3. **响应式细节调整**
   - 小屏幕下“最新观察”改为横向信息行，避免标题和读数挤压。
   - 不改变既有 1440px、1024px、768px 和 390px 的页面结构。

4. **设计技能记录**
   - 已安装并使用 GitHub `leonxlnx/taste-skill` 的审美校准原则；该技能不强行覆盖研究终端规范，仅用于间距、密度、颜色层级和动效克制。
   - Product Design 方向仍为已确认的“盘后研究简报”。

### 后续执行：P0 免费行情源质量核对

本次已开始执行明日启动清单中的 P0，不改动页面组件。

- 新增 `data_pipeline/validate_market_snapshot.py`，把快照质量检查固化为可重复运行的命令。
- 新增 `data_pipeline/test_validate_market_snapshot.py`，先验证覆盖率、供应商日期分组、重复日期和 OHLC 边界异常，再实现校验逻辑。
- 新增 `data/market_snapshot_quality.json`，保存本次对本地行情快照的质量报告。
- 现有行情快照结果：76/76 标的，覆盖率 100%；4,815 根完整 K 线；无缺失标的、重复日期、非法 OHLC 边界、负成交量或最新日期指针错误。
- 当前唯一发现为低风险交易日历差异：Binance BTC 日期范围为 `2026-06-01 → 2026-08-29`，Yahoo 美股日期范围为 `2026-05-29 → 2026-08-27`。这属于供应商日历差异，不应被当作数据损坏；网页需要继续保留日期提示。
- `pendingCount=75` 与快照中的 Yahoo 未收盘候选日线一致；这些记录不参与收盘价、RSI 和多周期收益计算。
- Stockbee 快照核验：20 行、15 个 schema 字段、每行日期 + 15 指标、20 个唯一日期，日期倒序正确，最新日期 `2026-08-28`，来源状态为 `loaded`。

### 日期口径修正：已完成

- `data/market_snapshot.json` 现已为每个标的写入 `calendar`：美股为 `us-equity`，BTC 为 `crypto-24x7`。
- 快照元数据新增 `comparisonDate`、`calendarLatestDates` 和 `calendars`，当前共同比较日为 `2026-08-27`。
- 页面保留 BTC 原生最新日 `2026-08-29`，美股仍以 SPX 的已确认收盘日 `2026-08-27` 为页面基准，不补造周末美股 K 线。
- 质量报告将日历差异从低风险 finding 调整为 `info` note；当前高/中风险 finding 数量为 `0`。
- 页面日期提示明确区分“美股收盘日”和“BTC 最新日”，跨资产比较使用 `comparisonDate`。

可重复运行：

```powershell
<PYTHON> StockTest/data_pipeline/validate_market_snapshot.py StockTest/data/market_snapshot.json --report StockTest/data/market_snapshot_quality.json
```

### P1 半实时刷新状态与备用源评估：已完成

- `refresh_local_data.py` 现在每次尝试都会生成 `data/refresh_status.json`；失败时不覆盖上一份行情与 Stockbee 快照。
- 状态契约覆盖 `ok`、`partial`、`failed`，并保留最近完成时间、最近完整成功时间、分来源状态和错误摘要。
- 网页新增独立刷新状态徽章，90 分钟内显示“数据新鲜”，超过阈值显示“数据过期”，并支持“局部缺失”和“刷新失败 · 保留上次数据”。
- 状态文件缺失不会阻断行情或 Stockbee 快照加载；异步加载顺序也不会覆盖已判断的过期状态。
- 当前实际快照最后成功刷新为 `2026-08-29T17:03:50Z`，本地实测正确显示“数据过期 · 15 小时”。
- 免费备用源评估：
  - Alpaca Basic 覆盖美国股票与 ETF，但免费实时源仅 IEX、需要账号密钥，且不能直接替代四个现货指数；可作为未来 ETF 级备用，不作为当前全量主备切换。
  - Alpha Vantage 免费层为 25 次请求/日，无法支撑 76 个标的一小时轮询；不接入当前半实时流程。
  - CoinGecko Keyless Public API 适合 BTC 低频、非商业教育用途备用，但有 IP 限流；当前 Binance 公开只读 K 线保持主源。
- 本轮没有安装新依赖或插件，避免在没有明确数据授权、密钥和口径收益时增加维护面。

### P2 本地一键常驻运行：已完成

- 新增 `data_pipeline/local_runtime.py`，统一管理网页服务器和每 60 分钟刷新进程。
- 新增 `start-local.cmd`、`status-local.cmd`、`stop-local.cmd`：支持双击启动、状态查看和精确停止。
- 后台进程、PID 和日志只写入 `StockTest/.runtime/`；关闭命令窗口后仍会运行，但不会注册 Windows 计划任务，电脑重启后需要重新启动。
- 重复运行 `start-local.cmd` 会验证进程命令并复用原 PID，不创建第二个网页服务器或刷新循环。
- 停止操作只对 PID 与项目路径、服务命令均匹配的进程生效，避免陈旧 PID 指向其他程序时误停。
- 首次实际运行发现并修复 Windows 批处理尾部反斜杠吞并参数的问题；新增回归测试覆盖精确项目路径。
- 2026-08-30 首次常驻刷新约 90 秒完成：`status=ok`，行情 `76/76`，Stockbee `20` 行；美股最新确认日 `2026-08-28`，BTC 最新日 `2026-08-30`。
- 重复启动实测保持网页 PID `21972`、刷新 PID `16124` 不变；当前两个进程继续在本地运行。
- 页面实测刷新徽章为“数据新鲜 · 16:44”，控制台错误和警告为 `0`。
- 新快照质量结果：`4,890` 根完整 K 线、覆盖率 `100%`、未收盘候选 `0`、finding `0`。

当前判断：P0、P1、P2 均通过；主题 AI 排名仍保持暂停。下一阶段数据工程入口为“美股 ETF 备用源适配”，但候选源需要账号密钥或存在单一交易所口径限制。

### GitHub 版本基线：已完成

- 已安装并验证 GitHub 官方 CLI `2.98.0`，账号为 `bravo-189`。
- 已将 `StockTest/` 初始化为 `main` 分支并创建私有仓库：`https://github.com/bravo-189/StockTest`。
- 基线提交为 `51586daf504b082c6fef6f831646e3422de53263`，提交说明为 `chore: establish StockTest project baseline`。
- `.gitignore` 排除了 `.runtime/`、`.qa-*/`、Python 缓存、日志、环境密钥文件和每小时更新的本地数据快照；动态数据仍保留在本机，不进入 GitHub 历史。
- 上传前大文件检查无超过 10 MB 的待提交文件，敏感模式扫描无命中。
- 基线前重新运行 50 项 Python 测试与 JavaScript 语法检查，全部通过。
- GitHub CLI/API 已验证远程仓库为 `PRIVATE`、默认分支为 `main`，远程提交 SHA 与本地一致。
- 当前 GitHub 连接器尚未列出这个新建私有仓库；后续若要直接用连接器操作 PR/Issue，需要在 GitHub App 设置中授予该仓库访问权限。现有 GitHub CLI 推送不受影响。

### 本次涉及文件

- `index.html`：市场宽度图表标题、最新读数和原始数据滚动控件。
- `styles.css`：图表层级、最新读数、顶部横向滚动条和移动端规则。
- `app.js`：最新值同步、滚动条初始化、滚动同步、ARIA 状态和键盘操作。
- `data_pipeline/test_ui_flow_contract.py`：市场宽度重构契约测试。
- `data_pipeline/refresh_local_data.py`、`data_pipeline/test_refresh_local_data.py`：刷新状态、失败保留和局部缺失测试。
- `data/refresh_status.json`：最近一次本地刷新结果。
- `data_pipeline/local_runtime.py`、`data_pipeline/test_local_runtime.py`：本地服务生命周期与真实进程回归测试。
- `start-local.cmd`、`status-local.cmd`、`stop-local.cmd`：Windows 一键入口。
- `data_pipeline/validate_market_snapshot.py`、`data_pipeline/test_validate_market_snapshot.py`：行情质量检查和回归测试。
- `data/market_snapshot_quality.json`：行情快照质量报告。
- `README.md`、`PROJECT_CONTEXT.md`、`design-qa.md`：同步新的交互说明和验收记录。

### 验证证据

- Python 数据/UI 测试：`50` 项全部通过（刷新状态 3 项、本地运行生命周期与 Windows 路径 2 项）。
- JavaScript 语法检查：通过。
- 本地服务器：`http://127.0.0.1:8765/index.html` 返回 HTTP `200`。
- 浏览器回归：
  - Stockbee 原始表 `20` 行。
  - 首行数据 `16` 个单元格（日期 + 15 指标）。
  - 原始表宽度 `1532px`，视窗宽度 `933px`，横向可滚动范围 `599px`。
  - 顶部滚动条移动到 `360px` 后，表格视窗同步到 `360px`。
  - 最新观察显示 `0.98`，日期为 `2026-08-28`。
  - 刷新状态显示“数据过期 · 15 小时”，类名为 `is-stale`，并保留最后成功时间。
  - 1440、1024、768、390 四个目标宽度均无页面级横向溢出。
  - “全部 60”显示 60 行；板块排序后 SPY 仍为首行；抽屉显示 10 个持仓；Stockbee 展开后保持 20 行。
  - 控制台 error/warn 数量为 `0`。
- `design-qa.md` 已保持 `final result: passed`。

## 当前产品口径（不可回退）

- 网页优先，小程序延期到网页稳定后另立项目。
- 主题 Top 20 当前暂停，不在主动网页展示；候选目录和 AI 契约保留为后续资产。
- 新闻热度和独立基本面 UI 已移除；基本面数据仅可作为未来后台研究输入。
- 主要市场为 SPX、NDX、DJI、RUT 和 BTC，共 5 张卡片；近一个月约 21 个交易日迷你 K 线。
- 板块 ETF 与权重股属于同一页面模块；板块 ETF 共 14 个（含 IBIT），SPY 必须固定在首行。
- 板块表 RSI14、Δ5、Δ20 支持排序，状态使用表头筛选菜单；SPY 行状态不可被改变。
- 板块模块保留 12 个 ETF 权重股入口；详情统一使用右侧抽屉查看前十大持仓。
- 行业表支持“强势 15 / 全部 60”切换、RSI14/Δ5/20 日排序和每行前十大入口，并删除“动能”数据列。
- 市场宽度直接展示 Stockbee 原始列折线图和可展开原始表，不添加左侧解释卡。
- 浏览器只读取本地 JSON；不把行情 API 或 Stockbee 抓取逻辑放进浏览器。

## 明日启动清单

按以下顺序执行，完成一步再进入下一步：

1. 阅读本文件和 [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md)，确认没有新的用户决策覆盖当前口径。
2. 检查 `StockTest/sources/` 未被修改；不要重新制作已有页面、截图或数据契约。
3. 运行现有验证：

   ```powershell
   <PYTHON> -m unittest discover -s StockTest/data_pipeline -p 'test_*.py' -v
   <NODE> --check StockTest/app.js
   ```

4. 确认本地页面 `http://127.0.0.1:8765/index.html` 可访问，再检查四个区域：总览、板块与权重股、行业动能、市场宽度。
5. “免费行情源质量核对、半实时刷新异常状态和备用源评估”已于 2026-08-30 完成；不重复运行同一轮检查，除非快照刷新或用户要求复核。
6. 本地一键常驻刷新已完成；后续若无新产品需求，进入需要密钥的美股 ETF 备用源适配决策，主题 AI 排名继续保持暂停。

## 待办优先级

### P0：免费行情源质量核对（已完成：2026-08-30）

- [x] 对 `data/market_snapshot.json` 做结构质量核对，并记录异常，不修改页面组件。
- [x] 确认 Yahoo 未收盘日线仍只进入 `pendingBars`，不混入收盘指标。
- [x] 确认 Stockbee 最新抓取日期、20 行限制和字段完整性。

### P1：半实时刷新与备用源评估（已完成：2026-08-30）

- [x] 完善本地半实时刷新失败提示、数据过期和局部缺失状态。
- [x] 评估免费备用行情源；本轮结论是不新增依赖，美股候选需密钥或存在口径限制。
- [x] 重新执行桌面、平板、窄屏和控制台 QA。

### P2：本地一键常驻运行（已完成：2026-08-30）

- [x] 一键启动网页服务器和每小时刷新进程。
- [x] 重复启动保护、项目进程身份校验和安全停止。
- [x] 项目内 PID/日志记录，不注册系统级任务。
- [x] 完成真实刷新、状态徽章、HTTP 和控制台回归。

### 暂停项

- 20 个主题最终排名和主题网页模块。
- 小程序页面/运行时。
- GitHub Pages 发布。
- 新闻热度和独立基本面展示。

## 防重复工作规则

- 先更新 `PROJECT_PROGRESS.md`，不要新建同类日志文件。
- 先查文件地图和现有测试，再决定是否需要新增文件。
- 页面已有交互不重做：导航、主题切换、排序、状态筛选、SPY 固定、15/60 切换、抽屉和 Stockbee 字段切换均已存在。
- 只在需求直接相关的文件中做精准修改，不顺手重构无关模块。
- 任何“已完成”结论都必须附测试或浏览器证据；没有证据时标记为“待验证”。
- 真实数据、来源、抓取时间和缺失状态必须与数据一起保存；不把示例值描述成实时行情。

## 2026-08-31 本地执行状态（GitHub 暂停后）

### 当前结论

项目已经从“网页 UI 原型 + 本地行情刷新”进入“本地可审计市场分析管线”阶段。GitHub 远程仓库、推送、PR、Pages 发布和线上授权操作全部暂停；本地代码、分支和运行方式保留。

### 本地分支与版本

- 主工作区：`StockTest/`，`main` 当前为 `5423708`，仅比 `origin/main` 多 1 个本地忽略规则提交；没有继续推送。
- 隔离开发区：`.worktrees/market-analysis-evidence/StockTest/`，本地分支 `feature/market-analysis-evidence`，当前最新为 `6d315f6`。
- 特性分支尚未合并回 `main`，也没有远程跟踪分支；新的本地需求应优先在该隔离分支继续，避免覆盖主工作区。
- `sources/` 未修改，继续保持只读。

### 已完成的本地分析能力

1. **来源与证据契约（Task 1，已审查通过）**
   - `data/source_registry.json` 登记一期允许来源：Yahoo Chart、Binance 公共 K 线、Stockbee、质量报告；后续 SEC/Fed/BLS/BEA/Treasury/ETF 官网来源保持禁用。
   - `data_pipeline/market_analysis.py` 拒绝重复 ID、禁用来源、无证据 claim、lead 驱动评分和空评分证据，并支持原子写入。
   - 任务提交：`a144187`、`e333c67`、`281eeed`；最终定向/完整测试为 59 项通过。

2. **五因子确定性评分（Task 2，已审查通过）**
   - 已实现趋势、宽度、动量、轮动、风险偏好五因子；使用 Wilder RSI、固定阈值、缺失即 `unavailable`。
   - BTC 只有在存在与美股 `asOf` 同日有效 K 线时才进入正式风险偏好评分；周末 BTC 仍可作为页面最新行情展示，但不会倒灌周五结论。
   - Python 与浏览器 RSI 已统一为 Wilder 口径；动量评分固定为 12 个板块/风格 + 60 项行业目录中排除 IBIT 后的 59 个合格观测，共 71 个。
   - IBIT 只参与风险偏好，不参与动量；ARKK 的双业务角色保留，但证据引用稳定去重。
   - 任务提交：`ca81ca1`、`6a75faa`、`5086dc8`；最终完整数据管线测试为 70 项通过。

3. **证据化结论与置信度（Task 3，已审查通过）**
   - 已实现 `build_market_analysis`、evidence materialize、claim/briefing/watchNext 引用校验、置信度和本地 CLI。
   - 质量报告会影响置信度但不改变因子分数：high 每项扣 0.15（上限 0.30），medium 每项扣 0.05（上限 0.15），low 只展示不扣分。
   - provider 使用封闭映射；`binance-spot` 会规范为 `binance-public-klines`，未知或禁用 provider 直接失败。
   - 当前真实复制快照已生成并回读通过：`asOf=2026-08-28`、状态“震荡”、总分 `-1`、置信度 `1.00`、163 条 evidence、10 条 claims。
   - 任务提交：`ba16585`、`9b91b93`；最终完整数据管线测试为 80 项通过。

4. **刷新流程接入（Task 4，实现已完成，独立复审待做）**
   - `refresh_local_data.py` 已在快照写入成功后生成分析，并将分析状态、`asOf`、置信度、生成时间写入刷新状态。
   - 同一 `asOf` 且输入指纹、canonical registry 和现有分析均有效时复用，不重复构建；快照、质量报告、逻辑刷新状态或 registry 改变时重建。
   - builder/writer 失败不会覆盖上一份有效 analysis；刷新状态标记为 `partial`，保留失败原因和最近完整成功时间。
   - 任务提交：`0cd2bcf`；本地定向 7 项、完整数据管线 83 项通过，离线 copied-snapshot smoke 成功。
   - 待办：按 SDD 流程完成 Task 4 独立规格/质量复审；同时清理不应进入版本历史的临时 SDD 报告提交。

### 当前未完成与明确暂停

- **未完成：** Task 4 独立复审；Task 5 首页市场结论卡和证据抽屉；Task 6 端到端浏览器 QA、文档收口和本地交付验收。
- **暂停：** GitHub 推送/上线、GitHub Pages、主题 Top 20 AI 排名、小程序、新闻热度、独立基本面 UI、真实行情 API 直连浏览器。
- **本地服务：** 继续使用 `start-local.cmd`、`status-local.cmd`、`stop-local.cmd`；不要为隔离分支重复启动 8765 端口，若要验证特性分支请使用单独本地端口。

### 新对话启动入口

新窗口必须先阅读 `PROJECT_HANDOFF.md`、`PROJECT_CONTEXT.md` 和本文件最近这一节，然后运行本地测试。建议从以下上下文开始：

> 请只在本机继续 StockTest，不进行任何 GitHub 推送、PR、Pages 发布或授权操作。先阅读 `StockTest/PROJECT_HANDOFF.md`、`PROJECT_CONTEXT.md`、`PROJECT_PROGRESS.md` 最近一节；当前本地特性分支 `.worktrees/market-analysis-evidence/StockTest` 已完成 Task 1–3，Task 4 已实现但待独立复审，Task 5/6 尚未开始。不要重复制作已有页面、数据契约或进度文档；先运行现有 data_pipeline 测试和 `app.js` 语法检查，再等待我提出新的本地需求。主题 AI、小程序、新闻热度、基本面 UI 与线上部署继续暂停。
