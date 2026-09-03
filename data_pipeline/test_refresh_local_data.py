import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from StockTest.data_pipeline.refresh_local_data import _daily_refresh_due, _write_json, refresh_once, run_refresh_attempt


class RefreshLocalDataTests(unittest.TestCase):

    def test_preclose_bootstrap_is_followed_by_after_close_daily_refresh(self):
        previous = {
            "metadata": {"dailyRefreshDate": "2026-09-03"},
            "instruments": {"SPY": {"latestDate": "2026-09-03"}},
        }
        before_close = datetime(2026, 9, 3, 16, 30, tzinfo=ZoneInfo("America/New_York"))
        after_close = datetime(2026, 9, 3, 17, 5, tzinfo=ZoneInfo("America/New_York"))
        with patch("StockTest.data_pipeline.refresh_local_data._eastern_now", return_value=before_close):
            self.assertFalse(_daily_refresh_due(previous))
        with patch("StockTest.data_pipeline.refresh_local_data._eastern_now", return_value=after_close):
            self.assertTrue(_daily_refresh_due(previous))

    def test_write_json_replaces_snapshot_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "snapshot.json"
            _write_json(target, {"version": 2, "rows": [1, 2, 3]})
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"version": 2, "rows": [1, 2, 3]})
            self.assertEqual(list(Path(directory).glob("*.tmp")), [])
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
            self.assertEqual(stockbee["metadata"]["rowCount"], 21)
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

    def test_partial_market_refresh_retains_previous_valid_instruments(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            previous = {"metadata": {"sourceStatus": "loaded", "loadedCount": 2, "requiredCount": 2, "missing": []}, "instruments": {"SPY": {"bars": [1]}, "COPX": {"bars": [2]}}}
            (output_dir / "market_snapshot.json").write_text(json.dumps(previous), encoding="utf-8")
            market = {"metadata": {"sourceStatus": "partial", "loadedCount": 1, "requiredCount": 2, "missing": [{"symbol": "COPX"}]}, "instruments": {"SPY": {"bars": [3]}}}
            csv_text = "Date,Number of stocks up 4% plus today,Number of stocks down 4% plus today,5 day ratio,10 day ratio,T2108,S&P\n08/28/2026,84,382,0.98,1.09,41.91,7711.23\n"

            result = refresh_once(output_dir, market_builder=lambda: market, stockbee_csv=csv_text, fetched_at="2026-08-30T01:00:00Z")

            self.assertEqual(result["market"]["metadata"]["sourceStatus"], "loaded")
            self.assertEqual(result["market"]["metadata"]["retainedSymbols"], ["COPX"])
            self.assertEqual(result["market"]["instruments"]["COPX"]["bars"], [2])

    def test_btc_only_refresh_replaces_btc_and_retains_daily_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            previous_market = {
                "metadata": {"sourceStatus": "loaded", "dailyRefreshDate": "2026-09-01"},
                "instruments": {"SPY": {"latestDate": "2026-09-01"}, "BTC": {"latestDate": "2026-09-01"}},
            }
            (output_dir / "market_snapshot.json").write_text(json.dumps(previous_market), encoding="utf-8")
            (output_dir / "stockbee.json").write_text(json.dumps({"metadata": {"latestDate": "2026-09-01"}}), encoding="utf-8")
            (output_dir / "stockbee_momentum.json").write_text(json.dumps({"metadata": {"latestDate": "2026-09-01"}}), encoding="utf-8")
            btc = {"metadata": {"latestDate": "2026-09-02", "intraday": {"sourceStatus": "loaded"}}, "instruments": {"BTC": {"latestDate": "2026-09-02"}}}
            with patch("StockTest.data_pipeline.refresh_local_data._build_live_btc_snapshot", return_value=btc):
                result = refresh_once(output_dir, fetched_at="2026-09-02T01:00:00Z", btc_only=True)
            saved = json.loads((output_dir / "market_snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["instruments"]["SPY"]["latestDate"], "2026-09-01")
            self.assertEqual(saved["instruments"]["BTC"]["latestDate"], "2026-09-02")
            self.assertEqual(result["stockbee"]["metadata"]["latestDate"], "2026-09-01")


if __name__ == "__main__":
    unittest.main()
