import unittest

from StockTest.data_pipeline.theme_agent import build_agent_request, validate_agent_output


class ThemeAgentContractTests(unittest.TestCase):
    def test_request_contains_sixty_etfs_and_investor_prompt(self):
        catalog = {"industryUniverse": [["SPY", "大盘股", "标普 500"]], "themes": []}
        request = build_agent_request(catalog, {"SPY": {"d20": 1.2}}, "2026-08-27")
        self.assertEqual(request["asOf"], "2026-08-27")
        self.assertIn("对冲基金经理", request["systemPrompt"])
        self.assertEqual(request["etfCount"], 1)
        self.assertEqual(request["etfs"][0]["ticker"], "SPY")

    def test_output_requires_twenty_ranked_themes_with_sources(self):
        output = {
            "asOf": "2026-08-27",
            "themes": [
                {"rank": 1, "themeId": "theme-ai", "score": 82, "sourceUrls": ["https://example.test/source"], "leadingStocks": ["NVDA"], "catalysts": ["capex"]}
            ],
        }
        with self.assertRaises(ValueError):
            validate_agent_output(output, expected_count=20)


if __name__ == "__main__":
    unittest.main()
