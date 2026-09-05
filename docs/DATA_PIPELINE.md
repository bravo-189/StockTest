# StockTest 数据管线与自动更新契约

## 目标

网页只负责展示已校验的静态快照，不在浏览器中直接请求行情或第三方网页。所有数据由同一套刷新器生成，经过质量检查后才发布，因此页面不需要用户每天手动提醒或手动刷新数据源。

## 数据分层

| 文件 | 数据粒度 | 更新节奏 | 页面用途 |
| --- | --- | --- | --- |
| `data/market_snapshot.json` | 每个指数、ETF、BTC 一条 `instruments` 记录，内含日线、日内线、RSI、收益、MA150 和交易日历 | 美股收盘后每日；BTC 每小时 | 市场总览、板块 ETF、行业动能、RSI 历史和指数气泡 |
| `data/stockbee.json` | 每个自然日一行的 Stockbee 市场宽度指标 | 美股收盘后每日 | 市场宽度图表和半年表 |
| `data/stockbee_momentum.json` | Stockbee 50 每个代码一行，含板块/行业分类和来源日期 | 来源发布新表后每日追赶 | Stockbee 动能股票 |
| `data/market_snapshot_quality.json` | 最近行情快照的覆盖、日期、OHLCV、未收盘柱和日内边界检查结果 | 每次行情刷新 | 页面数据状态和发布门禁 |
| `data/refresh_status.json` | 每次刷新尝试的状态、时间、来源计数、缺失项和错误 | 每次尝试（包括失败） | 页面新鲜度提示和故障审计 |

### `market_snapshot.json` 的关键约定

- `metadata.comparisonDate`：跨资产比较使用的最近一个已确认美股交易日。
- `metadata.dailyRefreshDate`：最近一次完整美股收盘刷新对应的交易日。
- `metadata.latestDate`：快照中全局最新日期，BTC 周末/盘中可能比美股更新，不能单独用它判断美股是否新鲜。
- `metadata.calendarLatestDates`：按 `us-equity`、`crypto-24x7` 分组的最新日期。
- `instruments[SYMBOL].calendar`：严格为 `us-equity` 或 `crypto-24x7`。
- `instruments[SYMBOL].latestDate`：该标的自身最近已确认日线日期；`pendingBars` 只表示未收盘候选柱，不参与 RSI、收益和 MA150。
- `instruments[SYMBOL].source`：保存 provider、query symbol、来源 URL、抓取时间，便于复核而不是把回退值伪装成实时值。

## 自动更新流程

GitHub Actions 工作流 `.github/workflows/refresh-and-deploy.yml` 每小时第 5 分钟运行一次：

1. 从 `data-state` 分支恢复上一份已发布快照。
2. 运行完整回归测试。
3. 刷新行情和 Stockbee 数据：
   - 美股、板块 ETF、行业 ETF、市场宽度和 Stockbee 50：在美股收盘后每日刷新一次；来源延迟时允许 6 小时冷却后的追赶刷新。
   - BTC：在非完整日刷新时只更新 BTC，使用 24×7 日历。
4. 运行行情质量检查；不通过则停止发布并保留上一份线上快照。
5. 以原子方式写入 JSON，并把新快照提交到独立 `data-state` 分支。
6. 构建 GitHub Pages 静态产物并部署；Vercel 从同一主分支构建网页，网页运行时解析 `data-state` 的最新提交 SHA，读取不可变版本的 JSON，避免 CDN 缓存拿到混合版本。

## 交易日与节假日

刷新器不会把周末或主要 NYSE 全天休市日当成交易日。`_last_us_session_date()` 会识别元旦、马丁·路德·金日、总统日、耶稣受难日、阵亡将士纪念日、六月节、独立日、劳动节、感恩节和圣诞节，并返回此前最近的实际交易日。早收盘不影响“盘后”定义，完整日刷新仍要求所有美股标的拥有同一确认日期。

## 失败与回退语义

- `ok`：全部必需标的和质量门禁通过。
- `partial`：个别来源暂时缺失，但上一份该标的快照被保留；页面会标记局部缺失。
- `failed`：本次没有生成可发布的完整结果；线上继续使用上一份快照，`refresh_status.json` 保留错误来源和消息。
- 文件写入使用临时文件 + 替换，避免部署过程中出现半个 JSON 文件。
- 持仓按日缓存 24 小时；行情每小时更新不会重复请求持仓来源。

## 来源与可靠性边界

- 美股指数/ETF：Yahoo Chart 公共接口（免密钥、非官方聚合接口）；数据结构、日期和 OHLCV 会自动校验，但供应商偶发延迟仍可能造成 `partial` 或保留上一份数据。
- BTC：Binance 公共 Spot K 线接口；采用 24×7 日历，未收盘柱不参与收盘指标。
- Stockbee：用户指定的公开 Google Sheet 导出；保留来源 URL、抓取时间和来源最新日期，来源停更时显示过期而不静默造数。
- ETF 持仓：普通 ETF 使用 StockAnalysis（页面标注 Finnhub 来源），IBIT 使用 iShares 官方 CSV，USO 使用 USCF 官方接口；每行保留来源与 as-of 日期。
- RSI14 使用完整历史日线的 Wilder 平滑算法；MA150 只在至少 150 根已确认日线时判断趋势。

## 日常检查入口

用户无需每天进入网页触发更新。需要审计时查看：

- GitHub Actions 的 `Refresh data and deploy Pages` 最近一次运行是否为绿色；
- 页面数据状态中的 `最后尝试`、`最后完整成功` 和来源计数；
- `data/market_snapshot_quality.json` 的 `coverage`、`latestDateByCalendar` 和 `pendingCount`。

如果连续失败，系统会继续显示上一份可用数据并保留错误证据，不会把空表或示例数据伪装成最新数据。
