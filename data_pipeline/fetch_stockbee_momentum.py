"""Fetch the public Stockbee 50 sheet into a ticker-only local snapshot.

The public sheet is a wide, date-by-column export.  We keep the newest
available date and its first 50 symbols; the source date is retained so the
UI can clearly flag an old or paused public list instead of presenting it as
current market data.
"""

import argparse
import csv
import io
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SOURCE_PAGE_URL = "https://stockbee.blogspot.com/p/stockbee-50.html"
# The Stockbee 50 tab is the dated watchlist at gid=1499398020.  Keep the
# export URL explicit so refreshes always read the user's intended tab.
SHEET_URL = "https://docs.google.com/spreadsheets/d/1xjbe9SF0HsxwY_Uy3NC2tT92BqK0nhArUaYU16Q0p9M/export?format=csv&gid=1499398020"
CLASSIFICATION_SOURCE_NAME = "StockAnalysis company profile"
ETF_CLASSIFICATION_SOURCE_NAME = "StockAnalysis ETF profile"
CLASSIFICATION_URL = "https://stockanalysis.com/stocks/{ticker}/company/"
ETF_CLASSIFICATION_URL = "https://stockanalysis.com/etf/{ticker}/"


def fetch_csv(url=SHEET_URL, timeout=20):
    request = Request(url, headers={"User-Agent": "StockTest data pipeline/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8-sig")


def _parse_date(value):
    try:
        return datetime.strptime(str(value).strip(), "%m/%d/%Y").date()
    except (TypeError, ValueError):
        return None


def parse_stockbee_momentum_csv(text, limit=50):
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 3:
        return {"latestDate": None, "rows": []}
    candidates = [(index, _parse_date(value)) for index, value in enumerate(rows[0])]
    candidates = [(index, value) for index, value in candidates if value]
    if not candidates:
        return {"latestDate": None, "rows": []}
    column, latest = max(candidates, key=lambda item: item[1])
    # Some exports include a descriptive "Six Month" row between the date
    # header and the symbols; the current Stockbee 50 tab starts symbols on
    # the very next row.  Detect the label instead of assuming a fixed offset
    # so both public-sheet layouts yield the complete 50-name list.
    start_row = 1
    if len(rows) > 1:
        marker = rows[1][column].strip().lower() if column < len(rows[1]) else ""
        if not marker or "month" in marker or "ticker" in marker or "symbol" in marker:
            start_row = 2
    symbols = []
    for row in rows[start_row:]:
        value = row[column].strip().upper() if column < len(row) else ""
        if value and value not in symbols:
            symbols.append(value)
        if len(symbols) >= limit:
            break
    return {"latestDate": latest.isoformat(), "rows": [{"rank": index + 1, "ticker": ticker} for index, ticker in enumerate(symbols)]}


def build_snapshot(csv_text, fetched_at=None):
    parsed = parse_stockbee_momentum_csv(csv_text)
    latest_date = date.fromisoformat(parsed["latestDate"]) if parsed["latestDate"] else None
    age_days = (date.today() - latest_date).days if latest_date else None
    return {
        "metadata": {
            "sourceStatus": "loaded" if parsed["rows"] else "unavailable",
            "latestDate": parsed["latestDate"],
            "rowCount": len(parsed["rows"]),
            "isStale": age_days is None or age_days > 30,
            "ageDays": age_days,
            "fetchedAt": fetched_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "listName": "Stockbee 50",
        },
        "source": {"name": "Stockbee 50", "pageUrl": SOURCE_PAGE_URL, "url": SHEET_URL, "format": "google-sheets-csv"},
        "rows": parsed["rows"],
    }


def _extract_profile_value(html, field):
    """Read a sector/industry value from StockAnalysis' embedded profile data.

    The company page exposes a compact object in its HTML.  A small fallback
    handles the rendered table markup so a harmless page-format change does
    not turn every classification into a false missing value.
    """
    embedded = re.search(rf"{field}:\{{value:\"([^\"]+)\"", html or "")
    if embedded:
        return embedded.group(1).strip()
    table = re.search(
        rf"(?is)>{field}</(?:td|th)>.*?>([^<]+)</(?:a|td)>",
        html or "",
    )
    return table.group(1).strip() if table else None


def parse_stock_classification_html(html, ticker):
    """Parse a verified sector and industry pair from a company profile page."""
    sector = _extract_profile_value(html, "sector")
    industry = _extract_profile_value(html, "industry")
    if not sector or not industry:
        return {
            "ticker": ticker,
            "sector": "未找到可核验分类",
            "industry": "未找到可核验分类",
            "classificationStatus": "unverified",
            "classificationSource": CLASSIFICATION_SOURCE_NAME,
        }
    return {
        "ticker": ticker,
        "sector": sector,
        "industry": industry,
        "classificationStatus": "verified",
        "classificationSource": CLASSIFICATION_SOURCE_NAME,
    }


def parse_stockanalysis_etf_html(html, ticker):
    """Parse the asset class/category shown on a StockAnalysis ETF page."""
    def label_value(label):
        match = re.search(rf"(?is){label}</span>\s*<span>([^<]*)", html or "")
        return match.group(1).strip() if match and match.group(1).strip() else None

    sector = label_value("Asset Class")
    industry = label_value("Category")
    if not sector and not industry:
        return None
    return {
        "ticker": ticker,
        "sector": sector or "未找到可核验板块",
        "industry": industry or "未找到可核验行业",
        "classificationStatus": "verified" if sector and industry else "partial",
        "classificationSource": ETF_CLASSIFICATION_SOURCE_NAME,
    }


def fetch_stock_classification(ticker, timeout=5):
    """Fetch one ticker's public sector/industry classification."""
    symbol = str(ticker or "").strip().upper()
    if not symbol:
        return None
    headers = {"User-Agent": "StockTest data pipeline/1.0"}
    url = CLASSIFICATION_URL.format(ticker=symbol.lower())
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            html = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError, OSError):
        html = ""
    parsed = parse_stock_classification_html(html, symbol) if html else None
    if parsed and parsed.get("classificationStatus") == "verified":
        return parsed
    # Many Stockbee entries are leveraged or crypto ETFs, which do not have a
    # company profile.  Fall back to the ETF profile's asset class/category.
    try:
        etf_url = ETF_CLASSIFICATION_URL.format(ticker=symbol.lower())
        with urlopen(Request(etf_url, headers=headers), timeout=timeout) as response:
            etf_html = response.read().decode("utf-8", errors="replace")
        etf_parsed = parse_stockanalysis_etf_html(etf_html, symbol)
        if etf_parsed:
            return etf_parsed
    except (HTTPError, URLError, TimeoutError, OSError):
        pass
    return {
        "ticker": symbol,
        "sector": "未找到可核验分类",
        "industry": "未找到可核验分类",
        "classificationStatus": "unverified",
        "classificationSource": CLASSIFICATION_SOURCE_NAME,
    }


def enrich_stockbee_rows(rows, fetcher=fetch_stock_classification, cached=None):
    """Attach real classifications, reusing prior verified results when present."""
    cached = cached or {}
    enriched = []
    pending = {}
    for index, row in enumerate(rows or []):
        item = dict(row)
        ticker = item.get("ticker")
        prior = cached.get(ticker) if ticker else None
        if prior and prior.get("classificationStatus"):
            item.update({key: prior.get(key) for key in (
                "sector", "industry", "classificationStatus", "classificationSource"
            ) if prior.get(key) is not None})
        elif ticker:
            pending[index] = (item, ticker)
        enriched.append(item)
    if pending:
        # Profile lookups are independent and can be slow for invalid symbols;
        # parallel requests keep a live refresh bounded without changing row order.
        with ThreadPoolExecutor(max_workers=min(8, len(pending))) as pool:
            futures = {pool.submit(fetcher, ticker): index for index, (_, ticker) in pending.items()}
            for future in as_completed(futures):
                index = futures[future]
                try:
                    classification = future.result()
                except Exception:
                    classification = None
                if classification:
                    enriched[index].update(classification)
    return enriched


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch the public Stockbee 50 ticker list")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    snapshot = build_snapshot(fetch_csv())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"loaded {snapshot['metadata']['rowCount']} symbols through {snapshot['metadata']['latestDate']} -> {output}")


if __name__ == "__main__":
    main()
