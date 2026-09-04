import unittest
from pathlib import Path


class LocalSnapshotContractTests(unittest.TestCase):
    def test_browser_reads_only_pipeline_snapshot(self):
        app = Path("StockTest/app.js").read_text(encoding="utf-8")
        self.assertIn('fetch(snapshotUrl("stockbee.json"), { cache: "no-store" })', app)
        self.assertIn('fetch(snapshotUrl("market_snapshot.json"), { cache: "no-store" })', app)
        self.assertIn('fetch(snapshotUrl("refresh_status.json"), { cache: "no-store" })', app)
        self.assertIn('const DATA_STATE_BASE_URL = "https://raw.githubusercontent.com/bravo-189/StockTest/data-state/data/";', app)
        self.assertIn('setInterval', app)
        self.assertIn('pendingBars', app)
        self.assertIn("hydrateMarketSnapshot", app)
        self.assertIn("DashboardData.breadth = breadth", app)
        self.assertIn('comparisonDate', app)
        self.assertIn('BTC 最新', app)
        for state in ("刷新失败", "局部缺失", "数据过期", "数据新鲜"):
            self.assertIn(state, app)
        self.assertIn('if (window.location.protocol === "file:") return;', app)
        self.assertNotIn("query1.finance.yahoo.com", app)
        self.assertNotIn("api.binance.com", app)


if __name__ == "__main__":
    unittest.main()
