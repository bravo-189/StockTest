(function () {
  "use strict";

  function redirectFilePreview() {
    if (window.location.protocol !== "file:") return;
    const localUrl = `http://127.0.0.1:8765/index.html${window.location.search || ""}`;
    const probe = new Image();
    probe.onload = () => window.location.replace(localUrl);
    probe.onerror = () => {
      const notice = document.createElement("div");
      notice.className = "file-runtime-notice";
      notice.innerHTML = `当前是文件预览模式，无法读取真实快照。请先启动本地服务，再打开 <a href="${localUrl}">${localUrl}</a>。`;
      document.addEventListener("DOMContentLoaded", () => document.body.prepend(notice), { once: true });
    };
    probe.src = "http://127.0.0.1:8765/favicon.svg?probe=" + Date.now();
  }
  redirectFilePreview();

  const SNAPSHOT_DATE = "2026-08-27";
  const INDEX_TRADING_DAYS = 21;
  const MONTH_TRADING_DAYS = 21;
  const US_INTRADAY_BARS = 79;
  const BTC_INTRADAY_BARS = 12;
  const DETAIL_TRADING_DAYS = 60;
  const RSI_HISTORY_DAYS = 42;
  const RSI_GAIN_THRESHOLD = 6;
  const BTC_REFRESH_INTERVAL_MS = 60 * 60 * 1000;
  const STALE_AFTER_MS = 90 * 60 * 1000;
  const STORAGE_KEY = "stocktest-theme";
  const sectorDefs = [
    ["XLV", "医疗保健", 64, 0.86], ["XLP", "必需消费", 62, 0.72], ["XLU", "公用事业", 61, 0.68],
    ["XLF", "金融", 57, 0.42], ["XLI", "工业", 55, 0.3], ["XLE", "能源", 54, 0.25],
    ["XLB", "材料", 53, 0.12], ["XLRE", "房地产", 51, 0.04], ["XLY", "可选消费", 49, -0.08],
    ["XLC", "通信服务", 48, -0.16], ["XLK", "科技", 47, -0.32], ["ARKK", "创新科技", 46, -0.38], ["IBIT", "加密货币", 58, 0.54], ["SPY", "标普 500", 52, 0.1]
  ];
  const industryDefs = [
    ["COPX", "铜矿", "材料"], ["LIT", "锂电池", "材料"], ["XME", "金属采矿", "材料"], ["GDX", "黄金矿业", "材料"], ["QTUM", "量子计算", "科技"], ["SOXX", "半导体", "科技"], ["ARKQ", "自动驾驶", "创新科技"], ["AIQ", "人工智能", "科技"], ["DTCR", "数据中心", "科技"], ["CHAT", "生成式 AI", "科技"], ["XOP", "油气勘探", "能源"], ["NLR", "核能", "能源"], ["KBWB", "银行", "金融"], ["OIH", "油服", "能源"], ["ITA", "航空航天", "工业"], ["MAGS", "大型科技", "科技"], ["ARKX", "太空经济", "创新科技"], ["QQQ", "纳斯达克 100", "科技"], ["XBI", "生物科技", "医疗保健"], ["ARKK", "颠覆创新", "创新科技"], ["SPY", "大盘股", "标普 500"], ["IWV", "全市场", "标普 500"], ["MTUM", "动量因子", "标普 500"], ["ARKW", "互联网", "创新科技"], ["DIA", "道琼斯", "标普 500"], ["IDRV", "电动车", "可选消费"], ["XTL", "电信", "通信服务"], ["PRNT", "3D 打印", "工业"], ["IGV", "软件", "科技"], ["USO", "原油", "能源"], ["IWM", "小盘股", "标普 500"], ["KWEB", "中国互联网", "通信服务"], ["TAN", "太阳能", "公用事业"], ["SLX", "钢铁", "材料"], ["SKYY", "云计算", "科技"], ["ARKG", "基因组学", "医疗保健"], ["BLOK", "区块链", "金融"], ["IYT", "运输", "工业"], ["CIBR", "网络安全", "科技"], ["IBUY", "线上零售", "可选消费"], ["KIE", "保险", "金融"], ["CLOU", "云基础设施", "科技"], ["BOTZ", "机器人", "工业"], ["PAVE", "基础设施", "工业"], ["KBE", "银行", "金融"], ["XRT", "零售", "可选消费"], ["HERO", "游戏", "通信服务"], ["ARKF", "金融科技", "金融"], ["VNQ", "房地产", "房地产"], ["KRE", "区域银行", "金融"], ["IEUR", "欧洲股票", "全球市场"], ["IAI", "券商", "金融"], ["MJ", "大麻产业", "医疗保健"], ["IYH", "医疗服务", "医疗保健"], ["FINX", "数字支付", "金融"], ["XHB", "住宅建筑", "可选消费"], ["IBIT", "比特币", "金融"], ["JETS", "航空运输", "工业"], ["IHI", "医疗器械", "医疗保健"], ["IPAY", "支付网络", "金融"]
  ];
  const themeNames = [
    ["AI 算力与数据中心", "AIQ"], ["半导体与量子计算", "SOXX"], ["云软件与互联网", "IGV"], ["网络安全", "CIBR"], ["机器人与自动化", "BOTZ"], ["航天、国防与航空", "ITA"], ["铜矿、金属与钢铁", "COPX"], ["电池与电动车", "LIT"], ["核能与能源转型", "NLR"], ["油气与能源服务", "XOP"], ["银行与保险", "KBWB"], ["金融科技、支付与券商", "ARKF"], ["数字资产与区块链", "IBIT"], ["黄金与避险", "GDX"], ["生物科技与基因组", "XBI"], ["医疗器械与服务", "IHI"], ["消费、零售与住房", "IBUY"], ["房地产、运输与基础设施", "VNQ"], ["美国大盘与动量因子", "SPY"], ["全球市场、通信与新消费", "KWEB"]
  ];
  const themeFactorDefs = [["trend", "趋势"], ["breadth", "扩散"], ["d1", "1D"], ["d20", "20D"], ["rsi", "RSI"]];
  const indexDefs = [
    ["SPX", "标普 500", "5,982.72", 0.34], ["NDX", "纳斯达克 100", "21,582.91", 0.61], ["DJI", "道琼斯工业", "43,908.14", -0.18], ["RUT", "罗素 2000", "2,154.83", 0.42], ["BTC", "Bitcoin", "77,655.00", -2.44]
  ];
  // Yahoo identifies the primary listings as NGM (Nasdaq), PCX (NYSE Arca)
  // and BTS (Cboe). TradingView uses its public venue names instead.
  const tradingViewExchanges = { DTCR: "NASDAQ", QTUM: "NASDAQ", IBIT: "NASDAQ", QQQ: "NASDAQ", SOXX: "NASDAQ", ARKK: "CBOE" };
  const tradingViewIndexSymbols = { SPX: "SP:SPX", NDX: "NASDAQ:NDX", DJI: "DJ:DJI", RUT: "TVC:RUT", BTC: "COINBASE:BTCUSD" };
  const sectorLabelsZh = {
    "Communication Services": "通信服务", Currency: "货币", Energy: "能源", Equity: "股票",
    Financials: "金融", Healthcare: "医疗保健", Industrials: "工业", Materials: "材料", Technology: "科技"
  };
  const industryLabelsZh = {
    "Advertising Agencies": "广告代理", "Asset Management": "资产管理", Biotechnology: "生物科技",
    Broadcasting: "广播", "Capital Markets": "资本市场", "Coking Coal": "炼焦煤", "Computer Hardware": "计算机硬件",
    "Derivative Income": "衍生品收益", "Digital Assets": "数字资产", "Electrical Equipment & Parts": "电气设备及零部件",
    Entertainment: "娱乐", "Health Information Services": "医疗信息服务", "Information Technology Services": "信息技术服务",
    "Marine Shipping": "海运", "Medical Devices": "医疗器械", "Other Precious Metals & Mining": "其他贵金属与采矿",
    "Software - Application": "应用软件", "Software - Infrastructure": "基础设施软件", "Trading--Leveraged Equity": "杠杆股票交易",
    "Trading--Miscellaneous": "其他交易策略", Uranium: "铀矿"
  };
  const companyNames = [
    ["MSFT", "Microsoft"], ["NVDA", "NVIDIA"], ["AAPL", "Apple"], ["AMZN", "Amazon"], ["META", "Meta Platforms"], ["GOOGL", "Alphabet"], ["AVGO", "Broadcom"], ["LLY", "Eli Lilly"], ["JPM", "JPMorgan Chase"], ["XOM", "Exxon Mobil"], ["V", "Visa"], ["UNH", "UnitedHealth"], ["COST", "Costco"], ["CAT", "Caterpillar"], ["NEE", "NextEra Energy"], ["GE", "GE Aerospace"], ["RTX", "RTX Corp"], ["CRM", "Salesforce"], ["ORCL", "Oracle"], ["AMD", "AMD"], ["LIN", "Linde"], ["WMT", "Walmart"], ["PG", "Procter & Gamble"], ["JNJ", "Johnson & Johnson"], ["HD", "Home Depot"], ["PLTR", "Palantir"], ["TSLA", "Tesla"], ["NFLX", "Netflix"], ["ADBE", "Adobe"], ["GS", "Goldman Sachs"]
  ];

  const state = { sectorMode: "d1", sectorSort: { key: "d1", direction: "desc" }, industryView: "top", industrySort: { key: "rsi", direction: "desc" }, rsiRankingSort: { top: { key: "rsi", direction: "desc" }, bottom: { key: "rsi", direction: "asc" } }, breadthMetric: "ratio5", query: "", drawerTicker: null, toastTimer: null, rsiHistorySelection: { sector: "SPY", industry: "SPY" }, lastFullRefreshAt: null };
  const $ = (selector, root) => (root || document).querySelector(selector);
  const $$ = (selector, root) => Array.from((root || document).querySelectorAll(selector));
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const signedNumber = (value, digits) => `${value >= 0 ? "+" : "−"}${Math.abs(value).toFixed(digits == null ? 1 : digits)}`;
  const signed = (value, digits) => `${signedNumber(value, digits)}%`;
  const signedDelta = (value) => {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "—";
    const rounded = Number(numeric.toFixed(2));
    const body = Math.abs(rounded).toFixed(2).replace(/\.00$/, "").replace(/(\.\d)0$/, "$1");
    return `${rounded >= 0 ? "+" : "−"}${body}`;
  };
  const deltaDisplay = (value) => {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return '<span class="delta-display is-neutral" title="绝对价格变化，不含百分号"><span class="delta-triangle" aria-hidden="true">•</span><span>—</span></span>';
    const direction = numeric > 0.08 ? "positive" : numeric < -0.08 ? "negative" : "neutral";
    const glyph = direction === "positive" ? "▲" : direction === "negative" ? "▼" : "•";
    return `<span class="delta-display is-${direction}" title="绝对价格变化，不含百分号" aria-label="${signedDelta(numeric)}"><span class="delta-triangle" aria-hidden="true">${glyph}</span><span>${signedDelta(numeric)}</span></span>`;
  };
  const classFor = (value) => value > 0.08 ? "positive" : value < -0.08 ? "negative" : "neutral";
  const html = (value) => String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
  const classificationLabel = (value, labels) => labels[value] || value || "未找到可核验分类";
  const valueFrom = (seed, offset, spread) => {
    const n = Math.sin(seed * 12.9898 + offset * 78.233) * 43758.5453;
    return ((n - Math.floor(n)) * 2 - 1) * spread;
  };
  const breadthMetricDefs = {
    up: { label: "4% 上涨家数", color: "--green", digits: 0 }, down: { label: "4% 下跌家数", color: "--red", digits: 0 },
    ratio5: { label: "5 日上涨／下跌比", color: "--blue", digits: 2 }, ratio10: { label: "10 日上涨／下跌比", color: "--cyan", digits: 2 },
    up25Quarter: { label: "25% 上涨 · 季度", color: "--green", digits: 0 }, down25Quarter: { label: "25% 下跌 · 季度", color: "--red", digits: 0 },
    up25Month: { label: "25% 上涨 · 月", color: "--green", digits: 0 }, down25Month: { label: "25% 下跌 · 月", color: "--red", digits: 0 },
    up50Month: { label: "50% 上涨 · 月", color: "--green", digits: 0 }, down50Month: { label: "50% 下跌 · 月", color: "--red", digits: 0 },
    up13_34d: { label: "13% 上涨 · 34日", color: "--green", digits: 0 }, down13_34d: { label: "13% 下跌 · 34日", color: "--red", digits: 0 },
    wordenUniverse: { label: "Worden 股票宇宙", color: "--cyan", digits: 0 },
    t2108: { label: "T2108", color: "--amber", digits: 2 }, sp500: { label: "S&P 500", color: "--blue", digits: 2 }
  };
  const breadthColumnDefs = [
    ["up", "4%上涨 · 今日", "positive", 0], ["down", "4%下跌 · 今日", "negative", 0], ["ratio5", "5日比率", "neutral", 2], ["ratio10", "10日比率", "neutral", 2],
    ["up25Quarter", "25%上涨 · 季度", "positive", 0], ["down25Quarter", "25%下跌 · 季度", "negative", 0], ["up25Month", "25%上涨 · 月", "positive", 0], ["down25Month", "25%下跌 · 月", "negative", 0],
    ["up50Month", "50%上涨 · 月", "positive", 0], ["down50Month", "50%下跌 · 月", "negative", 0], ["up13_34d", "13%上涨 · 34日", "positive", 0], ["down13_34d", "13%下跌 · 34日", "negative", 0],
    ["wordenUniverse", "Worden股票宇宙", "positive", 0], ["t2108", "T2108", "neutral", 2], ["sp500", "S&P 500", "positive", 2]
  ];

  const sectors = sectorDefs.map((entry, index) => {
    const [ticker, name, rsi, d1] = entry;
    const d5 = +(d1 * 1.55 + valueFrom(index + 2, 4, 0.8)).toFixed(2);
    const d20 = +(d1 * 2.65 + valueFrom(index + 3, 7, 1.2)).toFixed(2);
    return { ticker, name, rsi, d1, d5, d20, price: +(98 + index * 8 + valueFrom(index, 2, 2.5)).toFixed(2), trend: d1 > .18 ? "改善" : d1 < -.18 ? "转弱" : "盘整", trend150: index % 3 === 0 ? "上涨" : "下降", ma150: null };
  });
  const industries = industryDefs.map((entry, index) => {
    const [ticker, name, group] = entry;
    const rsi = clamp(71 - index * .42 + valueFrom(index + 11, 2, 8), 35, 76);
    const d1 = +(valueFrom(index + 11, 2, 1.2) + (rsi - 50) * .03).toFixed(2);
    const d5 = +(valueFrom(index + 21, 3, 3.3) + (rsi - 50) * .07).toFixed(2);
    const d20 = +(valueFrom(index + 31, 6, 7) + (rsi - 50) * .18).toFixed(2);
    return { ticker, name, group, rsi: +rsi.toFixed(1), d1, d5, d20, momentum: clamp(Math.round(rsi * .84 + d5 * 1.8), 25, 96), trend150: index % 3 === 0 ? "上涨" : "下降", ma150: null };
  });
  let themes = themeNames.map(([name, ticker], index) => {
    const total = clamp(Math.round(92 - index * 2.1 + valueFrom(index + 81, 3, 7)), 42, 96);
    const factorValues = [valueFrom(index, 1, 8), valueFrom(index, 2, 11), valueFrom(index, 4, 13), valueFrom(index, 7, 10), valueFrom(index, 9, 15)].map((value) => clamp(Math.round(total + value), 30, 99));
    return { rank: index + 1, name, ticker, total, factors: Object.fromEntries(themeFactorDefs.map(([key], factorIndex) => [key, factorValues[factorIndex]])), memberEtfs: [ticker], analysisStatus: "pending" };
  });
  let holdings = Object.fromEntries(sectorDefs.map(([ticker], sectorIndex) => [ticker, Array.from({ length: 10 }, (_, index) => {
    const company = companyNames[(sectorIndex * 3 + index) % companyNames.length];
    return { ticker: company[0], name: company[1], weight: +(16.4 - index * 1.2 + valueFrom(sectorIndex + index, 5, .7)).toFixed(1) };
  })]));
  let stockbeeMomentum = [];
  let stockbeeMomentumMeta = { sourceStatus: "unavailable", latestDate: null, rowCount: 0 };
  let breadth = Array.from({ length: 126 }, (_, index) => {
    const day = new Date("2026-08-28T00:00:00Z");
    day.setUTCDate(day.getUTCDate() - index);
    const up = Math.round(112 + index * 1.8 + valueFrom(index + 200, 2, 22));
    const down = Math.round(86 + index * 1.1 + valueFrom(index + 220, 3, 18));
    const ratio5 = +(up / Math.max(down, 1) * .92).toFixed(2);
    const ratio10 = +(up / Math.max(down, 1) * .84).toFixed(2);
    const up25Quarter = Math.round(1420 + index * 7 + valueFrom(index + 260, 2, 95));
    const down25Quarter = Math.round(1080 + index * 5 + valueFrom(index + 270, 3, 80));
    const up25Month = Math.round(250 + index * 2 + valueFrom(index + 280, 4, 28));
    const down25Month = Math.round(96 + index * 1.3 + valueFrom(index + 290, 5, 18));
    const up50Month = Math.round(52 + index * .4 + valueFrom(index + 300, 6, 9));
    const down50Month = Math.round(24 + index * .2 + valueFrom(index + 310, 7, 8));
    const up13_34d = Math.round(1740 + index * 8 + valueFrom(index + 320, 8, 90));
    const down13_34d = Math.round(1410 + index * 6 + valueFrom(index + 330, 9, 85));
    const wordenUniverse = Math.round(6540 - index * .8 + valueFrom(index + 340, 10, 5));
    const t2108 = +(46 + index * .45 + valueFrom(index + 240, 2, 4)).toFixed(1);
    const sp500 = +(7600 + index * 8 + valueFrom(index + 350, 11, 85)).toFixed(2);
    const composite = clamp(Math.round((ratio5 - 1) * 4 + (t2108 - 50) / 8), -3, 4);
    return { date: day.toISOString().slice(0, 10), up, down, ratio5, ratio10, up25Quarter, down25Quarter, up25Month, down25Month, up50Month, down50Month, up13_34d, down13_34d, wordenUniverse, t2108, sp500, composite };
  });
  // Future API contract: renderers below consume these same named collections.
  const DashboardData = {
    metadata: { dataDate: SNAPSHOT_DATE, generatedAt: `${SNAPSHOT_DATE}T18:30:00-04:00`, sourceStatus: "sample", isStale: true, missing: [] },
    marketStatus: { state: "震荡", score: 1, signals: { trend: 1, breadth: 0, momentum: 1, liquidity: 0, risk: -1 } },
    indices: indexDefs.map(([ticker, name, close, change]) => ({ ticker, name, close, change })),
    sectorEtfs: sectors,
    industryEtfs: industries,
    themes,
    holdings,
    stockbeeMomentum,
    breadth
  };
  const marketBars = {};
  const marketIntradayBars = {};
  const marketPendingBars = {};
  window.StockTestData = DashboardData;

  function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
  function drawSparkline(canvas, seed, positive, pointCount = INDEX_TRADING_DAYS, sourceBars) {
    if (!canvas) return;
    const ratio = Math.max(window.devicePixelRatio || 1, canvas.classList.contains("bubble-sparkline") ? 3 : 2);
    const width = canvas.clientWidth || 240;
    const height = canvas.clientHeight || 42;
    canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
    const ctx = canvas.getContext("2d"); ctx.scale(ratio, ratio); ctx.clearRect(0, 0, width, height);
    const upColor = cssVar("--green"); const downColor = cssVar("--red"); const color = positive >= 0 ? upColor : downColor;
    const bars = Array.isArray(sourceBars) && sourceBars.length ? sourceBars.slice(-pointCount) : null;
    const synthetic = Array.from({ length: pointCount }, (_, i) => { const close = height * .54 - (i * positive * .06) - valueFrom(seed, i + 1, height * .22); const open = close + valueFrom(seed + i, 41, 7); return { open, high: Math.max(open, close) + Math.abs(valueFrom(seed + i, 42, 5)), low: Math.min(open, close) - Math.abs(valueFrom(seed + i, 43, 5)), close }; });
    const candleData = bars || synthetic;
    const rawHigh = Math.max(...candleData.map((bar) => bar.high)); const rawLow = Math.min(...candleData.map((bar) => bar.low)); const priceRange = Math.max(rawHigh - rawLow, Number.EPSILON);
    const mapY = (value) => 4 + ((rawHigh - value) / priceRange) * (height - 8);
    ctx.strokeStyle = cssVar("--line"); ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(0, height - 1); ctx.lineTo(width, height - 1); ctx.stroke();
    const step = width / candleData.length; const candleWidth = Math.max(2, step * .38);
    candleData.forEach((bar, index) => {
      const x = index * step + step / 2; const rising = bar.close >= bar.open; ctx.strokeStyle = rising ? upColor : downColor; ctx.fillStyle = rising ? upColor : downColor; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, clamp(mapY(bar.high), 4, height - 4)); ctx.lineTo(x, clamp(mapY(bar.low), 4, height - 4)); ctx.stroke();
      const bodyTop = clamp(Math.min(mapY(bar.open), mapY(bar.close)), 4, height - 4); const bodyHeight = Math.max(2, Math.min(height - 8, Math.abs(mapY(bar.close) - mapY(bar.open)))); ctx.globalAlpha = .82; ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight); ctx.globalAlpha = 1;
    });
  }
  function drawLineAreaChart(canvas, bars, positive) {
    if (!canvas) return;
    const data = Array.isArray(bars) && bars.length ? bars : [];
    if (!data.length) return;
    const ratio = Math.max(window.devicePixelRatio || 1, canvas.classList.contains("bubble-sparkline") ? 3 : 2);
    const width = canvas.clientWidth || 260;
    const height = canvas.clientHeight || 76;
    canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
    const ctx = canvas.getContext("2d"); ctx.scale(ratio, ratio); ctx.clearRect(0, 0, width, height);
    const lineColor = positive >= 0 ? cssVar("--green") : cssVar("--red");
    const muted = cssVar("--muted-2"); const guide = cssVar("--line");
    const values = data.map((bar) => Number(bar.close)).filter(Number.isFinite);
    if (!values.length) return;
    const minValue = Math.min(...values); const maxValue = Math.max(...values);
    const padding = Math.max((maxValue - minValue) * .16, Math.abs(maxValue || 1) * .001);
    const min = minValue - padding; const max = maxValue + padding; const plotTop = 8; const plotBottom = height - 18;
    const stepX = width / Math.max(values.length - 1, 1);
    const yFor = (value) => plotBottom - ((value - min) / Math.max(max - min, Number.EPSILON)) * (plotBottom - plotTop);
    ctx.strokeStyle = guide; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(0, plotBottom); ctx.lineTo(width, plotBottom); ctx.stroke();
    ctx.beginPath(); values.forEach((value, index) => { const x = index * stepX; const y = yFor(value); if (!index) ctx.moveTo(x, y); else ctx.lineTo(x, y); }); ctx.lineTo(width, plotBottom); ctx.lineTo(0, plotBottom); ctx.closePath(); ctx.globalAlpha = .14; ctx.fillStyle = lineColor; ctx.fill(); ctx.globalAlpha = 1;
    ctx.strokeStyle = lineColor; ctx.lineWidth = 2; ctx.lineJoin = "round"; ctx.lineCap = "round"; ctx.beginPath(); values.forEach((value, index) => { const x = index * stepX; const y = yFor(value); if (!index) ctx.moveTo(x, y); else ctx.lineTo(x, y); }); ctx.stroke();
    const lastY = yFor(values[values.length - 1]); ctx.fillStyle = lineColor; ctx.beginPath(); ctx.arc(width - 1, lastY, 3, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = muted; ctx.font = "9px IBM Plex Mono, monospace"; ctx.textBaseline = "bottom"; ctx.textAlign = "left"; ctx.fillText(data[0].time || data[0].date || "起点", 0, height - 2); ctx.textAlign = "center"; ctx.fillText(data[Math.floor((data.length - 1) / 2)].time || data[Math.floor((data.length - 1) / 2)].date || "", width / 2, height - 2); ctx.textAlign = "right"; ctx.fillText(data[data.length - 1].time || data[data.length - 1].date || "终点", width, height - 2); ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
  }
  function emaSeries(bars, period) {
    const closes = (Array.isArray(bars) ? bars : []).map((bar) => Number(bar.close));
    if (!closes.length) return [];
    const smoothing = 2 / (period + 1); let previous = closes[0];
    return closes.map((close, index) => { if (!Number.isFinite(close)) return previous; if (index === 0) { previous = close; return close; } previous = (close - previous) * smoothing + previous; return previous; });
  }
  function calendarBarsForDisplay(bars, calendar) {
    // Only render bars that came from the source snapshot. US index feeds do
    // not normally publish Saturday/Sunday sessions; never synthesize them.
    // If a future provider supplies genuine weekend bars, they pass through.
    return (Array.isArray(bars) ? bars : []).filter((bar) => /^\d{4}-\d{2}-\d{2}$/.test(String(bar.date))).slice(-MONTH_TRADING_DAYS).sort((a, b) => String(a.date).localeCompare(String(b.date)));
  }
  function drawBubbleCandlestickChart(canvas, bars, calendar) {
    if (!canvas || !Array.isArray(bars) || !bars.length) return;
    const data = calendarBarsForDisplay(bars, calendar); const ratio = Math.max(window.devicePixelRatio || 1, 3);
    const width = canvas.clientWidth || 560; const height = canvas.clientHeight || 220;
    canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
    const ctx = canvas.getContext("2d"); ctx.scale(ratio, ratio); ctx.clearRect(0, 0, width, height);
    const upColor = cssVar("--green"); const downColor = cssVar("--red"); const ema9Color = cssVar("--blue"); const ema21Color = cssVar("--amber"); const guide = cssVar("--line"); const muted = cssVar("--muted-2");
    const highs = data.map((bar) => Number(bar.high)).filter(Number.isFinite); const lows = data.map((bar) => Number(bar.low)).filter(Number.isFinite);
    if (!highs.length || !lows.length) return;
    const rawHigh = Math.max(...highs); const rawLow = Math.min(...lows); const padding = Math.max((rawHigh - rawLow) * .1, Math.abs(rawHigh || 1) * .002); const min = rawLow - padding; const max = rawHigh + padding;
    const plotTop = 10; const plotBottom = height - 26; const mapY = (value) => plotBottom - ((value - min) / Math.max(max - min, Number.EPSILON)) * (plotBottom - plotTop);
    [0, .5, 1].forEach((step) => { const y = plotBottom - step * (plotBottom - plotTop); ctx.strokeStyle = guide; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke(); });
    const stepX = width / data.length; const candleWidth = Math.max(4, Math.min(14, stepX * .52));
    data.forEach((bar, index) => {
      const x = index * stepX + stepX / 2;
      const open = Number(bar.open); const close = Number(bar.close); const high = Number(bar.high); const low = Number(bar.low); if (![open, close, high, low].every(Number.isFinite)) return;
      const rising = close >= open; const color = rising ? upColor : downColor; ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 1.1;
      ctx.beginPath(); ctx.moveTo(x, mapY(high)); ctx.lineTo(x, mapY(low)); ctx.stroke();
      const bodyTop = Math.min(mapY(open), mapY(close)); const bodyHeight = Math.max(2, Math.abs(mapY(close) - mapY(open))); ctx.globalAlpha = .86; ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight); ctx.globalAlpha = 1;
    });
    const drawEma = (period, color) => {
      const series = emaSeries(data, period); if (!series.length) return;
      ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.lineJoin = "round"; ctx.lineCap = "round"; ctx.beginPath();
      series.forEach((value, index) => { const x = index * stepX + stepX / 2; const y = mapY(value); if (!index) ctx.moveTo(x, y); else ctx.lineTo(x, y); });
      ctx.stroke();
    };
    drawEma(9, ema9Color); drawEma(21, ema21Color);
    ctx.fillStyle = muted; ctx.font = "10px IBM Plex Mono, monospace"; ctx.textBaseline = "bottom"; ctx.textAlign = "left"; ctx.fillText(data[0].date || "起点", 0, height - 4); ctx.textAlign = "center"; ctx.fillText(data[Math.floor((data.length - 1) / 2)].date || "", width / 2, height - 4); ctx.textAlign = "right"; ctx.fillText(data[data.length - 1].date || "终点", width, height - 4); ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
  }
  function buildIntradayBars(ticker, sourceBars, seed, positive) {
    const count = ticker === "BTC" ? BTC_INTRADAY_BARS : US_INTRADAY_BARS;
    const latest = Array.isArray(sourceBars) && sourceBars.length ? sourceBars[sourceBars.length - 1] : null;
    const anchor = Number(latest?.open) || Number(latest?.close) || 100;
    const target = Number(latest?.close) || anchor * (1 + Number(positive || 0) / 100);
    const noise = Math.max(anchor * .0018, Math.abs(target - anchor) * .22);
    let previous = anchor;
    return Array.from({ length: count }, (_, index) => {
      const drift = anchor + (target - anchor) * ((index + 1) / count);
      const close = Math.max(.01, drift + valueFrom(seed + index, 61, noise));
      const open = previous;
      previous = close;
      const spread = Math.max(anchor * .0008, Math.abs(valueFrom(seed + index, 62, noise * .65)));
      const intervalMinutes = ticker === "BTC" ? 120 : 5;
      const minutes = ticker === "BTC" ? index * intervalMinutes : 9 * 60 + 30 + index * intervalMinutes;
      const hour = Math.floor(minutes / 60) % 24; const minute = minutes % 60;
      const time = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
      return { open, close, high: Math.max(open, close) + spread, low: Math.max(.01, Math.min(open, close) - spread), time };
    });
  }
  function drawIndexCardChart(canvas) {
    if (!canvas) return;
    const ticker = canvas.dataset.sparkTicker;
    const seed = Number(canvas.dataset.sparkSeed);
    const change = Number(canvas.dataset.sparkChange);
    const sourceBars = Array.isArray(marketIntradayBars[ticker]) && marketIntradayBars[ticker].length ? marketIntradayBars[ticker] : null;
    const bars = sourceBars || (ticker === "BTC" ? buildIntradayBars(ticker, marketBars[ticker], seed, change) : calendarBarsForDisplay(marketBars[ticker], "us-equity"));
    if (ticker === "BTC") drawSparkline(canvas, seed, change, BTC_INTRADAY_BARS, bars);
    else drawLineAreaChart(canvas, bars, change);
    const incomplete = sourceBars?.[sourceBars.length - 1]?.status === "incomplete";
    canvas.setAttribute("aria-label", `${ticker} ${ticker === "BTC" ? "当日 2 小时 K 线" : sourceBars ? "当日 5 分钟折线面积图" : "近 1 个月日线折线图（周末含空档）"}${incomplete ? "（含未收盘柱）" : ""}`);
  }
  function positionIndexHoverBubble(card) {
    const bubble = card?.__hoverBubble || card?.querySelector(".index-hover-bubble");
    if (!bubble || bubble.hidden) return;
    const rect = card.getBoundingClientRect();
    const bubbleWidth = Math.min(640, Math.max(300, window.innerWidth - 24));
    const bubbleHeight = bubble.getBoundingClientRect().height || 199;
    const sideGap = 12;
    const canPlaceRight = rect.right + sideGap + bubbleWidth <= window.innerWidth - 14;
    const canPlaceLeft = rect.left - sideGap - bubbleWidth >= 14;
    const side = canPlaceRight ? "right" : canPlaceLeft ? "left" : null;
    const left = side === "right" ? rect.right + sideGap : side === "left" ? rect.left - sideGap - bubbleWidth : clamp(rect.left, 14, Math.max(14, window.innerWidth - bubbleWidth - 14));
    const belowTop = rect.bottom + 12;
    const aboveTop = rect.top - bubbleHeight - 12;
    const top = side ? clamp(rect.top, 14, Math.max(14, window.innerHeight - bubbleHeight - 14)) : (belowTop + bubbleHeight <= window.innerHeight - 12 || aboveTop < 12 ? Math.max(12, belowTop) : aboveTop);
    const arrowLeft = clamp(rect.left + rect.width / 2 - left - 5, 16, bubbleWidth - 26);
    bubble.style.left = `${Math.round(left)}px`;
    bubble.style.top = `${Math.round(top)}px`;
    bubble.style.setProperty("--bubble-arrow-left", `${Math.round(arrowLeft)}px`);
    bubble.dataset.placement = side || (top < rect.top ? "top" : "bottom");
  }
  function updateIndexHoverBubble(card) {
    const ticker = card?.querySelector(".sparkline")?.dataset.sparkTicker;
    if (!ticker) return;
    const source = marketBars[ticker];
    const bubble = card.__hoverBubble || card.querySelector(".index-hover-bubble");
    const chart = bubble?.querySelector(".bubble-sparkline");
    const item = source && source.length ? source[source.length - 1] : null;
    const pending = marketPendingBars[ticker];
    const intraday = marketIntradayBars[ticker];
    const latestIntraday = Array.isArray(intraday) && intraday.length ? intraday[intraday.length - 1] : null;
    const fallback = indexDefs.find((entry) => entry[0] === ticker);
    const calendar = ticker === "BTC" ? "crypto-24x7" : "us-equity";
    const displayItem = latestIntraday && Number.isFinite(Number(latestIntraday.close)) ? latestIntraday : item || (fallback ? { close: Number(String(fallback[2]).replace(/,/g, "")), date: SNAPSHOT_DATE } : null);
    const base = source && source.length > MONTH_TRADING_DAYS ? source[source.length - MONTH_TRADING_DAYS - 1] : null;
    const change = item && base && base.close ? (item.close / base.close - 1) * 100 : null;
    if (!bubble || !chart) return;
    if (!card.__hoverBubble) { card.__hoverBubble = bubble; bubble.__ownerCard = card; document.body.appendChild(bubble); }
    const bubblePrice = bubble.querySelector(".bubble-price");
    if (bubblePrice) bubblePrice.textContent = displayItem && Number.isFinite(Number(displayItem.close)) ? `价格 ${formatPrice(displayItem.close)}${latestIntraday?.time ? ` · ${latestIntraday.time}` : ""}` : "价格 —";
    bubble.querySelector(".bubble-change").textContent = Number.isFinite(change) ? signed(change) : "暂无区间数据";
    const chartBars = Array.isArray(source) ? source.slice() : [];
    if (pending && pending.date && (!chartBars.length || pending.date > chartBars[chartBars.length - 1].date)) chartBars.push(pending);
    const visibleBars = calendarBarsForDisplay(chartBars, calendar);
    bubble.querySelector(".bubble-range").textContent = visibleBars.length > 1 ? `${visibleBars[0].date} — ${visibleBars[visibleBars.length - 1].date}` : (item && base ? `${base.date} — ${item.date}` : "近 1 个月日线");
    const bubbleTitle = bubble.querySelector(".bubble-heading strong");
    const hasWeekendBars = visibleBars.some((bar) => { const day = new Date(`${bar.date}T00:00:00Z`).getUTCDay(); return day === 0 || day === 6; });
    if (bubbleTitle) bubbleTitle.textContent = calendar === "us-equity" ? (hasWeekendBars ? "放大 · 近 1 个月日线 K 线（含周末数据）" : "放大 · 近 1 个月美股交易日日线 K 线") : "放大 · 近 1 个月日线 K 线（24/7）";
    const refreshNote = bubble.querySelector(".bubble-refresh");
    if (refreshNote) refreshNote.textContent = pending ? (calendar === "us-equity" ? "盘中价格每小时刷新 · 含未收盘日线" : "盘中价格每小时刷新 · 含未收盘日线") : latestIntraday ? (calendar === "us-equity" ? (hasWeekendBars ? "盘中价格每小时刷新 · 周末数据源已提供" : "盘中价格每小时刷新 · 美股周末无指数成交") : "盘中价格每小时刷新 · 24/7") : "等待盘中快照";
    bubble.dataset.pendingDate = pending?.date || "";
    drawBubbleCandlestickChart(chart, chartBars, calendar);
    bubble.hidden = false;
    positionIndexHoverBubble(card);
  }
  function setupIndexCardInteractions(canvas) {
    const card = canvas.closest(".index-card");
    if (!card) return;
    const showBubble = () => updateIndexHoverBubble(card);
    const hideBubble = () => { const bubble = card.__hoverBubble || card.querySelector(".index-hover-bubble"); if (bubble) bubble.hidden = true; };
    const openTradingView = () => { const ticker = card.dataset.indexTicker; if (ticker) window.open(tradingViewIndexUrl(ticker), "_blank", "noopener,noreferrer"); };
    card.addEventListener("focus", showBubble);
    card.addEventListener("blur", hideBubble);
    card.addEventListener("mouseenter", showBubble);
    card.addEventListener("mouseleave", hideBubble);
    canvas.addEventListener("focus", showBubble);
    canvas.addEventListener("blur", hideBubble);
    card.addEventListener("click", openTradingView);
    card.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openTradingView(); } });
  }
  function breadthChartRows() {
    return breadth.filter((row) => row && row.date).slice().sort((a, b) => String(a.date).localeCompare(String(b.date)));
  }
  function drawBreadthChart() {
    const canvas = $("#breadth-chart"); if (!canvas) return;
    const ratio = window.devicePixelRatio || 1; const width = canvas.clientWidth || 760; const height = canvas.clientHeight || 240;
    canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
    const ctx = canvas.getContext("2d"); ctx.scale(ratio, ratio); ctx.clearRect(0, 0, width, height);
    const line = cssVar("--line"); const muted = cssVar("--muted-2"); const metric = breadthMetricDefs[state.breadthMetric] || breadthMetricDefs.ratio5;
    // Stockbee rows are kept newest-first for the table. Charts must be oldest-to-newest
    // so the rightmost point is the same latest observation shown at the top of the table.
    const rows = breadthChartRows();
    const points = rows.map((row) => ({ date: row.date, value: Number(row[state.breadthMetric]) })).filter((point) => Number.isFinite(point.value));
    const values = points.map((point) => point.value);
    if (!points.length) return;
    const minValue = Math.min(...values); const maxValue = Math.max(...values); const padding = Math.max((maxValue - minValue) * .12, metric.digits === 0 ? 4 : .04);
    const min = minValue - padding; const max = maxValue + padding; const plotTop = 18; const plotBottom = height - 22; const stepX = width / Math.max(values.length - 1, 1);
    [0, .25, .5, .75, 1].forEach((step) => { const y = plotBottom - step * (plotBottom - plotTop); ctx.strokeStyle = line; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke(); });
    const color = cssVar(metric.color); ctx.strokeStyle = color; ctx.lineWidth = 2.2; ctx.beginPath(); values.forEach((value, index) => { const x = index * stepX; const y = plotBottom - ((value - min) / Math.max(max - min, Number.EPSILON)) * (plotBottom - plotTop); if (!index) ctx.moveTo(x, y); else ctx.lineTo(x, y); }); ctx.stroke();
    const last = values[values.length - 1]; const lastY = plotBottom - ((last - min) / Math.max(max - min, Number.EPSILON)) * (plotBottom - plotTop); ctx.fillStyle = color; ctx.beginPath(); ctx.arc(width - 1, lastY, 3, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = muted; ctx.font = "10px IBM Plex Mono, monospace"; ctx.fillText(maxValue.toFixed(metric.digits), 4, 12); ctx.fillText(minValue.toFixed(metric.digits), 4, plotBottom - 2);
    ctx.textAlign = "left"; ctx.fillText(points[0].date, 4, height - 5); ctx.textAlign = "right"; ctx.fillText(points[points.length - 1].date, width - 4, height - 5); ctx.textAlign = "left";
    canvas.dataset.metric = state.breadthMetric; canvas.dataset.pointCount = String(points.length); canvas.dataset.latestDate = points[points.length - 1].date; canvas.dataset.latestValue = String(last);
    const latestValue = $("#breadth-latest-value"); const latestDate = $("#breadth-latest-date");
    if (latestValue) latestValue.textContent = last.toLocaleString("en-US", { minimumFractionDigits: metric.digits, maximumFractionDigits: metric.digits });
    if (latestDate) latestDate.textContent = points[points.length - 1].date;
  }

  function renderIndices() {
    const root = $("#index-grid");
    if (!root) return;
    $$(".index-hover-bubble", document.body).forEach((bubble) => bubble.remove());
    root.innerHTML = indexDefs.map(([ticker, name, fallbackPrice, fallbackChange], index) => {
      const bars = marketBars[ticker] || [];
      const latest = bars[bars.length - 1];
      const price = Number(latest?.close);
      const d1 = closeChange(bars, 1); const d5 = closeChange(bars, 5); const d20 = closeChange(bars, 20);
      const d1Delta = closeDelta(bars, 1); const d5Delta = closeDelta(bars, 5); const d20Delta = closeDelta(bars, 20);
      const change = Number.isFinite(d1) ? d1 : fallbackChange;
      const displayPrice = Number.isFinite(price) ? formatPrice(price) : formatPrice(String(fallbackPrice).replace(/,/g, ""));
      const latestIntraday = marketIntradayBars[ticker]?.[marketIntradayBars[ticker].length - 1]; const incomplete = latestIntraday?.status === "incomplete";
      const hasIntraday = Array.isArray(marketIntradayBars[ticker]) && marketIntradayBars[ticker].length > 0; const mode = ticker === "BTC" ? "当日 · 2H（24H）K 线" : hasIntraday ? "当日 · 5M 面积图" : "近 1 个月日线"; const weekendNow = ticker !== "BTC" && !hasIntraday && [0, 6].includes(new Date().getDay()); const note = incomplete ? "未收盘 · 悬停放大近 1 个月" : weekendNow ? "周末无成交 · 沿用最近收盘" : "悬停放大近 1 个月"; const aria = `${name} ${ticker === "BTC" ? "当日 2 小时 K 线" : hasIntraday ? "当日 5 分钟折线面积图" : "近 1 个月日线折线图"}${incomplete ? "（含未收盘柱）" : ""}`;
      const rsi = rsi14FromBars(bars);
      return `<article class="index-card" tabindex="0" role="link" data-index-ticker="${ticker}" aria-label="在 TradingView 查看 ${name}（${ticker}）"><div class="index-card-top"><div><div class="ticker">${ticker}</div><div class="index-name">${name}</div></div><span class="index-change ${classFor(change)}">${signed(change)}</span></div><div class="index-price">${displayPrice} <span class="index-rsi">RSI ${rsi == null ? "—" : rsi.toFixed(1)}</span></div><canvas class="sparkline" tabindex="0" data-spark-ticker="${ticker}" data-spark-seed="${index + 40}" data-spark-change="${change}" aria-label="${aria}"></canvas><div class="sparkline-caption"><span class="sparkline-mode">${mode}</span><span class="sparkline-note${incomplete ? " is-incomplete" : ""}">${note}</span></div><div class="index-overview-metrics"><span><small class="overview-index-delta-label">Δ1</small>${deltaDisplay(d1Delta)}</span><span><small class="overview-index-delta-label">Δ5</small>${deltaDisplay(d5Delta)}</span><span><small class="overview-index-delta-label">Δ20</small>${deltaDisplay(d20Delta)}</span></div><div class="index-hover-bubble" role="tooltip" hidden><div class="bubble-heading"><div class="bubble-title-group"><strong>放大 · 近 1 个月日线 K 线</strong><span class="bubble-price">价格 —</span></div><span class="bubble-change">—</span></div><div class="bubble-legend" aria-label="图例"><span><i class="legend-candle"></i>K 线</span><span><i class="legend-ema9"></i>EMA9</span><span><i class="legend-ema21"></i>EMA21</span></div><canvas class="bubble-sparkline" width="640" height="220" aria-hidden="true"></canvas><div class="bubble-meta"><span class="bubble-range">近 1 个月日线</span><span class="bubble-refresh">等待盘中快照</span><span>移开关闭</span></div></div></article>`;
    }).join("");
    $$(".sparkline", root).forEach((canvas) => { setupIndexCardInteractions(canvas); drawIndexCardChart(canvas); });
  }
  function renderRsiRankings() {
    const topBody = $("#rsi-top-body"); const bottomBody = $("#rsi-bottom-body");
    if (!topBody || !bottomBody) return;
    const rows = industries.filter((row) => Number.isFinite(Number(row.rsi))).slice().sort((a, b) => Number(b.rsi) - Number(a.rsi) || a.ticker.localeCompare(b.ticker));
    const topRows = rows.slice(0, 20); const bottomRows = rows.slice(-20).reverse();
    const sortRows = (items, kind) => { const sort = state.rsiRankingSort[kind]; if (sort.key !== "d1") return items; return items.slice().sort((a, b) => { const av = closeDelta(marketBars[a.ticker], 1); const bv = closeDelta(marketBars[b.ticker], 1); const delta = (Number.isFinite(av) ? av : -Infinity) - (Number.isFinite(bv) ? bv : -Infinity); return (sort.direction === "asc" ? 1 : -1) * (delta || a.ticker.localeCompare(b.ticker)); }); };
    const renderRows = (items, kind) => { const sortedItems = sortRows(items, kind); return sortedItems.length ? sortedItems.map((row, index) => { const delta = closeDelta(marketBars[row.ticker], 1); return `<tr><td class="rank">${String(index + 1).padStart(2, "0")}</td><td><a class="etf-button tradingview-link" href="${tradingViewUrl(row.ticker)}" target="_blank" rel="noopener noreferrer" aria-label="在 TradingView 查看 ${row.ticker}">${html(row.ticker)}</a></td><td><span class="sub-label overview-industry-name">${html(row.name)}</span></td><td class="rsi-history-value">${Number(row.rsi).toFixed(1)}</td><td>${deltaDisplay(delta)}</td></tr>`; }).join("") : `<tr><td colspan="5"><div class="drawer-empty">暂无可用 RSI 数据</div></td></tr>`; };
    topBody.innerHTML = renderRows(topRows, "top");
    bottomBody.innerHTML = renderRows(bottomRows, "bottom");
    updateRsiRankingSortButtons();
  }
  function renderMarketOverview() {
    const breadthRoot = $("#market-overview-breadth"); const meta = $("#market-overview-meta");
    if (!breadthRoot) return;
    const latestBreadth = breadth.slice().sort((a, b) => String(a.date).localeCompare(String(b.date))).at(-1) || {};
    const breadthCards = [["T2108", Number(latestBreadth.t2108), "%", "neutral", "40MA 以上股票占比"], ["4%上涨 · 今日", Number(latestBreadth.up), "", "positive", "今日涨幅 ≥ 4% 的股票数"], ["4%下跌 · 今日", Number(latestBreadth.down), "", "negative", "今日跌幅 ≤ −4% 的股票数"], ["5日比率", Number(latestBreadth.ratio5), "", "neutral", "5 日上涨 / 下跌比"], ["10日比率", Number(latestBreadth.ratio10), "", "neutral", "10 日上涨 / 下跌比"], ["25%上涨 · 季度", Number(latestBreadth.up25Quarter), "", "positive", "季度涨幅 ≥ 25% 的股票数"], ["25%下跌 · 季度", Number(latestBreadth.down25Quarter), "", "negative", "季度跌幅 ≤ −25% 的股票数"]];
    breadthRoot.innerHTML = breadthCards.map(([label, value, suffix, tone, description]) => `<article class="market-overview-breadth-card"><small>${label}</small><strong class="${tone}">${Number.isFinite(value) ? value.toLocaleString("en-US", { minimumFractionDigits: suffix === "%" ? 1 : value % 1 ? 2 : 0, maximumFractionDigits: suffix === "%" ? 1 : value % 1 ? 2 : 0 }) : "—"}${suffix}</strong><span class="breadth-card-description">${description}</span><span class="breadth-card-source">Stockbee 市场宽度</span></article>`).join("");
    if (meta) {
      const indexDate = DashboardData.metadata.dataDate || "";
      const breadthDate = latestBreadth.date || "";
      meta.textContent = indexDate && breadthDate && indexDate !== breadthDate ? `指数最新确认日 ${indexDate} · 市场宽度最新日 ${breadthDate} · 变化列为绝对价格差` : `最新交易日 ${indexDate || breadthDate || "—"} · 变化列为绝对价格差`;
    }
    renderRsiRankings();
  }
  function sectorScore(sector) { return state.sectorMode === "d1" ? sector.d1 : state.sectorMode === "d5" ? sector.d5 : sector.d20; }
  function tradingViewUrl(ticker) { const exchange = tradingViewExchanges[ticker] || "AMEX"; return `https://tw.tradingview.com/chart/e2o5U28E/?symbol=${encodeURIComponent(`${exchange}:${ticker}`)}`; }
  function tradingViewSymbolUrl(ticker) { return `https://tw.tradingview.com/symbols/${encodeURIComponent(ticker)}/`; }
  function tradingViewIndexUrl(ticker) { const symbol = tradingViewIndexSymbols[ticker] || ticker; return `https://tw.tradingview.com/chart/e2o5U28E/?symbol=${encodeURIComponent(symbol)}`; }
  function sectorRows() {
    const query = state.query.toLowerCase();
    const rows = sectors.filter((row) => !query || `${row.ticker} ${row.name}`.toLowerCase().includes(query)).slice().sort((a, b) => compareMetricRows(a, b, state.sectorSort.key, state.sectorSort.direction));
    const spy = rows.find((row) => row.ticker === "SPY");
    return spy ? [spy, ...rows.filter((row) => row.ticker !== "SPY")] : rows;
  }
  function syncPinnedRowCovers() {
    [".sector-table-scroll", ".industry-table-scroll"].forEach((selector) => {
      const shell = $(selector); const header = shell && $("thead", shell); const cover = shell && $(".pinned-row-cover", shell);
      if (!shell || !header) return;
      const headerHeight = header.getBoundingClientRect().height;
      shell.style.setProperty("--table-header-height", `${headerHeight}px`);
      if (cover) { cover.style.top = "0px"; cover.style.height = "0px"; }
    });
  }
  function renderSectors() {
    const body = $("#sector-table-body"); const rows = sectorRows();
    body.innerHTML = rows.length ? rows.map((row, index) => { const bars = marketBars[row.ticker]; const d1Delta = closeDelta(bars, 1); const d5Delta = closeDelta(bars, 5); const d20Delta = closeDelta(bars, 20); return `<tr class="${row.ticker === "SPY" ? "is-pinned" : ""}"><td class="rank">${String(index + 1).padStart(2, "0")}</td><td><a class="etf-button tradingview-link" href="${tradingViewUrl(row.ticker)}" target="_blank" rel="noopener noreferrer" aria-label="在 TradingView 查看 ${row.ticker}">${row.ticker}</a>${row.ticker === "SPY" ? '<span class="sub-label">锁定</span>' : ""}</td><td>${row.name}</td><td>${row.rsi.toFixed(1)}</td><td>${deltaDisplay(d1Delta)}</td><td>${deltaDisplay(d5Delta)}</td><td>${deltaDisplay(d20Delta)}</td><td><button class="holding-link" type="button" data-etf="${row.ticker}">前十大 →</button></td></tr>`; }).join("") : `<tr><td colspan="8"><div class="drawer-empty">没有匹配的板块或 ETF</div></td></tr>`;
    updateSectorSortButtons();
    requestAnimationFrame(syncPinnedRowCovers);
  }
  function renderIndustries() {
    const query = state.query.toLowerCase(); const filtered = industries.filter((row) => !query || `${row.ticker} ${row.name} ${row.group}`.toLowerCase().includes(query));
    const sorted = filtered.slice().sort((a, b) => compareMetricRows(a, b, state.industrySort.key, state.industrySort.direction));
    const spy = sorted.find((row) => row.ticker === "SPY");
    const ordered = spy ? [spy, ...sorted.filter((row) => row.ticker !== "SPY")] : sorted;
    const visible = state.industryView === "top" ? ordered.slice(0, 15) : ordered;
    const body = $("#industry-table-body");
    body.innerHTML = visible.length ? visible.map((row, index) => { const bars = marketBars[row.ticker]; const d1Delta = closeDelta(bars, 1); const d5Delta = closeDelta(bars, 5); const d20Delta = closeDelta(bars, 20); return `<tr class="${row.ticker === "SPY" ? "is-pinned" : ""}"><td class="rank">${String(index + 1).padStart(2, "0")}</td><td><a class="etf-button tradingview-link" href="${tradingViewUrl(row.ticker)}" target="_blank" rel="noopener noreferrer" aria-label="在 TradingView 查看 ${row.ticker}">${row.ticker}</a><span class="sub-label">${row.ticker === "SPY" ? "标普 500 · 锁定" : ""}</span></td><td>${row.name}<span class="sub-label">${row.group}</span></td><td>${row.rsi.toFixed(1)}</td><td>${deltaDisplay(d1Delta)}</td><td>${deltaDisplay(d5Delta)}</td><td>${deltaDisplay(d20Delta)}</td><td><button class="holding-link" type="button" data-etf="${row.ticker}">前十大 →</button></td></tr>`; }).join("") : `<tr><td colspan="8"><div class="drawer-empty">没有匹配的行业 ETF</div></td></tr>`;
    $("#industry-view-meta").textContent = `显示 ${visible.length} / ${filtered.length}`;
    const matrix = $("#industry-matrix");
    matrix.hidden = true;
    matrix.innerHTML = filtered.map((row) => { const delta = closeDelta(marketBars[row.ticker], 5); return `<button class="matrix-cell" type="button" data-etf="${row.ticker}" aria-label="查看 ${row.ticker} ${row.name} 详情"><span class="matrix-ticker">${row.ticker}</span><span class="matrix-name">${row.name}</span><span class="matrix-metric">${row.rsi.toFixed(0)} · ${deltaDisplay(delta)}</span></button>`; }).join("");
    updateIndustrySortButtons();
    requestAnimationFrame(syncPinnedRowCovers);
  }
  function renderThemes() {
    const themeRoot = $("#theme-grid"); if (!themeRoot) return;
    const query = state.query.toLowerCase(); const visible = themes.filter((theme) => !query || `${theme.ticker} ${theme.name}`.toLowerCase().includes(query));
    themeRoot.innerHTML = visible.length ? visible.map((theme) => `<article class="theme-card"><div class="theme-top"><span class="theme-rank">候选 ${String(theme.rank).padStart(2, "0")}</span><span class="theme-score">${theme.analysisStatus === "ready" ? theme.total : "待研究"}</span></div><div class="theme-name">${theme.name}</div><div class="theme-ticker">${theme.ticker} · ${theme.memberEtfs ? theme.memberEtfs.length : 1} 个 ETF · 候选集</div><div class="factor-list">${themeFactorDefs.map(([key, label]) => `<div class="factor-line"><span>${label}</span><i><span style="width:${theme.factors[key]}%"></span></i><b>${theme.factors[key]}</b></div>`).join("")}</div></article>`).join("") : `<div class="drawer-empty">没有匹配的主题</div>`;
  }
  function renderStockbeeMomentum() {
    const meta = $("#stockbee-momentum-meta"); const body = $("#stockbee-momentum-body");
    if (!body) return;
    const rows = Array.isArray(stockbeeMomentum) ? stockbeeMomentum : [];
    if (meta) {
      const dateLabel = stockbeeMomentumMeta.latestDate ? `来源最新日期 ${stockbeeMomentumMeta.latestDate}` : "尚无来源日期";
      const staleLabel = stockbeeMomentumMeta.isStale ? " · 来源已过期，仅供回溯" : " · 每日更新来源";
      const verified = Number(stockbeeMomentumMeta.classificationVerifiedCount);
      const total = Number(stockbeeMomentumMeta.rowCount);
      const coverageLabel = Number.isFinite(verified) && Number.isFinite(total) ? ` · 分类已核验 ${verified}/${total}` : "";
      meta.textContent = `${dateLabel}${staleLabel}${coverageLabel}`;
      meta.classList.toggle("is-stale", Boolean(stockbeeMomentumMeta.isStale));
    }
    body.innerHTML = rows.length ? rows.map((row, index) => `<tr><td class="rank">${String(index + 1).padStart(2, "0")}</td><td><a class="stockbee-ticker tradingview-link" href="${tradingViewSymbolUrl(row.ticker)}" target="_blank" rel="noopener noreferrer" aria-label="在 TradingView 查看 ${html(row.ticker)}">${html(row.ticker)}</a></td><td class="stockbee-classification">${html(classificationLabel(row.sector, sectorLabelsZh))}</td><td class="stockbee-classification">${html(classificationLabel(row.industry, industryLabelsZh))}</td></tr>`).join("") : `<tr><td colspan="4"><div class="drawer-empty">暂无可验证的 Stockbee 动能股票名单</div></td></tr>`;
    const shell = $(".stockbee-momentum-table-scroll"); if (shell) shell.scrollLeft = 0;
  }
  function renderBreadth() {
    const displayValue = (row, key, digits) => { const value = Number(row[key]); return Number.isFinite(value) ? (digits ? value.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits }) : value.toLocaleString("en-US")) : "—"; };
    const breadthGroupFor = (index) => index < 6 ? "primary" : index < 12 ? "secondary" : "context";
    const breadthCellFill = (row, key) => {
      if (key !== "up" && key !== "down") return "";
      const value = Number(row[key]); if (!Number.isFinite(value)) return "";
      if (key === "up") return value >= 300 ? "#339966" : value >= 150 ? "#00ff00" : "#f4cccc";
      return value >= 300 ? "#e06666" : value > 150 ? "#f4cccc" : "#00ff00";
    };
    $("#breadth-table-body").innerHTML = breadth.map((row) => `<tr><td class="breadth-date">${row.date}</td>${breadthColumnDefs.map(([key, label, tone, digits], index) => { const fill = breadthCellFill(row, key); return `<td class="breadth-cell breadth-cell-${breadthGroupFor(index)} ${tone}${fill ? " has-cell-fill" : ""}" data-metric="${key}"${fill ? ` style="--cell-fill: ${fill}"` : ""}>${displayValue(row, key, digits)}</td>`; }).join("")}</tr>`).join("");
    const metric = breadthMetricDefs[state.breadthMetric] || breadthMetricDefs.ratio5;
    $("#breadth-metric-label").textContent = metric.label;
    const chartRows = breadthChartRows();
    $("#breadth-chart-range").textContent = chartRows.length ? `${chartRows[0].date} — ${chartRows[chartRows.length - 1].date}` : "暂无日期";
    $$('[data-breadth-metric]').forEach((button) => { const active = button.dataset.breadthMetric === state.breadthMetric; button.classList.toggle("is-active", active); button.setAttribute("aria-pressed", String(active)); });
    drawBreadthChart();
    setupBreadthScroll();
  }
  function setupBreadthScroll() {
    const viewport = $("#breadth-table-viewport"); const scrollbar = $("#breadth-scrollbar"); const track = $("#breadth-scrollbar-track");
    if (!viewport || !scrollbar || !track) return;
    const update = () => { track.style.width = `${viewport.scrollWidth}px`; scrollbar.scrollLeft = viewport.scrollLeft; scrollbar.setAttribute("aria-valuemax", String(Math.max(viewport.scrollWidth - viewport.clientWidth, 0))); scrollbar.setAttribute("aria-valuenow", String(viewport.scrollLeft)); };
    if (!viewport.dataset.scrollBound) {
      viewport.addEventListener("scroll", () => { scrollbar.scrollLeft = viewport.scrollLeft; scrollbar.setAttribute("aria-valuenow", String(viewport.scrollLeft)); });
      scrollbar.addEventListener("scroll", () => { viewport.scrollLeft = scrollbar.scrollLeft; scrollbar.setAttribute("aria-valuenow", String(scrollbar.scrollLeft)); });
      scrollbar.addEventListener("keydown", (event) => { if (event.key === "ArrowLeft" || event.key === "ArrowRight" || event.key === "Home" || event.key === "End") { event.preventDefault(); const step = Math.max(viewport.clientWidth * .35, 120); viewport.scrollLeft = event.key === "Home" ? 0 : event.key === "End" ? viewport.scrollWidth : viewport.scrollLeft + (event.key === "ArrowLeft" ? -step : step); } });
      viewport.dataset.scrollBound = "true";
    }
    requestAnimationFrame(update);
  }
  function compositeFromSnapshot(row) { return clamp(Math.round((row.ratio5 - 1) * 4 + (row.t2108 - 50) / 8), -3, 4); }
  function closeChange(bars, periods) {
    if (!Array.isArray(bars) || bars.length <= periods) return null;
    const previous = Number(bars[bars.length - periods - 1].close); const latest = Number(bars[bars.length - 1].close);
    return Number.isFinite(previous) && previous !== 0 && Number.isFinite(latest) ? +((latest / previous - 1) * 100).toFixed(2) : null;
  }
  function closeDelta(bars, periods) {
    if (!Array.isArray(bars) || bars.length <= periods) return null;
    const previous = Number(bars[bars.length - periods - 1].close); const latest = Number(bars[bars.length - 1].close);
    return Number.isFinite(previous) && Number.isFinite(latest) ? +(latest - previous).toFixed(2) : null;
  }
  function compareMetricRows(a, b, key, direction) {
    const av = Number(a[key]); const bv = Number(b[key]);
    if (!Number.isFinite(av) && !Number.isFinite(bv)) return a.ticker.localeCompare(b.ticker);
    if (!Number.isFinite(av)) return 1;
    if (!Number.isFinite(bv)) return -1;
    const delta = bv - av;
    return (direction === "asc" ? -1 : 1) * (delta || a.ticker.localeCompare(b.ticker));
  }
  function rsi14FromBars(bars) {
    if (!Array.isArray(bars) || bars.length < 15) return null;
    const closes = bars.slice(-15).map((bar) => Number(bar.close)); const gains = []; const losses = [];
    for (let index = 1; index < closes.length; index += 1) { const change = closes[index] - closes[index - 1]; gains.push(Math.max(change, 0)); losses.push(Math.max(-change, 0)); }
    const averageGain = gains.reduce((sum, value) => sum + value, 0) / gains.length; const averageLoss = losses.reduce((sum, value) => sum + value, 0) / losses.length;
    if (!Number.isFinite(averageGain) || !Number.isFinite(averageLoss)) return null;
    return +(averageLoss === 0 ? 100 : (100 - 100 / (1 + averageGain / averageLoss))).toFixed(1);
  }
  function rsiHistoryFor(ticker) {
    const bars = Array.isArray(marketBars[ticker]) ? marketBars[ticker] : [];
    const points = [];
    for (let index = 14; index < bars.length; index += 1) {
      const value = rsi14FromBars(bars.slice(0, index + 1));
      const date = bars[index] && (bars[index].date || bars[index].timestamp);
      if (value != null && date) points.push({ date: String(date).slice(0, 10), value });
    }
    return points.slice(-RSI_HISTORY_DAYS).reverse();
  }
  function rsiBand(value) { return value >= 60 ? ["强势", "positive"] : value <= 40 ? ["弱势", "negative"] : ["中性", "neutral"]; }
  function renderRsiHistory(kind) {
    const rows = kind === "sector" ? sectors : industries;
    const select = $(`#${kind}-rsi-symbol`); const body = $(`#${kind}-rsi-history-body`);
    if (!select || !body) return;
    const available = rows.filter((row) => row && row.ticker);
    const requested = state.rsiHistorySelection[kind];
    const selected = available.some((row) => row.ticker === requested) ? requested : (available.find((row) => row.ticker === "SPY") || available[0] || {}).ticker;
    state.rsiHistorySelection[kind] = selected || "SPY";
    const optionSignature = available.map((row) => row.ticker).join("|");
    if (select.dataset.options !== optionSignature) {
      select.innerHTML = available.map((row) => `<option value="${html(row.ticker)}">${html(row.ticker)} · ${html(row.name)}</option>`).join("");
      select.dataset.options = optionSignature;
    }
    select.value = state.rsiHistorySelection[kind];
    const points = rsiHistoryFor(state.rsiHistorySelection[kind]);
    body.innerHTML = points.length ? points.map((point) => { const [label, tone] = rsiBand(point.value); return `<tr><td class="rsi-history-date">${html(point.date)}</td><td class="rsi-history-value">${point.value.toFixed(1)}</td><td><span class="status-label is-${tone}">${label}</span></td></tr>`; }).join("") : `<tr><td colspan="3"><div class="drawer-empty">暂无本地 RSI 历史数据</div></td></tr>`;
  }
  function renderRsiHistoryControls() { renderRsiHistory("sector"); renderRsiHistory("industry"); }
  function rsiDailyChangeFor(ticker) {
    const snapshotBars = DashboardData.marketSnapshot?.instruments?.[ticker]?.bars;
    const bars = Array.isArray(marketBars[ticker]) && marketBars[ticker].length ? marketBars[ticker] : (Array.isArray(snapshotBars) ? snapshotBars : []);
    if (bars.length < 16) return null;
    const current = rsi14FromBars(bars); const previous = rsi14FromBars(bars.slice(0, -1));
    if (current == null || previous == null) return null;
    return { current, previous, delta: +(current - previous).toFixed(1), date: String(bars[bars.length - 1].date || "").slice(0, 10) };
  }
  function renderRsiGainers() {
    const gainersBody = $("#rsi-gainers-body"); const losersBody = $("#rsi-losers-body"); const meta = $("#rsi-gainers-meta"); const gainersMeta = $("#rsi-gainers-panel-meta"); const losersMeta = $("#rsi-losers-panel-meta");
    if (!gainersBody && !losersBody) return;
    const sourceRows = [...sectors.map((row) => ({ ...row, scope: "板块" })), ...industries.map((row) => ({ ...row, scope: "行业" }))];
    const changesByTicker = new Map();
    sourceRows.forEach((row) => {
      const change = rsiDailyChangeFor(row.ticker);
      if (!change) return;
      const existing = changesByTicker.get(row.ticker);
      if (existing) { existing.labels.push(`${row.scope} · ${row.name}`); return; }
      changesByTicker.set(row.ticker, { ...row, labels: [`${row.scope} · ${row.name}`], change });
    });
    const changes = [...changesByTicker.values()];
    const gainers = changes.filter((entry) => entry.change.delta >= RSI_GAIN_THRESHOLD).sort((a, b) => b.change.delta - a.change.delta || a.ticker.localeCompare(b.ticker));
    const losers = changes.filter((entry) => entry.change.delta <= -RSI_GAIN_THRESHOLD).sort((a, b) => a.change.delta - b.change.delta || a.ticker.localeCompare(b.ticker));
    const renderRows = (rows, emptyCopy) => rows.length ? rows.map(({ change, ...row }, index) => `<tr><td class="rank">${String(index + 1).padStart(2, "0")}</td><td><a class="etf-button tradingview-link" href="${tradingViewUrl(row.ticker)}" target="_blank" rel="noopener noreferrer" aria-label="在 TradingView 查看 ${row.ticker}">${row.ticker}</a></td><td><span class="rsi-scope-list">${row.labels.map((label) => html(label)).join("<br>")}</span></td><td class="rsi-history-value">${change.current.toFixed(1)}</td><td class="rsi-history-value">${change.previous.toFixed(1)}</td><td>${deltaDisplay(change.delta)}</td></tr>`).join("") : `<tr><td colspan="6"><div class="drawer-empty">${emptyCopy}</div></td></tr>`;
    if (gainersBody) gainersBody.innerHTML = renderRows(gainers, `当前没有 RSI14 增长达到 ${RSI_GAIN_THRESHOLD} 点的板块或行业 ETF`);
    if (losersBody) losersBody.innerHTML = renderRows(losers, `当前没有 RSI14 减少达到 ${RSI_GAIN_THRESHOLD} 点的板块或行业 ETF`);
    if (meta) meta.textContent = `日增 ${gainers.length} 项 · 日减 ${losers.length} 项 · 同一代码已合并`;
    if (gainersMeta) gainersMeta.textContent = gainers.length ? `共 ${gainers.length} 项 · 门槛 +${RSI_GAIN_THRESHOLD} 点` : `暂无达到 +${RSI_GAIN_THRESHOLD} 点的标的`;
    if (losersMeta) losersMeta.textContent = losers.length ? `共 ${losers.length} 项 · 门槛 −${RSI_GAIN_THRESHOLD} 点` : `暂无达到 −${RSI_GAIN_THRESHOLD} 点的标的`;
  }
  function formatPrice(value) { return Number(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function applyMarketSnapshot(snapshot) {
    const instruments = snapshot && snapshot.instruments;
    if (!instruments || typeof instruments !== "object") return false;
    Object.entries(instruments).forEach(([ticker, instrument]) => {
      const bars = Array.isArray(instrument.bars) ? instrument.bars : [];
      if (!bars.length) return;
      marketBars[ticker] = bars;
      marketIntradayBars[ticker] = Array.isArray(instrument.intradayBars) ? instrument.intradayBars : [];
      marketPendingBars[ticker] = instrument.pendingBar || null;
      const latest = instrument.latest || bars[bars.length - 1];
      const index = indexDefs.find((entry) => entry[0] === ticker);
      if (index && latest) { index[2] = formatPrice(latest.close); index[3] = Number.isFinite(Number(latest.change)) ? Number(latest.change) : index[3]; }
      const sector = sectors.find((row) => row.ticker === ticker);
      if (sector && latest) {
        sector.price = Number(latest.close);
        sector.rsi = rsi14FromBars(bars) ?? sector.rsi;
        sector.d1 = closeChange(bars, 1) ?? sector.d1;
        sector.d5 = closeChange(bars, 5) ?? sector.d5;
        sector.d20 = closeChange(bars, 20) ?? sector.d20;
        sector.trend = sector.d1 > .18 ? "改善" : sector.d1 < -.18 ? "转弱" : "盘整";
        sector.ma150 = instrument.ma150 ?? sector.ma150;
        sector.trend150 = instrument.trend150 || sector.trend150;
      }
      const industry = industries.find((row) => row.ticker === ticker);
      if (industry && latest) {
        industry.rsi = rsi14FromBars(bars) ?? industry.rsi;
        industry.d1 = closeChange(bars, 1) ?? industry.d1;
        industry.d5 = closeChange(bars, 5) ?? industry.d5;
        industry.d20 = closeChange(bars, 20) ?? industry.d20;
        industry.momentum = clamp(Math.round(industry.rsi * .84 + industry.d5 * 1.8), 25, 96);
        industry.ma150 = instrument.ma150 ?? industry.ma150;
        industry.trend150 = instrument.trend150 || industry.trend150;
      }
    });
    const marketMeta = snapshot.metadata || {};
    const referenceDate = instruments.SPX && instruments.SPX.latestDate ? instruments.SPX.latestDate : marketMeta.latestDate;
    DashboardData.marketSnapshot = snapshot;
    if (snapshot.holdings && typeof snapshot.holdings === "object") DashboardData.holdings = snapshot.holdings;
    const comparisonDate = marketMeta.comparisonDate || referenceDate;
    const calendarLatestDates = marketMeta.calendarLatestDates || {};
    DashboardData.metadata = { ...DashboardData.metadata, dataDate: referenceDate || DashboardData.metadata.dataDate, comparisonDate, calendarLatestDates, generatedAt: marketMeta.fetchedAt || DashboardData.metadata.generatedAt, sourceStatus: marketMeta.sourceStatus || "loaded", isStale: DashboardData.metadata.refresh ? DashboardData.metadata.isStale : false, missing: marketMeta.missing || [], marketData: marketMeta };
    const heroDate = $(".hero-date");
    const btcDate = instruments.BTC && instruments.BTC.latestDate ? instruments.BTC.latestDate : calendarLatestDates["crypto-24x7"];
    if (heroDate && referenceDate) heroDate.innerHTML = `${html(referenceDate)} 美股收盘${btcDate && btcDate !== referenceDate ? ` <span class="dot-divider">·</span> BTC 最新 ${html(btcDate)}` : ""} <span class="dot-divider">·</span> 本地快照`;
    const loadedBadge = $(".data-status-row .data-badge.is-loaded");
    if (loadedBadge && Number.isFinite(Number(marketMeta.loadedCount))) loadedBadge.innerHTML = `<i></i>本地快照 · ${Number(marketMeta.loadedCount)} 项`;
    const staleBadge = $(".data-status-row .data-badge.is-stale");
    const pendingBars = Array.isArray(snapshot.pendingBars) ? snapshot.pendingBars : [];
    if (staleBadge) {
      staleBadge.innerHTML = pendingBars.length ? `<i></i>未收盘日线 · ${pendingBars.length} 项 · ${html(pendingBars[0].date)}` : (marketMeta.latestDate ? `<i></i>跨资产日期 · ${html(marketMeta.latestDate)}` : staleBadge.innerHTML);
      staleBadge.title = pendingBars.length ? pendingBars.map((item) => `${item.symbol} ${item.date}`).join("、") : "";
    }
    renderLocalMarketAnalysis();
    holdings = snapshot.holdings && typeof snapshot.holdings === "object" ? snapshot.holdings : holdings;
    const sidebarNote = $(".sidebar-note");
    if (sidebarNote) sidebarNote.innerHTML = "本地快照模式<br />不连接实时行情";
    const footer = $(".site-footer");
    if (footer) footer.textContent = "StockTest 原型 · 本地行情快照，仅供研究参考，不构成任何投资建议。行情可能延迟、缺失或出错。";
    return true;
  }
  async function hydrateMarketSnapshot() {
    if (window.location.protocol === "file:") return;
    try {
      const response = await fetch("data/market_snapshot.json", { cache: "no-store" });
      if (!response.ok) return;
      const snapshot = await response.json();
      const applied = applyMarketSnapshot(snapshot);
      if (!applied) return;
      const hoveredTicker = $(".index-card:hover .sparkline")?.dataset.sparkTicker;
      // Render the RSI mover tables before the other snapshot-driven sections.
      // A failure in an unrelated section must not leave these tables at their
      // initial empty state after the market bars have loaded.
      renderRsiGainers();
      try {
        renderIndices(); renderMarketOverview(); renderSectors(); renderIndustries(); renderRsiHistoryControls(); renderRsiGainers(); renderStockbeeMomentum();
      } catch (error) {
        console.error("snapshot render failed", error);
      }
      if (hoveredTicker) {
        const hoveredCanvas = $$(".sparkline", $("#index-grid")).find((canvas) => canvas.dataset.sparkTicker === hoveredTicker);
        if (hoveredCanvas) updateIndexHoverBubble(hoveredCanvas.closest(".index-card"));
      }
    } catch (_) {
      // Keep deterministic sample data when the local snapshot is unavailable.
    }
  }
  function applyRefreshStatus(status) {
    const badge = $("#refresh-status-badge");
    if (!badge || !status || typeof status !== "object") return false;
    const lastCompleted = status.lastCompletedAt || status.lastFullSuccessAt;
    const completedAt = lastCompleted ? new Date(lastCompleted) : null;
    const ageMs = completedAt && Number.isFinite(completedAt.getTime()) ? Math.max(Date.now() - completedAt.getTime(), 0) : null;
    const missingCount = Number(status.sources && status.sources.market && status.sources.market.missingCount) || 0;
    badge.hidden = false;
    badge.classList.remove("is-loaded", "is-stale", "is-missing");
    if (status.status === "failed") {
      badge.classList.add("is-missing");
      badge.innerHTML = "<i></i>刷新失败 · 保留上次数据";
      badge.title = (status.errors || []).map((item) => `${item.source}: ${item.message}`).join("；");
    } else if (status.status === "partial") {
      badge.classList.add("is-missing");
      badge.innerHTML = `<i></i>局部缺失 · ${missingCount} 项`;
      badge.title = "本次刷新完成，但部分市场标的缺失。";
    } else if (ageMs == null || ageMs > STALE_AFTER_MS) {
      const hours = ageMs == null ? null : Math.max(1, Math.floor(ageMs / 3_600_000));
      badge.classList.add("is-stale");
      badge.innerHTML = `<i></i>数据过期${hours == null ? "" : ` · ${hours} 小时`}`;
      badge.title = lastCompleted ? `最后成功刷新：${lastCompleted}` : "没有可用的刷新完成时间。";
    } else {
      badge.classList.add("is-loaded");
      badge.innerHTML = `<i></i>数据新鲜 · ${completedAt.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`;
      badge.title = `最后成功刷新：${lastCompleted}`;
    }
    const fullRefreshAt = status.lastFullSuccessAt || null;
    const shouldHydrateDaily = state.lastFullRefreshAt && fullRefreshAt && state.lastFullRefreshAt !== fullRefreshAt;
    state.lastFullRefreshAt = fullRefreshAt;
    DashboardData.metadata.refresh = status;
    DashboardData.metadata.isStale = status.status === "failed" || status.status === "partial" || ageMs == null || ageMs > STALE_AFTER_MS;
    renderLocalMarketAnalysis();
    if (shouldHydrateDaily) {
      hydrateStockbee();
      hydrateStockbeeMomentum();
      hydrateMarketSnapshot();
    }
    return true;
  }
  async function hydrateRefreshStatus() {
    if (window.location.protocol === "file:") return;
    try {
      const response = await fetch("data/refresh_status.json", { cache: "no-store" });
      if (!response.ok) return;
      applyRefreshStatus(await response.json());
    } catch (_) {
      // The market and Stockbee snapshots remain usable when status metadata is absent.
    }
  }
  async function hydrateStockbee() {
    if (window.location.protocol === "file:") return;
    try {
      const response = await fetch("data/stockbee.json", { cache: "no-store" });
      if (!response.ok) return;
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.rows) || !snapshot.rows.length) return;
      breadth = snapshot.rows.map((row) => ({ ...row, composite: compositeFromSnapshot(row) }));
      DashboardData.breadth = breadth;
      DashboardData.metadata.sourceStatus = snapshot.metadata && snapshot.metadata.sourceStatus ? snapshot.metadata.sourceStatus : "loaded";
      DashboardData.metadata.dataDate = snapshot.metadata && snapshot.metadata.latestDate ? snapshot.metadata.latestDate : DashboardData.metadata.dataDate;
      DashboardData.metadata.generatedAt = snapshot.metadata && snapshot.metadata.fetchedAt ? snapshot.metadata.fetchedAt : DashboardData.metadata.generatedAt;
      renderBreadth(); renderMarketOverview();
      renderLocalMarketAnalysis();
    } catch (_) {
      // Local file previews keep the deterministic fallback when fetch is unavailable.
    }
  }
  async function hydrateStockbeeMomentum() {
    if (window.location.protocol === "file:") return;
    try {
      const response = await fetch("data/stockbee_momentum.json", { cache: "no-store" });
      if (!response.ok) return;
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.rows)) return;
      stockbeeMomentum = snapshot.rows.filter((row) => row && row.ticker);
      stockbeeMomentumMeta = snapshot.metadata || stockbeeMomentumMeta;
      DashboardData.stockbeeMomentum = stockbeeMomentum;
      renderStockbeeMomentum();
    } catch (_) {
      // The list remains empty when the source snapshot is unavailable.
    }
  }
  const clockFormatters = {
    us: new Intl.DateTimeFormat("en-GB", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23" }),
    usDate: new Intl.DateTimeFormat("en-CA", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit" }),
    cn: new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Shanghai", hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23" })
  };
  function updateClocks(now = new Date()) {
    const timestamp = now instanceof Date ? now : new Date(now);
    [["#us-date", clockFormatters.usDate], ["#us-clock", clockFormatters.us], ["#cn-clock", clockFormatters.cn]].forEach(([selector, formatter]) => {
      const clock = $(selector); if (!clock) return; clock.textContent = formatter.format(timestamp); clock.dateTime = timestamp.toISOString();
    });
  }
  function renderLocalMarketAnalysis() {
    const latestBreadth = breadth[breadth.length - 1] || {};
    const avg = (items, key) => items.length ? items.reduce((sum, item) => sum + (Number(item[key]) || 0), 0) / items.length : 0;
    const signals = {
      trend: avg([...sectors, ...industries], "d5") > 0 ? 1 : -1,
      breadth: Number(latestBreadth.ratio5) >= 1 ? 1 : -1,
      momentum: avg(industries, "d5") > 0 ? 1 : -1,
      liquidity: avg(sectors, "d1") >= 0 ? 1 : 0,
      risk: (DashboardData.metadata.missing || []).length || DashboardData.metadata.isStale ? -1 : 0
    };
    const score = Object.values(signals).reduce((sum, value) => sum + value, 0);
    const stateLabel = score >= 3 ? "偏强" : score <= -2 ? "偏弱" : "震荡";
    const heroTitle = $("#overview-title"); if (heroTitle) heroTitle.innerHTML = `${stateLabel} <span class="hero-score">· ${score >= 0 ? "+" : "−"}${Math.abs(score)}</span>`;
    const heroCopy = $(".hero-copy"); if (heroCopy) heroCopy.textContent = `本地快照显示板块 5 日变化${avg(sectors, "d5") >= 0 ? "偏正" : "偏弱"}，Stockbee 5 日上涨／下跌比为 ${Number(latestBreadth.ratio5 || 0).toFixed(2)}。结论随下一次本地刷新更新。`;
    const signalLabels = { trend: "趋势", breadth: "宽度", momentum: "动量", liquidity: "流动", risk: "风险" };
    const signalRow = $(".signal-row"); if (signalRow) signalRow.innerHTML = Object.entries(signals).map(([key, value]) => `<span class="signal-chip is-${value > 0 ? "positive" : value < 0 ? "negative" : "neutral"}"><b>${signalLabels[key]}</b> ${value > 0 ? "+" : ""}${value}</span>`).join("");
    const date = DashboardData.metadata.dataDate || SNAPSHOT_DATE; const heroDate = $(".hero-date"); if (heroDate) heroDate.innerHTML = `${html(date)} 美股收盘 <span class="dot-divider">·</span> 本地分析`;
    const topSectors = [...sectors].sort((a, b) => b.d5 - a.d5).slice(0, 2).map((item) => `${item.ticker} ${item.name}`).join("、") || "暂无板块数据";
    const topIndustries = [...industries].sort((a, b) => b.d5 - a.d5).slice(0, 2).map((item) => `${item.ticker} ${item.name}`).join("、") || "暂无行业数据";
    const breadthLabel = Number(latestBreadth.ratio5) >= 1.2 ? "强势" : Number(latestBreadth.ratio5) >= 0.9 ? "中性" : "偏弱";
    const items = [["板块强势", topSectors], ["行业强势", topIndustries], ["Stockbee 宽度", `${breadthLabel} · 5 日上涨／下跌比 ${Number(latestBreadth.ratio5 || 0).toFixed(2)}`]];
    $$(".briefing-item").forEach((node, index) => { const item = items[index]; if (!item) return; const strong = $("strong", node); const text = $("p", node); if (strong) strong.textContent = item[0]; if (text) text.textContent = item[1]; });
  }
  function renderAll() { renderIndices(); renderMarketOverview(); renderSectors(); renderIndustries(); renderRsiHistoryControls(); renderRsiGainers(); renderThemes(); renderStockbeeMomentum(); renderBreadth(); renderLocalMarketAnalysis(); updateModeButtons(); }
  function updateSectorSortButtons() {
    $$('[data-sector-sort]').forEach((button) => { const active = button.dataset.sectorSort === state.sectorSort.key; const glyph = button.querySelector(".sort-glyph"); button.classList.toggle("is-active", active); button.setAttribute("aria-sort", active ? (state.sectorSort.direction === "asc" ? "ascending" : "descending") : "none"); if (glyph) glyph.textContent = active ? (state.sectorSort.direction === "asc" ? "↑" : "↓") : "↕"; });
  }
  function updateIndustrySortButtons() {
    $$('[data-industry-sort]').forEach((button) => { const active = button.dataset.industrySort === state.industrySort.key; const glyph = button.querySelector(".sort-glyph"); button.classList.toggle("is-active", active); button.setAttribute("aria-sort", active ? (state.industrySort.direction === "asc" ? "ascending" : "descending") : "none"); if (glyph) glyph.textContent = active ? (state.industrySort.direction === "asc" ? "↑" : "↓") : "↕"; });
  }
  function updateRsiRankingSortButtons() {
    $$('[data-rsi-sort]').forEach((button) => { const sort = state.rsiRankingSort[button.dataset.rsiSort]; const active = sort && sort.key === "d1"; const glyph = button.querySelector(".sort-glyph"); button.classList.toggle("is-active", active); button.setAttribute("aria-sort", active ? (sort.direction === "asc" ? "ascending" : "descending") : "none"); if (glyph) glyph.textContent = active ? (sort.direction === "asc" ? "↑" : "↓") : "↕"; });
  }
  function updateModeButtons() {
    $$('[data-sector-mode]').forEach((button) => { const active = button.dataset.sectorMode === state.sectorMode; button.classList.toggle("is-active", active); button.setAttribute("aria-pressed", String(active)); });
    $$('[data-industry-view]').forEach((button) => { const active = button.dataset.industryView === state.industryView; button.classList.toggle("is-active", active); button.setAttribute("aria-pressed", String(active)); });
  }
  function showToast(message) {
    const toast = $("#toast"); toast.textContent = message; toast.classList.add("is-visible"); clearTimeout(state.toastTimer); state.toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 2400);
  }
  function instrumentFor(ticker) { return sectors.find((row) => row.ticker === ticker) || industries.find((row) => row.ticker === ticker); }
  function openDrawer(ticker) {
    const item = instrumentFor(ticker); if (!item) return;
    state.drawerTicker = ticker; const drawer = $("#detail-drawer"); const backdrop = $("#drawer-backdrop"); const isSector = sectors.some((row) => row.ticker === ticker); const entry = holdings[ticker]; const holdingsMeta = DashboardData.metadata.marketData && DashboardData.metadata.marketData.holdings || {}; const missingEntry = Array.isArray(holdingsMeta.missing) ? holdingsMeta.missing.find((record) => record && record.ticker === ticker) : null; const coverageStatus = entry && !Array.isArray(entry) ? entry.coverageStatus : null; const isReal = Boolean(entry && !Array.isArray(entry) && entry.status === "loaded" && coverageStatus !== "partial"); const list = isReal && Array.isArray(entry.holdings) ? entry.holdings.slice(0, 10) : [];
    const asOf = entry && entry.asOf ? entry.asOf : "未提供日期";
    const source = entry && entry.provider ? entry.provider : "暂无真实持仓数据";
    const failureReason = missingEntry && missingEntry.reason ? `原因：${missingEntry.reason}` : coverageStatus === "partial" ? `原因：来源仅返回 ${Array.isArray(entry.holdings) ? entry.holdings.length : 0} 行，未达到前十大` : "来源未返回可验证记录";
    $("#drawer-title").textContent = `${ticker} · ${item.name}`; $("#drawer-subtitle").textContent = `${isSector ? "板块 ETF" : "行业 ETF"} · ${SNAPSHOT_DATE} 收盘 · ${isReal ? "真实前十大名单" : "持仓待核对"}`;
    const holdingsMarkup = list.length ? `<div class="holding-list">${list.map((holding, index) => `<div class="holding-row"><span>${String(index + 1).padStart(2, "0")}</span><div><strong>${html(holding.ticker || "未提供代码")}</strong><small>${html(holding.name)}</small></div></div>`).join("")}</div>` : `<div class="drawer-empty">该 ETF 暂无可验证的前十大名单。${html(failureReason)}</div>`;
    const d5Delta = closeDelta(marketBars[ticker], 5); const d20Delta = closeDelta(marketBars[ticker], 20);
    $("#drawer-content").innerHTML = `<canvas class="drawer-chart" id="drawer-chart" width="360" height="140" aria-label="${ticker} 60 日走势"></canvas><div class="drawer-metrics"><div class="drawer-metric"><span>RSI14</span><strong>${item.rsi.toFixed(1)}</strong></div><div class="drawer-metric"><span class="drawer-metric-label">Δ5</span><strong>${deltaDisplay(d5Delta)}</strong></div><div class="drawer-metric"><span class="drawer-metric-label">Δ20</span><strong>${deltaDisplay(d20Delta)}</strong></div></div><div class="drawer-section"><h3>前十大持仓名单</h3><p>来源 · ${html(source)}<br>持仓日期 · ${html(asOf)} · 日更<br>仅展示名单，不展示权重比例。</p>${holdingsMarkup}</div><div class="drawer-section"><h3>研究提示</h3><p>${isSector ? "板块 ETF 的前十大名单来自公开来源，已保留来源与日期，适合盘后研究核对；未使用其他 ETF 数据替代。" : "行业 ETF 的前十大名单来自公开来源，未使用其他 ETF 数据替代；点击 ETF 名称可在 TradingView 查看行情。"}</p></div>`;
    drawer.classList.add("is-open"); drawer.setAttribute("aria-hidden", "false"); backdrop.hidden = false; document.body.style.overflow = "hidden"; drawSparkline($("#drawer-chart"), ticker.length * 11, item.d5, DETAIL_TRADING_DAYS, marketBars[ticker]);
    $("#drawer-close").focus();
  }
  function closeDrawer() { const drawer = $("#detail-drawer"); drawer.classList.remove("is-open"); drawer.setAttribute("aria-hidden", "true"); $("#drawer-backdrop").hidden = true; document.body.style.overflow = ""; state.drawerTicker = null; }
  function openEvidenceDrawer() {
    const metadata = DashboardData.metadata || {}; const market = metadata.marketData || {}; const refresh = metadata.refresh || {};
    const holdings = market.holdings || {}; const content = $("#evidence-content"); if (!content) return;
    const sourceRows = [
      ["行情快照", `${market.loadedCount || 0}/${market.requiredCount || 0} 个标的`, market.fetchedAt || metadata.generatedAt || "未提供"],
      ["ETF 持仓", `${holdings.loadedCount || 0}/${holdings.requestedCount || 0} 个来源`, holdings.fetchedAt || "日更"],
      ["刷新状态", refresh.status === "ok" ? "刷新成功" : (refresh.status || "未知"), refresh.lastCompletedAt || "未提供"],
      ["数据日期", metadata.dataDate || "未提供", metadata.comparisonDate ? `共同观察日 ${metadata.comparisonDate}` : "美股交易日历与 BTC 24×7 分开处理"]
    ];
    content.innerHTML = `<div class="evidence-list">${sourceRows.map(([label, value, detail]) => `<div class="evidence-item"><strong>${html(label)} · ${html(value)}</strong><span>${html(detail)}</span></div>`).join("")}<div class="evidence-item"><strong>来源边界</strong><span>网页仅读取本地快照；Yahoo、Binance、Stockbee 与发行方持仓来源由本地刷新器处理。缺失时保留上一份有效快照。</span></div></div>`;
    const drawer = $("#evidence-drawer"); drawer.classList.add("is-open"); drawer.setAttribute("aria-hidden", "false"); $("#drawer-backdrop").hidden = false; document.body.style.overflow = "hidden"; $("#evidence-close").focus();
  }
  function closeEvidenceDrawer() { const drawer = $("#evidence-drawer"); if (!drawer) return; drawer.classList.remove("is-open"); drawer.setAttribute("aria-hidden", "true"); $("#drawer-backdrop").hidden = true; document.body.style.overflow = ""; }
  function setTheme(theme) { document.documentElement.dataset.theme = theme; const button = $("#theme-toggle"); const dark = theme === "dark"; button.querySelector(".theme-label").textContent = dark ? "浅色模式" : "深色模式"; button.classList.toggle("is-on", dark); button.setAttribute("aria-pressed", String(dark)); button.setAttribute("aria-label", dark ? "切换浅色模式" : "切换深色模式"); try { localStorage.setItem(STORAGE_KEY, theme); } catch (_) {} requestAnimationFrame(() => { renderIndices(); drawBreadthChart(); if (state.drawerTicker) drawSparkline($("#drawer-chart"), state.drawerTicker.length * 11, (instrumentFor(state.drawerTicker) || {}).d5 || 0, DETAIL_TRADING_DAYS, marketBars[state.drawerTicker]); }); }
  function initTheme() { let saved = "light"; try { saved = localStorage.getItem(STORAGE_KEY) || "light"; } catch (_) {} setTheme(saved === "dark" ? "dark" : "light"); }

  const navItems = $$(".nav-item");
  const setActiveNav = (targetId) => navItems.forEach((item) => {
    const active = item.dataset.target === targetId;
    item.classList.toggle("is-active", active);
    if (active) item.setAttribute("aria-current", "location"); else item.removeAttribute("aria-current");
  });
  setActiveNav(navItems[0]?.dataset.target);
  navItems.forEach((button) => button.addEventListener("click", () => { const target = document.getElementById(button.dataset.target); if (target) target.scrollIntoView({ behavior: "smooth", block: "start" }); setActiveNav(button.dataset.target); }));
  if ("IntersectionObserver" in window) {
    const navTargets = navItems.map((item) => document.getElementById(item.dataset.target)).filter(Boolean);
    const sectionObserver = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (!visible) return;
      setActiveNav(visible.target.id);
    }, { rootMargin: "-96px 0px -58% 0px", threshold: 0.01 });
    navTargets.forEach((target) => sectionObserver.observe(target));
  }
  $$('[data-sector-mode]').forEach((button) => button.addEventListener("click", () => { state.sectorMode = button.dataset.sectorMode; state.sectorSort = { key: state.sectorMode, direction: "desc" }; renderSectors(); updateModeButtons(); }));
  $$('[data-sector-sort]').forEach((button) => button.addEventListener("click", () => { const key = button.dataset.sectorSort; state.sectorSort = { key, direction: state.sectorSort.key === key && state.sectorSort.direction === "desc" ? "asc" : "desc" }; if (key === "d5" || key === "d20") state.sectorMode = key; renderSectors(); updateModeButtons(); }));
  $$('[data-industry-view]').forEach((button) => button.addEventListener("click", () => { state.industryView = button.dataset.industryView; renderIndustries(); updateModeButtons(); }));
  $$('[data-industry-sort]').forEach((button) => button.addEventListener("click", () => { const key = button.dataset.industrySort; state.industrySort = { key, direction: state.industrySort.key === key && state.industrySort.direction === "desc" ? "asc" : "desc" }; renderIndustries(); }));
  $$('[data-rsi-sort]').forEach((button) => button.addEventListener("click", () => { const kind = button.dataset.rsiSort; const current = state.rsiRankingSort[kind]; state.rsiRankingSort[kind] = { key: "d1", direction: current.key === "d1" && current.direction === "desc" ? "asc" : "desc" }; renderRsiRankings(); }));
  ["sector", "industry"].forEach((kind) => {
    $(`#${kind}-rsi-symbol`).addEventListener("change", (event) => { state.rsiHistorySelection[kind] = event.target.value; renderRsiHistory(kind); });
    $(`#${kind}-rsi-toggle`).addEventListener("click", (event) => { const button = event.currentTarget; const table = $(`#${kind}-rsi-history`); const expanded = button.getAttribute("aria-expanded") === "true"; button.setAttribute("aria-expanded", String(!expanded)); button.textContent = expanded ? "展开" : "收起"; table.hidden = expanded; if (!expanded) renderRsiHistory(kind); });
  });
  $$('[data-breadth-metric]').forEach((button) => button.addEventListener("click", () => { state.breadthMetric = button.dataset.breadthMetric; renderBreadth(); }));
  $("#theme-toggle").addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
  $("#breadth-toggle").addEventListener("click", (event) => { const table = $("#breadth-data"); const expanded = event.currentTarget.getAttribute("aria-expanded") === "true"; event.currentTarget.setAttribute("aria-expanded", String(!expanded)); event.currentTarget.textContent = expanded ? "展开半年数据" : "收起半年数据"; table.hidden = expanded; if (!expanded) setupBreadthScroll(); });
  $("#drawer-close").addEventListener("click", closeDrawer); $("#drawer-backdrop").addEventListener("click", closeDrawer);
  $("#evidence-open").addEventListener("click", openEvidenceDrawer); $("#evidence-close").addEventListener("click", closeEvidenceDrawer);
  document.addEventListener("click", (event) => { const trigger = event.target.closest("[data-etf]"); if (trigger) openDrawer(trigger.dataset.etf); });
  document.addEventListener("keydown", (event) => { if (event.key !== "Escape") return; if (state.drawerTicker) closeDrawer(); else if ($("#evidence-drawer")?.classList.contains("is-open")) closeEvidenceDrawer(); });
  window.addEventListener("resize", () => { $$(".sparkline", $("#index-grid")).forEach((canvas) => drawIndexCardChart(canvas)); $$(".index-hover-bubble:not([hidden])").forEach((bubble) => updateIndexHoverBubble(bubble.__ownerCard || bubble.closest(".index-card"))); drawBreadthChart(); setupBreadthScroll(); syncPinnedRowCovers(); });
  [".sector-table-scroll", ".industry-table-scroll"].forEach((selector) => { const shell = $(selector); if (shell) shell.addEventListener("scroll", () => requestAnimationFrame(syncPinnedRowCovers), { passive: true }); });
  window.addEventListener("scroll", () => { $$(".index-hover-bubble:not([hidden])").forEach((bubble) => positionIndexHoverBubble(bubble.__ownerCard || bubble.closest(".index-card"))); }, { passive: true });
  renderAll(); initTheme(); updateClocks(); window.setInterval(updateClocks, 1000); hydrateStockbee(); hydrateStockbeeMomentum(); hydrateMarketSnapshot(); hydrateRefreshStatus();
  window.setInterval(() => { hydrateMarketSnapshot(); hydrateRefreshStatus(); }, BTC_REFRESH_INTERVAL_MS);
})();
