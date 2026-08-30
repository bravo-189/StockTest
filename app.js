(function () {
  "use strict";

  const SNAPSHOT_DATE = "2026-08-27";
  const INDEX_TRADING_DAYS = 21;
  const DETAIL_TRADING_DAYS = 60;
  const REFRESH_INTERVAL_MS = 60 * 60 * 1000;
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
  const companyNames = [
    ["MSFT", "Microsoft"], ["NVDA", "NVIDIA"], ["AAPL", "Apple"], ["AMZN", "Amazon"], ["META", "Meta Platforms"], ["GOOGL", "Alphabet"], ["AVGO", "Broadcom"], ["LLY", "Eli Lilly"], ["JPM", "JPMorgan Chase"], ["XOM", "Exxon Mobil"], ["V", "Visa"], ["UNH", "UnitedHealth"], ["COST", "Costco"], ["CAT", "Caterpillar"], ["NEE", "NextEra Energy"], ["GE", "GE Aerospace"], ["RTX", "RTX Corp"], ["CRM", "Salesforce"], ["ORCL", "Oracle"], ["AMD", "AMD"], ["LIN", "Linde"], ["WMT", "Walmart"], ["PG", "Procter & Gamble"], ["JNJ", "Johnson & Johnson"], ["HD", "Home Depot"], ["PLTR", "Palantir"], ["TSLA", "Tesla"], ["NFLX", "Netflix"], ["ADBE", "Adobe"], ["GS", "Goldman Sachs"]
  ];

  const state = { sectorMode: "d1", sectorSort: { key: "d1", direction: "desc" }, sectorStatus: "all", industryView: "top", industrySort: { key: "rsi", direction: "desc" }, breadthMetric: "ratio5", query: "", drawerTicker: null, toastTimer: null };
  const $ = (selector, root) => (root || document).querySelector(selector);
  const $$ = (selector, root) => Array.from((root || document).querySelectorAll(selector));
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const signed = (value, digits) => `${value >= 0 ? "+" : "−"}${Math.abs(value).toFixed(digits == null ? 1 : digits)}%`;
  const classFor = (value) => value > 0.08 ? "positive" : value < -0.08 ? "negative" : "neutral";
  const html = (value) => String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
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
    ["wordenUniverse", "Worden股票宇宙", "neutral", 0], ["t2108", "T2108", "neutral", 2], ["sp500", "S&P 500", "neutral", 2]
  ];

  const sectors = sectorDefs.map((entry, index) => {
    const [ticker, name, rsi, d1] = entry;
    return { ticker, name, rsi, d1, d5: +(d1 * 1.55 + valueFrom(index + 2, 4, 0.8)).toFixed(2), d20: +(d1 * 2.65 + valueFrom(index + 3, 7, 1.2)).toFixed(2), price: +(98 + index * 8 + valueFrom(index, 2, 2.5)).toFixed(2), trend: d1 > .18 ? "改善" : d1 < -.18 ? "转弱" : "盘整" };
  });
  const industries = industryDefs.map((entry, index) => {
    const [ticker, name, group] = entry;
    const rsi = clamp(71 - index * .42 + valueFrom(index + 11, 2, 8), 35, 76);
    const d5 = +(valueFrom(index + 21, 3, 3.3) + (rsi - 50) * .07).toFixed(2);
    const d20 = +(valueFrom(index + 31, 6, 7) + (rsi - 50) * .18).toFixed(2);
    return { ticker, name, group, rsi: +rsi.toFixed(1), d5, d20, momentum: clamp(Math.round(rsi * .84 + d5 * 1.8), 25, 96) };
  });
  let themes = themeNames.map(([name, ticker], index) => {
    const total = clamp(Math.round(92 - index * 2.1 + valueFrom(index + 81, 3, 7)), 42, 96);
    const factorValues = [valueFrom(index, 1, 8), valueFrom(index, 2, 11), valueFrom(index, 4, 13), valueFrom(index, 7, 10), valueFrom(index, 9, 15)].map((value) => clamp(Math.round(total + value), 30, 99));
    return { rank: index + 1, name, ticker, total, factors: Object.fromEntries(themeFactorDefs.map(([key], factorIndex) => [key, factorValues[factorIndex]])), memberEtfs: [ticker], analysisStatus: "pending" };
  });
  const holdings = Object.fromEntries(sectorDefs.map(([ticker], sectorIndex) => [ticker, Array.from({ length: 10 }, (_, index) => {
    const company = companyNames[(sectorIndex * 3 + index) % companyNames.length];
    return { ticker: company[0], name: company[1], weight: +(16.4 - index * 1.2 + valueFrom(sectorIndex + index, 5, .7)).toFixed(1) };
  })]));
  let breadth = Array.from({ length: 20 }, (_, index) => {
    const day = 20 - index;
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
    return { date: `08-${String(8 + day).padStart(2, "0")}`, up, down, ratio5, ratio10, up25Quarter, down25Quarter, up25Month, down25Month, up50Month, down50Month, up13_34d, down13_34d, wordenUniverse, t2108, sp500, composite };
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
    breadth
  };
  const marketBars = {};
  window.StockTestData = DashboardData;

  function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
  function drawSparkline(canvas, seed, positive, pointCount = INDEX_TRADING_DAYS, sourceBars) {
    if (!canvas) return;
    const ratio = window.devicePixelRatio || 1;
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
    ctx.fillStyle = color; const lastY = clamp(mapY(candleData[candleData.length - 1].close), 5, height - 5); ctx.beginPath(); ctx.arc(width - 1, lastY, 2.5, 0, Math.PI * 2); ctx.fill();
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
    root.innerHTML = indexDefs.map(([ticker, name, price, change], index) => `<article class="index-card"><div class="index-card-top"><div><div class="ticker">${ticker}</div><div class="index-name">${name}</div></div><span class="index-change ${classFor(change)}">${signed(change)}</span></div><div class="index-price">${price}</div><canvas class="sparkline" data-spark-ticker="${ticker}" data-spark-seed="${index + 40}" data-spark-change="${change}" aria-label="${name} 近一个月交易日 K 线"></canvas></article>`).join("");
    $$(".sparkline", root).forEach((canvas) => drawSparkline(canvas, Number(canvas.dataset.sparkSeed), Number(canvas.dataset.sparkChange), INDEX_TRADING_DAYS, marketBars[canvas.dataset.sparkTicker]));
  }
  function sectorScore(sector) { return state.sectorMode === "d1" ? sector.d1 : state.sectorMode === "d5" ? sector.d5 : sector.d20; }
  function sectorRows() {
    const query = state.query.toLowerCase();
    const rows = sectors.filter((row) => (!query || `${row.ticker} ${row.name}`.toLowerCase().includes(query)) && (row.ticker === "SPY" || state.sectorStatus === "all" || row.trend === state.sectorStatus)).slice().sort((a, b) => {
      const delta = Number(b[state.sectorSort.key]) - Number(a[state.sectorSort.key]);
      return (state.sectorSort.direction === "asc" ? -1 : 1) * (delta || a.ticker.localeCompare(b.ticker));
    });
    const spy = rows.find((row) => row.ticker === "SPY");
    return spy ? [spy, ...rows.filter((row) => row.ticker !== "SPY")] : rows;
  }
  function renderSectors() {
    const body = $("#sector-table-body"); const rows = sectorRows();
    body.innerHTML = rows.length ? rows.map((row, index) => { const tone = row.trend === "改善" ? "positive" : row.trend === "转弱" ? "negative" : "neutral"; return `<tr class="${row.ticker === "SPY" ? "is-pinned" : ""}"><td class="rank">${String(index + 1).padStart(2, "0")}</td><td><button class="etf-button" type="button" data-etf="${row.ticker}">${row.ticker}</button><span class="sub-label">${row.name}${row.ticker === "SPY" ? " · 锁定" : ""}</span></td><td class="price">${row.price.toFixed(2)}</td><td>${row.rsi.toFixed(1)}</td><td class="${classFor(row.d1)}">${signed(row.d1)}</td><td class="${classFor(row.d5)}">${signed(row.d5)}</td><td class="${classFor(row.d20)}">${signed(row.d20)}</td><td><span class="status-label is-${tone}">${row.trend}</span></td></tr>`; }).join("") : `<tr><td colspan="8"><div class="drawer-empty">没有匹配的板块或 ETF</div></td></tr>`;
    updateSectorSortButtons();
  }
  function renderIndustries() {
    const query = state.query.toLowerCase(); const filtered = industries.filter((row) => !query || `${row.ticker} ${row.name} ${row.group}`.toLowerCase().includes(query));
    const sorted = filtered.slice().sort((a, b) => { const delta = Number(b[state.industrySort.key]) - Number(a[state.industrySort.key]); return (state.industrySort.direction === "asc" ? -1 : 1) * (delta || a.ticker.localeCompare(b.ticker)); });
    const spy = sorted.find((row) => row.ticker === "SPY");
    const ordered = spy ? [spy, ...sorted.filter((row) => row.ticker !== "SPY")] : sorted;
    const visible = state.industryView === "top" ? ordered.slice(0, 15) : ordered;
    const body = $("#industry-table-body");
    body.innerHTML = visible.length ? visible.map((row, index) => `<tr class="${row.ticker === "SPY" ? "is-pinned" : ""}"><td class="rank">${String(index + 1).padStart(2, "0")}</td><td><button class="etf-button" type="button" data-etf="${row.ticker}">${row.ticker}</button><span class="sub-label">${row.ticker === "SPY" ? "标普 500 · 锁定" : ""}</span></td><td>${row.name}<span class="sub-label">${row.group}</span></td><td>${row.rsi.toFixed(1)}</td><td class="${classFor(row.d5)}">${signed(row.d5)}</td><td class="${classFor(row.d20)}">${signed(row.d20)}</td><td><button class="holding-link" type="button" data-etf="${row.ticker}">前十大 →</button></td></tr>`).join("") : `<tr><td colspan="7"><div class="drawer-empty">没有匹配的行业 ETF</div></td></tr>`;
    $("#industry-view-meta").textContent = `显示 ${visible.length} / ${filtered.length}`;
    const matrix = $("#industry-matrix");
    matrix.hidden = true;
    matrix.innerHTML = filtered.map((row) => `<button class="matrix-cell" type="button" data-etf="${row.ticker}" aria-label="查看 ${row.ticker} ${row.name} 详情"><span class="matrix-ticker">${row.ticker}</span><span class="matrix-name">${row.name}</span><span class="matrix-metric ${classFor(row.d5)}">${row.rsi.toFixed(0)} · ${signed(row.d5)}</span></button>`).join("");
    updateIndustrySortButtons();
  }
  function renderThemes() {
    const themeRoot = $("#theme-grid"); if (!themeRoot) return;
    const query = state.query.toLowerCase(); const visible = themes.filter((theme) => !query || `${theme.ticker} ${theme.name}`.toLowerCase().includes(query));
    themeRoot.innerHTML = visible.length ? visible.map((theme) => `<article class="theme-card"><div class="theme-top"><span class="theme-rank">候选 ${String(theme.rank).padStart(2, "0")}</span><span class="theme-score">${theme.analysisStatus === "ready" ? theme.total : "待研究"}</span></div><div class="theme-name">${theme.name}</div><div class="theme-ticker">${theme.ticker} · ${theme.memberEtfs ? theme.memberEtfs.length : 1} 个 ETF · 候选集</div><div class="factor-list">${themeFactorDefs.map(([key, label]) => `<div class="factor-line"><span>${label}</span><i><span style="width:${theme.factors[key]}%"></span></i><b>${theme.factors[key]}</b></div>`).join("")}</div></article>`).join("") : `<div class="drawer-empty">没有匹配的主题</div>`;
  }
  function renderHoldings() {
    $("#holdings-strip").innerHTML = sectors.filter((sector) => sector.ticker !== "SPY").slice(0, 12).map((sector) => `<button class="holding-button" type="button" data-etf="${sector.ticker}"><span class="ticker">${sector.ticker}</span><small>${sector.name} · 前十大持仓</small><span class="holding-arrow">查看详情 →</span></button>`).join("");
  }
  function renderBreadth() {
    const displayValue = (row, key, digits) => { const value = Number(row[key]); return Number.isFinite(value) ? (digits ? value.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits }) : value.toLocaleString("en-US")) : "—"; };
    $("#breadth-table-body").innerHTML = breadth.map((row) => `<tr><td class="breadth-date">${row.date}</td>${breadthColumnDefs.map(([key, label, tone, digits]) => `<td class="${tone}">${displayValue(row, key, digits)}</td>`).join("")}</tr>`).join("");
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
  function rsi14FromBars(bars) {
    if (!Array.isArray(bars) || bars.length < 15) return null;
    const closes = bars.slice(-15).map((bar) => Number(bar.close)); const gains = []; const losses = [];
    for (let index = 1; index < closes.length; index += 1) { const change = closes[index] - closes[index - 1]; gains.push(Math.max(change, 0)); losses.push(Math.max(-change, 0)); }
    const averageGain = gains.reduce((sum, value) => sum + value, 0) / gains.length; const averageLoss = losses.reduce((sum, value) => sum + value, 0) / losses.length;
    if (!Number.isFinite(averageGain) || !Number.isFinite(averageLoss)) return null;
    return +(averageLoss === 0 ? 100 : (100 - 100 / (1 + averageGain / averageLoss))).toFixed(1);
  }
  function formatPrice(value) { return Number(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function applyMarketSnapshot(snapshot) {
    const instruments = snapshot && snapshot.instruments;
    if (!instruments || typeof instruments !== "object") return false;
    Object.entries(instruments).forEach(([ticker, instrument]) => {
      const bars = Array.isArray(instrument.bars) ? instrument.bars : [];
      if (!bars.length) return;
      marketBars[ticker] = bars;
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
      }
      const industry = industries.find((row) => row.ticker === ticker);
      if (industry && latest) {
        industry.rsi = rsi14FromBars(bars) ?? industry.rsi;
        industry.d5 = closeChange(bars, 5) ?? industry.d5;
        industry.d20 = closeChange(bars, 20) ?? industry.d20;
        industry.momentum = clamp(Math.round(industry.rsi * .84 + industry.d5 * 1.8), 25, 96);
      }
    });
    const marketMeta = snapshot.metadata || {};
    const referenceDate = instruments.SPX && instruments.SPX.latestDate ? instruments.SPX.latestDate : marketMeta.latestDate;
    DashboardData.marketSnapshot = snapshot;
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
      if (!applyMarketSnapshot(snapshot)) return;
      renderIndices(); renderSectors(); renderIndustries(); renderHoldings();
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
    DashboardData.metadata.refresh = status;
    DashboardData.metadata.isStale = status.status === "failed" || status.status === "partial" || ageMs == null || ageMs > STALE_AFTER_MS;
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
      breadth = snapshot.rows.slice(0, 20).map((row) => ({ ...row, composite: compositeFromSnapshot(row) }));
      DashboardData.breadth = breadth;
      DashboardData.metadata.sourceStatus = snapshot.metadata && snapshot.metadata.sourceStatus ? snapshot.metadata.sourceStatus : "loaded";
      DashboardData.metadata.dataDate = snapshot.metadata && snapshot.metadata.latestDate ? snapshot.metadata.latestDate : DashboardData.metadata.dataDate;
      DashboardData.metadata.generatedAt = snapshot.metadata && snapshot.metadata.fetchedAt ? snapshot.metadata.fetchedAt : DashboardData.metadata.generatedAt;
      renderBreadth();
    } catch (_) {
      // Local file previews keep the deterministic fallback when fetch is unavailable.
    }
  }
  function renderAll() { renderIndices(); renderSectors(); renderIndustries(); renderThemes(); renderHoldings(); renderBreadth(); updateModeButtons(); }
  function updateSectorSortButtons() {
    $$('[data-sector-sort]').forEach((button) => { const active = button.dataset.sectorSort === state.sectorSort.key; const glyph = button.querySelector(".sort-glyph"); button.classList.toggle("is-active", active); button.setAttribute("aria-sort", active ? (state.sectorSort.direction === "asc" ? "ascending" : "descending") : "none"); if (glyph) glyph.textContent = active ? (state.sectorSort.direction === "asc" ? "↑" : "↓") : "↕"; });
  }
  function updateIndustrySortButtons() {
    $$('[data-industry-sort]').forEach((button) => { const active = button.dataset.industrySort === state.industrySort.key; const glyph = button.querySelector(".sort-glyph"); button.classList.toggle("is-active", active); button.setAttribute("aria-sort", active ? (state.industrySort.direction === "asc" ? "ascending" : "descending") : "none"); if (glyph) glyph.textContent = active ? (state.industrySort.direction === "asc" ? "↑" : "↓") : "↕"; });
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
    state.drawerTicker = ticker; const drawer = $("#detail-drawer"); const backdrop = $("#drawer-backdrop"); const isSector = sectors.some((row) => row.ticker === ticker); const list = holdings[ticker] || holdings.SPY;
    $("#drawer-title").textContent = `${ticker} · ${item.name}`; $("#drawer-subtitle").textContent = `${isSector ? "板块 ETF" : "行业 ETF"} · ${SNAPSHOT_DATE} 收盘 · 示例数据`;
    $("#drawer-content").innerHTML = `<canvas class="drawer-chart" id="drawer-chart" width="360" height="140" aria-label="${ticker} 60 日走势"></canvas><div class="drawer-metrics"><div class="drawer-metric"><span>RSI14</span><strong>${item.rsi.toFixed(1)}</strong></div><div class="drawer-metric"><span>Δ5</span><strong class="${classFor(item.d5)}">${signed(item.d5)}</strong></div><div class="drawer-metric"><span>Δ20</span><strong class="${classFor(item.d20)}">${signed(item.d20)}</strong></div></div><div class="drawer-section"><h3>前十大权重股</h3><p>持仓数据日期 · ${SNAPSHOT_DATE}</p><div class="holding-list">${list.map((holding, index) => `<div class="holding-row"><span>${String(index + 1).padStart(2, "0")}</span><div><strong>${holding.ticker}</strong><small>${holding.name}</small></div><span class="mono">${holding.weight.toFixed(1)}%</span><div class="weight-track"><span style="width:${clamp(holding.weight * 4.6, 0, 100)}%"></span></div></div>`).join("")}</div></div><div class="drawer-section"><h3>研究提示</h3><p>${isSector ? "该板块的多周期动能与相对强弱仅用于盘后研究排序；点击外部区域或按 Escape 关闭抽屉。" : "该行业来自 60 个行业 ETF 矩阵，当前详情沿用同一抽屉组件，便于快速对照持仓与多周期表现。"}</p></div>`;
    drawer.classList.add("is-open"); drawer.setAttribute("aria-hidden", "false"); backdrop.hidden = false; document.body.style.overflow = "hidden"; drawSparkline($("#drawer-chart"), ticker.length * 11, item.d5, DETAIL_TRADING_DAYS, marketBars[ticker]);
    $("#drawer-close").focus();
  }
  function closeDrawer() { const drawer = $("#detail-drawer"); drawer.classList.remove("is-open"); drawer.setAttribute("aria-hidden", "true"); $("#drawer-backdrop").hidden = true; document.body.style.overflow = ""; state.drawerTicker = null; }
  function setTheme(theme) { document.documentElement.dataset.theme = theme; const button = $("#theme-toggle"); const dark = theme === "dark"; button.querySelector(".theme-label").textContent = dark ? "浅色模式" : "深色模式"; button.classList.toggle("is-on", dark); button.setAttribute("aria-pressed", String(dark)); button.setAttribute("aria-label", dark ? "切换浅色模式" : "切换深色模式"); try { localStorage.setItem(STORAGE_KEY, theme); } catch (_) {} requestAnimationFrame(() => { renderIndices(); drawBreadthChart(); if (state.drawerTicker) drawSparkline($("#drawer-chart"), state.drawerTicker.length * 11, (instrumentFor(state.drawerTicker) || {}).d5 || 0, DETAIL_TRADING_DAYS, marketBars[state.drawerTicker]); }); }
  function initTheme() { let saved = "light"; try { saved = localStorage.getItem(STORAGE_KEY) || "light"; } catch (_) {} setTheme(saved === "dark" ? "dark" : "light"); }

  $$(".nav-item").forEach((button) => button.addEventListener("click", () => { const target = document.getElementById(button.dataset.target); if (target) target.scrollIntoView({ behavior: "smooth", block: "start" }); $$(".nav-item").forEach((item) => item.classList.toggle("is-active", item === button)); }));
  $$('[data-sector-mode]').forEach((button) => button.addEventListener("click", () => { state.sectorMode = button.dataset.sectorMode; state.sectorSort = { key: state.sectorMode, direction: "desc" }; renderSectors(); updateModeButtons(); }));
  $$('[data-sector-sort]').forEach((button) => button.addEventListener("click", () => { const key = button.dataset.sectorSort; state.sectorSort = { key, direction: state.sectorSort.key === key && state.sectorSort.direction === "desc" ? "asc" : "desc" }; if (key === "d5" || key === "d20") state.sectorMode = key; renderSectors(); updateModeButtons(); }));
  $$('[data-industry-view]').forEach((button) => button.addEventListener("click", () => { state.industryView = button.dataset.industryView; renderIndustries(); updateModeButtons(); }));
  $$('[data-industry-sort]').forEach((button) => button.addEventListener("click", () => { const key = button.dataset.industrySort; state.industrySort = { key, direction: state.industrySort.key === key && state.industrySort.direction === "desc" ? "asc" : "desc" }; renderIndustries(); }));
  $$('[data-breadth-metric]').forEach((button) => button.addEventListener("click", () => { state.breadthMetric = button.dataset.breadthMetric; renderBreadth(); }));
  $("#global-search").addEventListener("input", (event) => { state.query = event.target.value.trim(); renderSectors(); renderIndustries(); renderThemes(); if (state.query) showToast(`正在筛选「${state.query}」`); });
  $("#sector-status-filter").addEventListener("change", (event) => { state.sectorStatus = event.target.value; renderSectors(); showToast(state.sectorStatus === "all" ? "已显示全部板块" : `已筛选状态：${state.sectorStatus}（SPY 固定首行）`); });
  $("#focus-search").addEventListener("click", () => $("#global-search").focus());
  $("#theme-toggle").addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
  $("#breadth-toggle").addEventListener("click", (event) => { const table = $("#breadth-data"); const expanded = event.currentTarget.getAttribute("aria-expanded") === "true"; event.currentTarget.setAttribute("aria-expanded", String(!expanded)); event.currentTarget.textContent = expanded ? "展开 20 日数据" : "收起 20 日数据"; table.hidden = expanded; if (!expanded) setupBreadthScroll(); });
  $("#drawer-close").addEventListener("click", closeDrawer); $("#drawer-backdrop").addEventListener("click", closeDrawer);
  document.addEventListener("click", (event) => { const trigger = event.target.closest("[data-etf]"); if (trigger) openDrawer(trigger.dataset.etf); });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && state.drawerTicker) closeDrawer(); if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); $("#global-search").focus(); } });
  window.addEventListener("resize", () => { $$(".sparkline").forEach((canvas) => drawSparkline(canvas, Number(canvas.dataset.sparkSeed), Number(canvas.dataset.sparkChange), INDEX_TRADING_DAYS, marketBars[canvas.dataset.sparkTicker])); drawBreadthChart(); setupBreadthScroll(); });
  renderAll(); initTheme(); hydrateStockbee(); hydrateMarketSnapshot(); hydrateRefreshStatus();
  window.setInterval(() => { hydrateStockbee(); hydrateMarketSnapshot(); hydrateRefreshStatus(); }, REFRESH_INTERVAL_MS);
})();
