/**
 * Águia Trader - Dashboard Quantitativo & Motor Gráfico B3
 * Integração com API Python 3.11, Yahoo Finance, Indicadores e IA Local.
 */

// Universo inicial de ações B3 monitoradas
let ASSETS_UNIVERSE = [
    { ticker: "ASAI3", price: 13.27, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 5.17, target: 13.96, stop: 12.65, payoff: "1.11 : 1", dayVar: "+0.85%" },
    { ticker: "ANIM3", price: 5.29, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.46, target: 5.53, stop: 5.08, payoff: "1.14 : 1", dayVar: "+1.15%" },
    { ticker: "ARML3", price: 6.48, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 5.45, target: 6.83, stop: 6.18, payoff: "1.17 : 1", dayVar: "+0.62%" },
    { ticker: "AURE3", price: 15.59, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.53, target: 16.30, stop: 14.95, payoff: "1.11 : 1", dayVar: "+0.32%" },
    { ticker: "PETR4", price: 38.45, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 3.80, target: 39.91, stop: 37.10, payoff: "1.08 : 1", dayVar: "+1.42%" },
    { ticker: "VALE3", price: 61.20, trend: "BAIXA", trendText: "BAIXA (BEARISH)", returnPct: -2.75, target: 59.52, stop: 62.60, payoff: "1.20 : 1", dayVar: "-0.95%" },
    { ticker: "ITUB4", price: 34.80, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.10, target: 36.23, stop: 33.60, payoff: "1.19 : 1", dayVar: "+0.78%" },
    { ticker: "BBAS3", price: 27.60, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 3.95, target: 28.69, stop: 26.70, payoff: "1.21 : 1", dayVar: "+0.55%" },
    { ticker: "BBDC4", price: 14.90, trend: "NEUTRO", trendText: "LATERAL (NEUTRAL)", returnPct: 0.67, target: 15.00, stop: 14.60, payoff: "0.33 : 1", dayVar: "+0.10%" },
    { ticker: "WEGE3", price: 52.80, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 6.25, target: 56.10, stop: 50.40, payoff: "1.38 : 1", dayVar: "+1.85%" },
    { ticker: "MGLU3", price: 8.90, trend: "BAIXA", trendText: "BAIXA (BEARISH)", returnPct: -5.40, target: 8.42, stop: 9.35, payoff: "1.07 : 1", dayVar: "-2.10%" },
    { ticker: "PRIO3", price: 44.50, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.85, target: 46.66, stop: 42.80, payoff: "1.27 : 1", dayVar: "+0.90%" },
    { ticker: "RENT3", price: 54.30, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.20, target: 56.58, stop: 52.40, payoff: "1.20 : 1", dayVar: "+0.60%" },
    { ticker: "EMBR3", price: 49.80, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 5.60, target: 52.59, stop: 47.90, payoff: "1.47 : 1", dayVar: "+1.95%" },
    { ticker: "GGBR4", price: 21.15, trend: "NEUTRO", trendText: "LATERAL (NEUTRAL)", returnPct: 0.45, target: 21.25, stop: 20.80, payoff: "0.28 : 1", dayVar: "+0.05%" },
    { ticker: "CSNA3", price: 12.40, trend: "BAIXA", trendText: "BAIXA (BEARISH)", returnPct: -3.80, target: 11.93, stop: 12.85, payoff: "1.04 : 1", dayVar: "-1.30%" },
    { ticker: "SUZB3", price: 58.70, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.30, target: 61.22, stop: 56.90, payoff: "1.40 : 1", dayVar: "+0.70%" },
    { ticker: "JBSS3", price: 35.10, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 3.70, target: 36.40, stop: 34.10, payoff: "1.30 : 1", dayVar: "+0.45%" }
];

// Estado da Aplicação
let currentSelectedTicker = "PETR4";
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
const metricStopDiff = document.getElementById("metricStopDiff");
const metricPayoff = document.getElementById("metricPayoff");
const aiReasoningText = document.getElementById("aiReasoningText");
const snapshotTimestamp = document.getElementById("snapshotTimestamp");

const canvas = document.getElementById("tradingChartCanvas");
const ctx = canvas.getContext("2d");

/**
 * Retorna o endpoint base da API com suporte para navegador e Electron
 */
function getApiBaseUrl() {
    if (window.location.protocol === "file:" || !window.location.origin.includes(":8000")) {
        return "http://127.0.0.1:8000";
    }
    return "";
}

/**
 * Formatação de moeda no padrão brasileiro (R$ 13,27)
 */
function formatarMoeda(valor) {
    if (valor === null || valor === undefined || isNaN(valor)) return "R$ —";
    return `R$ ${valor.toFixed(2).replace(".", ",")}`;
}

/**
 * Formatação de porcentagem no padrão brasileiro (+5,17%)
 */
function formatarPorcentagem(valor) {
    if (valor === null || valor === undefined || isNaN(valor)) return "—%";
    const sinal = valor >= 0 ? "+" : "";
    return `${sinal}${valor.toFixed(2).replace(".", ",")}%`;
}

/**
 * Renderiza a lista de ações na barra lateral esquerda ('Ações')
 */
function renderStockList() {
    const prevScroll = stockListContainer ? stockListContainer.scrollTop : 0;
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

        const returnVal = asset.returnPct || 0;
        const returnSign = returnVal >= 0 ? "+" : "";
        const returnClass = returnVal > 0 ? "positive" : (returnVal < 0 ? "negative" : "neutral");
        const priceFormatted = typeof asset.price === "number" ? formatarMoeda(asset.price) : `R$ ${asset.price}`;

        card.innerHTML = `
            <div class="stock-card-left">
                <span class="stock-ticker">${asset.ticker}</span>
                <span class="stock-price">${priceFormatted}</span>
            </div>
            <div class="stock-card-right">
                <span class="trend-badge ${asset.trend}">${asset.trend}</span>
                <span class="stock-return ${returnClass}">${returnSign}${returnVal.toFixed(2).replace(".", ",")}%</span>
            </div>
        `;

        card.addEventListener("click", () => {
            selectStock(asset.ticker);
        });

        stockListContainer.appendChild(card);
    });

    if (stockListContainer) {
        stockListContainer.scrollTop = prevScroll;
    }

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
 * Define o estado visual de carregamento nos cards
 */
function setLoadingState(isLoading) {
    const cards = document.querySelectorAll(".quant-card, .reasoning-card");
    cards.forEach(card => {
        card.classList.toggle("loading", isLoading);
    });
}

/**
 * Seleciona uma ação, aciona a API em background e atualiza dinamicamente todo o painel
 */
async function selectStock(ticker) {
    currentSelectedTicker = ticker;

    // Atualiza destaque imediato na lista lateral
    document.querySelectorAll(".stock-card-item").forEach(el => {
        el.classList.toggle("selected", el.dataset.ticker === ticker);
    });

    headlineTicker.textContent = ticker;

    // Se já temos os dados em cache de memória recente, renderiza imediatamente
    if (chartDataCache[ticker]) {
        aplicarDadosAnalise(chartDataCache[ticker]);
        return;
    }

    // Exibe estado de carregamento suave
    setLoadingState(true);
    metricPriceDiff.textContent = "Carregando B3...";
    metricTargetReturn.textContent = "Calculando...";
    if (metricStopDiff) metricStopDiff.textContent = "Calculando...";
    aiReasoningText.textContent = "Consultando cotações e calculando projeção estatística...";

    const baseUrl = getApiBaseUrl();

    try {
        const res = await fetch(`${baseUrl}/api/analise?ticker=${ticker}`);
        if (res.ok) {
            const json = await res.json();
            if (json.sucesso && json.dados) {
                chartDataCache[ticker] = json.dados;
                aplicarDadosAnalise(json.dados);

                // Atualiza o ativo na lista local para refletir a nova cotação
                const localAsset = ASSETS_UNIVERSE.find(a => a.ticker === ticker);
                if (localAsset) {
                    localAsset.price = json.dados.preco;
                    localAsset.target = json.dados.alvo;
                    localAsset.stop = json.dados.stop;
                    localAsset.payoff = json.dados.payoff;
                    localAsset.returnPct = json.dados.projecao_pct;
                    localAsset.trend = json.dados.tendencia;
                    localAsset.trendText = json.dados.tendencia_texto;
                    localAsset.dayVar = json.dados.variacao_dia;
                    renderStockList();
                }
                return;
            }
        }
        throw new Error(`Falha na resposta: HTTP ${res.status}`);
    } catch (err) {
        // Fallback em caso de falha de conexão: utiliza dados estáticos locais
        const fallback = ASSETS_UNIVERSE.find(a => a.ticker === ticker) || ASSETS_UNIVERSE[0];
        aplicarDadosFallback(fallback);
    } finally {
        setLoadingState(false);
    }
}

/**
 * Aplica os dados reais recebidos da API ao painel e ao gráfico
 */
function aplicarDadosAnalise(dados) {
    setLoadingState(false);

    const sign = dados.projecao_pct >= 0 ? "+" : "";
    headlineReturn.textContent = `(${formatarPorcentagem(dados.projecao_pct)})`;
    headlineReturn.className = dados.projecao_pct >= 0 ? "text-green" : "text-red";
    headlineTrend.textContent = dados.tendencia_texto;

    badgeTrendAction.textContent = dados.tendencia_texto;
    badgeTargetPrice.textContent = formatarMoeda(dados.alvo);
    badgeTargetReturn.textContent = formatarPorcentagem(dados.projecao_pct);

    floatingTargetBadge.className = `target-floating-badge ${
        dados.tendencia === "ALTA" ? "badge-bullish" : (dados.tendencia === "BAIXA" ? "badge-bearish" : "badge-neutral")
    }`;

    metricCurrentPrice.textContent = formatarMoeda(dados.preco);
    metricPriceDiff.textContent = `${dados.variacao_dia} hoje`;

    metricTargetPrice.textContent = formatarMoeda(dados.alvo);
    metricTargetReturn.textContent = `${formatarPorcentagem(dados.projecao_pct)} de projeção`;
    metricTargetPrice.className = `quant-card-val ${dados.projecao_pct >= 0 ? "text-green" : "text-red"}`;

    metricStopLoss.textContent = formatarMoeda(dados.stop);
    if (metricStopDiff) {
        metricStopDiff.textContent = `${dados.risco_pct?.toFixed(2).replace(".", ",")}% de risco`;
    }

    metricPayoff.textContent = dados.payoff;
    aiReasoningText.textContent = dados.resumo;

    // Renderiza o gráfico Canvas com candles reais
    if (dados.candles && dados.candles.length > 0) {
        renderTradingChartReal(dados.candles, dados);
    }
}

/**
 * Fallback determinístico caso o backend esteja offline
 */
function aplicarDadosFallback(asset) {
    setLoadingState(false);

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
    if (metricStopDiff) {
        metricStopDiff.textContent = `-4.67% de risco`;
    }
    metricPayoff.textContent = asset.payoff;

    aiReasoningText.innerHTML = `
        O ativo <strong>${asset.ticker}</strong> apresenta configuração técnica acompanhada pelo modelo quantitativo. Projeção estatística baseada em 14 períodos com bandas de controle delimitadas pelo ATR 14.
    `;
}

/**
 * Renderização de Candlesticks Reais no HTML5 Canvas
 */
function renderTradingChartReal(candles, asset) {
    if (!canvas) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;

    ctx.save();
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    // Fundo escuro profissional
    ctx.fillStyle = "#060911";
    ctx.fillRect(0, 0, width, height);

    // Margens
    const marginLeft = 68;
    const marginRight = 30;
    const marginTop = 45;
    const volumeHeight = 75;
    const chartBottom = height - volumeHeight - 35;
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
        if (c.wma30 && c.wma30 < minPrice) minPrice = c.wma30;
        if (c.wma30 && c.wma30 > maxPrice) maxPrice = c.wma30;
        if (c.sma200 && c.sma200 < minPrice) minPrice = c.sma200;
        if (c.sma200 && c.sma200 > maxPrice) maxPrice = c.sma200;
    });

    const targetPrice = asset.alvo || asset.target || candles[candles.length - 1].close;
    if (targetPrice > maxPrice) maxPrice = targetPrice;
    if (targetPrice < minPrice) minPrice = targetPrice;

    const priceMargin = (maxPrice - minPrice) * 0.10;
    minPrice -= priceMargin;
    maxPrice += priceMargin;

    function priceToY(price) {
        return chartBottom - ((price - minPrice) / (maxPrice - minPrice)) * chartHeight;
    }

    // 1. Grade horizontal e eixos de preço (Y-Axis) formatados com 2 decimais
    ctx.strokeStyle = "#121927";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#64748b";
    ctx.font = "11px 'JetBrains Mono', monospace";
    ctx.textAlign = "right";

    const priceTicksCount = 6;
    for (let i = 0; i <= priceTicksCount; i++) {
        const p = minPrice + ((maxPrice - minPrice) / priceTicksCount) * i;
        const y = priceToY(p);

        ctx.beginPath();
        ctx.moveTo(marginLeft, y);
        ctx.lineTo(width - marginRight, y);
        ctx.stroke();

        ctx.fillText(`R$ ${p.toFixed(2).replace(".", ",")}`, marginLeft - 10, y + 4);
    }

    // 2. Faixa sombreada de Projeção 14D
    const projStartX = marginLeft + candles.length * slotWidth;
    const projWidth = futureSteps * slotWidth;
    const isBull = (asset.tendencia || asset.trend) === "ALTA";

    const projGradient = ctx.createLinearGradient(projStartX, 0, projStartX + projWidth, 0);
    if (isBull) {
        projGradient.addColorStop(0, "rgba(34, 197, 94, 0.03)");
        projGradient.addColorStop(1, "rgba(34, 197, 94, 0.18)");
    } else {
        projGradient.addColorStop(0, "rgba(239, 68, 68, 0.03)");
        projGradient.addColorStop(1, "rgba(239, 68, 68, 0.18)");
    }

    ctx.fillStyle = projGradient;
    ctx.fillRect(projStartX, marginTop, projWidth, chartHeight);

    // Linha vertical divisória da projeção
    ctx.strokeStyle = isBull ? "rgba(34, 197, 94, 0.35)" : "rgba(239, 68, 68, 0.35)";
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
        const candleColor = isUp ? "#22c55e" : "#ef4444";

        // Pavio
        ctx.strokeStyle = candleColor;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(x, highY);
        ctx.lineTo(x, lowY);
        ctx.stroke();

        // Corpo
        ctx.fillStyle = candleColor;
        const bodyTop = Math.min(openY, closeY);
        const bodyHeight = Math.max(2, Math.abs(closeY - openY));
        ctx.fillRect(x - candleBarWidth / 2, bodyTop, candleBarWidth, bodyHeight);

        // Rótulos de datas no eixo X (a cada 12 candles)
        if (idx % 12 === 0 && c.date) {
            ctx.fillStyle = "#64748b";
            ctx.font = "10px 'JetBrains Mono', monospace";
            ctx.textAlign = "center";
            const dateShort = c.date.slice(5).replace("-", "/"); // MM/DD
            ctx.fillText(dateShort, x, chartBottom + 16);
        }
    });

    // 4. Curva SMA 200 (Azul)
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    let smaStarted = false;
    candles.forEach((c, idx) => {
        if (c.sma200) {
            const x = marginLeft + idx * slotWidth + slotWidth / 2;
            const y = priceToY(c.sma200);
            if (!smaStarted) {
                ctx.moveTo(x, y);
                smaStarted = true;
            } else {
                ctx.lineTo(x, y);
            }
        }
    });
    if (smaStarted) ctx.stroke();

    // 5. Curva WMA 30 (Amarela)
    ctx.strokeStyle = "#facc15";
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    let wmaStarted = false;
    candles.forEach((c, idx) => {
        if (c.wma30) {
            const x = marginLeft + idx * slotWidth + slotWidth / 2;
            const y = priceToY(c.wma30);
            if (!wmaStarted) {
                ctx.moveTo(x, y);
                wmaStarted = true;
            } else {
                ctx.lineTo(x, y);
            }
        }
    });
    if (wmaStarted) ctx.stroke();

    // 6. Projeção Tracejada até o Alvo (14D)
    const lastX = marginLeft + (candles.length - 1) * slotWidth + slotWidth / 2;
    const lastPriceY = priceToY(candles[candles.length - 1].close);
    const targetX = marginLeft + (totalSlots - 1) * slotWidth;
    const targetY = priceToY(targetPrice);

    ctx.strokeStyle = isBull ? "#4ade80" : "#f87171";
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(lastX, lastPriceY);
    ctx.quadraticCurveTo((lastX + targetX) / 2, (lastPriceY + targetY) / 2 + (isBull ? -8 : 8), targetX, targetY);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = isBull ? "#22c55e" : "#ef4444";
    ctx.beginPath();
    ctx.arc(targetX, targetY, 4.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = isBull ? "#4ade80" : "#f87171";
    ctx.font = "bold 11px 'JetBrains Mono', monospace";
    ctx.textAlign = "left";
    ctx.fillText(`Alvo: R$ ${targetPrice.toFixed(2).replace(".", ",")}`, targetX - 95, targetY - 10);

    // 7. Painel de Volume
    const volumeTop = chartBottom + 26;
    ctx.strokeStyle = "#161f30";
    ctx.beginPath();
    ctx.moveTo(marginLeft, volumeTop - 4);
    ctx.lineTo(width - marginRight, volumeTop - 4);
    ctx.stroke();

    let maxVol = 0;
    candles.forEach(c => { if (c.volume > maxVol) maxVol = c.volume; });
    if (maxVol === 0) maxVol = 1;

    ctx.fillStyle = "#64748b";
    ctx.font = "10px 'JetBrains Mono', monospace";
    ctx.textAlign = "right";
    const maxVolStr = (maxVol / 1000000).toFixed(0);
    ctx.fillText(`${maxVolStr}M`, marginLeft - 10, volumeTop + 20);

    candles.forEach((c, idx) => {
        const x = marginLeft + idx * slotWidth + slotWidth / 2;
        const isUp = c.close >= c.open;
        const vHeight = (c.volume / maxVol) * (volumeHeight - 16);
        ctx.fillStyle = isUp ? "rgba(34, 197, 94, 0.65)" : "rgba(239, 68, 68, 0.65)";
        ctx.fillRect(x - candleBarWidth / 2, volumeTop + volumeHeight - vHeight, candleBarWidth, vHeight);
    });

    ctx.restore();
}

/**
 * Conexão e sincronização inicial com backend Python 3.11
 */
async function testPythonBackend() {
    const connIndicator = document.getElementById("connectionStatus");
    const connText = document.getElementById("connText");
    const baseUrl = getApiBaseUrl();

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2500);

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
            connIndicator.title = `Conectado ao Águia Trader (Python ${data.python_version}) - Ollama: ${data.ollama?.online ? "Ativo (" + data.ollama.modelo + ")" : "Offline (Modo Determinístico)"}`;

            if (data.server_time && snapshotTimestamp) {
                const dt = new Date(data.server_time);
                snapshotTimestamp.textContent = dt.toLocaleDateString("pt-BR", {
                    day: "2-digit", month: "2-digit", year: "numeric",
                    hour: "2-digit", minute: "2-digit"
                });
            }

            fetchBackendAssets(baseUrl);
            return true;
        }
        throw new Error(`HTTP ${res.status}`);
    } catch {
        isServerOnline = false;
        connIndicator.className = "connection-indicator offline";
        connText.textContent = "Offline (Local)";
        connIndicator.title = "Servidor Python 3.11 não detectado. Clique para reconectar.";
        return false;
    }
}

/**
 * Busca a lista de ações do backend Python (/api/acoes)
 */
async function fetchBackendAssets(baseUrl) {
    try {
        const res = await fetch(`${baseUrl}/api/acoes`);
        if (res.ok) {
            const json = await res.json();
            const list = json.dados || json.assets;
            if (list && list.length > 0) {
                ASSETS_UNIVERSE = list;
                renderStockList();
            }
        }
    } catch {
        // Mantém lista local em fallback silencioso
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

let resizeDebounceTimer = null;
window.addEventListener("resize", () => {
    clearTimeout(resizeDebounceTimer);
    resizeDebounceTimer = setTimeout(() => {
        syncSidebarHeight();
        if (chartDataCache[currentSelectedTicker]) {
            renderTradingChartReal(chartDataCache[currentSelectedTicker].candles, chartDataCache[currentSelectedTicker]);
        }
    }, 80);
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
    testPythonBackend();
    selectStock("PETR4");

    // Sincronização periódica suave de status
    setInterval(testPythonBackend, 15000);
});
