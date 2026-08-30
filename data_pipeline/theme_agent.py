"""Build and validate the backend research-agent contract for theme ranking."""


SYSTEM_PROMPT = """你是一位对冲基金经理，擅长中短线投机交易（swing trade、突破交易等）。
请把输入的行业 ETF 归纳为最多 20 个可解释主题，并按未来 1-2 年强势上涨可能性排序。
结合最新市场热点、概念、催化剂、成分股基本面与公司叙事；所有外部事实必须给出来源 URL 和日期。
不要使用新闻数量作为评分；催化剂必须能解释价格、资金或产业周期。明确写出风险、失效条件和时间周期。
"""


def build_agent_request(catalog: dict, etf_metrics: dict, as_of: str) -> dict:
    """Create a deterministic, source-ready payload for a later AI agent call."""
    universe = catalog.get("industryUniverse", [])
    etfs = []
    for ticker, name, group in universe:
        metrics = etf_metrics.get(ticker, {})
        etfs.append({"ticker": ticker, "name": name, "group": group, "metrics": metrics})
    return {
        "asOf": as_of,
        "systemPrompt": SYSTEM_PROMPT,
        "etfCount": len(etfs),
        "etfs": etfs,
        "requiredOutput": ["rank", "themeId", "score", "leadingStocks", "catalysts", "sourceUrls", "risks", "timeHorizon"],
    }


def validate_agent_output(output: dict, expected_count: int = 20) -> None:
    """Reject incomplete or uncited agent results before they reach the UI."""
    themes = output.get("themes")
    if not isinstance(themes, list) or len(themes) != expected_count:
        raise ValueError(f"agent output must contain exactly {expected_count} themes")
    ranks = [theme.get("rank") for theme in themes]
    if ranks != list(range(1, expected_count + 1)):
        raise ValueError("agent theme ranks must be unique and contiguous")
    for theme in themes:
        if not theme.get("themeId"):
            raise ValueError("agent themeId is required")
        if not isinstance(theme.get("score"), (int, float)) or not 0 <= theme["score"] <= 100:
            raise ValueError(f"invalid score for {theme.get('themeId')}")
        if not isinstance(theme.get("sourceUrls"), list) or not theme["sourceUrls"]:
            raise ValueError(f"sourceUrls are required for {theme.get('themeId')}")
        if not isinstance(theme.get("leadingStocks"), list) or not theme["leadingStocks"]:
            raise ValueError(f"leadingStocks are required for {theme.get('themeId')}")
        if not isinstance(theme.get("catalysts"), list) or not theme["catalysts"]:
            raise ValueError(f"catalysts are required for {theme.get('themeId')}")
