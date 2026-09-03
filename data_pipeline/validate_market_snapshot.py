"""Profile and quality-check a local StockTest market snapshot."""

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path


NUMERIC_FIELDS = ("open", "high", "low", "close", "volume")


def _finding(check, severity, evidence, risk, confidence="high"):
    return {
        "check": check,
        "severity": severity,
        "evidence": evidence,
        "risk": risk,
        "confidence": confidence,
    }


def _finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def analyze_snapshot(snapshot, min_bars=21):
    """Return an inspectable quality report without mutating the snapshot."""
    metadata = snapshot.get("metadata") or {}
    instruments = snapshot.get("instruments") or {}
    required = int(metadata.get("requiredCount") or len(instruments))
    loaded = int(metadata.get("loadedCount") or len(instruments))
    missing = metadata.get("missing") or []
    pending = snapshot.get("pendingBars") or []
    holdings = snapshot.get("holdings") or {}
    holdings_meta = metadata.get("holdings") or {}
    findings = []
    notes = []
    provider_dates = defaultdict(list)
    total_bars = 0
    intraday_summary = {}

    if required != loaded:
        findings.append(_finding(
            "coverage",
            "high",
            f"loaded {loaded} of required {required}; missing {len(missing)}",
            "核心市场或行业数据缺失会让页面排序和比较失真",
        ))

    if len(instruments) != loaded:
        findings.append(_finding(
            "loaded_count_consistency",
            "high",
            f"metadata loadedCount={loaded}, instrument keys={len(instruments)}",
            "元数据与实际记录数量不一致，可能导致状态条误报",
        ))

    if len(pending) != int(metadata.get("pendingCount") or 0):
        findings.append(_finding(
            "pending_count_consistency",
            "medium",
            f"metadata pendingCount={metadata.get('pendingCount', 0)}, pendingBars={len(pending)}",
            "未收盘提示数量可能与实际记录不一致",
        ))

    if holdings_meta:
        holdings_required = int(holdings_meta.get("requestedCount") or len(holdings))
        holdings_loaded = int(holdings_meta.get("loadedCount") or len(holdings))
        holdings_missing = holdings_meta.get("missing") or []
        if holdings_required != holdings_loaded or holdings_missing:
            findings.append(_finding(
                "holdings_coverage",
                "high",
                f"holdings loaded {holdings_loaded} of requested {holdings_required}; missing {len(holdings_missing)}",
                "持仓缺口会让前十大权重股入口和行业比较失真",
            ))
        for symbol in ("IBIT", "USO"):
            record = holdings.get(symbol)
            if record and record.get("coverageStatus") != "complete":
                findings.append(_finding(
                    "holdings_source_coverage",
                    "high",
                    f"{symbol} coverageStatus={record.get('coverageStatus', 'unknown')}",
                    "发行方持仓来源未完整加载时，页面可能显示不完整或错误的权重股",
                ))
        rank_issues = []
        duplicate_issues = []
        invalid_weight_issues = []
        unit_issues = []
        for symbol, record in holdings.items():
            if not isinstance(record, dict):
                continue
            rows = record.get("holdings") if isinstance(record.get("holdings"), list) else []
            ranks = [row.get("rank") for row in rows if isinstance(row, dict)]
            if ranks and ranks != list(range(1, len(ranks) + 1)):
                rank_issues.append(symbol)
            tickers = [str(row.get("ticker") or "").strip().upper() for row in rows if isinstance(row, dict)]
            if len(tickers) != len(set(tickers)):
                duplicate_issues.append(symbol)
            for row in rows:
                if not isinstance(row, dict):
                    continue
                weight = row.get("weight")
                if weight is not None and (not _finite(weight) or weight < 0):
                    invalid_weight_issues.append(symbol)
                if row.get("weightUnit") not in (None, "percent"):
                    unit_issues.append(symbol)
        if rank_issues:
            findings.append(_finding(
                "holdings_rank_sequence",
                "medium",
                f"rank gaps in {', '.join(sorted(set(rank_issues)))}",
                "前十大名单的排名可能与来源顺序不一致",
            ))
        if duplicate_issues:
            findings.append(_finding(
                "holdings_duplicate_ticker",
                "medium",
                f"duplicate tickers in {', '.join(sorted(set(duplicate_issues)))}",
                "重复代码会让前十大名单误计或掩盖真实持仓",
            ))
        if invalid_weight_issues:
            findings.append(_finding(
                "holdings_invalid_weight",
                "high",
                f"invalid weights in {', '.join(sorted(set(invalid_weight_issues)))}",
                "非法权重会让持仓数据产生错误的比例解释",
            ))
        if unit_issues:
            findings.append(_finding(
                "holdings_weight_unit",
                "high",
                f"unsupported weight units in {', '.join(sorted(set(unit_issues)))}",
                "不同来源的权重单位不一致会直接造成百分比展示错误",
            ))

    for symbol, instrument in instruments.items():
        provider = instrument.get("provider") or "unknown"
        calendar = instrument.get("calendar") or provider
        raw_bars = instrument.get("bars") or []
        malformed_bars = sum(1 for bar in raw_bars if not isinstance(bar, dict))
        bars = [bar for bar in raw_bars if isinstance(bar, dict)]
        total_bars += len(bars)
        if malformed_bars:
            findings.append(_finding(
                "malformed_bars",
                "high",
                f"{symbol} contains {malformed_bars} non-object daily bars",
                "无法从非结构化 K 线计算 RSI、收益和趋势",
            ))
        intraday_bars = instrument.get("intradayBars") or []
        if intraday_bars:
            timestamps = [bar.get("timestamp") for bar in intraday_bars]
            intraday_summary[symbol] = {
                "interval": (instrument.get("intraday") or {}).get("interval"),
                "latestDate": (instrument.get("intraday") or {}).get("latestDate"),
                "barCount": len(intraday_bars),
                "firstTimestamp": timestamps[0] if timestamps else None,
                "lastTimestamp": timestamps[-1] if timestamps else None,
                "incompleteCount": sum(1 for bar in intraday_bars if bar.get("status") == "incomplete"),
            }
            if timestamps != sorted(timestamps) or len(set(timestamps)) != len(timestamps):
                findings.append(_finding(
                    "intraday_timestamp_order",
                    "high",
                    f"{symbol} intraday timestamps are not unique and ascending",
                    "日内趋势图会出现重复或倒序数据",
                ))
            for bar in intraday_bars:
                values = [bar.get(field) for field in NUMERIC_FIELDS]
                if any(not _finite(value) for value in values):
                    findings.append(_finding(
                        "intraday_numeric_values",
                        "high",
                        f"{symbol} has non-finite intraday OHLCV",
                        "日内图表和价格悬停提示可能失真",
                    ))
                    break
                if bar["high"] < max(bar["open"], bar["close"]) or bar["low"] > min(bar["open"], bar["close"]) or bar["high"] < bar["low"]:
                    findings.append(_finding(
                        "intraday_invalid_ohlc_bounds",
                        "high",
                        f"{symbol} has invalid intraday OHLC bounds",
                        "日内价格区间不可能，可能导致面积图误读",
                    ))
                    break
        dates = [bar.get("date") for bar in bars]
        if dates:
            provider_dates[calendar].extend(dates)
        if len(bars) < min_bars:
            findings.append(_finding(
                "minimum_bar_count",
                "high",
                f"{symbol} has {len(bars)} bars; {min_bars} required",
                "RSI14、一个月 K 线和多周期收益可能无法计算",
            ))
        if ("trend150" in instrument or "ma150" in instrument) and (
            instrument.get("trend150") == "数据不足" or instrument.get("ma150") is None
        ):
            findings.append(_finding(
                "trend150_insufficient",
                "medium",
                f"{symbol} has {len(bars)} confirmed daily bars; MA150 unavailable",
                "页面不应把数据不足的 MA150 趋势解释为上涨或下降",
            ))
        if len(set(dates)) != len(dates):
            findings.append(_finding(
                "duplicate_bar_dates",
                "high",
                f"{symbol} contains duplicate bar dates",
                "重复交易日会重复计权并污染收益和图表",
            ))
        if dates != sorted(dates):
            findings.append(_finding(
                "bar_date_order",
                "high",
                f"{symbol} bar dates are not ascending",
                "时间序列顺序错误会反转趋势和变化率",
            ))
        for bar in bars:
            values = [bar.get(field) for field in NUMERIC_FIELDS]
            if any(not _finite(value) for value in values):
                findings.append(_finding(
                    "numeric_values",
                    "high",
                    f"{symbol} has non-finite OHLCV on {bar.get('date')}",
                    "非法数值会破坏指标计算和前端绘图",
                ))
                break
            if bar["high"] < max(bar["open"], bar["close"]) or bar["low"] > min(bar["open"], bar["close"]) or bar["high"] < bar["low"]:
                findings.append(_finding(
                    "invalid_ohlc_bounds",
                    "high",
                    f"{symbol} has invalid OHLC bounds on {bar.get('date')}",
                    "价格边界不可能，可能导致收益和蜡烛图误读",
                ))
                break
            if bar["volume"] < 0:
                findings.append(_finding(
                    "negative_volume",
                    "high",
                    f"{symbol} has negative volume on {bar.get('date')}",
                    "成交量方向错误会影响流动性判断",
                ))
                break
        if bars and instrument.get("latestDate") != bars[-1].get("date"):
            findings.append(_finding(
                "latest_date_pointer",
                "medium",
                f"{symbol} latestDate={instrument.get('latestDate')} but last bar={bars[-1].get('date')}",
                "页面可能显示与走势图不一致的最新日期",
            ))

    ranges = {}
    for calendar, dates in sorted(provider_dates.items()):
        ranges[calendar] = {"earliest": min(dates), "latest": max(dates), "instrumentCount": sum(1 for item in instruments.values() if (item.get("calendar") or item.get("provider") or "unknown") == calendar)}
    latest_dates = {value["latest"] for value in ranges.values()}
    if len(latest_dates) > 1:
        notes.append({
            "check": "calendar_note",
            "severity": "info",
            "evidence": " | ".join(f"{calendar}: {value['earliest']} → {value['latest']}" for calendar, value in ranges.items()),
            "message": "不同交易日历是预期差异；跨资产比较使用共同观察日，不补造缺失 K 线。",
        })

    coverage_rate = round(loaded / required, 4) if required else 0.0
    return {
        "summary": {
            "requiredCount": required,
            "loadedCount": loaded,
            "coverageRate": coverage_rate,
            "instrumentCount": len(instruments),
            "totalBars": total_bars,
            "pendingCount": len(pending),
            "findingCount": len(findings),
        },
        "providerDateRanges": ranges,
        "intraday": intraday_summary,
        "notes": notes,
        "findings": findings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a StockTest market snapshot")
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--min-bars", type=int, default=21)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    report = analyze_snapshot(snapshot, min_bars=args.min_bars)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if any(item["severity"] in {"critical", "high"} for item in report["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
