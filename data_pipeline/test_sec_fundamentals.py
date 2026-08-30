import unittest

from StockTest.data_pipeline.sec_fundamentals import build_fundamental_record


def annual(value, start, end, accn):
    return {"val": value, "start": start, "end": end, "form": "10-K", "fp": "FY", "filed": end[:4] + "-12-31", "accn": accn}


def fixture_with_revenue_and_net_income():
    return {
        "entityName": "Example Corp",
        "facts": {
            "us-gaap": {
                "Revenues": {"units": {"USD": [annual(100, "2024-01-01", "2024-12-31", "rev-2024"), annual(110, "2025-01-01", "2025-12-31", "rev-2025")]}},
                "NetIncomeLoss": {"units": {"USD": [annual(20, "2025-01-01", "2025-12-31", "ni-2025")]}},
            }
        },
    }


class SecFundamentalTests(unittest.TestCase):
    def test_prefers_newest_period_across_revenue_fallback_tags(self):
        payload = {
            "entityName": "Example Corp",
            "facts": {"us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [annual(27, "2021-01-01", "2022-01-30", "old")]}},
                "Revenues": {"units": {"USD": [annual(215, "2025-01-27", "2026-01-25", "new")]}},
            }},
        }
        record = build_fundamental_record("TEST", "0000000000", payload)
        self.assertEqual(record["values"]["revenue"]["value"], 215)
        self.assertEqual(record["values"]["revenue"]["source"]["tag"], "Revenues")

    def test_selects_latest_annual_value_and_provenance(self):
        record = build_fundamental_record("TEST", "0000000000", fixture_with_revenue_and_net_income())
        self.assertEqual(record["values"]["revenue"]["value"], 110)
        self.assertEqual(record["values"]["revenue"]["source"]["form"], "10-K")
        self.assertEqual(record["values"]["revenue"]["source"]["accn"], "rev-2025")

    def test_derives_margin_and_growth_from_annual_values(self):
        record = build_fundamental_record("TEST", "0000000000", fixture_with_revenue_and_net_income())
        self.assertAlmostEqual(record["metrics"]["netMargin"], 20 / 110, places=5)
        self.assertAlmostEqual(record["metrics"]["revenueGrowthYoY"], 0.1, places=5)

    def test_missing_fact_is_explicit(self):
        record = build_fundamental_record("TEST", "0000000000", {"entityName": "Example", "facts": {"us-gaap": {}}})
        self.assertIsNone(record["values"]["cash"]["value"])
        self.assertEqual(record["values"]["cash"]["status"], "missing")

    def test_derives_liabilities_from_assets_less_equity_when_tag_is_missing(self):
        payload = {"entityName": "Example Corp", "facts": {"us-gaap": {
            "Assets": {"units": {"USD": [annual(100, None, "2025-12-31", "assets")]}},
            "StockholdersEquity": {"units": {"USD": [annual(40, None, "2025-12-31", "equity")]}},
        }}}
        record = build_fundamental_record("TEST", "0000000000", payload)
        self.assertEqual(record["values"]["liabilities"]["value"], 60)
        self.assertEqual(record["values"]["liabilities"]["status"], "derived")


if __name__ == "__main__":
    unittest.main()
