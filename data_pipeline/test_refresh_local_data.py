import json
import tempfile
import unittest
from pathlib import Path

from StockTest.data_pipeline.refresh_local_data import refresh_once, run_refresh_attempt


class RefreshLocalDataTests(unittest.TestCase):
    def test_refresh_once_writes_market_and_stockbee_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)

            def fake_market_builder():
                return {"metadata": {"sourceStatus": "loaded"}, "instruments": {"SPY": {"bars": []}}}

            csv_header = "Date,Number of stocks up 4% plus today,Number of stocks down 4% plus today,5 day ratio,10 day ratio,T2108,S&P"
            csv_rows = "\n".join(f"08/{28 - index:02d}/2026,84,382,0.98,1.09,41.91,7711.23" for index in range(21))
            result = refresh_once(
                output_dir,
                market_builder=fake_market_builder,
                stockbee_csv=f"{csv_header}\n{csv_rows}\n",
                fetched_at="2026-08-29T14:00:00Z",
            )

            self.assertEqual(result["market"]["metadata"]["sourceStatus"], "loaded")
            self.assertTrue((output_dir / "market_snapshot.json").exists())
            self.assertTrue((output_dir / "stockbee.json").exists())
            stockbee = json.loads((output_dir / "stockbee.json").read_text(encoding="utf-8"))
            self.assertEqual(stockbee["metadata"]["rowCount"], 20)
            self.assertEqual(stockbee["metadata"]["latestDate"], "2026-08-28")

    def test_successful_attempt_writes_refresh_status(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            market = {"metadata": {"sourceStatus": "loaded", "loadedCount": 2, "requiredCount": 2, "missing": [], "latestDate": "2026-08-28"}, "instruments": {"SPY": {"bars": []}}}
            csv_text = "Date,Number of stocks up 4% plus today,Number of stocks down 4% plus today,5 day ratio,10 day ratio,T2108,S&P\n08/28/2026,84,382,0.98,1.09,41.91,7711.23\n"

            status = run_refresh_attempt(output_dir, market_builder=lambda: market, stockbee_csv=csv_text, attempted_at="2026-08-30T01:00:00Z")

            saved = json.loads((output_dir / "refresh_status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["status"], "ok")
            self.assertEqual(saved["lastCompletedAt"], "2026-08-30T01:00:00Z")
            self.assertEqual(saved["lastFullSuccessAt"], "2026-08-30T01:00:00Z")
            self.assertEqual(saved["sources"]["market"]["loadedCount"], 2)

    def test_failed_attempt_preserves_snapshots_and_last_success(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "market_snapshot.json").write_text('{"sentinel":"keep"}\n', encoding="utf-8")
            (output_dir / "refresh_status.json").write_text(json.dumps({"lastCompletedAt": "2026-08-29T01:00:00Z", "lastFullSuccessAt": "2026-08-29T01:00:00Z"}), encoding="utf-8")

            def fail_market():
                raise RuntimeError("provider unavailable")

            status = run_refresh_attempt(output_dir, market_builder=fail_market, attempted_at="2026-08-30T01:00:00Z")

            self.assertEqual(status["status"], "failed")
            self.assertEqual(status["errors"][0]["source"], "market")
            self.assertEqual(status["lastFullSuccessAt"], "2026-08-29T01:00:00Z")
            self.assertEqual(json.loads((output_dir / "market_snapshot.json").read_text(encoding="utf-8"))["sentinel"], "keep")

    def test_partial_market_snapshot_is_visible_in_status(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            market = {"metadata": {"sourceStatus": "partial", "loadedCount": 1, "requiredCount": 2, "missing": [{"symbol": "QQQ"}], "latestDate": "2026-08-28"}, "instruments": {"SPY": {"bars": []}}}
            csv_text = "Date,Number of stocks up 4% plus today,Number of stocks down 4% plus today,5 day ratio,10 day ratio,T2108,S&P\n08/28/2026,84,382,0.98,1.09,41.91,7711.23\n"

            status = run_refresh_attempt(output_dir, market_builder=lambda: market, stockbee_csv=csv_text, attempted_at="2026-08-30T01:00:00Z")

            self.assertEqual(status["status"], "partial")
            self.assertEqual(status["sources"]["market"]["missingCount"], 1)
            self.assertIsNone(status["lastFullSuccessAt"])


if __name__ == "__main__":
    unittest.main()
