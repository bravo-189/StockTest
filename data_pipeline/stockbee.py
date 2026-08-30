"""Parse and validate the public Stockbee Market Monitor export."""

import csv
import io
from datetime import datetime


REQUIRED_COLUMNS = (
    "Date",
    "Number of stocks up 4% plus today",
    "Number of stocks down 4% plus today",
    "5 day ratio",
    "10 day ratio",
    "T2108",
    "S&P",
)

# These columns are part of the public Market Monitor sheet. They are kept
# optional for backwards-compatible parsing of small fixtures and older
# exports, but are preserved whenever the source provides them.
OPTIONAL_COLUMNS = {
    "up25Quarter": "Number of stocks up 25% plus in a quarter",
    "down25Quarter": "Number of stocks down 25% + in a quarter",
    "up25Month": "Number of stocks up 25% + in a month",
    "down25Month": "Number of stocks down 25% + in a month",
    "up50Month": "Number of stocks up 50% + in a month",
    "down50Month": "Number of stocks down 50% + in a month",
    "up13_34d": "Number of stocks up 13% + in 34 days",
    "down13_34d": "Number of stocks down 13% + in 34 days",
    "wordenUniverse": "Worden Common stock universe",
}

STOCKBEE_SCHEMA = [
    {"key": "up", "source": "Number of stocks up 4% plus today", "label": "4%上涨 · 今日", "group": "primary", "type": "count"},
    {"key": "down", "source": "Number of stocks down 4% plus today", "label": "4%下跌 · 今日", "group": "primary", "type": "count"},
    {"key": "ratio5", "source": "5 day ratio", "label": "5日比率", "group": "primary", "type": "ratio"},
    {"key": "ratio10", "source": "10 day ratio", "label": "10日比率", "group": "primary", "type": "ratio"},
    {"key": "up25Quarter", "source": OPTIONAL_COLUMNS["up25Quarter"], "label": "25%上涨 · 季度", "group": "primary", "type": "count"},
    {"key": "down25Quarter", "source": OPTIONAL_COLUMNS["down25Quarter"], "label": "25%下跌 · 季度", "group": "primary", "type": "count"},
    {"key": "up25Month", "source": OPTIONAL_COLUMNS["up25Month"], "label": "25%上涨 · 月", "group": "secondary", "type": "count"},
    {"key": "down25Month", "source": OPTIONAL_COLUMNS["down25Month"], "label": "25%下跌 · 月", "group": "secondary", "type": "count"},
    {"key": "up50Month", "source": OPTIONAL_COLUMNS["up50Month"], "label": "50%上涨 · 月", "group": "secondary", "type": "count"},
    {"key": "down50Month", "source": OPTIONAL_COLUMNS["down50Month"], "label": "50%下跌 · 月", "group": "secondary", "type": "count"},
    {"key": "up13_34d", "source": OPTIONAL_COLUMNS["up13_34d"], "label": "13%上涨 · 34日", "group": "secondary", "type": "count"},
    {"key": "down13_34d", "source": OPTIONAL_COLUMNS["down13_34d"], "label": "13%下跌 · 34日", "group": "secondary", "type": "count"},
    {"key": "wordenUniverse", "source": OPTIONAL_COLUMNS["wordenUniverse"], "label": "Worden 股票宇宙", "group": "context", "type": "count"},
    {"key": "t2108", "source": "T2108", "label": "T2108", "group": "context", "type": "decimal"},
    {"key": "sp500", "source": "S&P", "label": "S&P 500", "group": "context", "type": "decimal"},
]


def _clean_key(value):
    return " ".join(str(value or "").replace("\ufeff", "").split())


def _clean_number(value, field):
    raw = str(value or "").strip().replace(",", "")
    if not raw:
        raise ValueError(f"{field} must be numeric")
    try:
        number = float(raw)
    except ValueError as exc:
        raise ValueError(f"{field} must be numeric") from exc
    return number


def parse_stockbee_csv(text):
    """Return raw row dictionaries from either CSV or the two-row sheet export."""
    rows = list(csv.reader(io.StringIO(text.lstrip("\ufeff"))))
    header_index = next(
        (
            index
            for index, row in enumerate(rows)
            if "Date" in {_clean_key(cell) for cell in row}
            and "S&P" in {_clean_key(cell) for cell in row}
        ),
        None,
    )
    if header_index is None:
        raise ValueError("Stockbee CSV header is missing")
    headers = [_clean_key(cell) for cell in rows[header_index]]
    parsed = []
    for values in rows[header_index + 1 :]:
        if not any(str(value).strip() for value in values):
            continue
        row = {headers[index]: values[index].strip() if index < len(values) else "" for index in range(len(headers))}
        if row.get("Date"):
            parsed.append(row)
    validate_stockbee_rows(parsed)
    return parsed


def validate_stockbee_rows(rows):
    if not rows:
        raise ValueError("Stockbee rows are empty")
    available = {_clean_key(key) for key in rows[0]}
    missing = [column for column in REQUIRED_COLUMNS if column not in available]
    if missing:
        raise ValueError(f"Stockbee required columns missing: {', '.join(missing)}")


def normalize_stockbee_row(row):
    normalized = {_clean_key(key): value for key, value in row.items()}
    missing = [column for column in REQUIRED_COLUMNS if column not in normalized]
    if missing:
        raise ValueError(f"Stockbee required columns missing: {', '.join(missing)}")
    try:
        date = datetime.strptime(normalized["Date"].strip(), "%m/%d/%Y").date().isoformat()
    except (TypeError, ValueError) as exc:
        raise ValueError("Date must use MM/DD/YYYY") from exc
    normalized_row = {
        "date": date,
        "up": int(_clean_number(normalized["Number of stocks up 4% plus today"], "up")),
        "down": int(_clean_number(normalized["Number of stocks down 4% plus today"], "down")),
        "ratio5": _clean_number(normalized["5 day ratio"], "ratio5"),
        "ratio10": _clean_number(normalized["10 day ratio"], "ratio10"),
        "t2108": _clean_number(normalized["T2108"], "t2108"),
        "sp500": _clean_number(normalized["S&P"], "sp500"),
    }
    for output_key, source_key in OPTIONAL_COLUMNS.items():
        if source_key in normalized and str(normalized[source_key]).strip():
            number = _clean_number(normalized[source_key], output_key)
            normalized_row[output_key] = int(number) if output_key != "wordenUniverse" else int(number)
    return normalized_row


def normalize_stockbee_rows(rows):
    return [normalize_stockbee_row(row) for row in rows]
