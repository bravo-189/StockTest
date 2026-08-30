import unittest

from StockTest.data_pipeline.validate_market_snapshot import analyze_snapshot


def _bars(start="2026-08-01", count=3):
    from datetime import date, timedelta

    first = date.fromisoformat(start)
    return [
        {
            "date": (first + timedelta(days=index)).isoformat(),
            "open": 100 + index,
            "high": 101 + index,
            "low": 99 + index,
            "close": 100.5 + index,
            "volume": 1000,
        }
        for index in range(count)
    ]


class MarketSnapshotQualityTests(unittest.TestCase):
    def test_reports_coverage_and_provider_date_ranges(self):
        snapshot = {
            "metadata": {"requiredCount": 2, "loadedCount": 2, "missing": [], "pendingCount": 1},
            "instruments": {
                "SPY": {"symbol": "SPY", "provider": "yahoo-chart", "latestDate": "2026-08-03", "bars": _bars()},
                "BTC": {"symbol": "BTC", "provider": "binance-spot", "latestDate": "2026-08-04", "bars": _bars("2026-08-02")},
            },
            "pendingBars": [{"symbol": "SPY", "date": "2026-08-04", "status": "incomplete"}],
        }

        report = analyze_snapshot(snapshot, min_bars=3)

        self.assertEqual(report["summary"]["loadedCount"], 2)
        self.assertEqual(report["summary"]["coverageRate"], 1.0)
        self.assertEqual(report["providerDateRanges"]["yahoo-chart"]["latest"], "2026-08-03")
        self.assertEqual(report["providerDateRanges"]["binance-spot"]["latest"], "2026-08-04")
        self.assertTrue(any(item["check"] == "calendar_note" for item in report["notes"]))
        self.assertEqual(report["findings"], [])

    def test_flags_duplicate_dates_and_invalid_ohlc_as_high_findings(self):
        bars = _bars()
        bars[1]["date"] = bars[0]["date"]
        bars[2]["high"] = 98
        snapshot = {
            "metadata": {"requiredCount": 1, "loadedCount": 1, "missing": [], "pendingCount": 0},
            "instruments": {"SPY": {"symbol": "SPY", "provider": "yahoo-chart", "latestDate": "2026-08-03", "bars": bars}},
            "pendingBars": [],
        }

        report = analyze_snapshot(snapshot, min_bars=3)
        checks = {item["check"]: item for item in report["findings"]}

        self.assertEqual(checks["duplicate_bar_dates"]["severity"], "high")
        self.assertEqual(checks["invalid_ohlc_bounds"]["severity"], "high")


if __name__ == "__main__":
    unittest.main()
