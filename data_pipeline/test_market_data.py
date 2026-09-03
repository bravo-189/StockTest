import unittest

from StockTest.data_pipeline.market_data import (
    aggregate_intraday_bars,
    normalize_binance_intraday,
    normalize_binance_klines,
    normalize_yahoo_chart,
    normalize_yahoo_intraday,
    relative_strength_metrics,
    relative_strength_ratings,
    validate_market_snapshot,
)
from StockTest.data_pipeline.fetch_market_data import DEFAULT_INSTRUMENTS, _provider_url, build_snapshot
from StockTest.data_pipeline.fetch_market_data import _intraday_provider_url


def yahoo_payload(count=21):
    timestamps = [1_700_000_000 + index * 86_400 for index in range(count)]
    return {
        "chart": {
            "result": [
                {
                    "meta": {"symbol": "SPY", "regularMarketPrice": 105.0},
                    "timestamp": timestamps,
                    "indicators": {
                        "quote": [
                            {
                                "open": [100 + index for index in range(count)],
                                "high": [101 + index for index in range(count)],
                                "low": [99 + index for index in range(count)],
                                "close": [100.5 + index for index in range(count)],
                                "volume": [1_000_000 for _ in range(count)],
                            }
                        ]
                    },
                }
            ]
        }
    }


def yahoo_payload_with_pending_bar(count=21):
    payload = yahoo_payload(count)
    result = payload["chart"]["result"][0]
    result["timestamp"].append(result["timestamp"][-1] + 86_400)
    for field in ("open", "high", "low", "close", "volume"):
        result["indicators"]["quote"][0][field].append(None if field == "close" else result["indicators"]["quote"][0][field][-1])
    return payload


class MarketDataTests(unittest.TestCase):
    def test_relative_strength_metrics_compare_to_spy_on_shared_dates(self):
        asset = [{"date": f"2026-01-{index:02d}", "close": 100 + index, "open": 100 + index, "high": 101 + index, "low": 99 + index, "volume": 1} for index in range(1, 24)]
        benchmark = [{"date": f"2026-01-{index:02d}", "close": 100 + index * 0.5, "open": 100, "high": 101, "low": 99, "volume": 1} for index in range(1, 24)]
        metrics = relative_strength_metrics(asset, benchmark)
        self.assertEqual(set(metrics), {"rs1m", "rs3m", "rs6m", "rs12m"})
        expected = ((123 / 102) / (111.5 / 101) - 1) * 100
        self.assertAlmostEqual(metrics["rs1m"], round(expected, 2))
        self.assertIsNone(metrics["rs3m"])

    def test_relative_strength_ratings_rank_returns_within_universe(self):
        def bars(closes):
            return [{"date": f"2026-01-{index:02d}", "close": close, "open": close, "high": close, "low": close, "volume": 1} for index, close in enumerate(closes, start=1)]

        instruments = {
            "SPY": {"calendar": "us-equity", "bars": bars([100 + index for index in range(23)])},
            "AAA": {"calendar": "us-equity", "bars": bars([100 + index * 3 for index in range(23)])},
            "BBB": {"calendar": "us-equity", "bars": bars([100 - index for index in range(23)])},
        }
        ratings = relative_strength_ratings(instruments, ("SPY", "AAA", "BBB"))
        self.assertEqual(ratings["AAA"]["rs1m"], 99)
        self.assertEqual(ratings["SPY"]["rs1m"], 50)
        self.assertEqual(ratings["BBB"]["rs1m"], 1)

    def test_yahoo_history_window_covers_twelve_month_relative_strength(self):
        self.assertIn("range=2y", _provider_url(DEFAULT_INSTRUMENTS["SPY"]))

    def test_intraday_provider_urls_use_requested_intervals(self):
        self.assertIn("interval=5m", _intraday_provider_url(DEFAULT_INSTRUMENTS["SPY"]))
        self.assertIn("interval=2h", _intraday_provider_url(DEFAULT_INSTRUMENTS["BTC"]))

    def test_normalizes_yahoo_intraday_with_local_time_fields(self):
        payload = yahoo_payload(4)
        result = payload["chart"]["result"][0]
        result["timestamp"] = [1_709_218_200 + index * 600 for index in range(4)]
        instrument = normalize_yahoo_intraday(payload, "SPX", "https://example.test/10m", interval_minutes=10)
        self.assertEqual(instrument["interval"], "10m")
        self.assertEqual(len(instrument["bars"]), 4)
        self.assertIn("timestamp", instrument["bars"][0])
        self.assertIn("time", instrument["bars"][0])

    def test_normalizes_binance_intraday_and_validates_timestamp_order(self):
        rows = [[1_700_000_000_000 + index * 3_600_000, "100", "101", "99", str(100.5 + index), "10", 1_700_000_000_000 + (index + 1) * 3_600_000 - 1] for index in range(4)]
        instrument = normalize_binance_intraday(rows, "BTC", "https://example.test/1h")
        self.assertEqual(instrument["interval"], "1h")
        self.assertEqual(len(instrument["bars"]), 4)
        self.assertEqual(instrument["bars"][0]["time"], "22:13")

    def test_aggregates_yahoo_five_minute_bars_into_ten_minute_sessions(self):
        payload = yahoo_payload(4)
        result = payload["chart"]["result"][0]
        result["timestamp"] = [1_787_923_800 + index * 300 for index in range(4)]
        instrument = normalize_yahoo_intraday(payload, "SPX", "https://example.test/5m", interval_minutes=5)
        aggregated = aggregate_intraday_bars(instrument, target_minutes=10)
        self.assertEqual(aggregated["interval"], "10m")
        self.assertEqual(len(aggregated["bars"]), 2)
        self.assertEqual(aggregated["bars"][0]["open"], 100.0)
        self.assertEqual(aggregated["bars"][0]["close"], 101.5)

    def test_normalizes_yahoo_chart_to_sorted_ohlcv_bars(self):
        instrument = normalize_yahoo_chart(yahoo_payload(), "SPY", "https://query1.finance.yahoo.com/v8/finance/chart/SPY")
        self.assertEqual(instrument["symbol"], "SPY")
        self.assertEqual(len(instrument["bars"]), 21)
        self.assertLess(instrument["bars"][0]["date"], instrument["bars"][-1]["date"])
        self.assertEqual(instrument["bars"][-1]["close"], 120.5)
        self.assertEqual(instrument["provider"], "yahoo-chart")

    def test_normalizes_binance_klines_to_same_bar_contract(self):
        rows = [
            [1_700_000_000_000 + index * 86_400_000, "100", "101", "99", str(100.5 + index), "10", 0, "0", 1, "0", "0", "0"]
            for index in range(21)
        ]
        instrument = normalize_binance_klines(rows, "BTCUSDT", "https://api.binance.com/api/v3/klines")
        self.assertEqual(len(instrument["bars"]), 21)
        self.assertEqual(instrument["bars"][0]["open"], 100.0)
        self.assertEqual(instrument["provider"], "binance-spot")

    def test_preserves_incomplete_latest_yahoo_bar_as_pending_metadata(self):
        instrument = normalize_yahoo_chart(yahoo_payload_with_pending_bar(), "SPY", "https://example.test/chart")
        self.assertEqual(len(instrument["bars"]), 21)
        self.assertEqual(instrument["latestDate"], instrument["bars"][-1]["date"])
        self.assertEqual(instrument["pendingBar"]["status"], "incomplete")
        self.assertIsNone(instrument["pendingBar"]["close"])

    def test_rejects_invalid_or_short_market_snapshot(self):
        instrument = normalize_yahoo_chart(yahoo_payload(20), "SPY", "https://example.test/chart")
        with self.assertRaises(ValueError):
            validate_market_snapshot({"instruments": {"SPY": instrument}}, min_bars=21)

        invalid = normalize_yahoo_chart(yahoo_payload(), "SPY", "https://example.test/chart")
        invalid["bars"][0]["high"] = 98.0
        with self.assertRaises(ValueError):
            validate_market_snapshot({"instruments": {"SPY": invalid}}, min_bars=21)

    def test_build_snapshot_covers_indexes_sectors_and_btc(self):
        btc_rows = [
            [1_700_000_000_000 + index * 86_400_000, str(100 + index), str(101 + index), str(99 + index), str(100.5 + index), "10", 0, "0", 1, "0", "0", "0"]
            for index in range(26)
        ]

        def fake_fetch(url):
            return btc_rows if "api.binance.com" in url else yahoo_payload()

        snapshot = build_snapshot(fetcher=fake_fetch, fetched_at="2026-08-29T10:00:00Z")
        self.assertEqual(set(("SPX", "NDX", "DJI", "RUT", "BTC")), set(snapshot["instruments"]).intersection(("SPX", "NDX", "DJI", "RUT", "BTC")))
        self.assertEqual(len(snapshot["instruments"]), len(DEFAULT_INSTRUMENTS))
        self.assertEqual(snapshot["metadata"]["sourceStatus"], "loaded")
        self.assertEqual(snapshot["metadata"]["comparisonDate"], "2023-12-04")
        self.assertEqual(snapshot["metadata"]["calendarLatestDates"]["us-equity"], "2023-12-04")
        self.assertEqual(snapshot["metadata"]["calendarLatestDates"]["crypto-24x7"], "2023-12-09")
        self.assertEqual(snapshot["instruments"]["BTC"]["calendar"], "crypto-24x7")
        self.assertEqual(snapshot["instruments"]["SPX"]["calendar"], "us-equity")
        self.assertIn("relativeStrengthRating", snapshot["instruments"]["SPY"])
        self.assertIn("sector", snapshot["instruments"]["SPY"]["relativeStrengthRating"])
        self.assertEqual(snapshot["metadata"]["relativeStrength"]["scale"], "1-99")
        validate_market_snapshot(snapshot)

    def test_build_snapshot_can_attach_real_intraday_contract(self):
        daily_btc_rows = [[1_700_000_000_000 + index * 86_400_000, str(100 + index), str(101 + index), str(99 + index), str(100.5 + index), "10", 0, "0", 1, "0", "0", "0"] for index in range(26)]
        intraday_btc_rows = [[1_700_000_000_000 + index * 7_200_000, str(100 + index), str(101 + index), str(99 + index), str(100.5 + index), "10", 1_700_000_000_000 + (index + 1) * 7_200_000 - 1] for index in range(26)]

        intraday_payload = yahoo_payload(4)
        intraday_payload["chart"]["result"][0]["timestamp"] = [1_787_923_800 + index * 300 for index in range(4)]

        def fake_fetch(url):
            if "api.binance.com" in url:
                return intraday_btc_rows if "interval=2h" in url else daily_btc_rows
            return intraday_payload if "interval=5m" in url else yahoo_payload()

        snapshot = build_snapshot(fetcher=fake_fetch, include_intraday=True, fetched_at="2026-08-29T10:00:00Z")
        self.assertEqual(snapshot["metadata"]["intraday"]["sourceStatus"], "loaded")
        self.assertIn("intradayBars", snapshot["instruments"]["SPX"])
        self.assertIn("intradayBars", snapshot["instruments"]["BTC"])
        self.assertEqual(snapshot["instruments"]["SPX"]["intraday"]["interval"], "5m")
        self.assertEqual(len(snapshot["instruments"]["SPX"]["intradayBars"]), 4)
        self.assertEqual(snapshot["instruments"]["BTC"]["intraday"]["interval"], "2h")

    def test_validate_market_snapshot_checks_attached_intraday_bars(self):
        instrument = normalize_yahoo_chart(yahoo_payload(), "SPY", "https://example.test/chart")
        instrument["intradayBars"] = [{
            "timestamp": "2026-08-28T13:30:00Z",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 10.0,
        }]
        validate_market_snapshot({"instruments": {"SPY": instrument}})
        instrument["intradayBars"][0]["high"] = 98.0
        with self.assertRaises(ValueError):
            validate_market_snapshot({"instruments": {"SPY": instrument}})

    def test_default_universe_includes_sixty_industry_etfs(self):
        self.assertEqual(len(snapshot_industry_symbols()), 60)
        self.assertTrue(set(snapshot_industry_symbols()).issubset(DEFAULT_INSTRUMENTS))


def snapshot_industry_symbols():
    from StockTest.data_pipeline.fetch_market_data import INDUSTRY_SYMBOLS

    return INDUSTRY_SYMBOLS


if __name__ == "__main__":
    unittest.main()
