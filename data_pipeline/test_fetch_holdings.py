import unittest

from StockTest.data_pipeline.fetch_holdings import (
    fetch_holdings_snapshot,
    parse_ishares_holdings_csv,
    parse_stockanalysis_holdings,
    parse_uscfinvestments_holdings,
    normalize_holding_symbol,
)
from StockTest.data_pipeline.market_data import trend_vs_moving_average


def holdings_fixture():
    rows = ",".join(
        f'{{no:{index},n:"Company {index}",s:"$T{index}",as:"{10-index/2:.2f}%",sh:"{index},000"}}'
        for index in range(1, 11)
    )
    return f'<script>holdings:[{rows}],asset_allocation:[];lastUpdated:"Aug 19, 2026"</script>'


class HoldingsTests(unittest.TestCase):
    def test_parses_ibit_issuer_csv_with_single_bitcoin_position(self):
        csv_text = """iShares Bitcoin Trust ETF\nFund Holdings as of,"Aug 28, 2026"\n\nTicker,Name,Sector,Asset Class,Market Value,Weight (%),Notional Value,Quantity\nBTC,BITCOIN,-,Alternative,100,100.00,100,1\nUSD,USD CASH,-,Cash,1,0.00,1,1\n"""
        result = parse_ishares_holdings_csv(csv_text)
        self.assertEqual(result["provider"], "iShares issuer holdings CSV")
        self.assertEqual(result["asOf"], "Aug 28, 2026")
        self.assertEqual(result["holdings"][0]["ticker"], "BTC")
        self.assertEqual(result["holdings"][0]["weight"], 100.0)
        self.assertEqual(result["holdings"][0]["weightUnit"], "percent")
        self.assertEqual(result["totalHoldings"], 2)

    def test_parses_uso_issuer_api_rows_as_complete_top_ten(self):
        payload = [{"identifiertodisplay": "CLV6", "name": "WTI CRUDE FUTURE", "weight": 0.81, "shares": 10, "asofdate": "2026-08-31", "possessionname": "Hold"}]
        result = parse_uscfinvestments_holdings(payload)
        self.assertEqual(result["provider"], "USCF issuer holdings API")
        self.assertEqual(result["holdings"][0]["ticker"], "CLV6")
        self.assertEqual(result["holdings"][0]["weight"], 81.0)
        self.assertEqual(result["weightUnit"], "percent")
        self.assertEqual(result["totalHoldings"], 1)
        self.assertEqual(result["coverageStatus"], "complete")

    def test_source_overrides_replace_stockanalysis_gaps(self):
        ibit_csv = """Fund Holdings as of,Aug 28, 2026\nTicker,Name,Weight (%),Quantity\nBTC,BITCOIN,100.00,1\n"""
        uso_payload = [{"identifiertodisplay": "CLV6", "name": "WTI CRUDE FUTURE", "weight": 0.81, "shares": 10, "asofdate": "2026-08-31", "possessionname": "Hold"}]
        result = fetch_holdings_snapshot(
            ("IBIT", "USO"),
            fetcher=lambda _url: "",
            source_fetchers={"IBIT": lambda _url: ibit_csv, "USO": lambda _url: uso_payload},
        )
        self.assertEqual(result["metadata"]["loadedCount"], 2)
        self.assertFalse(result["metadata"]["missing"])
        self.assertEqual(result["holdings"]["IBIT"]["holdings"][0]["ticker"], "BTC")
        self.assertEqual(result["holdings"]["USO"]["holdings"][0]["ticker"], "CLV6")
    def test_parses_top_ten_with_source_and_as_of_metadata(self):
        result = parse_stockanalysis_holdings(holdings_fixture(), "TEST", "https://example.test/holdings")
        self.assertEqual(len(result["holdings"]), 10)
        self.assertEqual(result["holdings"][0]["ticker"], "T1")
        self.assertEqual(result["holdings"][0]["sourceTicker"], "$T1")
        self.assertEqual(result["asOf"], "Aug 19, 2026")
        self.assertEqual(result["status"], "loaded")

    def test_preserves_source_rows_without_symbol_and_venue_qualified_symbols(self):
        rows = ['{no:1,n:"Unnamed asset",as:"6.01%",sh:"10"}', '{no:2,n:"Rio Tinto",s:"$RIO",as:"5.00%",sh:"20"}', '{no:3,n:"Rio Tinto ASX",s:"!asx/RIO",as:"4.00%",sh:"30"}']
        rows.extend(f'{{no:{index},n:"Company {index}",s:"$T{index}",as:"1.00%",sh:"1"}}' for index in range(4, 11))
        html = f'<script>holdings:[{",".join(rows)}],asset_allocation:[]</script>'
        result = parse_stockanalysis_holdings(html, "TEST")
        self.assertEqual(result["holdings"][0]["ticker"], "")
        self.assertEqual(result["holdings"][2]["ticker"], "ASX:RIO")
        self.assertEqual(normalize_holding_symbol("!asx/RIO"), "ASX:RIO")

    def test_snapshot_exposes_missing_without_substituting_other_etf(self):
        result = fetch_holdings_snapshot(("AAA", "BBB"), fetcher=lambda url: holdings_fixture() if "aaa" in url else "")
        self.assertEqual(result["metadata"]["loadedCount"], 1)
        self.assertEqual(result["metadata"]["sourceStatus"], "partial")
        self.assertIn("BBB", {item["ticker"] for item in result["metadata"]["missing"]})
        self.assertNotIn("BBB", result["holdings"])

    def test_ma150_trend_uses_latest_confirmed_close(self):
        bars = [{"close": 100 + index} for index in range(150)]
        result = trend_vs_moving_average(bars)
        self.assertEqual(result["trend"], "上涨")
        self.assertIsNotNone(result["ma"])
        self.assertEqual(trend_vs_moving_average(bars[:20])["trend"], "数据不足")


if __name__ == "__main__":
    unittest.main()
