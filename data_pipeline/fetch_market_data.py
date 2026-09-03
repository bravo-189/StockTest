"""Fetch public daily market data into a local, validated JSON snapshot."""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from .market_data import normalize_binance_intraday, normalize_binance_klines, normalize_yahoo_chart, normalize_yahoo_intraday, relative_strength_metrics, relative_strength_ratings, select_latest_intraday_session, trend_vs_moving_average, validate_instrument, validate_intraday_bars, validate_market_snapshot
except ImportError:  # pragma: no cover - supports direct CLI execution
    from market_data import normalize_binance_intraday, normalize_binance_klines, normalize_yahoo_chart, normalize_yahoo_intraday, relative_strength_metrics, relative_strength_ratings, select_latest_intraday_session, trend_vs_moving_average, validate_instrument, validate_intraday_bars, validate_market_snapshot

try:
    from .fetch_holdings import fetch_holdings_snapshot
except ImportError:  # pragma: no cover
    from fetch_holdings import fetch_holdings_snapshot


YAHOO_CHART_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
INTRADAY_SYMBOLS = ("SPX", "NDX", "DJI", "RUT", "BTC")

CALENDAR_DEFS = {
    "us-equity": {"label": "美股交易日", "timezone": "America/New_York", "frequency": "exchange-sessions"},
    "crypto-24x7": {"label": "加密资产 24/7", "timezone": "UTC", "frequency": "calendar-days"},
}

INDUSTRY_SYMBOLS = (
    "COPX", "LIT", "XME", "GDX", "QTUM", "SOXX", "ARKQ", "AIQ", "DTCR", "CHAT", "XOP", "NLR", "KBWB", "OIH", "ITA", "MAGS", "ARKX", "QQQ", "XBI", "ARKK", "SPY", "IWV", "MTUM", "ARKW", "DIA", "IDRV", "XTL", "PRNT", "IGV", "USO", "IWM", "KWEB", "TAN", "SLX", "SKYY", "ARKG", "BLOK", "IYT", "CIBR", "IBUY", "KIE", "CLOU", "BOTZ", "PAVE", "KBE", "XRT", "HERO", "ARKF", "VNQ", "KRE", "IEUR", "IAI", "MJ", "IYH", "FINX", "XHB", "IBIT", "JETS", "IHI", "IPAY"
)

DEFAULT_INSTRUMENTS = {
    "SPX": {"provider": "yahoo-chart", "querySymbol": "^GSPC", "kind": "index"},
    "NDX": {"provider": "yahoo-chart", "querySymbol": "^NDX", "kind": "index"},
    "DJI": {"provider": "yahoo-chart", "querySymbol": "^DJI", "kind": "index"},
    "RUT": {"provider": "yahoo-chart", "querySymbol": "^RUT", "kind": "index"},
    "SPY": {"provider": "yahoo-chart", "querySymbol": "SPY", "kind": "sector"},
    "XLV": {"provider": "yahoo-chart", "querySymbol": "XLV", "kind": "sector"},
    "XLP": {"provider": "yahoo-chart", "querySymbol": "XLP", "kind": "sector"},
    "XLU": {"provider": "yahoo-chart", "querySymbol": "XLU", "kind": "sector"},
    "XLF": {"provider": "yahoo-chart", "querySymbol": "XLF", "kind": "sector"},
    "XLI": {"provider": "yahoo-chart", "querySymbol": "XLI", "kind": "sector"},
    "XLE": {"provider": "yahoo-chart", "querySymbol": "XLE", "kind": "sector"},
    "XLB": {"provider": "yahoo-chart", "querySymbol": "XLB", "kind": "sector"},
    "XLRE": {"provider": "yahoo-chart", "querySymbol": "XLRE", "kind": "sector"},
    "XLY": {"provider": "yahoo-chart", "querySymbol": "XLY", "kind": "sector"},
    "XLC": {"provider": "yahoo-chart", "querySymbol": "XLC", "kind": "sector"},
    "XLK": {"provider": "yahoo-chart", "querySymbol": "XLK", "kind": "sector"},
    "ARKK": {"provider": "yahoo-chart", "querySymbol": "ARKK", "kind": "sector"},
    "IBIT": {"provider": "yahoo-chart", "querySymbol": "IBIT", "kind": "sector"},
    "BTC": {"provider": "binance-spot", "querySymbol": "BTCUSDT", "kind": "crypto", "calendar": "crypto-24x7"},
}

for _ticker in INDUSTRY_SYMBOLS:
    DEFAULT_INSTRUMENTS.setdefault(_ticker, {"provider": "yahoo-chart", "querySymbol": _ticker, "kind": "industry"})


def _fetch_json_with_source(url, timeout=20):
    candidates = [url]
    if "query1.finance.yahoo.com" in url:
        candidates.append(url.replace("query1.finance.yahoo.com", "query2.finance.yahoo.com"))
    if "api.binance.com" in url:
        candidates.append(url.replace("https://api.binance.com", "https://data-api.binance.vision"))
    last_error = None
    for candidate in candidates:
        request = Request(candidate, headers={"Accept": "application/json", "User-Agent": "StockTest local market snapshot/1.0"})
        for attempt in range(3):
            try:
                with urlopen(request, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8")), candidate
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(0.4 * (attempt + 1))
    raise last_error


def fetch_json(url, timeout=20):
    return _fetch_json_with_source(url, timeout)[0]


def _fetch_with_source(url, fetcher):
    """Return payload plus the endpoint that actually supplied it."""
    if fetcher is fetch_json:
        return _fetch_json_with_source(url)
    return fetcher(url), url


def _provider_url(config):
    if config["provider"] == "binance-spot":
        return f"{BINANCE_KLINES_URL}?{urlencode({'symbol': config['querySymbol'], 'interval': '1d', 'limit': 90})}"
    return f"{YAHOO_CHART_BASE}{config['querySymbol']}?{urlencode({'range': '2y', 'interval': '1d', 'events': 'div,splits'})}"


def _intraday_provider_url(config):
    if config["provider"] == "binance-spot":
        return f"{BINANCE_KLINES_URL}?{urlencode({'symbol': config['querySymbol'], 'interval': '2h', 'limit': 42})}"
    # Use Yahoo's native 5m bars directly for the intraday preview.
    return f"{YAHOO_CHART_BASE}{config['querySymbol']}?{urlencode({'range': '5d', 'interval': '5m', 'includePrePost': 'false', 'events': 'div,splits'})}"


def build_snapshot(symbols=None, fetched_at=None, fetcher=fetch_json, include_intraday=False, intraday_fetcher=None, holdings_fetcher=None):
    symbols = symbols or DEFAULT_INSTRUMENTS
    fetched_at = fetched_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    instruments = {}
    missing = []
    for ticker, config in symbols.items():
        provider_url = _provider_url(config)
        try:
            payload, actual_provider_url = _fetch_with_source(provider_url, fetcher)
            if config["provider"] == "binance-spot":
                instrument = normalize_binance_klines(payload, ticker, actual_provider_url)
            else:
                instrument = normalize_yahoo_chart(payload, ticker, actual_provider_url)
            instrument.update({"kind": config["kind"], "querySymbol": config["querySymbol"], "calendar": config.get("calendar", "us-equity")})
            trend = trend_vs_moving_average(instrument.get("bars"), period=150)
            instrument.update({"ma150": trend["ma"], "trend150": trend["trend"]})
            validate_instrument(instrument)
            instruments[ticker] = instrument
        except Exception as exc:  # keep a visible missing list for partial data
            missing.append({"symbol": ticker, "provider": config["provider"], "reason": str(exc)})

    intraday_missing = []
    intraday_loaded = []
    if include_intraday:
        intraday_fetcher = intraday_fetcher or fetcher
        for ticker in INTRADAY_SYMBOLS:
            config = symbols.get(ticker)
            if not config or ticker not in instruments:
                continue
            try:
                provider_url = _intraday_provider_url(config)
                payload, actual_provider_url = _fetch_with_source(provider_url, intraday_fetcher)
                if config["provider"] == "binance-spot":
                    intraday = normalize_binance_intraday(payload, ticker, actual_provider_url, interval="2h", timezone_name="UTC")
                else:
                    intraday = normalize_yahoo_intraday(payload, ticker, actual_provider_url, timezone_name="America/New_York", interval_minutes=5)
                minimum = 1
                intraday = select_latest_intraday_session(intraday, minimum_bars=minimum)
                validate_intraday_bars(intraday, minimum_bars=minimum)
                instruments[ticker]["intradayBars"] = intraday["bars"]
                instruments[ticker]["intraday"] = {key: intraday[key] for key in ("provider", "providerUrl", "interval", "timezone", "latestDate")}
                intraday_loaded.append(ticker)
            except Exception as exc:
                intraday_missing.append({"symbol": ticker, "provider": config["provider"], "reason": str(exc)})

    if not instruments:
        raise RuntimeError("market data fetch returned no valid instruments")
    benchmark = instruments.get("SPY")
    if benchmark:
        for instrument in instruments.values():
            if instrument.get("calendar", "us-equity") == "us-equity":
                instrument["relativeStrength"] = relative_strength_metrics(instrument.get("bars"), benchmark.get("bars"))
        sector_ratings = relative_strength_ratings(instruments, tuple(ticker for ticker, config in symbols.items() if config.get("kind") == "sector"))
        industry_ratings = relative_strength_ratings(instruments, INDUSTRY_SYMBOLS)
        for ticker, instrument in instruments.items():
            instrument["relativeStrengthRating"] = {
                "sector": sector_ratings.get(ticker, {}),
                "industry": industry_ratings.get(ticker, {}),
            }
    pending_bars = [{"symbol": ticker, **instrument["pendingBar"]} for ticker, instrument in instruments.items() if instrument.get("pendingBar")]
    industry_missing = [item for item in missing if item["symbol"] in INDUSTRY_SYMBOLS]
    calendar_latest_dates = {}
    for instrument in instruments.values():
        calendar = instrument.get("calendar", "us-equity")
        calendar_latest_dates[calendar] = max(calendar_latest_dates.get(calendar, ""), instrument["latestDate"])
    comparison_date = min(calendar_latest_dates.values()) if calendar_latest_dates else None
    holdings_snapshot = {"metadata": {"sourceStatus": "not-requested", "requestedCount": 0, "loadedCount": 0, "missing": []}, "holdings": {}}
    if holdings_fetcher is not None:
        holdings_tickers = [ticker for ticker, config in symbols.items() if config.get("kind") in ("sector", "industry")]
        holdings_snapshot = fetch_holdings_snapshot(holdings_tickers, fetcher=holdings_fetcher, fetched_at=fetched_at)
    snapshot = {
        "metadata": {
            "schemaVersion": "1.0",
            "sourceStatus": "loaded" if not missing else "partial",
            "fetchedAt": fetched_at,
            "latestDate": max((instrument["latestDate"] for instrument in instruments.values()), default=None),
            "requiredCount": len(symbols),
            "loadedCount": len(instruments),
            "missing": missing,
            "pendingCount": len(pending_bars),
            "pendingSymbols": [item["symbol"] for item in pending_bars],
            "industryCount": len(INDUSTRY_SYMBOLS),
            "industryLoadedCount": sum(1 for ticker in INDUSTRY_SYMBOLS if ticker in instruments),
            "industryMissing": industry_missing,
            "comparisonDate": comparison_date,
            "calendarLatestDates": calendar_latest_dates,
            "calendars": CALENDAR_DEFS,
            "intraday": {
                "requested": list(INTRADAY_SYMBOLS) if include_intraday else [],
                "loaded": intraday_loaded,
                "missing": intraday_missing,
                "sourceStatus": "loaded" if include_intraday and not intraday_missing else ("partial" if include_intraday else "not-requested"),
            },
            "relativeStrength": {
                "method": "cross-sectional close-return rank",
                "scale": "1-99",
                "lookbacks": {"rs1m": 21, "rs3m": 63, "rs6m": 126, "rs12m": 252},
                "universes": {"sector": "sector ETFs including SPY", "industry": "industrySymbols including SPY"},
            },
            "trend": {"method": "latest confirmed close versus SMA150", "field": "trend150", "insufficientData": "数据不足"},
            "holdings": holdings_snapshot["metadata"],
        },
        "sources": {
            "equities": {"provider": "Yahoo Finance chart (unofficial endpoint)", "access": "public read-only", "notes": "Daily chart data; endpoint may change without notice."},
            "crypto": {"provider": "Binance Spot REST", "access": "public read-only", "notes": "BTCUSDT daily klines; no trading key is used."},
            "holdings": {"provider": "StockAnalysis (source listed: Finnhub) plus issuer overrides", "access": "public read-only", "notes": "Most equity ETFs use StockAnalysis; IBIT uses the iShares issuer CSV and USO uses the USCF issuer API. Each record retains provider URL and as-of metadata."},
        },
        "industrySymbols": list(INDUSTRY_SYMBOLS),
        "pendingBars": pending_bars,
        "intradayMissing": intraday_missing,
        "instruments": instruments,
        "holdings": holdings_snapshot["holdings"],
    }
    validate_market_snapshot(snapshot)
    return snapshot


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch StockTest public market data into a local snapshot")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    snapshot = build_snapshot(include_intraday=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = snapshot["metadata"]["sourceStatus"]
    print(f"{status}: {snapshot['metadata']['loadedCount']}/{snapshot['metadata']['requiredCount']} instruments through {snapshot['metadata']['latestDate']} -> {output}")


if __name__ == "__main__":
    main()
