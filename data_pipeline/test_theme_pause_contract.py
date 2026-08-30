import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ThemePauseContractTests(unittest.TestCase):
    def setUp(self):
        self.page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.app = (ROOT / "app.js").read_text(encoding="utf-8")

    def test_theme_module_is_not_an_active_navigation_or_page_section(self):
        self.assertNotIn('data-target="themes"', self.page)
        self.assertNotIn('id="themes"', self.page)
        self.assertNotIn('id="theme-grid"', self.page)
        self.assertNotIn("主题候选集", self.page)
        self.assertNotIn("代码、名称或主题", self.page)

    def test_theme_catalog_is_preserved_but_not_loaded_by_active_page(self):
        self.assertTrue((ROOT / "data" / "theme_catalog.json").exists())
        self.assertTrue((ROOT / "data_pipeline" / "theme_agent.py").exists())
        self.assertNotIn("data/theme_catalog.json", self.app)
        self.assertNotIn("hydrateThemeCatalog()", self.app)

    def test_core_sections_remain_reachable(self):
        for target in ("overview", "sectors", "industries", "breadth"):
            self.assertIn(f'data-target="{target}"', self.page)


if __name__ == "__main__":
    unittest.main()
