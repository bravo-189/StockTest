"""Normalize and validate local market-data snapshots."""

from datetime import datetime, timezone


def _number(value, field):
    if value is None or value == "":
        raise ValueError(f"{field} is missing")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc


def _optional_number(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _date_from_ms(timestamp):
    try:
        return datetime.fromtimestamp(float(timestamp) / 1000, tz=timezone.utc).date().isoformat()
    except (TypeError, ValueError, OverflowError, OSError) as exc:
        raise ValueError("bar timestamp is invalid") from exc


def _date_from_seconds(timestamp):
    try:
        return datetime.fromtimestamp(float(timestamp), tz=timezone.utc).date().isoformat()
    except (TypeError, ValueError, OverflowError, OSError) as exc:
        raise ValueError("bar timestamp is invalid") from exc


def _with_latest(instrument):
    bars = instrument["bars"]
    latest = bars[-1]
    previous = bars[-2] if len(bars) > 1 else None
    change = None
    if previous and previous["close"]:
        change = round((latest["close"] - previous["close"]) / previous["close"] * 100, 4)
    instrument["latest"] = {"date": latest["date"], "close": latest["close"], "change": change}
    instrument["latestDate"] = latest["date"]
    return instrument


def normalize_yahoo_chart(payload, symbol, provider_url):
    """Convert Yahoo chart JSON into the common instrument contract."""
    results = (((payload or {}).get("chart") or {}).get("result") or [])
    if not results:
        raise ValueError(f"Yahoo chart returned no result for {symbol}")
    result = results[0]
    timestamps = result.get("timestamp") or []
    quotes = ((result.get("indicators") or {}).get("quote") or [])
    quote = quotes[0] if quotes else {}
    bars = []
    pending_bar = None
    if timestamps:
        last_index = len(timestamps) - 1
        latest_values = {field: quote.get(field, [])[last_index] if last_index < len(quote.get(field, [])) else None for field in ("open", "high", "low", "close", "volume")}
        if any(value is None or value == "" for value in latest_values.values()):
            pending_bar = {"date": _date_from_seconds(timestamps[last_index]), "status": "incomplete", **{field: _optional_number(value) for field, value in latest_values.items()}}
    for index, timestamp in enumerate(timestamps):
        try:
            values = {field: quote.get(field, [])[index] for field in ("open", "high", "low", "close", "volume")}
            bar = {"date": _date_from_seconds(timestamp), **{field: _number(value, field) for field, value in values.items()}}
        except (IndexError, KeyError, TypeError, ValueError):
            continue
        bars.append(bar)
    instrument = _with_latest({"symbol": symbol, "provider": "yahoo-chart", "providerUrl": provider_url, "bars": sorted(bars, key=lambda row: row["date"])})
    if pending_bar:
        instrument["pendingBar"] = pending_bar
    return instrument


def normalize_binance_klines(rows, symbol, provider_url):
    """Convert Binance Spot kline tuples into the common instrument contract."""
    bars = []
    for row in rows or []:
        if not isinstance(row, (list, tuple)) or len(row) < 6:
            continue
        try:
            bars.append({"date": _date_from_ms(row[0]), "open": _number(row[1], "open"), "high": _number(row[2], "high"), "low": _number(row[3], "low"), "close": _number(row[4], "close"), "volume": _number(row[5], "volume")})
        except (TypeError, ValueError):
            continue
    return _with_latest({"symbol": symbol, "provider": "binance-spot", "providerUrl": provider_url, "bars": sorted(bars, key=lambda row: row["date"])})


def validate_instrument(instrument, min_bars=21):
    if not isinstance(instrument, dict) or not instrument.get("symbol"):
        raise ValueError("instrument symbol is missing")
    bars = instrument.get("bars") or []
    if len(bars) < min_bars:
        raise ValueError(f"{instrument['symbol']} has {len(bars)} bars; {min_bars} required")
    dates = [bar.get("date") for bar in bars]
    if any(not date for date in dates) or dates != sorted(dates) or len(set(dates)) != len(dates):
        raise ValueError(f"{instrument['symbol']} bars must have unique ascending dates")
    for bar in bars:
        values = [bar.get(field) for field in ("open", "high", "low", "close", "volume")]
        if any(value is None for value in values):
            raise ValueError(f"{instrument['symbol']} has an incomplete bar")
        if bar["high"] < max(bar["open"], bar["close"]) or bar["low"] > min(bar["open"], bar["close"]) or bar["high"] < bar["low"]:
            raise ValueError(f"{instrument['symbol']} has invalid OHLC bounds on {bar['date']}")
        if bar["volume"] < 0:
            raise ValueError(f"{instrument['symbol']} has negative volume on {bar['date']}")


def validate_market_snapshot(snapshot, min_bars=21):
    instruments = (snapshot or {}).get("instruments") or {}
    if not instruments:
        raise ValueError("market snapshot has no instruments")
    for instrument in instruments.values():
        validate_instrument(instrument, min_bars=min_bars)
