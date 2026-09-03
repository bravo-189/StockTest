"""Normalize and validate local market-data snapshots."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


RELATIVE_STRENGTH_LOOKBACKS = {
    "rs1m": 21,
    "rs3m": 63,
    "rs6m": 126,
    "rs12m": 252,
}


def moving_average(bars, period=150):
    """Return the simple moving average of the latest confirmed closes."""
    closes = [
        _optional_number(bar.get("close"))
        for bar in (bars or [])
        if isinstance(bar, dict)
    ]
    closes = [close for close in closes if close is not None]
    if len(closes) < period or period <= 0:
        return None
    return sum(closes[-period:]) / period


def trend_vs_moving_average(bars, period=150):
    """Classify the latest close versus a moving average without using pending bars."""
    ma = moving_average(bars, period)
    closes = [_optional_number(bar.get("close")) for bar in (bars or []) if isinstance(bar, dict)]
    closes = [close for close in closes if close is not None]
    if ma is None or not closes:
        return {"ma": None, "trend": "数据不足"}
    latest = closes[-1]
    return {"ma": round(ma, 6), "trend": "上涨" if latest >= ma else "下降"}


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


def _intraday_time_fields(timestamp, timezone_name):
    try:
        utc_value = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
        local_value = utc_value.astimezone(ZoneInfo(timezone_name))
    except (TypeError, ValueError, OverflowError, OSError, KeyError) as exc:
        raise ValueError("intraday bar timestamp is invalid") from exc
    return {
        "timestamp": utc_value.isoformat().replace("+00:00", "Z"),
        "date": local_value.date().isoformat(),
        "time": local_value.strftime("%H:%M"),
    }


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


def relative_strength_metrics(asset_bars, benchmark_bars):
    """Return excess performance versus the benchmark on shared dates."""
    asset_by_date = {
        bar.get("date"): _optional_number(bar.get("close"))
        for bar in asset_bars or []
        if bar.get("date")
    }
    benchmark_by_date = {
        bar.get("date"): _optional_number(bar.get("close"))
        for bar in benchmark_bars or []
        if bar.get("date")
    }
    shared = [
        date
        for date in sorted(set(asset_by_date) & set(benchmark_by_date))
        if asset_by_date[date] is not None and benchmark_by_date[date] is not None
    ]
    metrics = {}
    for key, lookback in RELATIVE_STRENGTH_LOOKBACKS.items():
        if len(shared) <= lookback:
            metrics[key] = None
            continue
        base_date = shared[-lookback - 1]
        latest_date = shared[-1]
        asset_base = asset_by_date[base_date]
        benchmark_base = benchmark_by_date[base_date]
        asset_latest = asset_by_date[latest_date]
        benchmark_latest = benchmark_by_date[latest_date]
        if not asset_base or not benchmark_base or asset_latest is None or benchmark_latest is None:
            metrics[key] = None
            continue
        asset_return = asset_latest / asset_base
        benchmark_return = benchmark_latest / benchmark_base
        metrics[key] = round((asset_return / benchmark_return - 1) * 100, 2)
    return metrics


def relative_strength_ratings(instruments, universe_tickers):
    """Return 1–99 cross-sectional RS Rating scores for one ETF universe.

    Each period ranks close-to-close total price return among the supplied
    instruments.  The highest return receives 99 and the lowest receives 1.
    Dates are shared across the universe so stale or non-trading-day rows do
    not get compared against a different as-of date.
    """
    eligible = {
        ticker: instruments[ticker]
        for ticker in universe_tickers
        if ticker in instruments and instruments[ticker].get("calendar", "us-equity") == "us-equity"
    }
    ratings = {ticker: {} for ticker in eligible}
    if not eligible:
        return ratings
    date_sets = []
    closes = {}
    for ticker, instrument in eligible.items():
        series = {
            bar.get("date"): _optional_number(bar.get("close"))
            for bar in instrument.get("bars", [])
            if bar.get("date")
        }
        closes[ticker] = series
        date_sets.append({date for date, close in series.items() if close is not None})
    shared_dates = sorted(set.intersection(*date_sets)) if date_sets else []
    for key, lookback in RELATIVE_STRENGTH_LOOKBACKS.items():
        if len(shared_dates) <= lookback:
            continue
        base_date = shared_dates[-lookback - 1]
        latest_date = shared_dates[-1]
        returns = {}
        for ticker in eligible:
            base = closes[ticker].get(base_date)
            latest = closes[ticker].get(latest_date)
            if base and latest is not None:
                returns[ticker] = latest / base - 1
        ordered = sorted(returns.items(), key=lambda item: (-item[1], item[0]))
        count = len(ordered)
        if not count:
            continue
        for position, (ticker, _) in enumerate(ordered, start=1):
            score = 50 if count == 1 else round(1 + ((count - position) / (count - 1)) * 98)
            ratings[ticker][key] = score
    return ratings


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
    bars.sort(key=lambda row: row["date"])
    # Yahoo may return a partially formed current-session daily bar with
    # unstable OHLC bounds. Keep it as pending data instead of rejecting the
    # whole instrument or treating it as a completed close.
    today = datetime.now(timezone.utc).date().isoformat()
    if bars and bars[-1]["date"] >= today:
        latest = bars.pop()
        pending_bar = {"date": latest["date"], "status": "incomplete", **{field: latest.get(field) for field in ("open", "high", "low", "close", "volume")}}
    instrument = _with_latest({"symbol": symbol, "provider": "yahoo-chart", "providerUrl": provider_url, "bars": bars})
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


def normalize_yahoo_intraday(payload, symbol, provider_url, timezone_name="America/New_York", interval_minutes=10):
    """Convert Yahoo intraday chart JSON into timestamped OHLCV bars."""
    results = (((payload or {}).get("chart") or {}).get("result") or [])
    if not results:
        raise ValueError(f"Yahoo intraday chart returned no result for {symbol}")
    result = results[0]
    timestamps = result.get("timestamp") or []
    quotes = ((result.get("indicators") or {}).get("quote") or [])
    quote = quotes[0] if quotes else {}
    bars = []
    now = datetime.now(timezone.utc).timestamp()
    for index, timestamp in enumerate(timestamps):
        try:
            values = {field: quote.get(field, [])[index] for field in ("open", "high", "low", "close", "volume")}
            fields = _intraday_time_fields(timestamp, timezone_name)
            bar = {
                **fields,
                "open": _number(values["open"], "open"),
                "high": _number(values["high"], "high"),
                "low": _number(values["low"], "low"),
                "close": _number(values["close"], "close"),
                "volume": _number(values["volume"], "volume"),
                "status": "incomplete" if float(timestamp) + interval_minutes * 60 > now else "complete",
            }
        except (IndexError, KeyError, TypeError, ValueError):
            continue
        bars.append(bar)
    bars.sort(key=lambda row: row["timestamp"])
    if not bars:
        raise ValueError(f"Yahoo intraday chart returned no valid bars for {symbol}")
    return {"symbol": symbol, "provider": "yahoo-chart", "providerUrl": provider_url, "interval": f"{interval_minutes}m", "timezone": timezone_name, "bars": bars}


def normalize_binance_intraday(rows, symbol, provider_url, interval="1h", timezone_name="UTC"):
    """Convert Binance intraday kline tuples into timestamped OHLCV bars."""
    bars = []
    now_ms = datetime.now(timezone.utc).timestamp() * 1000
    interval_ms = 60 * 60 * 1000 if interval == "1h" else 0
    for row in rows or []:
        if not isinstance(row, (list, tuple)) or len(row) < 7:
            continue
        try:
            fields = _intraday_time_fields(float(row[0]) / 1000, timezone_name)
            bars.append({
                **fields,
                "open": _number(row[1], "open"),
                "high": _number(row[2], "high"),
                "low": _number(row[3], "low"),
                "close": _number(row[4], "close"),
                "volume": _number(row[5], "volume"),
                "status": "complete" if float(row[6]) <= now_ms else "incomplete",
            })
        except (TypeError, ValueError):
            continue
    bars.sort(key=lambda row: row["timestamp"])
    if not bars:
        raise ValueError(f"Binance intraday klines returned no valid bars for {symbol}")
    return {"symbol": symbol, "provider": "binance-spot", "providerUrl": provider_url, "interval": interval, "timezone": timezone_name, "bars": bars}


def select_latest_intraday_session(intraday, minimum_bars=1):
    """Keep the latest local-calendar session while preserving timestamped bars."""
    bars = list((intraday or {}).get("bars") or [])
    if not bars:
        raise ValueError("intraday data has no bars")
    latest_date = max(bar.get("date", "") for bar in bars)
    selected = [bar for bar in bars if bar.get("date") == latest_date]
    if len(selected) < minimum_bars:
        raise ValueError(f"intraday session {latest_date} has {len(selected)} bars; {minimum_bars} required")
    return {**intraday, "latestDate": latest_date, "bars": selected}


def aggregate_intraday_bars(intraday, target_minutes=10, timezone_name="America/New_York", session_start_minutes=570, session_bars=39):
    """Aggregate a finer-grained session (for example Yahoo 5m) into 10m bars."""
    bars = list((intraday or {}).get("bars") or [])
    if not bars or target_minutes <= 0:
        raise ValueError("intraday data cannot be aggregated")
    grouped = {}
    timezone_value = ZoneInfo(timezone_name)
    for bar in bars:
        try:
            stamp = datetime.fromisoformat(str(bar["timestamp"]).replace("Z", "+00:00")).astimezone(timezone_value)
            offset = stamp.hour * 60 + stamp.minute - session_start_minutes
            if offset < 0:
                continue
            bucket = offset // target_minutes
            if bucket >= session_bars:
                continue
            grouped.setdefault((stamp.date().isoformat(), bucket), []).append(bar)
        except (KeyError, TypeError, ValueError):
            continue
    result = []
    for key in sorted(grouped):
        chunk = sorted(grouped[key], key=lambda row: row["timestamp"])
        first, last = chunk[0], chunk[-1]
        result.append({
            "timestamp": first["timestamp"],
            "date": first["date"],
            "time": first["time"],
            "open": first["open"],
            "high": max(row["high"] for row in chunk),
            "low": min(row["low"] for row in chunk),
            "close": last["close"],
            "volume": sum(row["volume"] for row in chunk),
            "status": "incomplete" if any(row.get("status") == "incomplete" for row in chunk) else "complete",
        })
    if not result:
        raise ValueError("intraday aggregation returned no session bars")
    return {**intraday, "interval": f"{target_minutes}m", "timezone": timezone_name, "bars": result}


def validate_intraday_bars(intraday, minimum_bars=1):
    if not isinstance(intraday, dict) or not intraday.get("symbol"):
        raise ValueError("intraday symbol is missing")
    bars = intraday.get("bars") or []
    if len(bars) < minimum_bars:
        raise ValueError(f"{intraday['symbol']} has {len(bars)} intraday bars; {minimum_bars} required")
    timestamps = [bar.get("timestamp") for bar in bars]
    if any(not value for value in timestamps) or timestamps != sorted(timestamps) or len(set(timestamps)) != len(timestamps):
        raise ValueError(f"{intraday['symbol']} intraday bars must have unique ascending timestamps")
    for bar in bars:
        values = [bar.get(field) for field in ("open", "high", "low", "close", "volume")]
        if any(value is None for value in values):
            raise ValueError(f"{intraday['symbol']} has an incomplete intraday bar")
        if bar["high"] < max(bar["open"], bar["close"]) or bar["low"] > min(bar["open"], bar["close"]) or bar["high"] < bar["low"]:
            raise ValueError(f"{intraday['symbol']} has invalid intraday OHLC bounds")
        if bar["volume"] < 0:
            raise ValueError(f"{intraday['symbol']} has negative intraday volume")


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
        intraday_bars = instrument.get("intradayBars") or []
        if intraday_bars:
            intraday = {
                "symbol": instrument.get("symbol"),
                "bars": intraday_bars,
            }
            validate_intraday_bars(intraday, minimum_bars=1)
