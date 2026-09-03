"""Provider-neutral AI analysis contract; no network calls are made yet."""

import json
from pathlib import Path


class AIProviderUnavailable(RuntimeError):
    """Raised when an AI provider is intentionally disabled or lacks credentials."""


def load_source_policy(path: Path) -> dict:
    """Load the local source policy without enabling any provider."""
    policy = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(policy.get("sources"), list):
        raise ValueError("analysis source policy must contain a sources list")
    return policy


def build_analysis_payload(local_snapshots: dict, news_items: list | None = None) -> dict:
    """Build the future AI input envelope from local, dated evidence only."""
    return {
        "schemaVersion": "1.0",
        "localSnapshots": local_snapshots,
        "news": news_items or [],
        "outputRequirements": ["claims", "evidence", "asOf", "confidence", "invalidation"],
    }


def analyze_with_provider(payload: dict, provider=None) -> dict:
    """Call an injected provider later; default behavior is safe, explicit no-op."""
    if provider is None:
        raise AIProviderUnavailable("AI provider is disabled; no API call was made")
    result = provider(payload)
    if not isinstance(result, dict):
        raise ValueError("AI provider must return a JSON object")
    return result
