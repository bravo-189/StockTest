import unittest

from StockTest.data_pipeline.fetch_stockbee import STOCKBEE_LOOKBACK_DAYS, build_snapshot, trim_stockbee_rows


class StockbeeSnapshotTests(unittest.TestCase):
    def test_snapshot_keeps_provenance_and_latest_rows(self):
        csv_text = (
            "Date,Number of stocks up 4% plus today,Number of stocks down 4% plus today,5 day ratio,10 day  ratio,T2108 ,S&P\n"
            "8/27/2026,298,145,1.76,1.30,45.17,\"7,728.65\"\n"
        )
        snapshot = build_snapshot(csv_text, "https://example.test/mm.csv", "2026-08-28T10:00:00Z")
        self.assertTrue(snapshot["source"]["url"].endswith("mm.csv"))
        self.assertEqual(snapshot["source"]["pageUrl"], "https://stockbee.blogspot.com/p/mm.html")
        self.assertEqual(snapshot["source"]["format"], "csv")
        self.assertEqual(snapshot["rows"][0]["date"], "2026-08-27")
        self.assertEqual(snapshot["metadata"]["rowCount"], 1)

    def test_snapshot_retains_six_calendar_months_of_rows(self):
        csv_text = (
            "Date,Number of stocks up 4% plus today,Number of stocks down 4% plus today,5 day ratio,10 day ratio,T2108,S&P\n"
            "08/28/2026,84,382,0.98,1.09,41.91,7711.23\n"
            "02/28/2026,70,410,0.72,0.81,38.20,6800.00\n"
            "02/27/2026,69,411,0.71,0.80,38.10,6790.00\n"
            "12/18/2025,55,430,0.62,0.70,35.00,6500.00\n"
        )
        snapshot = build_snapshot(csv_text, "https://example.test/mm.csv", "2026-08-29T10:00:00Z")
        self.assertEqual(snapshot["metadata"]["historyWindow"], "6mo")
        self.assertEqual(snapshot["metadata"]["lookbackDays"], STOCKBEE_LOOKBACK_DAYS)
        self.assertEqual([row["date"] for row in snapshot["rows"]], ["2026-08-28", "2026-02-28", "2026-02-27"])

    def test_trim_stockbee_rows_uses_latest_date_not_current_clock(self):
        rows = [{"date": "2026-08-28"}, {"date": "2026-02-28"}, {"date": "2025-12-18"}]
        trimmed = trim_stockbee_rows(rows, lookback_days=181)
        self.assertEqual([row["date"] for row in trimmed], ["2026-08-28", "2026-02-28"])


if __name__ == "__main__":
    unittest.main()
