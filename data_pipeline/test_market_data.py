import unittest

from StockTest.data_pipeline.market_data import (
    normalize_binance_klines,
    normalize_yahoo_chart,
    validate_market_snapshot,
)
from StockTest.data_pipeline.fetch_market_data import DEFAULT_INSTRUMENTS, build_snapshot


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
        validate_market_snapshot(snapshot)

    def test_default_universe_includes_sixty_industry_etfs(self):
        self.assertEqual(len(snapshot_industry_symbols()), 60)
        self.assertTrue(set(snapshot_industry_symbols()).issubset(DEFAULT_INSTRUMENTS))


def snapshot_industry_symbols():
    from StockTest.data_pipeline.fetch_market_data import INDUSTRY_SYMBOLS

    return INDUSTRY_SYMBOLS


if __name__ == "__main__":
    unittest.main()
