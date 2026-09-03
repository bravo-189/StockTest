# 数据与资料可靠性审计

审计时间：2026-09-02 04:28（Asia/Shanghai，约 2026-09-01 20:28 UTC）

本审计只检查现有本地快照、来源记录、刷新状态、计算契约和来源可访问性，不修改行情或持仓数据。

## 总体结论

当前结论为 **需带条件使用；前十大名单展示口径已收敛，已完成本轮来源异常修复，仍需持续监控来源日期和刷新存活**。

- 行情快照的覆盖、日期顺序、OHLCV 数值边界和日内时间戳通过现有校验；但 9 月 1 日的 75 个美股临时日线柱仍标为 `incomplete`，BTC 只有 90 根日线，不能可靠计算 MA150。
- Stockbee 宽度和 Stockbee 50 有可追溯的公开来源，字段完整度良好；Stockbee 50 的 50 个代码唯一，分类为 49 条完整核验、1 条部分核验。
- ETF 持仓 71/71 有记录，IBIT/USO 使用发行方来源；页面只展示可核验的前十名单，不展示可能混淆单位的占比。解析器保留无代码资产行，并保留交易所前缀，避免把不同市场的同名代码误判为缺失或重复。
- `market_snapshot_quality.json` 已纳入刷新流程，保存快照时同步重算，避免报告与快照错位。
- 本地网页服务运行中，但刷新进程当前为 stopped；因此“每小时 BTC、盘后美股/Stockbee”不能视为正在持续执行。
- AI、新闻和 X 来源仍明确禁用，主题目录为 sample/pending；页面当前没有可声称为网络新闻或 AI 研究结论的内容。

## 检查证据

### 行情快照 `data/market_snapshot.json`

- 76/76 标的加载，75 个 Yahoo Chart、1 个 Binance Spot；共 37,526 根已确认日线。
- 75 个美股 `pendingBars` 都是 2026-09-01、状态 `incomplete`；它们应继续被当作临时盘中数据，不得参与收盘 RSI、收益率或 MA150。
- 日线日期唯一且升序；OHLCV 均为有限数值，且 high/low 与 open/close 边界一致；未发现负成交量。
- 日内数据：SPX/NDX/DJI/RUT 为 Yahoo 原生 5m，BTC 为 Binance 2h；各序列时间戳唯一且升序，BTC 当前最后一根仍是未完成柱。
- 美股历史日线约 499–500 根；BTC 仅 90 根，因此 BTC 的 MA150 属于数据不足，不能解释为可靠的“上涨/下降”趋势。

### Stockbee 宽度 `data/stockbee.json`

- 127 行、127 个唯一日期，日期范围 2026-03-02 至 2026-08-31，15 个字段均存在。
- 计数、比值、T2108 和 Worden Universe 的数值范围未发现非法值。
- 来源和页面可访问；Stockbee 页面将 Market Monitor 定义为 breadth-based market timing tracker，并说明 Stockbee 50 列表按日更新。[Stockbee Market Monitor](https://stockbee.blogspot.com/p/mm.html) · [Stockbee 50](https://stockbee.blogspot.com/p/stockbee-50.html)

### Stockbee 50 `data/stockbee_momentum.json`

- 50 行、50 个唯一排名、50 个唯一代码；最新日期 2026-08-31，抓取时间 2026-09-01T17:01:12Z。
- 49 行板块和行业完整核验，1 行（ZCSH）为 partial；该行行业字段仍需人工/第二来源复核。
- 使用 Google Sheet CSV 导出作为名单源；当前导出端点可访问，但名单本身是“动能筛选结果”，不是基本面或投资建议。

### ETF 持仓 `data/market_snapshot.json` 的 `holdings`

- 71/71 个请求标的有记录；普通标的来自 StockAnalysis 聚合页（页面注明来源为 Finnhub），IBIT 来自 iShares 官方 CSV，USO 来自 USCF 官方 API。
- IBIT 官方资料显示其 Number of Holdings 为 1，且持仓数据会变动；本地同时保留 BTC 与 USD CASH 两行，应明确这是“资产 + 现金行”，不能按普通股票 ETF 的十只股票理解。[iShares IBIT](https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf)
- 已修复的数据契约风险：iShares CSV 的 `Weight (%)` 按百分数保存，USCF 原始小数权重转换为百分数并标记 gross exposure；前端不再展示比例或权重进度条，只展示前十代码和名称。
- 首次审计发现的局部结构异常已完成来源核对：ARKF/ARKW/BLOK/DTCR 的跳号来自源站无代码资产行，现已保留为“未提供代码”；SLX 的两个 RIO 分别是 `$RIO` 与 `!asx/RIO`，现保存为 `RIO` 与 `ASX:RIO`。MAGS/USO 的权重语义仍按来源记录，不在页面展示比例。
- 持仓 `asOf` 日期从 2026-06-30 到 2026-08-31 不等，抓取时间统一为 2026-09-01；VNQ、GDX 等记录已经明显旧于一周，页面应保留逐 ETF 的 as-of 日期和过期提示。

### 质量报告与刷新状态

- 当前快照质量脚本（`data_pipeline/validate_market_snapshot.py --min-bars 21`）会额外检查持仓排名连续性、重复代码、非法权重和单位契约；来源修复刷新后仅剩 1 项 medium finding，即 BTC MA150 数据不足。需要注意：BTC MA150 当前仅是后台统一 schema 的准备性检查，页面没有 BTC 趋势列，不应被理解为用户界面的缺陷。
- 质量报告已由 `refresh_local_data.py` 在 BTC 小时刷新和盘后全量刷新后同步生成；若快照有异常，报告会保留逐项证据。
- `data/refresh_status.json` 最近一次记录为 `btc-hourly`、`ok`，但 `local_runtime.py status` 显示 refresh 进程已停止；状态文件不能替代进程存活检查。

### AI、新闻和主题资料

- `data/analysis_sources.json` 中 `aiEnabled=false`、`newsEnabled=false`，X 白名单为空；`data_pipeline/ai_analysis.py` 在未注入 provider 时不会发起 API 请求。
- `data/theme_catalog.json` 标记为 `sourceStatus=sample`、主题 `analysisStatus=pending`。这些是候选目录，不是已经由 AI、新闻或基本面资料验证的主题排名。

## 已执行的验证

- JavaScript 语法检查通过。
- 刷新、UI 契约、行情质量、持仓解析和 Stockbee 分类专项测试共 99 项通过。
- 本地首页 HTTP 200，静态资源版本标记可读取。
- Stockbee 页面、两个 Google Sheet CSV、Yahoo Chart、iShares CSV 和 USCF 持仓页当前均返回 HTTP 200；Binance 主域名在当前网络返回 451，备用 `data-api.binance.vision` 返回 200。抓取器现记录实际成功的 Binance 端点，当前快照已记录备用域名。

## 修复优先级

1. 继续监控过期 `asOf` 和异常权重，并在来源变化后重新验证。
2. 保证每次快照写入后都生成同版本质量报告；不把质量报告当作实时进程存活证明。
3. 恢复并监控本地 refresh 进程；状态文件应包含实际运行状态和最近失败原因。
4. 对过期 `asOf` 和异常权重增加自动化阻断/警告；排名与跨市场代码的处理已纳入解析器。
5. 为 BTC MA150 明确显示“数据不足”，不要输出确定性的上涨/下降。
6. 在真正接入 AI/新闻前继续保持 sample/pending 标识，不把候选主题或规则摘要包装成外部研究结论。

## 2026-09-03 来源异常复核补充

- 直接复核 StockAnalysis 持仓页后确认，ARKF、ARKW、BLOK、DTCR 的跳号是无代码资产行被旧解析器跳过造成的；解析器现已保留这些行，代码为空时页面显示“未提供代码”。
- 直接复核 SLX 页面后确认，`$RIO` 与 `!asx/RIO` 是不同交易所证券；解析器现已规范为 `RIO` 与 `ASX:RIO`，质量检查不再报重复代码。
- 已单独刷新 71 个 ETF 持仓并同步质量报告；当前 `market_snapshot_quality.json` 仅剩 BTC MA150 数据不足 1 项 medium finding。该项不对应当前 BTC 卡片展示，属于后台统一 schema 的准备性检查。
