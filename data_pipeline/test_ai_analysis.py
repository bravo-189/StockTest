import unittest
from pathlib import Path

from StockTest.data_pipeline.ai_analysis import AIProviderUnavailable, analyze_with_provider, build_analysis_payload, load_source_policy


class AIAnalysisContractTests(unittest.TestCase):
    def test_policy_is_disabled_by_default(self):
        policy = load_source_policy(Path("StockTest/data/analysis_sources.json"))
        self.assertFalse(policy["policy"]["aiEnabled"])
        self.assertFalse(policy["policy"]["newsEnabled"])
        self.assertTrue(all(item["enabled"] is False for item in policy["sources"]))

    def test_payload_requires_dated_evidence_fields(self):
        payload = build_analysis_payload({"market": {"asOf": "2026-09-01"}}, [{"sourceId": "reuters", "publishedAt": "2026-09-01T00:00:00Z"}])
        self.assertEqual(payload["outputRequirements"][-1], "invalidation")
        self.assertEqual(payload["news"][0]["sourceId"], "reuters")

    def test_no_provider_never_makes_an_api_call(self):
        with self.assertRaises(AIProviderUnavailable):
            analyze_with_provider({"x": 1})


if __name__ == "__main__":
    unittest.main()
