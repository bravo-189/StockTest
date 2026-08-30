import unittest

from StockTest.data_pipeline.validate_fundamentals import validate_snapshot


def fixture_valid_snapshot():
    return {
        "metadata": {"requestedTickerCount": 1, "tickerCount": 1},
        "source": {"provider": "SEC EDGAR Company Facts"},
        "records": [{
            "ticker": "MSFT",
            "latestAnnualEnd": "2025-06-30",
            "status": "complete",
            "values": {
                "revenue": {"value": 100, "status": "ok", "source": {"accn": "a"}},
                "netIncome": {"value": 20, "status": "ok", "source": {"accn": "b"}},
                "assets": {"value": 200, "status": "ok", "source": {"accn": "c"}},
                "liabilities": {"value": 100, "status": "ok", "source": {"accn": "d"}},
                "equity": {"value": 100, "status": "ok", "source": {"accn": "e"}},
                "cash": {"value": 30, "status": "ok", "source": {"accn": "f"}},
                "dilutedEps": {"value": 2, "status": "ok", "source": {"accn": "g"}},
            },
            "metrics": {"netMargin": 0.2, "revenueGrowthYoY": 0.1},
        }],
        "errors": [],
    }


class FundamentalQualityTests(unittest.TestCase):
    def test_valid_snapshot_has_no_high_severity_findings(self):
        findings = validate_snapshot(fixture_valid_snapshot())
        self.assertFalse([item for item in findings if item["severity"] in {"high", "critical"}])

    def test_duplicate_ticker_is_high_severity(self):
        snapshot = fixture_valid_snapshot()
        snapshot["records"].append(snapshot["records"][0].copy())
        findings = validate_snapshot(snapshot)
        self.assertTrue(any(item["severity"] == "high" and item["check"] == "unique_ticker" for item in findings))


if __name__ == "__main__":
    unittest.main()
