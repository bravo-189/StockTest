import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UiFlowContractTests(unittest.TestCase):
    def setUp(self):
        self.page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.app = (ROOT / "app.js").read_text(encoding="utf-8")

    def test_sector_and_holdings_share_one_navigation_section(self):
        self.assertIn('data-target="sectors"', self.page)
        self.assertIn("板块与权重股", self.page)
        self.assertNotIn('data-target="holdings"', self.page)
        self.assertEqual(self.page.count('id="holdings"'), 0)
        self.assertIn('id="holdings-strip"', self.page)

    def test_sector_table_pins_spy_and_exposes_requested_controls(self):
        self.assertIn('data-sector-sort="rsi"', self.page)
        self.assertIn('data-sector-sort="d1"', self.page)
        self.assertIn('data-sector-sort="d5"', self.page)
        self.assertIn('data-sector-sort="d20"', self.page)
        self.assertNotIn('<th scope="col">趋势</th>', self.page)
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
        self.assertIn('class="holding-link"', self.app)
        self.assertIn('state.industryView === "top"', self.app)
        self.assertIn('industrySort', self.app)

    def test_sector_and_industry_tables_have_internal_scroll_and_pinned_spy_rows(self):
        self.assertIn('class="table-shell sector-table-scroll"', self.page)
        self.assertIn('class="industry-leaderboard table-shell industry-table-scroll"', self.page)
        self.assertIn('class="${row.ticker === "SPY" ? "is-pinned" : ""}"', self.app)
        self.assertIn('const spy = sorted.find((row) => row.ticker === "SPY")', self.app)
        self.assertIn('const ordered = spy ? [spy, ...sorted.filter((row) => row.ticker !== "SPY")] : sorted;', self.app)

    def test_major_markets_and_sector_universe_include_crypto(self):
        self.assertIn('["BTC", "Bitcoin"', self.app)
        self.assertIn('["IBIT", "加密货币"', self.app)

    def test_industry_snapshot_and_pending_bar_are_rendered(self):
        self.assertIn("const industry = industries.find", self.app)
        self.assertIn("pendingBars", self.app)

    def test_index_cards_use_one_month_trading_day_candles(self):
        self.assertIn("const INDEX_TRADING_DAYS = 21;", self.app)
        self.assertIn("Array.from({ length: pointCount }", self.app)
        self.assertIn("近一个月交易日 K 线", self.app)
        self.assertIn("近 1 个月交易日", self.page)
        self.assertNotIn("60 日预览", self.page)

    def test_breadth_uses_stockbee_columns_as_metric_switches(self):
        for key in ("up", "down", "ratio5", "ratio10", "t2108", "sp500"):
            self.assertIn(f'data-breadth-metric="{key}"', self.page)
        self.assertNotIn('class="breadth-signals"', self.page)
        self.assertIn("breadthMetric", self.app)
        self.assertIn("breadthMetricDefs", self.app)

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

    def test_theme_agent_contract_is_backend_only(self):
        agent = json.loads((ROOT / "data" / "theme_catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(agent["metadata"]["method"], "backend AI research ranking contract")
        self.assertIn("agentPrompt", agent["metadata"])
        self.assertIn("sourceUrls", agent["metadata"])


if __name__ == "__main__":
    unittest.main()
