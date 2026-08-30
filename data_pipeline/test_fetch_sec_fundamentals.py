import unittest
import gzip
from unittest.mock import patch

from StockTest.data_pipeline.fetch_sec_fundamentals import build_snapshot, fetch_companyfacts


class SecFetchTests(unittest.TestCase):
    @patch("StockTest.data_pipeline.fetch_sec_fundamentals.urlopen")
    def test_decompresses_gzip_sec_response(self, urlopen_mock):
        class Response:
            headers = {"Content-Encoding": "gzip"}

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return gzip.compress(b'{"entityName":"Example","facts":{}}')

        urlopen_mock.return_value = Response()
        self.assertEqual(fetch_companyfacts("0000000000")["entityName"], "Example")

    @patch("StockTest.data_pipeline.fetch_sec_fundamentals.fetch_companyfacts")
    def test_snapshot_has_source_and_company_records(self, fetch_mock):
        fetch_mock.return_value = {"entityName": "Example", "facts": {"us-gaap": {}}}
        snapshot = build_snapshot(["MSFT"])
        self.assertEqual(snapshot["source"]["provider"], "SEC EDGAR Company Facts")
        self.assertEqual(snapshot["metadata"]["tickerCount"], 1)
        self.assertEqual(snapshot["records"][0]["ticker"], "MSFT")
        fetch_mock.assert_called_once_with("0000789019")


if __name__ == "__main__":
    unittest.main()
