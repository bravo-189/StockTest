"""Validate the curated industry ETF to theme taxonomy."""

import json
from pathlib import Path


REQUIRED_INPUTS = {"momentum", "breadth", "catalysts", "fundamentals", "narrative"}


def load_catalog(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_catalog(catalog: dict) -> None:
    themes = catalog.get("themes")
    universe = catalog.get("industryUniverse")
    if not isinstance(themes, list) or len(themes) != 20:
        raise ValueError("theme catalog must contain exactly 20 themes")
    if not isinstance(universe, list) or len(universe) != 60:
        raise ValueError("industry universe must contain exactly 60 ETFs")

    universe_tickers = [entry[0] for entry in universe]
    if len(set(universe_tickers)) != len(universe_tickers):
        raise ValueError("industry universe contains duplicate ETF tickers")

    theme_ids = [theme.get("id") for theme in themes]
    if len(set(theme_ids)) != len(theme_ids):
        raise ValueError("theme IDs must be unique")

    members = [ticker for theme in themes for ticker in theme.get("memberEtfs", [])]
    if len(members) != 60 or len(set(members)) != 60:
        raise ValueError("theme members must cover 60 unique ETFs exactly once")
    if set(members) != set(universe_tickers):
        raise ValueError("theme members must match the industry universe")

    for theme in themes:
        if not theme.get("memberEtfs"):
            raise ValueError(f"theme {theme.get('id')} has no ETF members")
        if theme.get("analysisStatus") not in {"pending", "ready"}:
            raise ValueError(f"theme {theme.get('id')} has invalid analysis status")
        if set(theme.get("researchInputs", [])) != REQUIRED_INPUTS:
            raise ValueError(f"theme {theme.get('id')} has an incomplete research contract")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate the StockTest theme taxonomy")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    validate_catalog(load_catalog(args.path))
    print("PASS: 20 themes cover 60 unique industry ETFs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
