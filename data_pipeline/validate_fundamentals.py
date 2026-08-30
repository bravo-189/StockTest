"""Quality checks for the normalized SEC fundamentals snapshot."""

import argparse
import json
from pathlib import Path


REQUIRED_VALUES = ("revenue", "netIncome", "assets", "liabilities", "equity", "cash", "dilutedEps")


def _finding(check, severity, evidence, risk):
    return {"check": check, "severity": severity, "evidence": evidence, "risk": risk}


def validate_snapshot(snapshot):
    findings = []
    records = snapshot.get("records", [])
    if snapshot.get("source", {}).get("provider") != "SEC EDGAR Company Facts":
        findings.append(_finding("source_provider", "high", "SEC provider metadata is missing", "The snapshot cannot be traced to the intended primary source."))
    if not records:
        findings.append(_finding("record_count", "critical", "0 company records", "No fundamental input is safe for downstream ranking."))
        return findings
    tickers = [record.get("ticker") for record in records]
    if len(set(tickers)) != len(tickers):
        findings.append(_finding("unique_ticker", "high", f"{len(tickers) - len(set(tickers))} duplicate ticker(s)", "Duplicate companies can double-weight a theme."))
    expected = snapshot.get("metadata", {}).get("tickerCount")
    if expected != len(records):
        findings.append(_finding("record_count", "medium", f"metadata={expected}, records={len(records)}", "The published snapshot may be partially loaded."))
    for record in records:
        ticker = record.get("ticker", "unknown")
        if not record.get("latestAnnualEnd"):
            findings.append(_finding("annual_period", "high", f"{ticker} has no annual end date", "Period alignment cannot be verified."))
        for key in REQUIRED_VALUES:
            value = record.get("values", {}).get(key)
            if not value or value.get("status") not in {"ok", "derived", "missing"}:
                findings.append(_finding("metric_status", "high", f"{ticker}.{key} has invalid status", "The metric cannot be safely interpreted."))
                continue
            if value["status"] == "missing":
                findings.append(_finding("metric_missing", "medium", f"{ticker}.{key} is missing", "The agent should down-weight this company for that factor."))
            elif value["status"] == "ok" and not value.get("source", {}).get("accn"):
                findings.append(_finding("metric_provenance", "high", f"{ticker}.{key} has no accession number", "The reported value cannot be audited back to a filing."))
            elif value["status"] == "derived" and not value.get("source", {}).get("derivedFrom"):
                findings.append(_finding("derived_provenance", "high", f"{ticker}.{key} has no derivation inputs", "A derived value without inputs is not reproducible."))
            numeric = value.get("value")
            if numeric is not None and key != "dilutedEps" and numeric < 0:
                findings.append(_finding("non_negative_balance", "medium", f"{ticker}.{key}={numeric}", "Negative balance-sheet values need issuer-specific review."))
        margin = record.get("metrics", {}).get("netMargin")
        if margin is not None and not -1 <= margin <= 1:
            findings.append(_finding("margin_range", "high", f"{ticker}.netMargin={margin}", "An implausible margin usually indicates a wrong period or unit."))
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a StockTest SEC fundamentals snapshot")
    parser.add_argument("snapshot")
    args = parser.parse_args(argv)
    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    findings = validate_snapshot(snapshot)
    if findings:
        for item in findings:
            print(f"[{item['severity']}] {item['check']}: {item['evidence']} — {item['risk']}")
    else:
        print("PASS: no data-quality findings")
    raise SystemExit(1 if any(item["severity"] in {"high", "critical"} for item in findings) else 0)


if __name__ == "__main__":
    main()
