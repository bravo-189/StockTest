"""SEC Company Facts normalization for StockTest's fundamental-data layer."""

from datetime import datetime


TAG_CANDIDATES = {
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"),
    "netIncome": ("NetIncomeLoss",),
    "assets": ("Assets",),
    "liabilities": ("Liabilities",),
    "equity": ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
    "cash": ("CashAndCashEquivalentsAtCarryingValue",),
    "dilutedEps": ("EarningsPerShareDiluted",),
}


def _annual_entries(companyfacts, tag, unit):
    facts = companyfacts.get("facts", {}).get("us-gaap", {})
    tag_fact = facts.get(tag) or {}
    units = tag_fact.get("units", {})
    values = units.get(unit, []) if unit else [entry for entries in units.values() for entry in entries]
    annual = [
        entry for entry in values
        if entry.get("form") in {"10-K", "10-K/A"} and entry.get("fp") in {None, "FY"} and entry.get("end")
    ]
    return sorted(annual, key=lambda entry: (entry.get("end", ""), entry.get("filed", ""), entry.get("accn", "")), reverse=True)


def _annual_candidates(companyfacts, tags, unit):
    candidates = []
    for priority, tag in enumerate(tags):
        for entry in _annual_entries(companyfacts, tag, unit):
            candidates.append((entry, tag, priority))
    return sorted(candidates, key=lambda item: (item[0].get("end", ""), item[0].get("filed", ""), -item[2], item[0].get("accn", "")), reverse=True)


def _source(entry, tag, unit):
    return {key: entry.get(key) for key in ("start", "end", "form", "fp", "fy", "filed", "accn") if entry.get(key) is not None} | {"tag": tag, "unit": unit}


def extract_annual_fact(companyfacts, tags, unit):
    """Return the latest annual fact with provenance, or an explicit missing record."""
    candidates = _annual_candidates(companyfacts, tags, unit)
    if candidates:
        entry, tag, _ = candidates[0]
        selected_unit = unit or next((key for key, values in companyfacts.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {}).items() if entry in values), None)
        return {"value": entry.get("val"), "unit": selected_unit, "status": "ok", "source": _source(entry, tag, selected_unit)}
    return {"value": None, "unit": unit, "status": "missing", "source": None}


def _prior_annual_value(companyfacts, tags, unit, latest_end):
    candidates = [item for item in _annual_candidates(companyfacts, tags, unit) if item[0].get("end") != latest_end]
    return candidates[0][0].get("val") if candidates else None


def _value(record):
    return record["value"] if record["status"] == "ok" else None


def _derive_liabilities(values):
    liabilities = values["liabilities"]
    assets = values["assets"]
    equity = values["equity"]
    if liabilities["status"] != "missing" or assets["status"] != "ok" or equity["status"] != "ok":
        return liabilities
    assets_end = assets["source"].get("end") if assets["source"] else None
    equity_end = equity["source"].get("end") if equity["source"] else None
    if not assets_end or assets_end != equity_end:
        return liabilities
    return {
        "value": assets["value"] - equity["value"],
        "unit": "USD",
        "status": "derived",
        "source": {"derivedFrom": [assets["source"], equity["source"]], "method": "assets - equity", "end": assets_end, "unit": "USD"},
    }


def build_fundamental_record(ticker, cik, companyfacts):
    values = {
        "revenue": extract_annual_fact(companyfacts, TAG_CANDIDATES["revenue"], "USD"),
        "netIncome": extract_annual_fact(companyfacts, TAG_CANDIDATES["netIncome"], "USD"),
        "assets": extract_annual_fact(companyfacts, TAG_CANDIDATES["assets"], "USD"),
        "liabilities": extract_annual_fact(companyfacts, TAG_CANDIDATES["liabilities"], "USD"),
        "equity": extract_annual_fact(companyfacts, TAG_CANDIDATES["equity"], "USD"),
        "cash": extract_annual_fact(companyfacts, TAG_CANDIDATES["cash"], "USD"),
        "dilutedEps": extract_annual_fact(companyfacts, TAG_CANDIDATES["dilutedEps"], None),
    }
    values["liabilities"] = _derive_liabilities(values)
    revenue = _value(values["revenue"])
    net_income = _value(values["netIncome"])
    latest_end = values["revenue"]["source"].get("end") if values["revenue"]["source"] else None
    prior_revenue = _prior_annual_value(companyfacts, TAG_CANDIDATES["revenue"], "USD", latest_end) if latest_end else None
    metrics = {
        "netMargin": round(net_income / revenue, 6) if revenue not in (None, 0) and net_income is not None else None,
        "revenueGrowthYoY": round(revenue / prior_revenue - 1, 6) if revenue is not None and prior_revenue not in (None, 0) else None,
    }
    return {
        "ticker": ticker.upper(),
        "cik": str(cik).zfill(10),
        "entityName": companyfacts.get("entityName"),
        "latestAnnualEnd": latest_end,
        "values": values,
        "metrics": metrics,
        "status": "partial" if any(item["status"] == "missing" for item in values.values()) else "complete",
    }
