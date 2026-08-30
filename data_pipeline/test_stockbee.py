import unittest

from StockTest.data_pipeline.stockbee import normalize_stockbee_row, parse_stockbee_csv, validate_stockbee_rows


class StockbeeParserTests(unittest.TestCase):
    def test_preserves_full_market_monitor_columns(self):
        row = {
            "Date": "8/28/2026",
            "Number of stocks up 4% plus today": "84",
            "Number of stocks down 4% plus today": "382",
            "5 day ratio": "0.98",
            "10 day  ratio": "1.09",
            "Number of stocks up 25% plus in a quarter": "1379",
            "Number of stocks down 25% + in a quarter": "1105",
            "Number of stocks up 25% + in a month": "256",
            "Number of stocks down 25% + in a month": "90",
            "Number of stocks up 50% + in a month": "56",
            "Number of stocks down 50% + in a month": "21",
            "Number of stocks up 13% + in 34 days": "1687",
            "Number of stocks down 13% + in 34 days": "1469",
            " Worden Common stock universe": "6541",
            "T2108 ": "41.91",
            "S&P": "7,711.23",
        }
        normalized = normalize_stockbee_row(row)
        self.assertEqual(normalized["up25Quarter"], 1379)
        self.assertEqual(normalized["down25Month"], 90)
        self.assertEqual(normalized["up50Month"], 56)
        self.assertEqual(normalized["down13_34d"], 1469)
        self.assertEqual(normalized["wordenUniverse"], 6541)

    def test_parses_quoted_sp500_value(self):
        rows = parse_stockbee_csv(
            "Date,Number of stocks up 4% plus today,Number of stocks down 4% plus today,5 day ratio,10 day  ratio, Worden Common stock universe,T2108 ,S&P\n"
            "8/27/2026,298,145,1.76,1.30,6539,45.17,\"7,728.65\"\n"
        )
        self.assertEqual(normalize_stockbee_row(rows[0])["sp500"], 7728.65)

    def test_normalizes_required_breadth_fields(self):
        row = {
            "Date": "8/27/2026",
            "Number of stocks up 4% plus today": "298",
            "Number of stocks down 4% plus today": "145",
            "5 day ratio": "1.76",
            "10 day  ratio": "1.30",
            "T2108 ": "45.17",
            "S&P": "7,728.65",
        }
        self.assertEqual(
            normalize_stockbee_row(row),
            {
                "date": "2026-08-27",
                "up": 298,
                "down": 145,
                "ratio5": 1.76,
                "ratio10": 1.30,
                "t2108": 45.17,
                "sp500": 7728.65,
            },
        )

    def test_rejects_missing_required_column(self):
        with self.assertRaisesRegex(ValueError, "required"):
            validate_stockbee_rows([{"Date": "8/27/2026"}])


if __name__ == "__main__":
    unittest.main()
