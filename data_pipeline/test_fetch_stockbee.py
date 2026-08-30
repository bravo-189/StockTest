import unittest

from StockTest.data_pipeline.fetch_stockbee import build_snapshot


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


if __name__ == "__main__":
    unittest.main()
