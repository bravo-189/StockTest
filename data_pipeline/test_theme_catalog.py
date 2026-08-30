import json
import unittest
from pathlib import Path

from StockTest.data_pipeline.theme_catalog import load_catalog, validate_catalog


ROOT = Path(__file__).resolve().parents[1]


class ThemeCatalogTests(unittest.TestCase):
    def test_catalog_has_twenty_themes_and_sixty_unique_etfs(self):
        catalog = load_catalog(ROOT / "data" / "theme_catalog.json")
        validate_catalog(catalog)
        themes = catalog["themes"]
        members = [ticker for theme in themes for ticker in theme["memberEtfs"]]
        self.assertEqual(len(themes), 20)
        self.assertEqual(len(members), 60)
        self.assertEqual(len(set(members)), 60)

    def test_catalog_has_agent_ready_research_contract(self):
        catalog = load_catalog(ROOT / "data" / "theme_catalog.json")
        for theme in catalog["themes"]:
            self.assertRegex(theme["id"], r"^theme-")
            self.assertTrue(theme["memberEtfs"])
            self.assertIn("analysisStatus", theme)
            self.assertIn(theme["analysisStatus"], {"pending", "ready"})
            self.assertIn("researchInputs", theme)
            self.assertEqual(set(theme["researchInputs"]), {"momentum", "breadth", "catalysts", "fundamentals", "narrative"})

    def test_catalog_matches_the_industry_universe(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        catalog = load_catalog(ROOT / "data" / "theme_catalog.json")
        expected = {ticker for ticker, _, _ in catalog["industryUniverse"]}
        for ticker in expected:
            self.assertIn(f'["{ticker}"', app)


if __name__ == "__main__":
    unittest.main()
