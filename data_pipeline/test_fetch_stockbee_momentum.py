import unittest

from StockTest.data_pipeline.fetch_stockbee_momentum import (
    SHEET_URL,
    build_snapshot,
    enrich_stockbee_rows,
    parse_stock_classification_html,
    parse_stockanalysis_etf_html,
    parse_stockbee_momentum_csv,
)


class StockbeeMomentumTests(unittest.TestCase):
    def test_parser_uses_newest_date_column_and_first_50_unique_symbols(self):
        csv_text = "2026-08-29,08/28/2026\nSix Month,Six Month\nAAA,BBB\nAAA,CCC\nDDD,CCC\n"
        parsed = parse_stockbee_momentum_csv(csv_text, limit=50)
        self.assertEqual(parsed["latestDate"], "2026-08-28")
        self.assertEqual([row["ticker"] for row in parsed["rows"]], ["BBB", "CCC"])

    def test_parser_keeps_first_symbol_when_sheet_has_no_descriptor_row(self):
        csv_text = "08/25/2026,08/24/2026\nDAIC,USDE\nRFAI,ZSTK\nZSTK,XHG\n"
        parsed = parse_stockbee_momentum_csv(csv_text, limit=50)
        self.assertEqual(parsed["latestDate"], "2026-08-25")
        self.assertEqual([row["ticker"] for row in parsed["rows"]], ["DAIC", "RFAI", "ZSTK"])

    def test_source_points_to_stockbee_50_tab(self):
        self.assertIn("gid=1499398020", SHEET_URL)

    def test_snapshot_marks_historical_public_sheet_as_stale(self):
        snapshot = build_snapshot("1/3/2017\nSix Month\nAMD\n", fetched_at="2026-08-31T00:00:00Z")
        self.assertEqual(snapshot["metadata"]["latestDate"], "2017-01-03")
        self.assertTrue(snapshot["metadata"]["isStale"])
        self.assertEqual(snapshot["rows"][0]["ticker"], "AMD")

    def test_classification_parser_reads_stockanalysis_profile(self):
        html = 'sector:{value:"Healthcare",url:"stocks/sector/healthcare"},industry:{value:"Biotechnology",url:"stocks/industry/biotechnology"}'
        parsed = parse_stock_classification_html(html, "MRNA")
        self.assertEqual(parsed["sector"], "Healthcare")
        self.assertEqual(parsed["industry"], "Biotechnology")
        self.assertEqual(parsed["classificationStatus"], "verified")

    def test_enrichment_uses_fetcher_and_cache_without_fabricating_values(self):
        calls = []

        def fetcher(ticker):
            calls.append(ticker)
            return {"ticker": ticker, "sector": "Technology", "industry": "Semiconductors", "classificationStatus": "verified"}

        rows = [{"rank": 1, "ticker": "AAA"}, {"rank": 2, "ticker": "BBB"}]
        enriched = enrich_stockbee_rows(rows, fetcher=fetcher, cached={"AAA": {"ticker": "AAA", "sector": "Healthcare", "industry": "Biotech", "classificationStatus": "verified"}})
        self.assertEqual(calls, ["BBB"])
        self.assertEqual(enriched[0]["sector"], "Healthcare")
        self.assertEqual(enriched[1]["industry"], "Semiconductors")

    def test_etf_classification_parser_reads_asset_class_and_category(self):
        html = '<span class="block font-semibold">Asset Class</span> <span>Currency</span><span class="block font-semibold">Category</span> <span>Digital Assets</span>'
        parsed = parse_stockanalysis_etf_html(html, "BITX")
        self.assertEqual(parsed["sector"], "Currency")
        self.assertEqual(parsed["industry"], "Digital Assets")
        self.assertEqual(parsed["classificationStatus"], "verified")


if __name__ == "__main__":
    unittest.main()
