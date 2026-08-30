"""Refresh StockTest local snapshots once or on a fixed local interval."""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from .fetch_market_data import build_snapshot
    from .fetch_stockbee import DEFAULT_URL, fetch_csv, build_snapshot as build_stockbee_snapshot
except ImportError:  # pragma: no cover - supports direct CLI execution
    from fetch_market_data import build_snapshot
    from fetch_stockbee import DEFAULT_URL, fetch_csv, build_snapshot as build_stockbee_snapshot


def _timestamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class RefreshSourceError(RuntimeError):
    def __init__(self, source, message):
        super().__init__(message)
        self.source = source


def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}


def refresh_once(output_dir, market_builder=build_snapshot, stockbee_csv=None, fetched_at=None):
    output_dir = Path(output_dir)
    fetched_at = fetched_at or _timestamp()
    try:
        market_snapshot = market_builder()
    except Exception as exc:
        raise RefreshSourceError("market", str(exc)) from exc
    try:
        csv_text = stockbee_csv if stockbee_csv is not None else fetch_csv(DEFAULT_URL)
        stockbee_snapshot = build_stockbee_snapshot(csv_text, DEFAULT_URL, fetched_at)
    except Exception as exc:
        raise RefreshSourceError("stockbee", str(exc)) from exc
    stockbee_snapshot["rows"] = stockbee_snapshot["rows"][:20]
    stockbee_snapshot["metadata"]["rowCount"] = len(stockbee_snapshot["rows"])
    stockbee_snapshot["metadata"]["latestDate"] = stockbee_snapshot["rows"][0]["date"] if stockbee_snapshot["rows"] else None
    _write_json(output_dir / "market_snapshot.json", market_snapshot)
    _write_json(output_dir / "stockbee.json", stockbee_snapshot)
    return {"market": market_snapshot, "stockbee": stockbee_snapshot}


def run_refresh_attempt(output_dir, market_builder=build_snapshot, stockbee_csv=None, attempted_at=None):
    """Refresh atomically and always persist an inspectable attempt status."""
    output_dir = Path(output_dir)
    attempted_at = attempted_at or _timestamp()
    status_path = output_dir / "refresh_status.json"
    previous = _read_json(status_path)
    try:
        result = refresh_once(output_dir, market_builder=market_builder, stockbee_csv=stockbee_csv, fetched_at=attempted_at)
        market_meta = result["market"].get("metadata") or {}
        stockbee_meta = result["stockbee"].get("metadata") or {}
        missing = market_meta.get("missing") or []
        status_name = "partial" if market_meta.get("sourceStatus") == "partial" or missing else "ok"
        status = {
            "schemaVersion": "1.0",
            "status": status_name,
            "attemptedAt": attempted_at,
            "lastCompletedAt": attempted_at,
            "lastFullSuccessAt": attempted_at if status_name == "ok" else previous.get("lastFullSuccessAt"),
            "sources": {
                "market": {
                    "status": market_meta.get("sourceStatus", "unknown"),
                    "latestDate": market_meta.get("latestDate"),
                    "loadedCount": market_meta.get("loadedCount"),
                    "requiredCount": market_meta.get("requiredCount"),
                    "missingCount": len(missing),
                },
                "stockbee": {
                    "status": stockbee_meta.get("sourceStatus", "unknown"),
                    "latestDate": stockbee_meta.get("latestDate"),
                    "rowCount": stockbee_meta.get("rowCount"),
                },
            },
            "errors": [],
        }
    except Exception as exc:
        source = exc.source if isinstance(exc, RefreshSourceError) else "refresh"
        status = {
            "schemaVersion": "1.0",
            "status": "failed",
            "attemptedAt": attempted_at,
            "lastCompletedAt": previous.get("lastCompletedAt"),
            "lastFullSuccessAt": previous.get("lastFullSuccessAt"),
            "sources": {source: {"status": "failed"}},
            "errors": [{"source": source, "message": str(exc)}],
        }
    _write_json(status_path, status)
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description="Refresh StockTest local data snapshots")
    parser.add_argument("--output-dir", default="data")
    parser.add_argument("--interval-minutes", type=float, default=60)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    while True:
        status = run_refresh_attempt(args.output_dir)
        print(f"refresh {status['status']} at {status['attemptedAt']}")
        if args.once:
            return 1 if status["status"] == "failed" else 0
        time.sleep(max(args.interval_minutes, 1) * 60)


if __name__ == "__main__":
    raise SystemExit(main())
