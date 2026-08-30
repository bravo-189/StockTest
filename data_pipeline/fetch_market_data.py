"""Fetch public daily market data into a local, validated JSON snapshot."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from .market_data import normalize_binance_klines, normalize_yahoo_chart, validate_instrument, validate_market_snapshot
except ImportError:  # pragma: no cover - supports direct CLI execution
    from market_data import normalize_binance_klines, normalize_yahoo_chart, validate_instrument, validate_market_snapshot


YAHOO_CHART_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"

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


def fetch_json(url, timeout=20):
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "StockTest local market snapshot/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _provider_url(config):
    if config["provider"] == "binance-spot":
        return f"{BINANCE_KLINES_URL}?{urlencode({'symbol': config['querySymbol'], 'interval': '1d', 'limit': 90})}"
    return f"{YAHOO_CHART_BASE}{config['querySymbol']}?{urlencode({'range': '3mo', 'interval': '1d', 'events': 'div,splits'})}"


def build_snapshot(symbols=None, fetched_at=None, fetcher=fetch_json):
    symbols = symbols or DEFAULT_INSTRUMENTS
    fetched_at = fetched_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    instruments = {}
    missing = []
    for ticker, config in symbols.items():
        provider_url = _provider_url(config)
        try:
            payload = fetcher(provider_url)
            if config["provider"] == "binance-spot":
                instrument = normalize_binance_klines(payload, ticker, provider_url)
            else:
                instrument = normalize_yahoo_chart(payload, ticker, provider_url)
            instrument.update({"kind": config["kind"], "querySymbol": config["querySymbol"], "calendar": config.get("calendar", "us-equity")})
            validate_instrument(instrument)
            instruments[ticker] = instrument
        except Exception as exc:  # keep a visible missing list for partial data
            missing.append({"symbol": ticker, "provider": config["provider"], "reason": str(exc)})

    if not instruments:
        raise RuntimeError("market data fetch returned no valid instruments")
    pending_bars = [{"symbol": ticker, **instrument["pendingBar"]} for ticker, instrument in instruments.items() if instrument.get("pendingBar")]
    industry_missing = [item for item in missing if item["symbol"] in INDUSTRY_SYMBOLS]
    calendar_latest_dates = {}
    for instrument in instruments.values():
        calendar = instrument.get("calendar", "us-equity")
        calendar_latest_dates[calendar] = max(calendar_latest_dates.get(calendar, ""), instrument["latestDate"])
    comparison_date = min(calendar_latest_dates.values()) if calendar_latest_dates else None
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
        },
        "sources": {
            "equities": {"provider": "Yahoo Finance chart (unofficial endpoint)", "access": "public read-only", "notes": "Daily chart data; endpoint may change without notice."},
            "crypto": {"provider": "Binance Spot REST", "access": "public read-only", "notes": "BTCUSDT daily klines; no trading key is used."},
        },
        "industrySymbols": list(INDUSTRY_SYMBOLS),
        "pendingBars": pending_bars,
        "instruments": instruments,
    }
    validate_market_snapshot(snapshot)
    return snapshot


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch StockTest public market data into a local snapshot")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    snapshot = build_snapshot()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = snapshot["metadata"]["sourceStatus"]
    print(f"{status}: {snapshot['metadata']['loadedCount']}/{snapshot['metadata']['requiredCount']} instruments through {snapshot['metadata']['latestDate']} -> {output}")


if __name__ == "__main__":
    main()
