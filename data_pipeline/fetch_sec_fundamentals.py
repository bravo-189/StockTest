"""Fetch a small, explicit SEC Company Facts pilot into a traceable JSON file."""

import argparse
import gzip
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

try:
    from .sec_fundamentals import build_fundamental_record
except ImportError:  # pragma: no cover - supports direct CLI execution
    from sec_fundamentals import build_fundamental_record


PILOT_CIKS = {
    "MSFT": "0000789019",
    "NVDA": "0001045810",
    "AAPL": "0000320193",
    "AMZN": "0001018724",
    "META": "0001326801",
}
SEC_URL_TEMPLATE = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
USER_AGENT = "StockTest research project"


def fetch_companyfacts(cik, timeout=30):
    cik_value = str(cik).zfill(10)
    request = Request(SEC_URL_TEMPLATE.format(cik=cik_value), headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read()
        if response.headers.get("Content-Encoding", "").lower() == "gzip":
            payload = gzip.decompress(payload)
        return json.loads(payload.decode("utf-8"))


def build_snapshot(tickers, pause_seconds=0.12):
    requested = list(dict.fromkeys(str(ticker).strip().upper() for ticker in tickers if str(ticker).strip()))
    records = []
    errors = []
    for index, ticker in enumerate(requested):
        cik = PILOT_CIKS.get(ticker)
        if not cik:
            errors.append({"ticker": ticker, "error": "No explicit CIK mapping in pilot universe"})
            continue
        try:
            records.append(build_fundamental_record(ticker, cik, fetch_companyfacts(cik)))
        except Exception as exc:  # keep the remaining pilot records usable
            errors.append({"ticker": ticker, "cik": cik, "error": str(exc)})
        if index < len(requested) - 1 and pause_seconds:
            time.sleep(pause_seconds)
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "metadata": {"requestedTickerCount": len(requested), "tickerCount": len(records), "generatedAt": fetched_at, "sourceStatus": "loaded" if records else "failed"},
        "source": {"provider": "SEC EDGAR Company Facts", "urlTemplate": SEC_URL_TEMPLATE, "userAgent": USER_AGENT, "terms": "Public SEC data; respect SEC access guidelines"},
        "records": records,
        "errors": errors,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch SEC Company Facts for the StockTest pilot universe")
    parser.add_argument("--tickers", default=",".join(PILOT_CIKS), help="Comma-separated pilot tickers")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    snapshot = build_snapshot(args.tickers.split(","))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"loaded {snapshot['metadata']['tickerCount']} of {snapshot['metadata']['requestedTickerCount']} tickers -> {output}")


if __name__ == "__main__":
    main()
