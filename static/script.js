/**
 * Águia Trader - Dashboard & Motor Gráfico Quantitativo
 * Renderização em HTML5 Canvas de Candlesticks, Médias WMA/SMA, Projeção 14D e Volume.
 */

// Universo de Ações B3 com dados quantitativos
let ASSETS_UNIVERSE = [
    { ticker: "ASAI3", price: 13.27, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 5.17, target: 13.96, stop: 12.65, payoff: "1.11 : 1", dayVar: "+0.85%", basePrice: 8.5 },
    { ticker: "ANIM3", price: 5.29, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.46, target: 5.53, stop: 5.08, payoff: "1.14 : 1", dayVar: "+1.15%", basePrice: 4.1 },
    { ticker: "ARML3", price: 6.48, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 5.45, target: 6.83, stop: 6.18, payoff: "1.17 : 1", dayVar: "+0.62%", basePrice: 5.2 },
    { ticker: "AURE3", price: 15.59, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.53, target: 16.30, stop: 14.95, payoff: "1.11 : 1", dayVar: "+0.32%", basePrice: 12.8 },
    { ticker: "PETR4", price: 38.45, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 3.80, target: 39.91, stop: 37.10, payoff: "1.08 : 1", dayVar: "+1.42%", basePrice: 32.0 },
    { ticker: "VALE3", price: 61.20, trend: "BAIXA", trendText: "BAIXA (BEARISH)", returnPct: -2.75, target: 59.52, stop: 62.60, payoff: "1.20 : 1", dayVar: "-0.95%", basePrice: 65.0 },
    { ticker: "ITUB4", price: 34.80, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.10, target: 36.23, stop: 33.60, payoff: "1.19 : 1", dayVar: "+0.78%", basePrice: 29.5 },
    { ticker: "BBAS3", price: 27.60, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 3.95, target: 28.69, stop: 26.70, payoff: "1.21 : 1", dayVar: "+0.55%", basePrice: 24.2 },
    { ticker: "BBDC4", price: 14.90, trend: "NEUTRO", trendText: "LATERAL (NEUTRAL)", returnPct: 0.67, target: 15.00, stop: 14.60, payoff: "0.33 : 1", dayVar: "+0.10%", basePrice: 14.5 },
    { ticker: "WEGE3", price: 52.80, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 6.25, target: 56.10, stop: 50.40, payoff: "1.38 : 1", dayVar: "+1.85%", basePrice: 42.0 },
    { ticker: "MGLU3", price: 8.90, trend: "BAIXA", trendText: "BAIXA (BEARISH)", returnPct: -5.40, target: 8.42, stop: 9.35, payoff: "1.07 : 1", dayVar: "-2.10%", basePrice: 11.2 },
    { ticker: "PRIO3", price: 44.50, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.85, target: 46.66, stop: 42.80, payoff: 1.27, dayVar: "+0.90%", basePrice: 38.0 },
    { ticker: "RENT3", price: 54.30, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.20, target: 56.58, stop: 52.40, payoff: 1.20, dayVar: "+0.60%", basePrice: 47.0 },
    { ticker: "EMBR3", price: 49.80, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 5.60, target: 52.59, stop: 47.90, payoff: 1.47, dayVar: "+1.95%", basePrice: 36.0 },
    { ticker: "GGBR4", price: 21.15, trend: "NEUTRO", trendText: "LATERAL (NEUTRAL)", returnPct: 0.45, target: 21.25, stop: 20.80, payoff: 0.28, dayVar: "+0.05%", basePrice: 20.8 },
    { ticker: "CSNA3", price: 12.40, trend: "BAIXA", trendText: "BAIXA (BEARISH)", returnPct: -3.80, target: 11.93, stop: 12.85, payoff: 1.04, dayVar: "-1.30%", basePrice: 14.2 },
    { ticker: "SUZB3", price: 58.70, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.30, target: 61.22, stop: 56.90, payoff: 1.40, dayVar: "+0.70%", basePrice: 51.0 },
    { ticker: "JBSS3", price: 35.10, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 3.70, target: 36.40, stop: 34.10, payoff: 1.30, dayVar: "+0.45%", basePrice: 30.0 }
];

// Estado da Aplicação
let currentSelectedTicker = "ASAI3";
let currentFilter = "TODOS";
let searchQuery = "";
let chartDataCache = {};
let isServerOnline = false;

// Elementos do DOM
const stockListContainer = document.getElementById("stockListContainer");
const searchInput = document.getElementById("searchInput");
const filterPills = document.querySelectorAll(".filter-pill");
const universeCount = document.getElementById("universeCount");

const headlineTicker = document.getElementById("headlineTicker");
const headlineReturn = document.getElementById("headlineReturn");
const headlineTrend = document.getElementById("headlineTrend");

const floatingTargetBadge = document.getElementById("floatingTargetBadge");
const badgeTrendAction = document.getElementById("badgeTrendAction");
const badgeTargetPrice = document.getElementById("badgeTargetPrice");
const badgeTargetReturn = document.getElementById("badgeTargetReturn");

const metricCurrentPrice = document.getElementById("metricCurrentPrice");
const metricPriceDiff = document.getElementById("metricPriceDiff");
const metricTargetPrice = document.getElementById("metricTargetPrice");
const metricTargetReturn = document.getElementById("metricTargetReturn");
const metricStopLoss = document.getElementById("metricStopLoss");
const metricPayoff = document.getElementById("metricPayoff");
const aiReasoningText = document.getElementById("aiReasoningText");
const snapshotTimestamp = document.getElementById("snapshotTimestamp");

const canvas = document.getElementById("tradingChartCanvas");
const ctx = canvas.getContext("2d");

/**
 * Retorna o endpoint base da API com fallback robusto
 */
function getApiBaseUrl() {
    if (window.location.protocol === "file:" || !window.location.origin.includes(":8000")) {
        return "http://localhost:8000";
    }
    return "";
}

/**
 * Gera dados sintéticos realistas de velas para o ativo selecionado
 */
function generateCandleData(asset) {
    if (chartDataCache[asset.ticker]) {
        return chartDataCache[asset.ticker];
    }

    const candlesCount = 65;
    const candles = [];
    const base = asset.basePrice || (asset.price * 0.75);
    let currentPrice = base;
    const finalPrice = asset.price;
    const priceStep = (finalPrice - base) / candlesCount;

    let seed = 0;
    for (let i = 0; i < asset.ticker.length; i++) {
        seed += asset.ticker.charCodeAt(i);
    }

    function pseudoRandom() {
        const x = Math.sin(seed++) * 10000;
        return x - Math.floor(x);
    }

    for (let i = 0; i < candlesCount; i++) {
        const noise = (pseudoRandom() - 0.48) * (finalPrice * 0.04);
        const open = currentPrice;
        let close = open + priceStep + noise;

        if (i === candlesCount - 1) {
            close = finalPrice;
        }

        const high = Math.max(open, close) + pseudoRandom() * (finalPrice * 0.02);
        const low = Math.min(open, close) - pseudoRandom() * (finalPrice * 0.02);
        const volume = (pseudoRandom() * 40 + 10) * 1000000;

        candles.push({ open, high, low, close, volume });
        currentPrice = close;
    }

    // Calcula WMA 30 e SMA 200
    const wma30 = [];
    const sma200 = [];

    for (let i = 0; i < candles.length; i++) {
        // WMA 30
        const periodWma = Math.min(30, i + 1);
        let weightSum = 0;
        let priceWeightedSum = 0;
        for (let j = 0; j < periodWma; j++) {
            const weight = periodWma - j;
            priceWeightedSum += candles[i - j].close * weight;
            weightSum += weight;
        }
        wma30.push(priceWeightedSum / weightSum);

        // SMA 200
        const periodSma = Math.min(200, i + 1);
        let sumSma = 0;
        for (let j = 0; j < periodSma; j++) {
            sumSma += candles[i - j].close;
        }
        const smaVal = (sumSma / periodSma) * 0.96;
        sma200.push(smaVal);
    }

    chartDataCache[asset.ticker] = { candles, wma30, sma200 };
    return chartDataCache[asset.ticker];
}

/**
 * Desenha o gráfico de Candlestick, WMA, SMA e Projeção no Canvas HTML5
 */
function renderTradingChart() {
    const asset = ASSETS_UNIVERSE.find(a => a.ticker === currentSelectedTicker) || ASSETS_UNIVERSE[0];
    const { candles, wma30, sma200 } = generateCandleData(asset);

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;

    ctx.save();
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    // Fundo limpo
    ctx.fillStyle = "#070b13";
    ctx.fillRect(0, 0, width, height);

    // Margens
    const marginLeft = 60;
    const marginRight = 30;
    const marginTop = 45;
    const volumeHeight = 85;
    const chartBottom = height - volumeHeight - 30;
    const chartHeight = chartBottom - marginTop;
    const plotWidth = width - marginLeft - marginRight;

    const futureSteps = 14;
    const totalSlots = candles.length + futureSteps;
    const slotWidth = plotWidth / totalSlots;
    const candleBarWidth = Math.max(3, slotWidth * 0.65);

    let minPrice = Infinity;
    let maxPrice = -Infinity;

    candles.forEach(c => {
        if (c.low < minPrice) minPrice = c.low;
        if (c.high > maxPrice) maxPrice = c.high;
    });

    wma30.forEach(w => {
        if (w < minPrice) minPrice = w;
        if (w > maxPrice) maxPrice = w;
    });

    sma200.forEach(s => {
        if (s < minPrice) minPrice = s;
        if (s > maxPrice) maxPrice = s;
    });

    if (asset.target > maxPrice) maxPrice = asset.target;
    if (asset.target < minPrice) minPrice = asset.target;

    const priceMargin = (maxPrice - minPrice) * 0.12;
    minPrice -= priceMargin;
    maxPrice += priceMargin;

    function priceToY(price) {
        return chartBottom - ((price - minPrice) / (maxPrice - minPrice)) * chartHeight;
    }

    // 1. Grade horizontal e eixos de preço (Y-Axis)
    ctx.strokeStyle = "#141c2c";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#64748b";
    ctx.font = "11px 'JetBrains Mono', monospace";
    ctx.textAlign = "right";

    const priceTicksCount = 7;
    for (let i = 0; i <= priceTicksCount; i++) {
        const p = minPrice + ((maxPrice - minPrice) / priceTicksCount) * i;
        const y = priceToY(p);

        ctx.beginPath();
        ctx.moveTo(marginLeft, y);
        ctx.lineTo(width - marginRight, y);
        ctx.stroke();

        ctx.fillText(p.toFixed(0), marginLeft - 12, y + 4);
    }

    // Rótulo vertical "Price" no eixo Y
    ctx.save();
    ctx.translate(18, chartBottom - chartHeight / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = "center";
    ctx.fillStyle = "#94a3b8";
    ctx.font = "12px 'Inter', sans-serif";
    ctx.fillText("Price", 0, 0);
    ctx.restore();

    // 2. Faixa sombreada de Projeção 14D
    const projStartX = marginLeft + candles.length * slotWidth;
    const projWidth = futureSteps * slotWidth;

    const isBull = asset.trend === "ALTA";
    const projGradient = ctx.createLinearGradient(projStartX, 0, projStartX + projWidth, 0);
    if (isBull) {
        projGradient.addColorStop(0, "rgba(16, 185, 129, 0.05)");
        projGradient.addColorStop(1, "rgba(16, 185, 129, 0.22)");
    } else {
        projGradient.addColorStop(0, "rgba(239, 68, 68, 0.05)");
        projGradient.addColorStop(1, "rgba(239, 68, 68, 0.22)");
    }

    ctx.fillStyle = projGradient;
    ctx.fillRect(projStartX, marginTop, projWidth, chartHeight);

    // Linha vertical divisória da projeção
    ctx.strokeStyle = isBull ? "rgba(16, 185, 129, 0.4)" : "rgba(239, 68, 68, 0.4)";
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(projStartX, marginTop);
    ctx.lineTo(projStartX, chartBottom);
    ctx.stroke();
    ctx.setLineDash([]);

    // 3. Desenho dos Candlesticks
    candles.forEach((c, idx) => {
        const x = marginLeft + idx * slotWidth + slotWidth / 2;
        const openY = priceToY(c.open);
        const closeY = priceToY(c.close);
        const highY = priceToY(c.high);
        const lowY = priceToY(c.low);

        const isUp = c.close >= c.open;
        const candleColor = isUp ? "#10b981" : "#ef4444";

        ctx.strokeStyle = candleColor;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(x, highY);
        ctx.lineTo(x, lowY);
        ctx.stroke();

        ctx.fillStyle = candleColor;
        const bodyTop = Math.min(openY, closeY);
        const bodyHeight = Math.max(2, Math.abs(closeY - openY));
        ctx.fillRect(x - candleBarWidth / 2, bodyTop, candleBarWidth, bodyHeight);
    });

    // 4. Curva SMA 200 (Azul)
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 2.4;
    ctx.beginPath();
    sma200.forEach((val, idx) => {
        const x = marginLeft + idx * slotWidth + slotWidth / 2;
        const y = priceToY(val);
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // 5. Curva WMA 30 (Amarela)
    ctx.strokeStyle = "#facc15";
    ctx.lineWidth = 2.4;
    ctx.beginPath();
    wma30.forEach((val, idx) => {
        const x = marginLeft + idx * slotWidth + slotWidth / 2;
        const y = priceToY(val);
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // 6. Projeção Tracejada até o Alvo (14D)
    const lastX = marginLeft + (candles.length - 1) * slotWidth + slotWidth / 2;
    const lastPriceY = priceToY(candles[candles.length - 1].close);
    const targetX = marginLeft + (totalSlots - 1) * slotWidth;
    const targetY = priceToY(asset.target);

    ctx.strokeStyle = isBull ? "#34d399" : "#f87171";
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(lastX, lastPriceY);
    ctx.quadraticCurveTo((lastX + targetX) / 2, (lastPriceY + targetY) / 2 + (isBull ? -8 : 8), targetX, targetY);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = isBull ? "#34d399" : "#f87171";
    ctx.beginPath();
    ctx.arc(targetX, targetY, 4.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = isBull ? "#34d399" : "#f87171";
    ctx.font = "bold 12px 'JetBrains Mono', monospace";
    ctx.textAlign = "left";
    ctx.fillText(`Alvo 14D: R$ ${asset.target.toFixed(2)}`, targetX - 105, targetY - 10);

    // 7. Painel de Volume (Inferior)
    const volumeTop = chartBottom + 12;
    ctx.strokeStyle = "#1a2436";
    ctx.beginPath();
    ctx.moveTo(marginLeft, volumeTop - 6);
    ctx.lineTo(width - marginRight, volumeTop - 6);
    ctx.stroke();

    ctx.fillStyle = "#64748b";
    ctx.font = "10px 'JetBrains Mono', monospace";
    ctx.textAlign = "right";
    ctx.fillText("40", marginLeft - 12, volumeTop + 24);

    ctx.save();
    ctx.translate(18, volumeTop + volumeHeight / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = "center";
    ctx.fillText("x 10⁶", 0, 0);
    ctx.restore();

    let maxVol = 0;
    candles.forEach(c => { if (c.volume > maxVol) maxVol = c.volume; });

    candles.forEach((c, idx) => {
        const x = marginLeft + idx * slotWidth + slotWidth / 2;
        const isUp = c.close >= c.open;
        const vHeight = (c.volume / maxVol) * (volumeHeight - 15);
        ctx.fillStyle = isUp ? "rgba(16, 185, 129, 0.75)" : "rgba(239, 68, 68, 0.75)";
        ctx.fillRect(x - candleBarWidth / 2, volumeTop + volumeHeight - vHeight, candleBarWidth, vHeight);
    });

    ctx.restore();
}

/**
 * Renderiza a lista de ações no painel lateral esquerdo
 */
function renderStockList() {
    stockListContainer.innerHTML = "";

    const filtered = ASSETS_UNIVERSE.filter(item => {
        const matchesSearch = item.ticker.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesFilter = currentFilter === "TODOS" || item.trend === currentFilter;
        return matchesSearch && matchesFilter;
    });

    universeCount.textContent = `${filtered.length} ATIVOS`;

    filtered.forEach(asset => {
        const card = document.createElement("div");
        card.className = `stock-card-item ${asset.ticker === currentSelectedTicker ? "selected" : ""}`;
        card.dataset.ticker = asset.ticker;

        const returnSign = asset.returnPct >= 0 ? "+" : "";
        const returnClass = asset.returnPct > 0 ? "positive" : (asset.returnPct < 0 ? "negative" : "neutral");

        card.innerHTML = `
            <div class="stock-card-left">
                <span class="stock-ticker">${asset.ticker}</span>
                <span class="stock-price">R$ ${asset.price.toFixed(2)}</span>
            </div>
            <div class="stock-card-right">
                <span class="trend-badge ${asset.trend}">${asset.trend}</span>
                <span class="stock-return ${returnClass}">${returnSign}${asset.returnPct.toFixed(2)}%</span>
            </div>
        `;

        card.addEventListener("click", () => {
            selectStock(asset.ticker);
        });

        stockListContainer.appendChild(card);
    });

    requestAnimationFrame(syncSidebarHeight);
}

/**
 * Sincroniza a altura da barra lateral para terminar exatamente alinhada ao card de Resumo
 */
function syncSidebarHeight() {
    const rightCol = document.querySelector(".chart-content-area");
    const sidebar = document.querySelector(".sidebar-stocks");
    const stockList = document.getElementById("stockListContainer");

    if (rightCol && sidebar && stockList && window.innerWidth > 1100) {
        const targetHeight = rightCol.offsetHeight;
        if (targetHeight > 400) {
            sidebar.style.height = `${targetHeight}px`;
            sidebar.style.maxHeight = `${targetHeight}px`;

            const headerEl = sidebar.querySelector(".sidebar-header");
            const searchEl = sidebar.querySelector(".search-box");
            const filterEl = sidebar.querySelector(".filter-pills");

            const headerH = headerEl ? headerEl.offsetHeight : 26;
            const searchH = searchEl ? searchEl.offsetHeight : 38;
            const filterH = filterEl ? filterEl.offsetHeight : 32;

            const overhead = headerH + searchH + filterH + 80;
            const availableH = Math.max(200, targetHeight - overhead);
            stockList.style.maxHeight = `${availableH}px`;
        }
    } else if (sidebar && stockList) {
        sidebar.style.height = "";
        sidebar.style.maxHeight = "";
        stockList.style.maxHeight = "";
    }
}

/**
 * Seleciona uma ação e atualiza todo o dashboard
 */
function selectStock(ticker) {
    currentSelectedTicker = ticker;
    const asset = ASSETS_UNIVERSE.find(a => a.ticker === ticker) || ASSETS_UNIVERSE[0];

    document.querySelectorAll(".stock-card-item").forEach(el => {
        el.classList.toggle("selected", el.dataset.ticker === ticker);
    });

    headlineTicker.textContent = asset.ticker;
    const sign = asset.returnPct >= 0 ? "+" : "";
    headlineReturn.textContent = `(${sign}${asset.returnPct.toFixed(2)}%)`;
    headlineReturn.className = asset.returnPct >= 0 ? "text-green" : "text-red";
    headlineTrend.textContent = asset.trendText;

    badgeTrendAction.textContent = asset.trendText;
    badgeTargetPrice.textContent = `R$ ${asset.target.toFixed(2)}`;
    badgeTargetReturn.textContent = `${sign}${asset.returnPct.toFixed(2)}%`;

    floatingTargetBadge.className = `target-floating-badge ${
        asset.trend === "ALTA" ? "badge-bullish" : (asset.trend === "BAIXA" ? "badge-bearish" : "badge-neutral")
    }`;

    metricCurrentPrice.textContent = `R$ ${asset.price.toFixed(2)}`;
    metricPriceDiff.textContent = `${asset.dayVar} hoje`;

    metricTargetPrice.textContent = `R$ ${asset.target.toFixed(2)}`;
    metricTargetReturn.textContent = `${sign}${asset.returnPct.toFixed(2)}% de projeção`;
    metricTargetPrice.className = `quant-card-val ${asset.returnPct >= 0 ? "text-green" : "text-red"}`;

    metricStopLoss.textContent = `R$ ${asset.stop.toFixed(2)}`;
    metricPayoff.textContent = asset.payoff;

    if (asset.trend === "ALTA") {
        aiReasoningText.innerHTML = `
            O ativo <strong>${asset.ticker}</strong> demonstrou rompimento sustentado acima da WMA 30 com confirmação de volume comprador superior à média de 20 períodos. O alinhamento com a SMA 200 sinaliza continuidade de tendência altista. Projeção estatística baseada em 14 períodos com expansão de volatilidade delimitada pelo ATR 14.
        `;
    } else if (asset.trend === "BAIXA") {
        aiReasoningText.innerHTML = `
            O ativo <strong>${asset.ticker}</strong> perdeu a sustentação da WMA 30 com pressão vendedora institucional. A divergência em relação à SMA 200 sugere realização de lucros e recuo tático até as bandas inferiores de suporte estatístico calculadas pelo algoritmo Águia Trader.
        `;
    } else {
        aiReasoningText.innerHTML = `
            O ativo <strong>${asset.ticker}</strong> encontra-se em fase de consolidação e compressão de volatilidade entre as médias SMA 200 e WMA 30. Relação risco/retorno simétrica. O motor estatístico recomenda aguardar gatilho de rompimento com volume.
        `;
    }

    renderTradingChart();
}

/**
 * Conexão e sincronização com backend Python 3.11
 */
async function testPythonBackend() {
    const connIndicator = document.getElementById("connectionStatus");
    const connText = document.getElementById("connText");
    const baseUrl = getApiBaseUrl();

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);

        const res = await fetch(`${baseUrl}/api/status`, {
            signal: controller.signal,
            headers: { "Accept": "application/json" }
        });
        clearTimeout(timeoutId);

        if (res.ok) {
            const data = await res.json();
            isServerOnline = true;
            connIndicator.className = "connection-indicator online";
            connText.textContent = `Python ${data.python_version || "3.11"}`;
            connIndicator.title = `Conectado ao Águia Trader (Python ${data.python_version}) - Clique para testar`;

            if (data.server_time && snapshotTimestamp) {
                snapshotTimestamp.textContent = data.server_time;
            }

            // Carrega ativos diretamente do backend se disponíveis
            fetchBackendAssets(baseUrl);
            return true;
        } else {
            throw new Error(`HTTP ${res.status}`);
        }
    } catch {
        isServerOnline = false;
        connIndicator.className = "connection-indicator offline";
        connText.textContent = "Offline (Local)";
        connIndicator.title = "Servidor Python 3.11 não detectado. Clique para tentar reconectar.";
        return false;
    }
}

/**
 * Busca os dados dos ativos do backend Python
 */
async function fetchBackendAssets(baseUrl) {
    try {
        const res = await fetch(`${baseUrl}/api/assets`);
        if (res.ok) {
            const data = await res.json();
            if (data.assets && data.assets.length > 0) {
                ASSETS_UNIVERSE = data.assets;
                renderStockList();
            }
        }
    } catch {
        // Fallback silencioso mantendo os dados locais
    }
}

// Configura eventos de filtro e busca
searchInput.addEventListener("input", (e) => {
    searchQuery = e.target.value.trim();
    renderStockList();
});

filterPills.forEach(pill => {
    pill.addEventListener("click", () => {
        filterPills.forEach(p => p.classList.remove("active"));
        pill.classList.add("active");
        currentFilter = pill.dataset.filter;
        renderStockList();
    });
});

window.addEventListener("resize", () => {
    renderTradingChart();
    syncSidebarHeight();
});

// Clique manual no indicador de status para reconectar
document.getElementById("connectionStatus")?.addEventListener("click", () => {
    const connText = document.getElementById("connText");
    connText.textContent = "Testando...";
    testPythonBackend();
});

// Inicialização
document.addEventListener("DOMContentLoaded", () => {
    renderStockList();
    selectStock("ASAI3");
    testPythonBackend();
    setTimeout(syncSidebarHeight, 50);

    // Verificação periódica automática a cada 3 segundos
    setInterval(testPythonBackend, 3000);
});
