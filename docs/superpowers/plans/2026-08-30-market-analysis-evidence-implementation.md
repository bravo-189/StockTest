# StockTest Market Analysis Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hardcoded homepage market regime and briefing with a deterministic, source-backed after-hours analysis generated from the existing local market and Stockbee snapshots.

**Architecture:** A focused Python module reads the existing snapshots plus a source whitelist, computes five transparent factors, validates every claim-to-evidence reference, and atomically writes `data/market_analysis.json`. The existing refresh process invokes this module after successful snapshot refreshes, and the vanilla JavaScript page hydrates the hero card and a new evidence drawer from that local file.

**Tech Stack:** Python 3 standard library, `unittest`, vanilla JavaScript, HTML, CSS, local JSON, Git/GitHub.

**Spec:** `docs/superpowers/specs/2026-08-30-market-analysis-evidence-design.md`

## Global Constraints

- Do not modify, rename, move, or delete anything under `sources/`.
- Browser code reads local JSON only and never calls Yahoo, Binance, Stockbee, SEC, news, or X directly.
- The first phase uses only Yahoo Chart, Binance public klines, Stockbee Market Monitor, refresh status, and the local quality report.
- AI does not calculate or override scores in this phase.
- A formal claim without at least one valid evidence ID is rejected.
- `lead` evidence never changes factor or composite scores.
- BTC is aligned to the US-equity `asOf` date; weekend BTC data cannot enter Friday's formal analysis.
- Do not restore the paused theme module, standalone fundamentals UI, mini-program, database, task queue, or frontend framework.
- Use TDD for each behavior change and keep existing 50 tests passing.
- Generated `data/market_analysis.json` remains local and ignored by Git.

Run every PowerShell command from the project parent directory after defining the verified bundled runtimes once:

```powershell
$PythonExe = 'C:\Users\i023j\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$NodeExe = 'C:\Users\i023j\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
```

---

### Task 1: Source whitelist and contract validator

**Files:**
- Create: `data/source_registry.json`
- Create: `data_pipeline/market_analysis.py`
- Create: `data_pipeline/test_market_analysis.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `load_source_registry(path: Path) -> dict[str, dict]`
- Produces: `validate_analysis(analysis: dict, registry: dict[str, dict]) -> None`
- Produces: `write_analysis(path: Path, analysis: dict, registry: dict[str, dict]) -> None`

- [ ] **Step 1: Add failing source and claim validation tests**

```python
from pathlib import Path
import tempfile
import unittest

from StockTest.data_pipeline.market_analysis import load_source_registry, validate_analysis


class MarketAnalysisContractTests(unittest.TestCase):
    def test_rejects_unknown_source_and_missing_evidence_reference(self):
        registry = {"stockbee-market-monitor": {"id": "stockbee-market-monitor", "enabled": True}}
        analysis = {
            "schemaVersion": "1.0",
            "evidence": [{"id": "e1", "sourceId": "unknown", "quality": "confirmed"}],
            "claims": [{"id": "c1", "kind": "fact", "text": "x", "evidenceIds": ["missing"]}],
        }
        with self.assertRaisesRegex(ValueError, "unknown source"):
            validate_analysis(analysis, registry)

    def test_rejects_lead_as_formal_claim_evidence(self):
        registry = {"manual-x": {"id": "manual-x", "enabled": True, "affectsScore": False}}
        analysis = {
            "schemaVersion": "1.0",
            "evidence": [{"id": "x1", "sourceId": "manual-x", "quality": "lead"}],
            "claims": [{"id": "c1", "kind": "fact", "text": "x", "evidenceIds": ["x1"]}],
        }
        with self.assertRaisesRegex(ValueError, "lead evidence"):
            validate_analysis(analysis, registry)
```

- [ ] **Step 2: Run the new tests and verify the module import fails**

Run from the project parent directory:

```powershell
& $PythonExe -m unittest StockTest.data_pipeline.test_market_analysis.MarketAnalysisContractTests -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'StockTest.data_pipeline.market_analysis'`.

- [ ] **Step 3: Add the initial source registry**

Create `data/source_registry.json` with four enabled first-phase sources and disabled future official sources:

```json
{
  "schemaVersion": "1.0",
  "sources": [
    {"id": "yahoo-chart", "name": "Yahoo Chart", "category": "market-price", "tier": 1, "mode": "automatic", "url": "https://finance.yahoo.com/", "enabled": true, "affectsScore": true},
    {"id": "binance-public-klines", "name": "Binance Public Klines", "category": "crypto-price", "tier": 1, "mode": "automatic", "url": "https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints", "enabled": true, "affectsScore": true},
    {"id": "stockbee-market-monitor", "name": "Stockbee Market Monitor", "category": "market-breadth", "tier": 1, "mode": "automatic", "url": "https://stockbee.blogspot.com/p/mm.html", "enabled": true, "affectsScore": true},
    {"id": "stocktest-quality-report", "name": "StockTest Quality Report", "category": "data-quality", "tier": 1, "mode": "automatic", "url": "local://data/market_snapshot_quality.json", "enabled": true, "affectsScore": false},
    {"id": "sec-edgar", "name": "SEC EDGAR", "category": "company-filings", "tier": 1, "mode": "automatic", "url": "https://data.sec.gov/", "enabled": false, "affectsScore": false},
    {"id": "federal-reserve", "name": "Federal Reserve", "category": "macro-official", "tier": 1, "mode": "automatic", "url": "https://www.federalreserve.gov/feeds/feeds.htm", "enabled": false, "affectsScore": false},
    {"id": "bls-public-data", "name": "BLS Public Data", "category": "macro-official", "tier": 1, "mode": "automatic", "url": "https://www.bls.gov/developers/", "enabled": false, "affectsScore": false},
    {"id": "bea-api", "name": "BEA Data API", "category": "macro-official", "tier": 1, "mode": "automatic", "url": "https://apps.bea.gov/api/", "enabled": false, "affectsScore": false},
    {"id": "us-treasury-fiscal-data", "name": "U.S. Treasury Fiscal Data", "category": "macro-official", "tier": 1, "mode": "automatic", "url": "https://fiscaldata.treasury.gov/", "enabled": false, "affectsScore": false},
    {"id": "ssga-holdings", "name": "State Street ETF Holdings", "category": "etf-holdings", "tier": 1, "mode": "automatic", "url": "https://www.ssga.com/", "enabled": false, "affectsScore": false},
    {"id": "ishares-holdings", "name": "iShares ETF Holdings", "category": "etf-holdings", "tier": 1, "mode": "automatic", "url": "https://www.ishares.com/", "enabled": false, "affectsScore": false},
    {"id": "vanguard-holdings", "name": "Vanguard ETF Holdings", "category": "etf-holdings", "tier": 1, "mode": "automatic", "url": "https://investor.vanguard.com/", "enabled": false, "affectsScore": false}
  ]
}
```

- [ ] **Step 4: Implement registry loading and contract validation**

Implement `load_source_registry` to reject duplicate IDs and return enabled and disabled sources by ID. Implement `validate_analysis` to enforce unique evidence/claim IDs, known enabled sources, allowed qualities/kinds, existing evidence references, and non-lead evidence for `fact`, `inference`, and `scenario`. Implement `write_analysis` with the existing atomic temp-file pattern used by `refresh_local_data.py`.

```python
FORMAL_KINDS = {"fact", "inference", "scenario"}
ALLOWED_KINDS = FORMAL_KINDS | {"watch", "lead"}
ALLOWED_QUALITIES = {"confirmed", "stale", "partial", "lead"}


def validate_analysis(analysis, registry):
    evidence_by_id = {}
    for item in analysis.get("evidence", []):
        evidence_id = item.get("id")
        if not evidence_id or evidence_id in evidence_by_id:
            raise ValueError(f"duplicate or missing evidence id: {evidence_id}")
        source = registry.get(item.get("sourceId"))
        if not source or not source.get("enabled"):
            raise ValueError(f"unknown source: {item.get('sourceId')}")
        if item.get("quality") not in ALLOWED_QUALITIES:
            raise ValueError(f"invalid evidence quality: {item.get('quality')}")
        evidence_by_id[evidence_id] = item
    for claim in analysis.get("claims", []):
        kind = claim.get("kind")
        references = claim.get("evidenceIds") or []
        if kind not in ALLOWED_KINDS:
            raise ValueError(f"invalid claim kind: {kind}")
        missing = [item for item in references if item not in evidence_by_id]
        if missing:
            raise ValueError(f"missing evidence reference: {missing[0]}")
        if kind in FORMAL_KINDS and (not references or all(evidence_by_id[item]["quality"] == "lead" for item in references)):
            raise ValueError("formal claim cannot rely on lead evidence")
```

- [ ] **Step 5: Ignore only the generated analysis snapshot**

Append `data/market_analysis.json` to `.gitignore`. Keep `data/source_registry.json` tracked.

- [ ] **Step 6: Run contract tests and commit**

```powershell
& $PythonExe -m unittest StockTest.data_pipeline.test_market_analysis.MarketAnalysisContractTests -v
git add .gitignore data/source_registry.json data_pipeline/market_analysis.py data_pipeline/test_market_analysis.py
git commit -m "feat: add market analysis evidence contract"
```

Expected: contract tests PASS.

---

### Task 2: Deterministic factor scoring and date alignment

**Files:**
- Modify: `data_pipeline/market_analysis.py`
- Modify: `data_pipeline/test_market_analysis.py`

**Interfaces:**
- Produces: `calculate_return(bars: list[dict], as_of: str, periods: int) -> float | None`
- Produces: `calculate_rsi(bars: list[dict], as_of: str, periods: int = 14) -> float | None`
- Produces: `score_factors(market: dict, stockbee: dict, as_of: str) -> list[dict]`
- Produces: `state_for_score(score: int) -> str`

- [ ] **Step 1: Add failing boundary and BTC alignment tests**

```python
def make_bars(multiplier=1.0):
    return [
        {
            "date": f"2026-08-{day:02d}",
            "open": (100 + day - 1) * multiplier,
            "high": (101 + day) * multiplier,
            "low": (99 + day - 1) * multiplier,
            "close": (100 + day) * multiplier,
            "volume": 1000.0,
        }
        for day in range(1, 29)
    ]


def make_market_fixture():
    instruments = {}
    for symbol in ["SPX", "NDX", "DJI", "RUT"]:
        instruments[symbol] = {"symbol": symbol, "kind": "index", "provider": "yahoo-chart", "calendar": "us-equity", "bars": make_bars()}
    for symbol in ["SPY", "XLU", "XLP", "XLV", "XLK", "XLY", "XLC", "ARKK", "XLF", "XLI", "XLE", "XLB", "XLRE", "IBIT"]:
        instruments[symbol] = {"symbol": symbol, "kind": "sector", "provider": "yahoo-chart", "calendar": "us-equity", "bars": make_bars()}
    for index in range(60):
        symbol = f"IND{index:02d}"
        instruments[symbol] = {"symbol": symbol, "kind": "industry", "provider": "yahoo-chart", "calendar": "us-equity", "bars": make_bars(1 + index / 1000)}
    instruments["BTC"] = {"symbol": "BTC", "kind": "crypto", "provider": "binance", "calendar": "crypto-24x7", "bars": make_bars() + [{"date": "2026-08-29", "close": 180.0}]}
    return {"metadata": {"comparisonDate": "2026-08-28", "missing": [], "sourceStatus": "loaded"}, "instruments": instruments}


def make_stockbee_fixture():
    return {
        "metadata": {"latestDate": "2026-08-28", "fetchedAt": "2026-08-30T09:00:00Z", "sourceStatus": "loaded"},
        "source": {"pageUrl": "https://stockbee.blogspot.com/p/mm.html"},
        "rows": [{"date": "2026-08-28", "up": 300, "down": 150, "ratio5": 1.6, "ratio10": 1.3, "t2108": 56.0}],
    }


def make_registry_fixture():
    return {
        "yahoo-chart": {"id": "yahoo-chart", "enabled": True, "affectsScore": True},
        "binance-public-klines": {"id": "binance-public-klines", "enabled": True, "affectsScore": True},
        "stockbee-market-monitor": {"id": "stockbee-market-monitor", "enabled": True, "affectsScore": True},
        "stocktest-quality-report": {"id": "stocktest-quality-report", "enabled": True, "affectsScore": False},
    }


class MarketFactorTests(unittest.TestCase):
    def test_btc_uses_us_equity_as_of_instead_of_weekend_latest(self):
        bars = [
            {"date": "2026-08-27", "close": 100.0},
            {"date": "2026-08-28", "close": 101.0},
            {"date": "2026-08-29", "close": 150.0},
            {"date": "2026-08-30", "close": 200.0},
        ]
        self.assertAlmostEqual(calculate_return(bars, "2026-08-28", 1), 1.0)

    def test_state_thresholds_cover_full_score_range(self):
        self.assertEqual(state_for_score(7), "强势上涨")
        self.assertEqual(state_for_score(3), "偏强")
        self.assertEqual(state_for_score(0), "震荡")
        self.assertEqual(state_for_score(-3), "偏弱")
        self.assertEqual(state_for_score(-7), "下跌")
```

- [ ] **Step 2: Run focused tests and verify missing functions fail**

```powershell
& $PythonExe -m unittest StockTest.data_pipeline.test_market_analysis.MarketFactorTests -v
```

Expected: FAIL with import/name errors for the scoring functions.

- [ ] **Step 3: Implement as-of-safe metric helpers**

Filter bars with `bar["date"] <= as_of` before selecting the current and comparison closes. Return `None` when history is insufficient. Use the same Wilder-style RSI calculation already used by the browser metrics so Python analysis and UI values do not diverge.

- [ ] **Step 4: Implement all five factor rules exactly from the spec**

Return factors in stable order with this shape:

```python
{
    "id": "trend",
    "label": "趋势",
    "score": 1,
    "status": "available",
    "summary": "四大指数中多数 5 日和 20 日收益为正。",
    "evidenceIds": ["market-2026-08-28-SPX-d5", "market-2026-08-28-SPX-d20"]
}
```

Do not substitute zero for missing factors. Use `score: None` and `status: "unavailable"` when required inputs are absent.

- [ ] **Step 5: Run factor tests and full baseline tests**

```powershell
& $PythonExe -m unittest StockTest.data_pipeline.test_market_analysis.MarketFactorTests -v
& $PythonExe -m unittest discover -s StockTest/data_pipeline -p 'test_*.py' -q
```

Expected: new factor tests PASS and all existing tests remain PASS.

- [ ] **Step 6: Commit factor scoring**

```powershell
git add data_pipeline/market_analysis.py data_pipeline/test_market_analysis.py
git commit -m "feat: score source-backed market factors"
```

---

### Task 3: Build claims, confidence, and the local analysis snapshot

**Files:**
- Modify: `data_pipeline/market_analysis.py`
- Modify: `data_pipeline/test_market_analysis.py`
- Create locally, ignored: `data/market_analysis.json`

**Interfaces:**
- Produces: `build_market_analysis(market: dict, stockbee: dict, refresh: dict, registry: dict, generated_at: str | None = None) -> dict`
- Produces CLI: `python -m StockTest.data_pipeline.market_analysis --data-dir StockTest/data`

- [ ] **Step 1: Add failing deterministic-output and confidence tests**

```python
class MarketAnalysisBuildTests(unittest.TestCase):
    def setUp(self):
        self.market = make_market_fixture()
        self.stockbee = make_stockbee_fixture()
        self.refresh = {"status": "ok", "sources": {}}
        self.registry = make_registry_fixture()

    def test_same_inputs_produce_same_research_content(self):
        first = build_market_analysis(self.market, self.stockbee, self.refresh, self.registry, "2026-08-30T10:00:00Z")
        second = build_market_analysis(self.market, self.stockbee, self.refresh, self.registry, "2026-08-30T10:00:00Z")
        self.assertEqual(first, second)
        self.assertTrue(all(item["evidenceIds"] for item in first["briefing"]))

    def test_partial_refresh_lowers_confidence(self):
        ok = build_market_analysis(self.market, self.stockbee, {"status": "ok", "sources": {}}, self.registry)
        partial = build_market_analysis(self.market, self.stockbee, {"status": "partial", "sources": {}}, self.registry)
        self.assertAlmostEqual(ok["confidence"] - partial["confidence"], 0.10, places=2)
```

- [ ] **Step 2: Run focused tests and verify they fail**

```powershell
& $PythonExe -m unittest StockTest.data_pipeline.test_market_analysis.MarketAnalysisBuildTests -v
```

- [ ] **Step 3: Implement evidence and claim construction**

Create evidence for each metric actually used by a factor. Use stable IDs containing type, date, ticker or Stockbee field. Build a stable `claims` array, then reference claim IDs from `briefing` and `watchNext`.

```python
analysis = {
    "schemaVersion": "1.0",
    "analysisId": f"us-close-{as_of}",
    "asOf": as_of,
    "generatedAt": generated_at or _timestamp(),
    "mode": "rules-only",
    "state": state_for_score(composite),
    "score": composite,
    "confidence": confidence,
    "headline": headline,
    "summary": summary,
    "factors": factors,
    "briefing": briefing[:3],
    "watchNext": watch_next[:3],
    "claims": claims,
    "evidence": evidence,
    "dataQuality": data_quality,
    "provenance": {"market": market["metadata"], "stockbee": stockbee["metadata"]},
}
```

- [ ] **Step 4: Implement confidence deductions and wording guardrails**

Apply exact spec deductions, clamp to `0.30..1.00`, and use low-confidence templates without “确认” or “明确” when confidence is below `0.60`.

- [ ] **Step 5: Add CLI and atomically generate the real local file**

```powershell
& $PythonExe -m StockTest.data_pipeline.market_analysis --data-dir StockTest/data
```

Expected: `StockTest/data/market_analysis.json` exists, passes `validate_analysis`, and remains ignored by Git.

- [ ] **Step 6: Run tests and commit**

```powershell
& $PythonExe -m unittest StockTest.data_pipeline.test_market_analysis -v
git check-ignore StockTest/data/market_analysis.json
git add data_pipeline/market_analysis.py data_pipeline/test_market_analysis.py
git commit -m "feat: generate deterministic market analysis"
```

---

### Task 4: Integrate analysis generation into local refresh

**Files:**
- Modify: `data_pipeline/refresh_local_data.py`
- Modify: `data_pipeline/test_refresh_local_data.py`

**Interfaces:**
- Consumes: `build_market_analysis(...)` and `write_analysis(...)`
- Adds injection seam: `analysis_builder=build_market_analysis`
- Changes: `refresh_once(...)` returns `{"market": ..., "stockbee": ..., "analysis": ...}`
- Changes: `refresh_status.json` gains `sources.analysis`

- [ ] **Step 1: Add a failing refresh integration test**

```python
def test_refresh_writes_analysis_and_status(self):
    with tempfile.TemporaryDirectory() as temp:
        output_dir = Path(temp)
        market = {"metadata": {"sourceStatus": "loaded", "loadedCount": 1, "requiredCount": 1, "missing": [], "comparisonDate": "2026-08-28"}, "instruments": {"SPY": {"bars": []}}}
        csv_text = "Date,Number of stocks up 4% plus today,Number of stocks down 4% plus today,5 day ratio,10 day ratio,T2108,S&P\n08/28/2026,84,382,0.98,1.09,41.91,7711.23\n"
        registry = {"stockbee-market-monitor": {"id": "stockbee-market-monitor", "enabled": True, "affectsScore": True}}
        analysis = {
            "schemaVersion": "1.0",
            "analysisId": "us-close-2026-08-28",
            "asOf": "2026-08-28",
            "generatedAt": "2026-08-30T10:00:00Z",
            "confidence": 1.0,
            "evidence": [{"id": "e1", "sourceId": "stockbee-market-monitor", "quality": "confirmed"}],
            "claims": [{"id": "c1", "kind": "fact", "text": "宽度快照可用。", "evidenceIds": ["e1"]}],
        }
        status = run_refresh_attempt(
            output_dir,
            market_builder=lambda: market,
            stockbee_csv=csv_text,
            attempted_at="2026-08-30T10:00:00Z",
            source_registry=registry,
            analysis_builder=lambda **_kwargs: analysis,
        )
        self.assertTrue((output_dir / "market_analysis.json").exists())
        self.assertEqual(status["sources"]["analysis"]["status"], "loaded")
```

- [ ] **Step 2: Run the refresh test and verify the new argument fails**

```powershell
& $PythonExe -m unittest StockTest.data_pipeline.test_refresh_local_data.RefreshLocalDataTests.test_refresh_writes_analysis_and_status -v
```

Expected: FAIL because `source_registry` and `analysis_builder` are not accepted.

- [ ] **Step 3: Generate analysis only after both snapshots validate**

Add optional `source_registry=None` and `analysis_builder=build_market_analysis` for tests. Production loads `data/source_registry.json`. Write `sources.analysis` with `status`, `asOf`, and `confidence`.

If an existing valid `market_analysis.json` has the same `asOf` as the newly confirmed US close, reuse it instead of regenerating research text. Add a test that runs two refresh attempts for the same `asOf` and asserts the analysis `generatedAt` remains unchanged; a new US close must produce a new analysis.

- [ ] **Step 4: Preserve the previous analysis on analysis failure**

Catch analysis errors separately after valid snapshot writes. Keep the existing `market_analysis.json`, set overall status to `partial`, set `sources.analysis.status` to `failed`, and append `{"source": "analysis", "message": "..."}` to errors.

- [ ] **Step 5: Run refresh and full tests, then commit**

```powershell
& $PythonExe -m unittest StockTest.data_pipeline.test_refresh_local_data -v
& $PythonExe -m unittest discover -s StockTest/data_pipeline -p 'test_*.py' -q
git add data_pipeline/refresh_local_data.py data_pipeline/test_refresh_local_data.py
git commit -m "feat: refresh market analysis with local data"
```

---

### Task 5: Hydrate the hero card and evidence drawer

**Files:**
- Modify: `index.html:52-95,176-184`
- Modify: `app.js:99-110,293-363,405-406`
- Modify: `styles.css`
- Modify: `data_pipeline/test_ui_flow_contract.py`

**Interfaces:**
- Produces: `hydrateMarketAnalysis() -> Promise<boolean>`
- Produces: `applyMarketAnalysis(analysis: object) -> boolean`
- Produces UI action: `[data-analysis-evidence]` opens `#analysis-evidence-drawer`

- [ ] **Step 1: Add failing UI contract tests**

```python
def test_market_analysis_is_local_and_source_backed(self):
    self.assertIn('fetch("data/market_analysis.json"', self.app)
    self.assertIn('id="analysis-evidence-trigger"', self.page)
    self.assertIn('id="analysis-evidence-drawer"', self.page)
    self.assertNotIn('marketStatus: { state: "震荡", score: 1', self.app)
    self.assertIn('evidenceIds', self.app)

def test_analysis_drawer_has_keyboard_contract(self):
    self.assertIn('aria-controls="analysis-evidence-drawer"', self.page)
    self.assertIn('event.key === "Escape"', self.app)
    self.assertIn('.focus()', self.app)
```

- [ ] **Step 2: Run UI contract tests and verify they fail**

```powershell
& $PythonExe -m unittest StockTest.data_pipeline.test_ui_flow_contract.UiFlowContractTests.test_market_analysis_is_local_and_source_backed -v
```

- [ ] **Step 3: Replace hardcoded hero text with stable DOM targets**

Add IDs for state, score, confidence, date, headline, summary, factor list, briefing list, mode label, and evidence trigger. Add an aside drawer with title, close button, content region, and status live region. Keep the existing hero layout and visual hierarchy.

- [ ] **Step 4: Implement hydration and strict rendering**

Fetch with `cache: "no-store"`. Verify required fields and ensure every displayed briefing item has at least one evidence ID found in `analysis.evidence`. On invalid/missing data, render “分析暂不可用” and hide the evidence trigger instead of restoring sample conclusions.

```javascript
async function hydrateMarketAnalysis() {
  try {
    const response = await fetch("data/market_analysis.json", { cache: "no-store" });
    if (!response.ok) return applyMarketAnalysisUnavailable();
    return applyMarketAnalysis(await response.json());
  } catch (_error) {
    return applyMarketAnalysisUnavailable();
  }
}
```

- [ ] **Step 5: Implement evidence drawer behavior and safe links**

Render evidence grouped by claim. Links must be `https://` before being assigned to `href`, and must use `target="_blank" rel="noopener noreferrer"`. Store the trigger element, close on Escape/backdrop/close button, and return focus to the trigger.

- [ ] **Step 6: Add restrained responsive styles**

Reuse existing surface, line, muted, green, red, blue, and amber tokens. Add source-count chips and a right-side drawer without altering tables, navigation, charts, or the ETF drawer. At 390px, make the evidence drawer full-width.

- [ ] **Step 7: Run UI tests and JavaScript syntax check**

```powershell
& $PythonExe -m unittest StockTest.data_pipeline.test_ui_flow_contract -v
& $NodeExe --check StockTest/app.js
```

- [ ] **Step 8: Commit the UI integration**

```powershell
git add index.html app.js styles.css data_pipeline/test_ui_flow_contract.py
git commit -m "feat: show source-backed market briefing"
```

---

### Task 6: End-to-end verification, progress record, and push

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_CONTEXT.md`
- Modify: `PROJECT_PROGRESS.md`
- Modify: `design-qa.md`

**Interfaces:**
- Verifies the complete local analysis flow and GitHub version state.

- [ ] **Step 1: Run the complete automated suite**

```powershell
& $PythonExe -m unittest discover -s StockTest/data_pipeline -p 'test_*.py' -v
& $NodeExe --check StockTest/app.js
```

Expected: all legacy and new tests PASS, JavaScript exits `0`.

- [ ] **Step 2: Generate a fresh analysis from the current snapshots**

```powershell
& $PythonExe -m StockTest.data_pipeline.market_analysis --data-dir StockTest/data
```

Check: the output `analysisId` uses the latest confirmed US close, every briefing evidence ID resolves, and BTC evidence uses the same `asOf`.

- [ ] **Step 3: Run browser QA on the existing local server**

Verify at 1440, 1024, 768, and 390 widths:

- market state, score, confidence, date, five factors, and three briefing items are visible;
- every briefing item shows a nonzero source count;
- evidence drawer opens, closes, supports Escape, and returns focus;
- source links are visible and safe;
- missing-analysis fallback is visible when the file is temporarily unavailable;
- existing sector, industry, holdings, and Stockbee interactions still work;
- console error/warn count is zero and page-level horizontal overflow is zero.

- [ ] **Step 4: Update only the existing durable documents**

Add run instructions and the new data contract to `README.md` and `PROJECT_CONTEXT.md`. Append one dated record to `PROJECT_PROGRESS.md`; do not create another progress document. Record visual QA and keep `design-qa.md` at `final result: passed` only if all visual checks pass.

- [ ] **Step 5: Commit documentation and push all commits**

```powershell
git add README.md PROJECT_CONTEXT.md PROJECT_PROGRESS.md design-qa.md
git commit -m "docs: record evidence-backed analysis delivery"
git push origin main
```

- [ ] **Step 6: Verify local and GitHub state**

```powershell
git status --short --branch
git rev-parse HEAD
gh api repos/bravo-189/StockTest/commits/main --jq .sha
```

Expected: clean `main...origin/main` and identical local/remote SHAs.
