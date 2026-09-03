"""Fetch and normalize public ETF holdings pages for the local StockTest snapshot."""

import json
import csv
import io
import re
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen


HOLDINGS_BASE = "https://stockanalysis.com/etf/{ticker}/holdings/"
IBIT_HOLDINGS_URL = "https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf/latest-holdings.csv"
USO_HOLDINGS_PAGE = "https://www.uscfinvestments.com/holdings/uso"
USO_API_KEY_URL = "https://www.uscfinvestments.com/site-template/assets/javascript/api_key.php"
USO_API_BASE = "https://secure.alpsinc.com/MarketingAPI/api/v1/holding/USO/full"
_HOLDING_RE = re.compile(
    r'\{no:(?P<rank>\d+),n:"(?P<name>(?:\\.|[^"])*)"(?:,s:"(?P<symbol>(?:\\.|[^"])*)")?,as:"(?P<weight>[^"%]+)%",sh:"(?P<shares>(?:\\.|[^"])*)"\}'
)
_UPDATED_RE = re.compile(r'(?:lastUpdated|updatedAt):"(?P<date>[^"]+)"')


def _decode_js_string(value):
    try:
        return json.loads('"' + value + '"')
    except (TypeError, ValueError):
        return value.replace('\\"', '"').replace('\\/', '/')


def normalize_holding_symbol(value):
    """Return a display symbol while preserving the source symbol separately."""
    source = _decode_js_string(value or "")
    if source.startswith("$"):
        return source[1:]
    if "/" in source:
        venue, symbol = source[1:].split("/", 1) if source.startswith("!") else ("", source.rsplit("/", 1)[-1])
        return f"{venue.upper()}:{symbol}" if venue else symbol
    return source


def parse_stockanalysis_holdings(html, ticker, provider_url=None, fetched_at=None):
    """Parse StockAnalysis' embedded holdings array without depending on its DOM."""
    if not isinstance(html, str) or not html:
        raise ValueError(f"{ticker} holdings response is empty")
    matches = list(_HOLDING_RE.finditer(html))
    if not matches:
        raise ValueError(f"{ticker} holdings array was not found")
    rows = []
    for match in matches[:10]:
        weight = float(match.group("weight"))
        rows.append({
            "rank": int(match.group("rank")),
            "ticker": normalize_holding_symbol(match.group("symbol") or ""),
            "sourceTicker": _decode_js_string(match.group("symbol") or ""),
            "name": _decode_js_string(match.group("name")),
            "weight": round(weight, 4),
            "weightUnit": "percent",
            "shares": _decode_js_string(match.group("shares")),
        })
    if len(rows) < 10:
        raise ValueError(f"{ticker} holdings returned only {len(rows)} rows")
    updated = _UPDATED_RE.search(html)
    return {
        "ticker": ticker,
        "provider": "StockAnalysis (source listed: Finnhub)",
        "providerUrl": provider_url or HOLDINGS_BASE.format(ticker=ticker.lower()),
        "fetchedAt": fetched_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "asOf": updated.group("date") if updated else None,
        "freshness": "daily",
        "updateFrequency": "daily",
        "totalHoldings": len(matches),
        "top10Weight": round(sum(row["weight"] for row in rows), 4),
        "weightUnit": "percent",
        "holdings": rows,
        "status": "loaded",
    }


def _holding_record(rank, ticker, name, weight, shares, source_ticker=None):
    return {
        "rank": rank,
        "ticker": normalize_holding_symbol(str(ticker or "")),
        "sourceTicker": source_ticker if source_ticker is not None else str(ticker or ""),
        "name": str(name or "").strip(),
        "weight": round(float(weight or 0), 4),
        "weightUnit": "percent",
        "shares": str(shares or ""),
    }


def parse_ishares_holdings_csv(csv_text, ticker="IBIT", provider_url=None, fetched_at=None):
    """Parse the issuer CSV; IBIT has one BTC position plus a small cash line."""
    if not isinstance(csv_text, str) or not csv_text.strip():
        raise ValueError(f"{ticker} issuer holdings response is empty")
    rows = list(csv.reader(io.StringIO(csv_text)))
    header_index = next((index for index, row in enumerate(rows) if row and row[0].strip().lower() == "ticker"), None)
    if header_index is None:
        raise ValueError(f"{ticker} issuer holdings header was not found")
    header = [cell.strip() for cell in rows[header_index]]
    records = []
    for row in rows[header_index + 1:]:
        if len(row) < len(header) or not row[0].strip():
            continue
        item = dict(zip(header, row))
        try:
            # The CSV column is explicitly expressed as a percentage (for
            # example 100.00 means 100%), matching the StockAnalysis contract.
            weight = float(item.get("Weight (%)", "0") or 0)
        except ValueError:
            continue
        records.append(_holding_record(len(records) + 1, item.get("Ticker"), item.get("Name"), weight, item.get("Quantity"), item.get("Ticker")))
    records.sort(key=lambda item: item["weight"], reverse=True)
    records = [{**item, "rank": index + 1} for index, item in enumerate(records[:10])]
    if not records:
        raise ValueError(f"{ticker} issuer holdings contained no rows")
    as_of = next((row[1].strip() for row in rows[:header_index] if row and row[0].strip().lower() == "fund holdings as of" and len(row) > 1), None)
    return {
        "ticker": ticker,
        "provider": "iShares issuer holdings CSV",
        "providerUrl": provider_url or IBIT_HOLDINGS_URL,
        "fetchedAt": fetched_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "asOf": as_of,
        "freshness": "daily",
        "updateFrequency": "daily",
        "totalHoldings": len(records),
        "top10Weight": round(sum(row["weight"] for row in records), 4),
        "weightUnit": "percent",
        "holdings": records,
        "status": "loaded",
        "coverageStatus": "complete",
    }


def parse_uscfinvestments_holdings(payload, ticker="USO", provider_url=None, fetched_at=None):
    """Normalize the fund issuer API, including futures, swaps and treasury bills."""
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{ticker} issuer holdings returned no rows")
    source_rows = [row for row in payload if isinstance(row, dict) and row.get("possessionname") == "Hold"]
    if not source_rows:
        source_rows = [row for row in payload if isinstance(row, dict)]
    source_rows.sort(key=lambda row: float(row.get("weight") or 0), reverse=True)
    records = []
    for index, row in enumerate(source_rows[:10], 1):
        # USCF's public API reports weight as a fraction (0.8144 = 81.44%).
        # Normalize to the percent unit used by the UI and other providers.
        raw_weight = float(row.get("weight") or 0)
        records.append(_holding_record(index, row.get("identifiertodisplay") or row.get("primaryidentifier"), row.get("name"), raw_weight * 100, row.get("shares"), row.get("identifiertodisplay")))
    as_of = source_rows[0].get("asofdate") if source_rows else None
    return {
        "ticker": ticker,
        "provider": "USCF issuer holdings API",
        "providerUrl": provider_url or USO_HOLDINGS_PAGE,
        "fetchedAt": fetched_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "asOf": as_of,
        "freshness": "daily",
        "updateFrequency": "daily",
        "totalHoldings": len(source_rows),
        "top10Weight": round(sum(row["weight"] for row in records), 4),
        "weightUnit": "percent",
        "weightBasis": "source-reported gross exposure",
        "holdings": records,
        "status": "loaded",
        "coverageStatus": "complete",
    }


def normalize_holdings_units(holdings):
    """Normalize legacy snapshots to the canonical percent weight contract."""
    if not isinstance(holdings, dict):
        return holdings
    for ticker, entry in holdings.items():
        if not isinstance(entry, dict):
            continue
        provider = str(entry.get("provider") or "")
        rows = entry.get("holdings") if isinstance(entry.get("holdings"), list) else []
        for row in rows:
            if not isinstance(row, dict):
                continue
            weight = row.get("weight")
            if row.get("weightUnit") != "percent" and isinstance(weight, (int, float)):
                # Legacy IBIT and USO records stored source fractions (0–1).
                if (ticker == "IBIT" and "iShares" in provider) or (ticker == "USO" and "USCF" in provider):
                    row["weight"] = round(weight * 100, 4)
            row["weightUnit"] = "percent"
        entry["weightUnit"] = "percent"
        if ticker == "USO" and "USCF" in provider:
            entry.setdefault("weightBasis", "source-reported gross exposure")
        if rows:
            entry["top10Weight"] = round(sum(float(row.get("weight") or 0) for row in rows), 4)
    return holdings


def fetch_holdings_html(url, timeout=20):
    request = Request(url, headers={"Accept": "text/html", "User-Agent": "StockTest local ETF holdings/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_ishares_holdings_csv(url=IBIT_HOLDINGS_URL, timeout=20):
    request = Request(url, headers={"Accept": "text/csv", "User-Agent": "StockTest local ETF holdings/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8-sig", errors="replace")


def fetch_uscfinvestments_holdings(url=USO_API_BASE, timeout=20):
    key_request = Request(USO_API_KEY_URL, headers={"Accept": "text/javascript", "User-Agent": "StockTest local ETF holdings/1.0"})
    with urlopen(key_request, timeout=timeout) as response:
        key_text = response.read().decode("utf-8", errors="replace")
    token_match = re.search(r"token\s*=\s*'([^']+)'", key_text)
    if not token_match:
        raise ValueError("USCF public API token was not found")
    request = Request(url, headers={"Accept": "application/json", "Authorization": f"Bearer {token_match.group(1)}", "User-Agent": "StockTest local ETF holdings/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_holdings_snapshot(tickers, fetcher=fetch_holdings_html, fetched_at=None, source_fetchers=None):
    """Fetch one real holdings page per ETF and expose explicit missing entries."""
    fetched_at = fetched_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    holdings = {}
    missing = []
    source_fetchers = source_fetchers or {}
    for ticker in dict.fromkeys(tickers):
        if ticker == "IBIT":
            url, fetch_one, parse_one = IBIT_HOLDINGS_URL, source_fetchers.get("IBIT", fetch_ishares_holdings_csv), parse_ishares_holdings_csv
        elif ticker == "USO":
            url, fetch_one, parse_one = USO_API_BASE, source_fetchers.get("USO", fetch_uscfinvestments_holdings), parse_uscfinvestments_holdings
        else:
            url, fetch_one, parse_one = HOLDINGS_BASE.format(ticker=ticker.lower()), fetcher, parse_stockanalysis_holdings
        try:
            last_error = None
            for attempt in range(3):
                try:
                    page = fetch_one(url)
                    break
                except Exception as exc:  # retry transient public-page failures
                    last_error = exc
                    if attempt < 2:
                        time.sleep(0.4 * (attempt + 1))
            else:
                raise last_error
            holdings[ticker] = parse_one(page, ticker, url, fetched_at)
        except Exception as exc:
            missing.append({"ticker": ticker, "provider": "stockanalysis", "url": url, "reason": str(exc)})
    normalize_holdings_units(holdings)
    return {
        "metadata": {
            "provider": "StockAnalysis (source listed: Finnhub) plus issuer overrides",
            "access": "public read-only",
            "fetchedAt": fetched_at,
            "requestedCount": len(tuple(dict.fromkeys(tickers))),
            "loadedCount": len(holdings),
            "missing": missing,
            "sourceStatus": "loaded" if not missing else ("partial" if holdings else "missing"),
            "freshness": "daily",
            "sourceOverrides": {"IBIT": "iShares issuer holdings CSV", "USO": "USCF issuer holdings API"},
        },
        "holdings": holdings,
    }
