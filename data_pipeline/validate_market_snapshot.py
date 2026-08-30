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
    findings = []
    notes = []
    provider_dates = defaultdict(list)
    total_bars = 0

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

    for symbol, instrument in instruments.items():
        provider = instrument.get("provider") or "unknown"
        calendar = instrument.get("calendar") or provider
        bars = instrument.get("bars") or []
        total_bars += len(bars)
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
