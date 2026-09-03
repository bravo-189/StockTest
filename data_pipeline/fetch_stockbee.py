"""Fetch the public Stockbee Market Monitor export into a local JSON snapshot."""

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

try:
    from .stockbee import STOCKBEE_SCHEMA, normalize_stockbee_rows, parse_stockbee_csv
except ImportError:  # pragma: no cover - supports direct CLI execution
    from stockbee import STOCKBEE_SCHEMA, normalize_stockbee_rows, parse_stockbee_csv


DEFAULT_URL = "https://docs.google.com/spreadsheets/d/0Am_cU8NLIU20dEhiQnVHN3Nnc3B1S3J6eGhKZFo0N3c/export?format=csv"
SOURCE_PAGE_URL = "https://stockbee.blogspot.com/p/mm.html"
STOCKBEE_LOOKBACK_DAYS = 183


def fetch_csv(url, timeout=20):
    request = Request(url, headers={"User-Agent": "StockTest data pipeline/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8-sig")


def trim_stockbee_rows(rows, lookback_days=STOCKBEE_LOOKBACK_DAYS):
    """Keep the latest six calendar months anchored to the source latest date."""
    ordered = sorted(rows, key=lambda row: row["date"], reverse=True)
    if not ordered:
        return []
    latest = date.fromisoformat(ordered[0]["date"])
    cutoff = latest - timedelta(days=lookback_days)
    return [row for row in ordered if date.fromisoformat(row["date"]) >= cutoff]


def build_snapshot(csv_text, source_url, fetched_at):
    rows = trim_stockbee_rows(normalize_stockbee_rows(parse_stockbee_csv(csv_text)))
    return {
        "metadata": {
            "rowCount": len(rows),
            "latestDate": rows[0]["date"] if rows else None,
            "sourceStatus": "loaded",
            "fetchedAt": fetched_at,
            "historyWindow": "6mo",
            "lookbackDays": STOCKBEE_LOOKBACK_DAYS,
        },
        "source": {"name": "Stockbee Market Monitor", "pageUrl": SOURCE_PAGE_URL, "url": source_url, "format": "csv"},
        "schema": STOCKBEE_SCHEMA,
        "rows": rows,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch Stockbee Market Monitor data")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args(argv)

    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    snapshot = build_snapshot(fetch_csv(args.url), args.url, fetched_at)
    if args.limit > 0:
        snapshot["rows"] = snapshot["rows"][: args.limit]
        snapshot["metadata"]["rowCount"] = len(snapshot["rows"])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"loaded {snapshot['metadata']['rowCount']} rows through {snapshot['metadata']['latestDate']} -> {output}")


if __name__ == "__main__":
    main()
