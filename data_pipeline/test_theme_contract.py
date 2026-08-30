import json
import unittest
from pathlib import Path


class ThemeContractTests(unittest.TestCase):
    def test_theme_contract_has_no_news_and_keeps_research_inputs_out_of_ui(self):
        app = Path("StockTest/app.js").read_text(encoding="utf-8")
        page = Path("StockTest/index.html").read_text(encoding="utf-8")
        catalog = json.loads(Path("StockTest/data/theme_catalog.json").read_text(encoding="utf-8"))
        self.assertNotIn("newsHeat", app)
        self.assertNotIn("NEWS", app)
        self.assertNotIn("新闻热度", page)
        self.assertNotIn("基本面代理", page)
        self.assertNotIn("fundamentalsAgent", app)
        self.assertNotIn("theme_catalog.json", app)
        self.assertIn("待研究", app)
        self.assertTrue(all("fundamentals" in theme["researchInputs"] for theme in catalog["themes"]))


if __name__ == "__main__":
    unittest.main()
