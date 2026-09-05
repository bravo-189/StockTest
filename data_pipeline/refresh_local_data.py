"""Refresh StockTest local snapshots once or on a fixed local interval."""

import argparse
import json
import os
import tempfile
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from .fetch_market_data import DEFAULT_INSTRUMENTS, build_snapshot
    from .fetch_holdings import fetch_holdings_snapshot, fetch_holdings_html, normalize_holdings_units
    from .fetch_stockbee import DEFAULT_URL, fetch_csv, build_snapshot as build_stockbee_snapshot
    from .fetch_stockbee_momentum import (
        fetch_csv as fetch_stockbee_momentum_csv,
        build_snapshot as build_stockbee_momentum_snapshot,
        enrich_stockbee_rows,
    )
    from .validate_market_snapshot import analyze_snapshot
except ImportError:  # pragma: no cover - supports direct CLI execution
    from fetch_market_data import DEFAULT_INSTRUMENTS, build_snapshot
    from fetch_holdings import fetch_holdings_snapshot, fetch_holdings_html, normalize_holdings_units
    from fetch_stockbee import DEFAULT_URL, fetch_csv, build_snapshot as build_stockbee_snapshot
    from fetch_stockbee_momentum import (
        fetch_csv as fetch_stockbee_momentum_csv,
        build_snapshot as build_stockbee_momentum_snapshot,
        enrich_stockbee_rows,
    )
    from validate_market_snapshot import analyze_snapshot


def _timestamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


class RefreshSourceError(RuntimeError):
    def __init__(self, source, message):
        super().__init__(message)
        self.source = source


def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}


def _write_market_quality_report(output_dir, market_snapshot):
    """Keep the quality report synchronized with the exact saved snapshot."""
    report = analyze_snapshot(market_snapshot or {}, min_bars=21)
    _write_json(Path(output_dir) / "market_snapshot_quality.json", report)
    return report


def _build_live_market_snapshot():
    return build_snapshot(include_intraday=True)


def _build_live_btc_snapshot():
    return build_snapshot(symbols={"BTC": DEFAULT_INSTRUMENTS["BTC"]}, include_intraday=True)


def _eastern_now():
    return datetime.now(timezone.utc).astimezone(ZoneInfo("America/New_York"))


def _nth_weekday(year, month, weekday, ordinal):
    """Return the ordinal weekday in a month (Monday is 0)."""
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + (ordinal - 1) * 7)


def _last_weekday(year, month, weekday):
    """Return the last weekday in a month (Monday is 0)."""
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    last = next_month - timedelta(days=1)
    return last - timedelta(days=(last.weekday() - weekday) % 7)


def _easter_sunday(year):
    """Return Western Easter Sunday using the Gregorian computus."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _observed_fixed_holiday(year, month, day):
    """Return a US federal holiday's observed date (Sat→Fri, Sun→Mon)."""
    holiday = date(year, month, day)
    if holiday.weekday() == 5:
        return holiday - timedelta(days=1)
    if holiday.weekday() == 6:
        return holiday + timedelta(days=1)
    return holiday


def _us_market_holidays(year):
    """Return the major full-day NYSE holidays for a calendar year.

    The refresh job only needs full-day closures, not early-close schedules.
    Keeping this small, explicit calendar avoids treating a holiday as a
    missing quote while remaining dependency-free in GitHub Actions.
    """
    return {
        _observed_fixed_holiday(year, 1, 1),       # New Year's Day
        _nth_weekday(year, 1, 0, 3),               # Martin Luther King Jr. Day
        _nth_weekday(year, 2, 0, 3),               # Presidents' Day
        _easter_sunday(year) - timedelta(days=2), # Good Friday
        _last_weekday(year, 5, 0),                 # Memorial Day
        _observed_fixed_holiday(year, 6, 19),      # Juneteenth
        _observed_fixed_holiday(year, 7, 4),       # Independence Day
        _nth_weekday(year, 9, 0, 1),               # Labor Day
        _nth_weekday(year, 11, 3, 4),              # Thanksgiving
        _observed_fixed_holiday(year, 12, 25),      # Christmas Day
    }


def _is_us_market_holiday(value):
    value = value.date() if isinstance(value, datetime) else value
    return any(value in _us_market_holidays(year) for year in (value.year - 1, value.year, value.year + 1))


def _last_us_session_date(now=None):
    """Return the most recent confirmed NYSE session date in New York time."""
    now = now or _eastern_now()
    candidate = now.date()
    while candidate.weekday() >= 5 or _is_us_market_holiday(candidate):
        candidate -= timedelta(days=1)
    return candidate.isoformat()


def _parse_refresh_timestamp(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _require_completed_us_equity_snapshot(snapshot, expected_date):
    """Reject a post-close snapshot unless every US ETF has that close."""
    instruments = snapshot.get("instruments") if isinstance(snapshot, dict) else {}
    stale = []
    for symbol, instrument in (instruments or {}).items():
        if not isinstance(instrument, dict) or instrument.get("calendar") != "us-equity":
            continue
        if instrument.get("latestDate") != expected_date:
            stale.append(str(symbol))
    if stale:
        raise RefreshSourceError(
            "market",
            f"post-close snapshot incomplete for {expected_date}: {', '.join(sorted(stale))}",
        )


def _daily_refresh_due(previous_market, previous_stockbee=None, previous_momentum=None):
    """Refresh non-BTC data after close, including late source publication."""
    if not isinstance(previous_market, dict) or not previous_market.get("instruments"):
        return True
    now = _eastern_now()
    if now.weekday() < 5 and now.hour < 17:
        return False
    metadata = previous_market.get("metadata") or {}
    previous_date = metadata.get("dailyRefreshDate")
    # Older snapshots only had dailyRefreshDate. Treat those as due once after
    # close so an initial pre-close bootstrap cannot suppress today's close run.
    if not metadata.get("dailyRefreshAt"):
        return True
    expected_date = _last_us_session_date(now)
    if previous_date != expected_date:
        return True
    # Stockbee publishes its two sheets asynchronously. If the market snapshot
    # already has Friday's date but either Stockbee source still lags, allow a
    # catch-up run after a short cooldown instead of permanently retaining the
    # older column through the weekend.
    source_lagging = any(
        isinstance(snapshot, dict)
        and (snapshot.get("metadata") or {}).get("latestDate")
        and (snapshot.get("metadata") or {}).get("latestDate") < expected_date
        for snapshot in (previous_stockbee, previous_momentum)
    )
    if not source_lagging:
        return False
    refreshed_at = _parse_refresh_timestamp(metadata.get("dailyRefreshAt"))
    if refreshed_at is None:
        return True
    return (now.astimezone(timezone.utc) - refreshed_at).total_seconds() >= 6 * 60 * 60


def _build_live_holdings_snapshot(fetched_at=None):
    tickers = [ticker for ticker, config in DEFAULT_INSTRUMENTS.items() if config.get("kind") in ("sector", "industry")]
    return fetch_holdings_snapshot(tickers, fetcher=fetch_holdings_html, fetched_at=fetched_at)


def refresh_once(output_dir, market_builder=None, stockbee_csv=None, fetched_at=None, holdings_builder=None, stockbee_momentum_csv=None, btc_only=False, daily_refresh_date=None):
    output_dir = Path(output_dir)
    fetched_at = fetched_at or _timestamp()
    previous_market = _read_json(output_dir / "market_snapshot.json")
    try:
        if btc_only and market_builder is None:
            btc_snapshot = _build_live_btc_snapshot()
            previous_instruments = previous_market.get("instruments") if isinstance(previous_market, dict) else {}
            if not isinstance(previous_instruments, dict) or not previous_instruments:
                market_snapshot = btc_snapshot
            else:
                market_snapshot = previous_market
                market_snapshot.setdefault("instruments", {})["BTC"] = btc_snapshot["instruments"]["BTC"]
                normalize_holdings_units(market_snapshot.get("holdings"))
                btc_meta = btc_snapshot.get("metadata") or {}
                market_snapshot.setdefault("metadata", {}).update({
                    "fetchedAt": fetched_at,
                    "btcRefreshAt": fetched_at,
                    "btcLatestDate": btc_meta.get("latestDate"),
                    "btcIntraday": btc_meta.get("intraday"),
                })
        else:
            market_snapshot = (market_builder or _build_live_market_snapshot)()
            if daily_refresh_date:
                metadata = market_snapshot.setdefault("metadata", {})
                metadata["dailyRefreshDate"] = daily_refresh_date
                metadata["dailyRefreshAt"] = fetched_at
                _require_completed_us_equity_snapshot(market_snapshot, daily_refresh_date)
    except Exception as exc:
        raise RefreshSourceError("market", str(exc)) from exc
    if btc_only:
        previous_stockbee = _read_json(output_dir / "stockbee.json")
        previous_momentum = _read_json(output_dir / "stockbee_momentum.json")
        normalize_holdings_units(market_snapshot.get("holdings"))
        _write_json(output_dir / "market_snapshot.json", market_snapshot)
        _write_market_quality_report(output_dir, market_snapshot)
        return {"market": market_snapshot, "stockbee": previous_stockbee, "stockbeeMomentum": previous_momentum}
    try:
        csv_text = stockbee_csv if stockbee_csv is not None else fetch_csv(DEFAULT_URL)
        stockbee_snapshot = build_stockbee_snapshot(csv_text, DEFAULT_URL, fetched_at)
    except Exception as exc:
        raise RefreshSourceError("stockbee", str(exc)) from exc
    previous_momentum = _read_json(output_dir / "stockbee_momentum.json")
    try:
        if stockbee_momentum_csv is None and (market_builder is not None or stockbee_csv is not None):
            raise RuntimeError("momentum source not requested by fixture refresh")
        momentum_csv = stockbee_momentum_csv if stockbee_momentum_csv is not None else fetch_stockbee_momentum_csv()
        momentum_snapshot = build_stockbee_momentum_snapshot(momentum_csv, fetched_at=fetched_at)
        # Classification is a slower, lower-frequency enrichment.  Only live
        # refreshes call the public company profiles, and prior results are
        # reused for symbols that remain on the list.
        if stockbee_momentum_csv is None:
            prior_rows = previous_momentum.get("rows", []) if isinstance(previous_momentum, dict) else []
            cached = {
                row.get("ticker"): row
                for row in prior_rows
                if isinstance(row, dict) and row.get("ticker") and row.get("classificationStatus")
            }
            momentum_snapshot["rows"] = enrich_stockbee_rows(momentum_snapshot.get("rows", []), cached=cached)
            verified = sum(1 for row in momentum_snapshot["rows"] if row.get("classificationStatus") == "verified")
            partial = sum(1 for row in momentum_snapshot["rows"] if row.get("classificationStatus") == "partial")
            unverified = sum(1 for row in momentum_snapshot["rows"] if row.get("classificationStatus") == "unverified")
            momentum_snapshot.setdefault("metadata", {}).update({
                "classificationSource": "StockAnalysis company and ETF profiles",
                "classificationVerifiedCount": verified,
                "classificationPartialCount": partial,
                "classificationUnverifiedCount": unverified,
            })
    except Exception:
        momentum_snapshot = previous_momentum if previous_momentum else {"metadata": {"sourceStatus": "unavailable", "latestDate": None, "rowCount": 0}, "source": {}, "rows": []}
    if holdings_builder is None and market_builder is None and stockbee_csv is None:
        holdings_builder = _build_live_holdings_snapshot
    try:
        if holdings_builder is not None:
            previous_holdings = previous_market.get("holdings") if isinstance(previous_market, dict) else {}
            previous_holdings_meta = (previous_market.get("metadata") or {}).get("holdings") if isinstance(previous_market, dict) else {}
            previous_fetched = previous_holdings_meta.get("fetchedAt") if isinstance(previous_holdings_meta, dict) else None
            previous_age = None
            if previous_fetched:
                try:
                    previous_age = max((datetime.now(timezone.utc) - datetime.fromisoformat(previous_fetched.replace("Z", "+00:00"))).total_seconds(), 0)
                except (TypeError, ValueError):
                    previous_age = None
            if previous_holdings and previous_age is not None and previous_age < 24 * 60 * 60:
                market_snapshot["holdings"] = previous_holdings
                market_snapshot.setdefault("metadata", {})["holdings"] = {**previous_holdings_meta, "sourceStatus": "retained"}
            else:
                holdings_snapshot = holdings_builder(fetched_at)
                market_snapshot["holdings"] = holdings_snapshot.get("holdings", {})
                normalize_holdings_units(market_snapshot["holdings"])
                market_snapshot.setdefault("metadata", {})["holdings"] = holdings_snapshot.get("metadata", {})
    except Exception as exc:
        previous_holdings = previous_market.get("holdings") if isinstance(previous_market, dict) else {}
        if previous_holdings:
            market_snapshot["holdings"] = previous_holdings
            normalize_holdings_units(market_snapshot["holdings"])
            market_snapshot.setdefault("metadata", {})["holdings"] = {"sourceStatus": "retained", "loadedCount": len(previous_holdings), "missing": [], "note": str(exc)}
        else:
            raise RefreshSourceError("holdings", str(exc)) from exc
    previous_instruments = previous_market.get("instruments") if isinstance(previous_market, dict) else {}
    market_meta = market_snapshot.get("metadata") if isinstance(market_snapshot, dict) else {}
    missing = list(market_meta.get("missing") or []) if isinstance(market_meta, dict) else []
    retained = []
    if isinstance(previous_instruments, dict) and isinstance(market_snapshot.get("instruments"), dict):
        for item in missing:
            ticker = item.get("symbol") if isinstance(item, dict) else None
            if ticker and ticker not in market_snapshot["instruments"] and ticker in previous_instruments:
                market_snapshot["instruments"][ticker] = previous_instruments[ticker]
                retained.append(ticker)
    if retained and isinstance(market_meta, dict):
        remaining = [item for item in missing if item.get("symbol") not in retained]
        market_meta["missing"] = remaining
        market_meta["loadedCount"] = len(market_snapshot["instruments"])
        market_meta["sourceStatus"] = "loaded" if not remaining else "partial"
        market_meta["retainedSymbols"] = retained
    normalize_holdings_units(market_snapshot.get("holdings"))
    _write_json(output_dir / "market_snapshot.json", market_snapshot)
    _write_market_quality_report(output_dir, market_snapshot)
    _write_json(output_dir / "stockbee.json", stockbee_snapshot)
    _write_json(output_dir / "stockbee_momentum.json", momentum_snapshot)
    return {"market": market_snapshot, "stockbee": stockbee_snapshot, "stockbeeMomentum": momentum_snapshot}


def run_refresh_attempt(output_dir, market_builder=None, stockbee_csv=None, attempted_at=None, btc_only=False, daily_refresh_date=None):
    """Refresh atomically and always persist an inspectable attempt status."""
    output_dir = Path(output_dir)
    attempted_at = attempted_at or _timestamp()
    status_path = output_dir / "refresh_status.json"
    previous = _read_json(status_path)
    try:
        result = refresh_once(output_dir, market_builder=market_builder, stockbee_csv=stockbee_csv, fetched_at=attempted_at, btc_only=btc_only, daily_refresh_date=daily_refresh_date)
        market_meta = result["market"].get("metadata") or {}
        stockbee_meta = result["stockbee"].get("metadata") or {}
        momentum_meta = result["stockbeeMomentum"].get("metadata") or {}
        missing = market_meta.get("missing") or []
        status_name = "partial" if market_meta.get("sourceStatus") == "partial" or missing else "ok"
        status = {
            "schemaVersion": "1.0",
            "status": status_name,
            "refreshMode": "btc-hourly" if btc_only else "daily-close",
            "attemptedAt": attempted_at,
            "lastCompletedAt": attempted_at,
            "lastFullSuccessAt": attempted_at if status_name == "ok" and not btc_only else previous.get("lastFullSuccessAt"),
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
                "stockbeeMomentum": {
                    "status": momentum_meta.get("sourceStatus", "unknown"),
                    "latestDate": momentum_meta.get("latestDate"),
                    "rowCount": momentum_meta.get("rowCount"),
                    "isStale": momentum_meta.get("isStale"),
                    "classificationVerifiedCount": momentum_meta.get("classificationVerifiedCount"),
                    "classificationPartialCount": momentum_meta.get("classificationPartialCount"),
                    "classificationUnverifiedCount": momentum_meta.get("classificationUnverifiedCount"),
                },
            },
            "errors": [],
        }
    except Exception as exc:
        source = exc.source if isinstance(exc, RefreshSourceError) else "refresh"
        status = {
            "schemaVersion": "1.0",
            "status": "failed",
            "refreshMode": "btc-hourly" if btc_only else "daily-close",
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
        previous_market = _read_json(Path(args.output_dir) / "market_snapshot.json")
        previous_stockbee = _read_json(Path(args.output_dir) / "stockbee.json")
        previous_momentum = _read_json(Path(args.output_dir) / "stockbee_momentum.json")
        now = _eastern_now()
        daily_due = _daily_refresh_due(previous_market, previous_stockbee, previous_momentum)
        after_close = (now.weekday() < 5 and now.hour >= 17) or now.weekday() >= 5
        status = run_refresh_attempt(
            args.output_dir,
            btc_only=not daily_due,
            daily_refresh_date=_last_us_session_date(now) if daily_due and after_close else None,
        )
        print(f"refresh {status['status']} at {status['attemptedAt']}")
        if args.once:
            return 1 if status["status"] == "failed" else 0
        time.sleep(max(args.interval_minutes, 1) * 60)


if __name__ == "__main__":
    raise SystemExit(main())
