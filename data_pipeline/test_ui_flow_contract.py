import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UiFlowContractTests(unittest.TestCase):
    def setUp(self):
        self.page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.styles = (ROOT / "styles.css").read_text(encoding="utf-8")

    def test_sector_and_holdings_share_one_navigation_section(self):
        self.assertIn('data-target="sectors"', self.page)
        self.assertIn("板块与权重股", self.page)
        self.assertNotIn('data-target="holdings"', self.page)
        self.assertEqual(self.page.count('id="holdings"'), 0)
        self.assertIn('id="holdings-strip"', self.page)

    def test_long_term_page_entry_and_empty_shell_exist(self):
        self.assertIn('href="long-term.html"', self.page)
        long_term = (ROOT / "long-term.html").read_text(encoding="utf-8")
        self.assertIn("长期投资", long_term)
        self.assertIn('class="page-placeholder section-surface"', long_term)
        self.assertIn('href="index.html"', long_term)

    def test_long_term_is_a_peer_product_space_not_a_research_nav_item(self):
        self.assertIn('class="product-switcher"', self.page)
        self.assertIn('class="product-switcher-item is-active"', self.page)
        self.assertNotIn('class="nav-item nav-link" href="long-term.html"', self.page)
        long_term = (ROOT / "long-term.html").read_text(encoding="utf-8")
        self.assertIn('class="product-switcher"', long_term)
        self.assertIn('class="product-switcher-item is-active"', long_term)

    def test_sector_table_pins_spy_and_exposes_requested_controls(self):
        self.assertIn('data-sector-sort="rsi"', self.page)
        self.assertIn('data-sector-sort="d1"', self.page)
        self.assertIn('data-sector-sort="d5"', self.page)
        self.assertIn('data-sector-sort="d20"', self.page)
        self.assertIn('趋势（MA150）', self.page)
        self.assertIn('id="sector-status-filter"', self.page)
        self.assertIn('class="status-filter"', self.page)
        self.assertIn('state.sectorStatus', self.app)
        self.assertIn('class="status-label is-${tone}"', self.app)
        self.assertNotIn('data-status-etf', self.app)
        self.assertNotIn('class="status-select', self.app)
        self.assertIn('ticker !== "SPY"', self.app)
        self.assertIn('slice(0, 12)', self.app)

    def test_industry_view_switch_sorting_and_holdings_action(self):
        for key in ("rsi", "d5", "d20"):
            self.assertIn(f'data-industry-sort="{key}"', self.page)
        self.assertNotIn('<th scope="col">动能</th>', self.page)
        for label in ("RS1M", "RS3M", "RS6M", "RS12M"):
            self.assertNotIn(label, self.page)
        self.assertIn('class="holding-link"', self.app)
        self.assertIn('state.industryView === "top"', self.app)
        self.assertIn('industrySort', self.app)

    def test_change_columns_use_numeric_day_labels_and_percent_suffix(self):
        for label in ("1日变化", "5日变化", "20日变化"):
            self.assertIn(label, self.page)
        self.assertNotIn(">Δ1<", self.page)
        self.assertNotIn(">Δ5<", self.page)
        self.assertNotIn(">Δ20<", self.page)
        self.assertIn("const signed = (value, digits) => `${signedNumber(value, digits)}%`;", self.app)
        self.assertIn('<span class="drawer-metric-label">5日变化</span>', self.app)
        self.assertIn('<span class="drawer-metric-label">20日变化</span>', self.app)

    def test_daily_rsi_gainers_page_filters_six_point_increases(self):
        self.assertIn('data-target="rsi-gainers"', self.page)
        self.assertIn('id="rsi-gainers"', self.page)
        self.assertIn("RSI 日增榜", self.page)
        for label in ("板块/行业", "当前 RSI14", "前一日 RSI14", "RSI 变化"):
            self.assertIn(label, self.page)
        self.assertIn("const RSI_GAIN_THRESHOLD = 6;", self.app)
        self.assertIn("function rsiDailyChangeFor(ticker)", self.app)
        self.assertIn("function renderRsiGainers()", self.app)
        self.assertIn("delta >= RSI_GAIN_THRESHOLD", self.app)
        self.assertIn("renderRsiGainers()", self.app)

    def test_market_overview_starts_with_indices_breadth_and_rsi_rankings(self):
        self.assertIn('id="market-overview"', self.page)
        self.assertIn("市场一览", self.page)
        for element_id in ("index-grid", "market-overview-breadth", "rsi-top-body", "rsi-bottom-body"):
            self.assertIn(f'id="{element_id}"', self.page)
        for label in ("RSI Top 20", "RSI Bottom 20", "市场宽度", "4%上涨", "4%下跌", "5日比率"):
            self.assertIn(label, self.page)
        self.assertIn("function renderMarketOverview()", self.app)
        self.assertIn("function renderRsiRankings()", self.app)
        self.assertIn("renderMarketOverview()", self.app)
        self.assertIn("renderRsiRankings()", self.app)
        self.assertIn("slice(0, 20)", self.app)
        self.assertIn("slice(-20).reverse()", self.app)
        self.assertIn('data-rsi-sort="top"', self.page)
        self.assertIn('data-rsi-sort="bottom"', self.page)
        self.assertIn('data-target="market-overview"', self.page)
        self.assertIn("breadth-card-description", self.app)
        self.assertNotIn("MARKET REGIME · 盘后状态", self.page)
        self.assertNotIn('id="indices"', self.page)

    def test_market_change_values_use_absolute_deltas_without_percent_suffix(self):
        self.assertIn("const signedDelta =", self.app)
        self.assertIn("function closeDelta", self.app)
        self.assertIn("const d1Delta = closeDelta", self.app)
        self.assertIn('class="overview-index-delta-label"', self.app)
        self.assertIn('title="绝对价格变化，不含百分号"', self.app)

    def test_industry_table_has_no_redundant_rsi_callout(self):
        self.assertIn('class="industry-layout"', self.page)
        self.assertNotIn('class="industry-callout', self.page)
        self.assertNotIn("SIGNAL NOTE", self.page)

    def test_relative_strength_columns_are_paused_from_active_ui(self):
        for label in ("RS1M", "RS3M", "RS6M", "RS12M"):
            self.assertNotIn(label, self.page)
        self.assertNotIn("relativeStrengthRatingsFromBars", self.app)
        self.assertNotIn("applyRelativeStrengthMetrics", self.app)

    def test_sector_and_industry_tables_have_internal_scroll_and_pinned_spy_rows(self):
        self.assertIn('class="table-shell sector-table-scroll"', self.page)
        self.assertIn('class="industry-leaderboard table-shell industry-table-scroll"', self.page)
        self.assertIn('<colgroup><col class="col-rank"><col class="col-etf"><col class="col-trend">', self.page)
        self.assertIn('<colgroup><col class="col-rank"><col class="col-etf"><col class="col-industry"><col class="col-trend"><col class="col-rsi"><col class="col-delta"><col class="col-delta"><col class="col-holdings"><col class="col-status"></colgroup>', self.page)
        self.assertIn('<th scope="col">状态</th>', self.page)
        self.assertIn('<td colspan="9">', self.app)
        self.assertIn('趋势（MA150）', self.page)
        self.assertIn('trend150', self.app)
        self.assertIn('class="trend-label is-${trendTone}"', self.app)
        self.assertIn('const status = row.d5 > .18 ? "改善"', self.app)
        self.assertIn('class="${row.ticker === "SPY" ? "is-pinned" : ""}"', self.app)
        self.assertIn('top: var(--table-header-height, 40px)', self.styles)
        self.assertIn('shell.style.setProperty("--table-header-height"', self.app)
        self.assertIn('cover.style.height = "0px"', self.app)
        self.assertIn('const spy = sorted.find((row) => row.ticker === "SPY")', self.app)
        self.assertIn('const ordered = spy ? [spy, ...sorted.filter((row) => row.ticker !== "SPY")] : sorted;', self.app)
        self.assertNotIn('class="col-price"', self.page)
        self.assertNotIn('<th scope="col">收盘价</th>', self.page)

    def test_sector_and_industry_expose_two_month_daily_rsi_history(self):
        self.assertIn('class="rsi-history-comparison"', self.page)
        self.assertIn('id="rsi-history-comparison-title"', self.page)
        for kind in ("sector", "industry"):
            self.assertIn(f'id="{kind}-rsi-history-panel"', self.page)
            self.assertIn(f'id="{kind}-rsi-symbol"', self.page)
            self.assertIn(f'id="{kind}-rsi-toggle"', self.page)
            self.assertIn(f'id="{kind}-rsi-history-body"', self.page)
        self.assertIn("const RSI_HISTORY_DAYS = 42;", self.app)
        self.assertIn("function rsiHistoryFor(ticker)", self.app)
        self.assertIn("slice(-RSI_HISTORY_DAYS)", self.app)
        self.assertIn("function renderRsiHistory(kind)", self.app)
        self.assertIn("RSI14 近 2 个月", self.page)
        self.assertIn("rsi-history-table-shell", self.styles)

    def test_major_markets_and_sector_universe_include_crypto(self):
        self.assertIn('["BTC", "Bitcoin"', self.app)
        self.assertIn('["IBIT", "加密货币"', self.app)

    def test_industry_snapshot_and_pending_bar_are_rendered(self):
        self.assertIn("const industry = industries.find", self.app)
        self.assertIn("pendingBars", self.app)

    def test_index_cards_default_to_intraday_and_hover_to_month(self):
        self.assertIn("const INDEX_TRADING_DAYS = 21;", self.app)
        self.assertIn("const MONTH_TRADING_DAYS = 21;", self.app)
        self.assertIn("Array.from({ length: pointCount }", self.app)
        self.assertIn("buildIntradayBars", self.app)
        self.assertIn("drawLineAreaChart", self.app)
        self.assertIn("drawBubbleCandlestickChart", self.app)
        self.assertIn("emaSeries", self.app)
        self.assertIn("drawEma(9", self.app)
        self.assertIn("drawEma(21", self.app)
        self.assertIn("const US_INTRADAY_BARS = 79;", self.app)
        self.assertIn("const BTC_INTRADAY_BARS = 12;", self.app)
        self.assertIn('const count = ticker === "BTC" ? BTC_INTRADAY_BARS : US_INTRADAY_BARS;', self.app)
        self.assertIn('ticker === "BTC" ? "当日 · 2H（24H）K 线" : "当日 · 5M 面积图"', self.app)
        self.assertIn("mouseenter", self.app)
        self.assertIn("mouseleave", self.app)
        self.assertIn("updateIndexHoverBubble", self.app)
        self.assertIn("index-hover-bubble", self.app)
        self.assertIn("bubble-sparkline", self.app)
        self.assertIn("bubble-legend", self.app)
        self.assertIn("EMA9", self.app)
        self.assertIn("EMA21", self.app)
        self.assertIn('tabindex="0"', self.page)
        self.assertIn("当日 5 分钟折线面积图", self.app)
        self.assertIn("当日 2 小时 K 线", self.app)
        self.assertIn('status === "incomplete"', self.app)
        self.assertIn("含未收盘柱", self.app)
        self.assertIn("bubble-price", self.app)
        self.assertIn("价格 ${formatPrice(displayItem.close)}", self.app)
        self.assertIn("放大 · 近 1 个月日线 K 线", self.app)
        self.assertIn("近 1 个月日线", self.app)
        self.assertIn("悬停放大近 1 个月", self.app)
        self.assertIn("min(640px", self.styles)
        self.assertIn("height: 220px", self.styles)
        self.assertNotIn("60 日预览", self.page)

    def test_topbar_has_live_us_and_beijing_clocks(self):
        self.assertIn('id="us-clock"', self.page)
        self.assertIn('id="cn-clock"', self.page)
        self.assertIn('timeZone: "America/New_York"', self.app)
        self.assertIn('timeZone: "Asia/Shanghai"', self.app)
        self.assertIn("window.setInterval(updateClocks, 1000)", self.app)

    def test_navigation_is_horizontal_and_search_actions_are_removed(self):
        self.assertIn(".app-shell { display: block;", self.styles)
        self.assertIn(".sidebar {", self.styles)
        self.assertIn(".nav-list { display: flex;", self.styles)
        self.assertIn(".main-content { width: 100%;", self.styles)
        self.assertNotIn('id="global-search"', self.page)
        self.assertNotIn('id="focus-search"', self.page)
        self.assertNotIn("$(\"#global-search\")", self.app)
        self.assertNotIn("$(\"#focus-search\")", self.app)

    def test_sector_etf_links_open_tradingview_while_holdings_keep_drawer_hooks(self):
        self.assertIn("function tradingViewUrl(ticker)", self.app)
        self.assertIn("tw.tradingview.com/chart/e2o5U28E", self.app)
        self.assertIn('const exchange = tradingViewExchanges[ticker] || "AMEX"', self.app)
        self.assertIn('DTCR: "NASDAQ"', self.app)
        self.assertIn('class="etf-button tradingview-link"', self.app)
        self.assertIn('target="_blank" rel="noopener noreferrer"', self.app)
        self.assertIn('class="holding-button" type="button" data-etf=', self.app)

    def test_industry_etf_links_open_tradingview_while_holdings_keep_drawer_hooks(self):
        self.assertIn('aria-label="在 TradingView 查看 ${row.ticker}"', self.app)
        self.assertIn('const entry = holdings[ticker]', self.app)
        self.assertIn('未使用其他 ETF 数据替代', self.app)

    def test_stockbee_momentum_list_has_source_backed_ticker_links(self):
        self.assertIn('data-target="stockbee-momentum"', self.page)
        self.assertIn('id="stockbee-momentum"', self.page)
        self.assertIn('id="stockbee-momentum-body"', self.page)
        self.assertIn('fetch("data/stockbee_momentum.json", { cache: "no-store" })', self.app)
        self.assertIn('function renderStockbeeMomentum()', self.app)
        self.assertIn('STOCKBEE 50', self.page)
        self.assertIn('function tradingViewSymbolUrl(ticker)', self.app)
        self.assertIn('href="${tradingViewSymbolUrl(row.ticker)}"', self.app)

    def test_file_preview_redirects_to_local_runtime_for_real_snapshots(self):
        self.assertIn("function redirectFilePreview()", self.app)
        self.assertIn("window.location.protocol !== \"file:\"", self.app)
        self.assertIn("http://127.0.0.1:8765/index.html", self.app)
        self.assertIn("无法读取真实快照", self.app)

    def test_hover_bubble_has_overlay_layer_above_tables(self):
        self.assertIn(".index-card:hover, .index-card:focus-within { z-index: 100; }", self.styles)
        self.assertIn(".index-hover-bubble { position: fixed; z-index: 101;", self.styles)
        self.assertIn("document.body.appendChild(bubble)", self.app)
        self.assertIn("盘中价格每小时刷新", self.app)
        self.assertIn("latestIntraday", self.app)
        self.assertIn("marketPendingBars", self.app)
        self.assertIn("含未收盘日线", self.app)

    def test_index_cards_open_verified_tradingview_symbols(self):
        self.assertIn('const tradingViewIndexSymbols = { SPX: "SP:SPX", NDX: "NASDAQ:NDX", DJI: "DJ:DJI", RUT: "TVC:RUT", BTC: "COINBASE:BTCUSD" };', self.app)
        self.assertIn("function tradingViewIndexUrl(ticker)", self.app)
        self.assertIn('data-index-ticker="${ticker}"', self.app)
        self.assertIn('role="link"', self.app)
        self.assertIn('window.open(tradingViewIndexUrl(ticker), "_blank", "noopener,noreferrer")', self.app)
        self.assertIn('event.key === "Enter" || event.key === " "', self.app)

    def test_breadth_uses_stockbee_columns_as_metric_switches(self):
        for key in ("up", "down", "ratio5", "ratio10", "t2108", "sp500"):
            self.assertIn(f'data-breadth-metric="{key}"', self.page)
        self.assertNotIn('class="breadth-signals"', self.page)
        self.assertIn("breadthMetric", self.app)
        self.assertIn("breadthMetricDefs", self.app)

    def test_breadth_metric_switch_is_grouped_by_direction_and_context(self):
        for group in ("breadth-group-up", "breadth-group-down", "breadth-group-context"):
            self.assertIn(f'class="breadth-metric-group {group}"', self.page)
        for label in ("上涨指标", "下跌指标", "其他指标"):
            self.assertIn(label, self.page)

    def test_breadth_chart_is_chronological_and_tracks_latest_point(self):
        self.assertIn("function breadthChartRows()", self.app)
        self.assertIn("sort((a, b) => String(a.date).localeCompare(String(b.date)))", self.app)
        self.assertIn("const points = rows.map", self.app)
        self.assertIn("canvas.dataset.latestDate", self.app)
        self.assertIn("chartRows[0].date", self.app)
        self.assertIn("chartRows[chartRows.length - 1].date", self.app)

    def test_breadth_table_exposes_full_stockbee_primary_secondary_structure(self):
        for label in ("Primary Breadth Indicators", "Secondary Breadth Indicators", "Worden股票宇宙", "T2108", "S&amp;P 500"):
            self.assertIn(label, self.page)
        for key in ("up25Quarter", "down25Quarter", "up25Month", "down25Month", "up50Month", "down50Month", "up13_34d", "down13_34d", "wordenUniverse"):
            self.assertIn(f'data-breadth-metric="{key}"', self.page)
            self.assertIn(f'"{key}"', self.app)

    def test_breadth_redesign_has_readout_and_independent_horizontal_scrollbar(self):
        self.assertIn('class="breadth-chart-heading"', self.page)
        self.assertIn('id="breadth-latest-value"', self.page)
        self.assertIn('id="breadth-table-viewport"', self.page)
        self.assertIn('id="breadth-scrollbar"', self.page)
        self.assertIn('id="breadth-scrollbar-track"', self.page)
        self.assertIn("function setupBreadthScroll()", self.app)
        self.assertIn('event.key === "ArrowLeft"', self.app)
        self.assertIn('event.key === "End"', self.app)

    def test_breadth_table_reproduces_source_cell_fills_and_group_boundaries(self):
        self.assertIn('const breadthGroupFor = (index) => index < 6 ? "primary" : index < 12 ? "secondary" : "context";', self.app)
        self.assertIn("const breadthCellFill = (row, key)", self.app)
        self.assertIn('has-cell-fill', self.app)
        self.assertIn('--cell-fill: ${fill}', self.app)
        self.assertIn('breadth-cell-${breadthGroupFor(index)}', self.app)
        for class_name in ("breadth-cell-primary", "breadth-cell-secondary", "breadth-cell-context"):
            self.assertIn(class_name, self.styles)
        for color in ("#339966", "#00ff00", "#f4cccc", "#e06666"):
            self.assertIn(color, self.app)
        self.assertIn(".breadth-raw-table tbody td:nth-child(2)", self.styles)
        self.assertIn(".breadth-raw-table tbody td:nth-child(8)", self.styles)
        self.assertIn(".breadth-raw-table tbody td:nth-child(14)", self.styles)

    def test_breadth_uses_six_month_snapshot(self):
        self.assertIn("最近半年的原始列", self.page)
        self.assertIn("展开半年数据", self.page)
        self.assertIn("snapshot.rows.map", self.app)
        self.assertNotIn("snapshot.rows.slice(0, 20)", self.app)

    def test_theme_agent_contract_is_backend_only(self):
        agent = json.loads((ROOT / "data" / "theme_catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(agent["metadata"]["method"], "backend AI research ranking contract")
        self.assertIn("agentPrompt", agent["metadata"])
        self.assertIn("sourceUrls", agent["metadata"])


if __name__ == "__main__":
    unittest.main()
