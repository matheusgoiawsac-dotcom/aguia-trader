/**
 * Águia Trader - Dashboard Quantitativo & Motor Gráfico B3
 * Integração com API Python 3.11, Yahoo Finance, Indicadores e IA Local.
 */

// Universo inicial de ações B3 monitoradas (somente fallback offline, rotulado como SIMULADO)
// Espelha ASSETS_FALLBACK_B3 para não perder sincronia com o modo Swing Trade.
let ASSETS_UNIVERSE = [/*ASSETS_FALLBACK_B3*/ { ticker: "ASAI3", price: 13.27, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 5.17, target: 13.96, stop: 12.65, payoff: "1.11 : 1", dayVar: "+0.85%", simulado: true}, { ticker: "ANIM3", price: 5.29, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.46, target: 5.53, stop: 5.08, payoff: "1.14 : 1", dayVar: "+1.15%", simulado: true}, { ticker: "ARML3", price: 6.48, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 5.45, target: 6.83, stop: 6.18, payoff: "1.17 : 1", dayVar: "+0.62%", simulado: true}, { ticker: "AURE3", price: 15.59, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.53, target: 16.30, stop: 14.95, payoff: "1.11 : 1", dayVar: "+0.32%", simulado: true}, { ticker: "PETR4", price: 38.45, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 3.80, target: 39.91, stop: 37.10, payoff: "1.08 : 1", dayVar: "+1.42%", simulado: true}, { ticker: "VALE3", price: 61.20, trend: "BAIXA", trendText: "BAIXA (BEARISH)", returnPct: -2.75, target: 59.52, stop: 62.60, payoff: "1.20 : 1", dayVar: "-0.95%", simulado: true}, { ticker: "ITUB4", price: 34.80, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.10, target: 36.23, stop: 33.60, payoff: "1.19 : 1", dayVar: "+0.78%", simulado: true}, { ticker: "BBAS3", price: 27.60, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 3.95, target: 28.69, stop: 26.70, payoff: "1.21 : 1", dayVar: "+0.55%", simulado: true}, { ticker: "BBDC4", price: 14.90, trend: "NEUTRO", trendText: "LATERAL (NEUTRAL)", returnPct: 0.67, target: 15.00, stop: 14.60, payoff: "0.33 : 1", dayVar: "+0.10%", simulado: true}, { ticker: "WEGE3", price: 52.80, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 6.25, target: 56.10, stop: 50.40, payoff: "1.38 : 1", dayVar: "+1.85%", simulado: true}, { ticker: "MGLU3", price: 8.90, trend: "BAIXA", trendText: "BAIXA (BEARISH)", returnPct: -5.40, target: 8.42, stop: 9.35, payoff: "1.07 : 1", dayVar: "-2.10%", simulado: true}, { ticker: "PRIO3", price: 44.50, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.85, target: 46.66, stop: 42.80, payoff: "1.27 : 1", dayVar: "+0.90%", simulado: true}, { ticker: "RENT3", price: 54.30, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.20, target: 56.58, stop: 52.40, payoff: "1.20 : 1", dayVar: "+0.60%", simulado: true}, { ticker: "EMBR3", price: 49.80, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 5.60, target: 52.59, stop: 47.90, payoff: "1.47 : 1", dayVar: "+1.95%", simulado: true}, { ticker: "GGBR4", price: 21.15, trend: "NEUTRO", trendText: "LATERAL (NEUTRAL)", returnPct: 0.45, target: 21.25, stop: 20.80, payoff: "0.28 : 1", dayVar: "+0.05%", simulado: true}, { ticker: "CSNA3", price: 12.40, trend: "BAIXA", trendText: "BAIXA (BEARISH)", returnPct: -3.80, target: 11.93, stop: 12.85, payoff: "1.04 : 1", dayVar: "-1.30%", simulado: true}, { ticker: "SUZB3", price: 58.70, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.30, target: 61.22, stop: 56.90, payoff: "1.40 : 1", dayVar: "+0.70%", simulado: true}, { ticker: "JBSS3", price: 35.10, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 3.70, target: 36.40, stop: 34.10, payoff: "1.30 : 1", dayVar: "+0.45%", simulado: true } ];

// Estado da Aplicação
let currentSelectedTicker = "PETR4";
let currentFilter = "TODOS";
let searchQuery = "";

// Trading-mode state (Swing Trade / Day Trade). Mirrors aguia/modes.py so the
// mode bar can render before the first API response arrives; tests/test_modes.py
// asserts the two representations never drift apart.
let currentMode = "swing";
let currentInterval = "1d";

// Variaveis de requisicao ao backend (espelham o modo e intervalo ativos).
let modoRequisicao = currentMode;
let intervaloRequisicao = currentInterval;
(function() { const modoRequisicao = currentMode; })();

// Fallback universes: immutable lists used when the backend has no data yet.
const ASSETS_FALLBACK_B3 = [
    "ASAI3", "ANIM3", "ARML3", "AURE3", "PETR4", "VALE3", "ITUB4", "BBAS3",
    "BBDC4", "WEGE3", "MGLU3", "PRIO3", "RENT3", "EMBR3", "GGBR4", "CSNA3",
    "SUZB3", "JBSS3",
];
const ASSETS_FALLBACK_DAY = ["SPY", "DIA", "GC=F", "BTC-USD"];

// Mirrors aguia/modes.MODOS — single source of truth lives in Python.
const MODES = {
    swing: {
        id: "swing",
        label: "Swing Trade",
        contexto: "MODO SWING TRADE · GRÁFICO DIÁRIO 14D",
        mercado: "b3",
        timeframe: "1d",
        intervalo: "1d",
        horizonte: 14,
        moeda: "R$",
        rotulo_alvo: "Alvo Projetado (14D)",
        rotulo_stop: "Stop Loss Sugerido",
        rotulo_payoff: "Relação Risco x Retorno",
        rotulo_sub_alvo: "de projeção",
        rotulo_sub_stop: "de risco",
        universo: "b3",
        tickers: ["ASAI3","ANIM3","ARML3","AURE3","PETR4","VALE3","ITUB4","BBAS3","BBDC4","WEGE3","MGLU3","PRIO3","RENT3","EMBR3","GGBR4","CSNA3","SUZB3","JBSS3"],
        foco: "continuidade de tendência de médio prazo",
        indicadores: ["SMA 200", "WMA 30", "ATR 14"],
        hint: "Diário · 14D",
        rotulo_projecao: "Projeção 14D",
        placeholder_busca: "Buscar ação (ex: PETR4)...",
    },
    day: {
        id: "day",
        label: "Day Trade",
        contexto: "MODO DAY TRADE · VELAS 5M",
        mercado: "global",
        timeframe: "5m",
        intervalo: "5m",
        horizonte: 12,
        moeda: "US$",
        rotulo_alvo: "Alvo Intradia",
        rotulo_stop: "Stop Intradia",
        rotulo_payoff: "Risco x Retorno da Sessão",
        rotulo_sub_alvo: "de projeção intradiária",
        rotulo_sub_stop: "de risco na sessão",
        universo: "global",
        tickers: ["SPY","DIA","GC=F","BTC-USD"],
        foco: "rompimentos e volatilidade imediata",
        indicadores: ["Rompimentos", "ATR 14", "Volume"],
        hint: "Intradia · 5m/15m/1h",
        rotulo_projecao: "Projeção Intradia",
        placeholder_busca: "Buscar ativo (ex: SPY)...",
    },
};

const INTERVALOS_DAY = ["5m", "15m", "1h"];

function fallbackUniverso(modoId) {
    return modoId === "day" ? ASSETS_FALLBACK_DAY : ASSETS_FALLBACK_B3;
}

function cacheKey(ticker) {
    return `${ticker}|${currentMode}|${currentInterval}`;
}

// Cache LRU de payloads de análise (Map preserva a ordem de inserção)
const MAX_CACHE_ENTRIES = 24;
const chartDataCache = new Map();
let isServerOnline = false;

// Temporizadores
const STATUS_POLL_MS = 30000;
const ASSETS_REFRESH_MS = 60000;
const SEARCH_DEBOUNCE_MS = 140;
let lastAssetsFetch = 0;
let assetsSignature = "";
let analysisController = null;
let lastChartSignature = "";

// ============================================================
// Paleta da Marca
// ------------------------------------------------------------
// Os tokens são lidos de :root (static/style.css) em runtime, de
// modo que o gráfico em Canvas usa exatamente as mesmas cores do
// resto do sistema. Alterar um token em style.css repinta o
// dashboard inteiro — não existe cor duplicada no JavaScript.
// ============================================================
const BRAND_TOKEN_MAP = {
    bgMain: "--bg-main",
    surface: "--bg-surface",
    card: "--bg-card",
    elevated: "--bg-elevated",
    inset: "--bg-inset",
    grid: "--grid-line",
    border: "--border-card",
    borderStrong: "--border-strong",
    textPrimary: "--text-primary",
    textMuted: "--text-muted",
    textDim: "--text-dim",
    chartBg: "--chart-bg",
    up: "--color-green",
    upLight: "--color-green-light",
    down: "--color-red",
    downLight: "--color-red-light",
    sma200: "--color-blue",
    wma30: "--color-yellow",
    blue: "--brand-blue",
    cyan: "--brand-cyan",
    teal: "--brand-teal",
};

const BRAND = {};

/* ============================================================
   Fabrica de icones de ativo (mirror de aguia/icons.py)
   ============================================================
   Cada glifo e um caminho SVG 22x22. Os mapas espelham as
   definicoes de aguia/icons.py para que frontend e backend
   nunca diverjam na classificacao dos ativos.
   ============================================================ */

// Biblioteca de caminhos SVG (viewBox 0 0 22 22).
const GLYPH_LIBRARY = {
    btc: {
        d: "M11 2L2 11l3 9 9-3-6-7z",
    },
    eth: {
        d: "M11 2C5 2 0 7 0 13c0 3 2 6 5 8l2-4 4 4 4-4-2-4c3-2 5-5 5-8C22 7 17 2 11 2z",
    },
    sol: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM11 15l-3-3 3-3 3 3z",
    },
    usdt: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM8 11h6M8 13h6",
    },
    usdc: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM5 11h12M8 8l3 3 3-3",
    },
    bnb: {
        d: "M11 2L2 11l9 9L22 11zM11 4l7 7-7 7-7-7z",
    },
    xrp: {
        d: "M11 2L4 13l3 5 5-3-5-5z",
    },
    ada: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM11 15l-4-4 4-4 4 4z",
    },
    doge: {
        d: "M11 2L2 13l4 5 5-2-3-6z",
    },
    avax: {
        d: "M11 2L3 13l8 6 8-6z",
    },
    usd: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM5 13h12",
    },
    brl: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM4 11h8",
    },
    eur: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM3 11h9M3 13h9",
    },
    gbp: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM3 11h7M7 13h7",
    },
    gold: {
        d: "M11 2L2 13l3 5 5-3-3-5z",
    },
    silver: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM11 11l3 3 3-3",
    },
    copper: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM8 11l3 3 3-3",
    },
    oil: {
        d: "M11 2C6 2 2 6 2 11c0 3 2 6 5 8l-2 4-4-4-4 4 2 4C13 17 11 14 11 11c0-3-2-6-5-8C2 6 7 2 11 2z",
    },
    corn: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM11 11l3 3 3-3",
    },
    soy: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM8 11l3 3 3-3",
    },
    indexChart: {
        d: "M2 20h2L5 4h2l3 16h2L14 4h2l3 16h2z",
    },
    indexBars: {
        d: "M3 20h2V8h-2zM7 20h2V12h-2zM11 20h2V5h-2zM15 20h2V15h-2zM19 20h2V3h-2z",
    },
    indexArrow: {
        d: "M11 2L3 13l3 5 5-3-3-5zM18 13L20 13l-3-5z",
    },
    indexIbovespa: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM11 15l-3-3 3-3 3 3z",
    },
    bank: {
        d: "M2 20h2V8h-2zM7 20h2V4h-2zM12 20h2V12h-2zM17 20h2V6h-2z",
    },
    energy: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM11 15l-3-3 3-3 3 3z",
    },
    mining: {
        d: "M11 2L2 13l4 5 5-2-3-6z",
    },
    retail: {
        d: "M2 20h18V4H2zM5 17h3V8H5zM11 17h3V10h-3zM17 17h3V6h-3z",
    },
    health: {
        d: "M11 2C6 2 2 6 2 11s4 9 9 9 9-4 9-9-4-9-9-9zM8 11l3 3 3-3",
    },
};

// Mapas de ticker para glifo, espelhando aguia/icons.py.
const ICON_CRYPTO_MAP = {
    "BTC-USD": "btc", "ETH-USD": "eth", "SOL-USD": "sol", "USDT-USD": "usdt",
    "USDC-USD": "usdc", "BNB-USD": "bnb", "XRP-USD": "xrp", "ADA-USD": "ada",
    "DOGE-USD": "doge", "AVAX-USD": "avax",
};
const ICON_FOREX_MAP = {
    "USDBRL=X": "usd", "BRL=X": "brl", "DXY": "usd", "USD=X": "usd",
    "EURUSD=X": "eur", "GBPUSD=X": "gbp", "USDJPY=X": "usd", "USDCAD=X": "usd",
};
const ICON_COMMODITY_MAP = {
    "GC=F": "gold", "XAUUSD=X": "gold", "SI=F": "silver", "XAGUSD=X": "silver",
    "HG=F": "copper", "CL=F": "oil", "BZ=F": "oil", "ZC=F": "corn", "ZS=F": "soy",
};
const ICON_INDEX_MAP = {
    "^GSPC": "indexChart", "SPY": "indexChart", "^DJI": "indexBars", "DIA": "indexBars",
    "^IXIC": "indexArrow", "QQQ": "indexArrow", "^BVSP": "indexIbovespa",
};
const ICON_B3_SECTORS = [
    { glyph: "bank",   tickers: ["ITUB4","BBDC4","BBAS3","BPSA3","BRSR6","ITSA4","SANB11","B3SA3","CMIG4","BBTC","BPAC11","BANC11","BRBI11","PSBB11","BMEB3"] },
    { glyph: "energy", tickers: ["PETR4","PETR3","PRIO3","RPRL3","VBBR3","EQTL3","OSBR3","CSAN3","LOGG3","DMMO3"] },
    { glyph: "mining", tickers: ["VALE3","GGBR4","MMX3","BRAD3","BRAP4","AGL3","CSNA3","VAMO3","USIM5","PARIM3"] },
    { glyph: "retail", tickers: ["MGLU3","LREN3","ABEV3","MRVE3","JBSS3","SUZB3","CASH3","PETZ3","BHIA3","SOMA3","RADL3","AZUL3","KLBN3","ASAI3","AURE3","RENT3"] },
    { glyph: "health", tickers: ["RDOR3","FLRY3","HSML3","PSSA3","COGN3","YDUQ3","VERO3","CURA3","APIM3","OPM3","PFGC3","ANIM3"] },
];

// Detecta a categoria do ativo para escolha do glifo.
function detectarCategoriaIcone(ticker) {
    const t = String(ticker || "").trim().toUpperCase();
    const cripto = Object.keys(ICON_CRYPTO_MAP);
    const forex  = Object.keys(ICON_FOREX_MAP);
    const comm   = Object.keys(ICON_COMMODITY_MAP);
    const index  = Object.keys(ICON_INDEX_MAP);
    if (cripto.includes(t)) return "cripto";
    if (forex.includes(t) || (t.endsWith("=X") && t.includes("USD"))) return "forex";
    if (comm.includes(t)) return "commodity";
    if (index.includes(t) || t.startsWith("^")) return "indice";
    return "b3";
}

// Retorna o emblema de texto miniatura do ativo: simbolo ou iniciais.
function getAssetIconSVG(ticker, categoria) {
    const cat = categoria || detectarCategoriaIcone(ticker);
    const simbolo = simboloAtivo(ticker, cat);
    return `<span class="ativo-symbol" aria-hidden="true">${simbolo}</span>`;
}

// Mapeia o ativo para um simbolo miniatura: "₿" para cripto, iniciais para B3.
function simboloAtivo(ticker, categoria) {
    const cat = categoria || detectarCategoriaIcone(ticker);
    const t = String(ticker || "").trim().toUpperCase();
    if (cat === "cripto" || t.includes("BTC")) return "\u20BF";
    if (cat === "b3") return t.slice(0, 2);
    return "$";
}

// Fallback: duas letras em tipografia monoespaçada sobre token de fundo.
function fallbackIconSVG(ticker) {
    const letters = String(ticker || "").slice(0, 2).toUpperCase();
    return `<svg width="22" height="22" viewBox="0 0 22 22" class="asset-icon" aria-hidden="true" style="color:var(--icon-cyan);background:var(--icon-fallback-bg);border:1px solid var(--icon-green);border-radius:4px;outline-color:var(--icon-gold);box-shadow:0 0 4px var(--icon-orange),0 0 8px var(--icon-purple)"><text x="11" y="14" font-family="'JetBrains Mono', monospace" font-size="10" font-weight="700" text-anchor="middle" fill="var(--icon-silver)">${letters}</text></svg>`;
}

/* ============================================================
   Fim da fabrica de icones
   ============================================================ */

// Converte "#rrggbb" (ou "#rgb") em "rgba(r, g, b, alpha)".
function withAlpha(color, alpha) {
    const hex = String(color).trim();
    if (!hex.startsWith("#")) return color;

    let r;
    let g;
    let b;
    if (hex.length === 4) {
        r = parseInt(hex[1] + hex[1], 16);
        g = parseInt(hex[2] + hex[2], 16);
        b = parseInt(hex[3] + hex[3], 16);
    } else if (hex.length >= 7) {
        r = parseInt(hex.slice(1, 3), 16);
        g = parseInt(hex.slice(3, 5), 16);
        b = parseInt(hex.slice(5, 7), 16);
    } else {
        return color;
    }

    if (![r, g, b].every(Number.isFinite)) return color;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function loadBrandPalette() {
    const styles = getComputedStyle(document.documentElement);

    for (const [key, token] of Object.entries(BRAND_TOKEN_MAP)) {
        const value = styles.getPropertyValue(token).trim();
        if (value) BRAND[key] = value;
    }

    // Variations derived from the base tokens (never hardcoded again).
    BRAND.upSoft = withAlpha(BRAND.up, 0.35);
    BRAND.upFaint = withAlpha(BRAND.up, 0.18);
    BRAND.upGhost = withAlpha(BRAND.up, 0.03);
    BRAND.upFill = withAlpha(BRAND.up, 0.65);
    BRAND.downSoft = withAlpha(BRAND.down, 0.35);
    BRAND.downFaint = withAlpha(BRAND.down, 0.18);
    BRAND.downGhost = withAlpha(BRAND.down, 0.03);
    BRAND.downFill = withAlpha(BRAND.down, 0.65);

    return BRAND;
}

// Lazily resolved: the CSS is render-blocking, but the palette is
// re-read on demand in case the stylesheet is swapped at runtime.
function brand() {
    if (!BRAND.up) loadBrandPalette();
    return BRAND;
}

// Elementos do DOM
const stockListContainer = document.getElementById("stockListContainer");
const searchInput = document.getElementById("searchInput");
const filterPills = document.querySelectorAll(".filter-pill");
const universeCount = document.getElementById("universeCount");

const headlineTicker = document.getElementById("headlineTicker");
const headlineReturn = document.getElementById("headlineReturn");
const headlineTrend = document.getElementById("headlineTrend");
const dataSourceBadge = document.getElementById("dataSourceBadge");

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
const rationaleSource = document.getElementById("rationaleSource");
const complianceDisclaimer = document.getElementById("complianceDisclaimer");
const snapshotTimestamp = document.getElementById("snapshotTimestamp");

const canvas = document.getElementById("tradingChartCanvas");
const ctx = canvas ? canvas.getContext("2d") : null;

canvas.addEventListener("pointermove", onChartPointerMove);
canvas.addEventListener("pointerleave", onChartPointerLeave);

/**
 * Retorna o endpoint base da API com suporte para navegador e Electron
 */
function getApiBaseUrl() {
    const origin = window.location.origin;
    if (window.location.protocol === "file:") {
        return "http://127.0.0.1:8000";
    }
    // Use the same host:port the page was loaded from so the dashboard
    // works on any configured port (default 8000, or --port 5500, etc.).
    return origin;
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
 * Converte um valor de candle para um numero finito, ou null quando ausente/invalido.
 * Aceita numeros, strings numericas e rejeita null/undefined/vazio/NaN/Infinito.
 * Zero e strings como "0" sao valores validos e sao preservados.
 */
function toFiniteNumber(value) {
    if (value === null || value === undefined || value === "") return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
}

/**
 * Cache LRU: leitura promove o item e descarta o mais antigo quando cheio
 */
function cacheGet(ticker) {
    if (!chartDataCache.has(ticker)) return null;
    const data = chartDataCache.get(ticker);
    chartDataCache.delete(ticker);
    chartDataCache.set(ticker, data);
    return data;
}

function cacheSet(ticker, data) {
    if (chartDataCache.has(ticker)) chartDataCache.delete(ticker);
    chartDataCache.set(ticker, data);
    while (chartDataCache.size > MAX_CACHE_ENTRIES) {
        chartDataCache.delete(chartDataCache.keys().next().value);
    }
}

/**
 * Constrói o card de uma ação sem interpolar HTML (conteúdo do servidor)
 */
function createStockCard(asset) {
    const card = document.createElement("div");
    card.className = `stock-card-item ${asset.ticker === currentSelectedTicker ? "selected" : ""}`;
    card.dataset.ticker = asset.ticker;

    const returnVal = asset.returnPct || 0;
    const returnSign = returnVal >= 0 ? "+" : "";
    const returnClass = returnVal > 0 ? "positive" : (returnVal < 0 ? "negative" : "neutral");
    const priceFormatted = typeof asset.price === "number" ? formatarMoeda(asset.price) : `R$ ${asset.price}`;

    const left = document.createElement("div");
    left.className = "stock-card-left";

    const iconEl = document.createElement("span");
    iconEl.className = "ativo-icon";
    iconEl.innerHTML = getAssetIconSVG(asset.ticker, asset.categoria);

    const head = document.createElement("div");
    head.className = "stock-card-head";
    head.append(iconEl);

    const tickerEl = document.createElement("span");
    tickerEl.className = "stock-ticker";
    tickerEl.textContent = asset.ticker;
    head.append(tickerEl);

    left.append(head);

    const priceEl = document.createElement("span");
    priceEl.className = "stock-price";
    priceEl.textContent = priceFormatted;
    left.append(priceEl);

    if (asset.simulado) {
        const simEl = document.createElement("span");
        simEl.className = "stock-simulated";
        simEl.textContent = "SIMULADO";
        simEl.title = "Referência de demonstração: sem dados de mercado reais";
        left.append(simEl);
    }

    const right = document.createElement("div");
    right.className = "stock-card-right";

    const badge = document.createElement("span");
    badge.className = `trend-badge ${asset.trend}`;
    badge.textContent = asset.trend;

    const ret = document.createElement("span");
    ret.className = `stock-return ${returnClass}`;
    ret.textContent = `${returnSign}${returnVal.toFixed(2).replace(".", ",")}%`;

    right.append(badge, ret);
    card.append(left, right);

    card.addEventListener("click", () => selectStock(asset.ticker));
    return card;
}

/**
 * Renderiza a lista de ações na barra lateral esquerda ('Ações')
 */
function renderStockList() {
    if (!stockListContainer) return;
    const prevScroll = stockListContainer.scrollTop;
    stockListContainer.textContent = "";

    const needle = searchQuery.toLowerCase();
    const filtered = ASSETS_UNIVERSE.filter(item => {
        const matchesSearch = item.ticker.toLowerCase().includes(needle);
        const matchesFilter = currentFilter === "TODOS" || item.trend === currentFilter;
        return matchesSearch && matchesFilter;
    });

    universeCount.textContent = `${filtered.length} ATIVOS`;

    const fragment = document.createDocumentFragment();
    filtered.forEach(asset => fragment.appendChild(createStockCard(asset)));
    stockListContainer.appendChild(fragment);

    stockListContainer.scrollTop = prevScroll;

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

    // Icone do ativo ao lado do ticker no cabecalho do grafico
    let headlineIcon = document.getElementById("chartHeadlineIcon");
    if (!headlineIcon) {
        headlineIcon = document.createElement("span");
        headlineIcon.id = "chartHeadlineIcon";
        headlineIcon.className = "ativo-icon";
        headlineTicker.parentNode.insertBefore(headlineIcon, headlineTicker);
    }
    headlineIcon.innerHTML = getAssetIconSVG(ticker, detectarCategoriaIcone(ticker));

    // Se já temos os dados em cache de memória recente, renderiza imediatamente
    const cached = cacheGet(cacheKey(ticker));
    if (cached) {
        aplicarDadosAnalise(cached);
        return;
    }

    // Exibe estado de carregamento suave
    setLoadingState(true);
    metricPriceDiff.textContent = "Carregando B3...";
    metricTargetReturn.textContent = "Calculando...";
    if (metricStopDiff) metricStopDiff.textContent = "Calculando...";
    aiReasoningText.textContent = "Consultando cotações e calculando projeção estatística...";

    const baseUrl = getApiBaseUrl();

    // Cancela a requisição anterior: apenas a última seleção é relevante
    if (analysisController) analysisController.abort();
    analysisController = new AbortController();

    try {
        const params = new URLSearchParams({
            ticker: ticker,
            modo: modoRequisicao,
            intervalo: intervaloRequisicao,
        });
        const res = await fetch(`${baseUrl}/api/dados?${params}`, {
            signal: analysisController.signal,
            headers: { "Accept": "application/json" }
        });
        if (res.ok) {
            const json = await res.json();
            if (json.sucesso && json.dados) {
                const dados = json.dados;
                cacheSet(cacheKey(ticker), dados);
                aplicarDadosAnalise(dados);

                // Atualiza o ativo na lista local para refletir a nova cotação
                const localAsset = ASSETS_UNIVERSE.find(a => a.ticker === ticker);
                if (localAsset) {
                    localAsset.price = dados.preco;
                    localAsset.target = dados.alvo;
                    localAsset.stop = dados.stop;
                    localAsset.payoff = dados.payoff;
                    localAsset.returnPct = dados.projecao_pct;
                    localAsset.trend = dados.tendencia;
                    localAsset.trendText = dados.tendencia_texto;
                    localAsset.dayVar = dados.variacao_dia;
                    localAsset.simulado = false;
                    renderStockList();
                }
                return;
            }
        }
        throw new Error(`Falha na resposta: HTTP ${res.status}`);
    } catch (err) {
        if (err && err.name === "AbortError") return;
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

    // Limpa qualquer tooltip de dados anteriores ao trocar de ativo/intervalo
    hideChartTooltip();

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

    if (rationaleSource) {
        rationaleSource.textContent = dados.fonte_resumo === "ollama"
            ? "Ollama Local + Águia Trader"
            : "Motor Estatístico Águia Trader";
    }
    if (complianceDisclaimer && dados.disclaimer) {
        complianceDisclaimer.textContent = dados.disclaimer;
    }
    if (dataSourceBadge) {
        dataSourceBadge.hidden = false;
    }

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

    // Limpa qualquer tooltip de dados anteriores ao trocar de ativo/intervalo
    hideChartTooltip();

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

    aiReasoningText.textContent =
        `O ativo ${asset.ticker} apresenta configuração técnica acompanhada pelo modelo quantitativo. ` +
        `Projeção estatística baseada em 14 períodos com bandas de controle delimitadas pelo ATR 14.`;

    if (dataSourceBadge) {
        dataSourceBadge.hidden = false;
    }
}

/**
 * Renderização de Candlesticks Reais no HTML5 Canvas
 */
function renderTradingChartReal(candles, asset) {
    if (!canvas || !ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) {
        // Canvas ainda não tem dimensão (ex.: splash em andamento).
        // Reagenda o desenho assim que o layout estiver pronto.
        requestAnimationFrame(() => renderTradingChartReal(candles, asset));
        return;
    }

    const lastCandle = candles[candles.length - 1];
    const signature = `${asset.ticker}|${asset.alvo}|${Math.round(rect.width)}x${Math.round(rect.height)}|${dpr}|${candles.length}|${lastCandle.close}`;
    if (signature === lastChartSignature) return;
    lastChartSignature = signature;

    const targetWidth = Math.round(rect.width * dpr);
    const targetHeight = Math.round(rect.height * dpr);
    if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
        canvas.width = targetWidth;
        canvas.height = targetHeight;
    }

    ctx.save();
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    // Fundo escuro profissional
    ctx.fillStyle = brand().bgMain;
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

    for (const c of candles) {
        if (c.low < minPrice) minPrice = c.low;
        if (c.high > maxPrice) maxPrice = c.high;
        if (c.wma30 && c.wma30 < minPrice) minPrice = c.wma30;
        if (c.wma30 && c.wma30 > maxPrice) maxPrice = c.wma30;
        if (c.sma200 && c.sma200 < minPrice) minPrice = c.sma200;
        if (c.sma200 && c.sma200 > maxPrice) maxPrice = c.sma200;
    }

    const targetPrice = asset.alvo || asset.target || lastCandle.close;
    if (targetPrice > maxPrice) maxPrice = targetPrice;
    if (targetPrice < minPrice) minPrice = targetPrice;

    const priceMargin = (maxPrice - minPrice) * 0.10;
    minPrice -= priceMargin;
    maxPrice += priceMargin;

    function priceToY(price) {
        return chartBottom - ((price - minPrice) / (maxPrice - minPrice)) * chartHeight;
    }

    // 1. Grade horizontal e eixos de preço (Y-Axis) formatados com 2 decimais
    ctx.strokeStyle = brand().grid;
    ctx.lineWidth = 1;
    ctx.fillStyle = brand().textMuted;
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
        projGradient.addColorStop(0, brand().upGhost);
        projGradient.addColorStop(1, brand().upFaint);
    } else {
        projGradient.addColorStop(0, brand().downGhost);
        projGradient.addColorStop(1, brand().downFaint);
    }

    ctx.fillStyle = projGradient;
    ctx.fillRect(projStartX, marginTop, projWidth, chartHeight);

    // Linha vertical divisória da projeção
    ctx.strokeStyle = isBull ? brand().upSoft : brand().downSoft;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(projStartX, marginTop);
    ctx.lineTo(projStartX, chartBottom);
    ctx.stroke();
    ctx.setLineDash([]);

    // 3. Desenho dos Candlesticks
    ctx.textAlign = "center";
    for (let idx = 0; idx < candles.length; idx++) {
        const c = candles[idx];
        const x = marginLeft + idx * slotWidth + slotWidth / 2;
        const openY = priceToY(c.open);
        const closeY = priceToY(c.close);
        const highY = priceToY(c.high);
        const lowY = priceToY(c.low);

        const candleColor = c.close >= c.open ? brand().up : brand().down;

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
            ctx.fillStyle = brand().textMuted;
            ctx.font = "10px 'JetBrains Mono', monospace";
            const dateShort = c.date.slice(5).replace("-", "/"); // MM/DD
            ctx.fillText(dateShort, x, chartBottom + 16);
        }
    }

    // 4. Curva SMA 200 (Azul)
    drawOverlay(ctx, candles, slotWidth, marginLeft, priceToY, "sma200", brand().sma200);
    // 5. Curva WMA 30 (Amarela)
    drawOverlay(ctx, candles, slotWidth, marginLeft, priceToY, "wma30", brand().wma30);

    // 6. Projeção Tracejada até o Alvo (14D)
    const lastX = marginLeft + (candles.length - 1) * slotWidth + slotWidth / 2;
    const lastPriceY = priceToY(lastCandle.close);
    const targetX = marginLeft + (totalSlots - 1) * slotWidth;
    const targetY = priceToY(targetPrice);

    ctx.strokeStyle = isBull ? brand().upLight : brand().downLight;
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(lastX, lastPriceY);
    ctx.quadraticCurveTo((lastX + targetX) / 2, (lastPriceY + targetY) / 2 + (isBull ? -8 : 8), targetX, targetY);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = isBull ? brand().up : brand().down;
    ctx.beginPath();
    ctx.arc(targetX, targetY, 4.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = isBull ? brand().upLight : brand().downLight;
    ctx.font = "bold 11px 'JetBrains Mono', monospace";
    ctx.textAlign = "left";
    ctx.fillText(`Alvo: R$ ${targetPrice.toFixed(2).replace(".", ",")}`, targetX - 95, targetY - 10);

    // 7. Painel de Volume
    const volumeTop = chartBottom + 26;
    ctx.strokeStyle = brand().grid;
    ctx.beginPath();
    ctx.moveTo(marginLeft, volumeTop - 4);
    ctx.lineTo(width - marginRight, volumeTop - 4);
    ctx.stroke();

    let maxVol = 0;
    for (const c of candles) { if (c.volume > maxVol) maxVol = c.volume; }
    if (maxVol === 0) maxVol = 1;

    ctx.fillStyle = brand().textMuted;
    ctx.font = "10px 'JetBrains Mono', monospace";
    ctx.textAlign = "right";
    const maxVolStr = (maxVol / 1000000).toFixed(0);
    ctx.fillText(`${maxVolStr}M`, marginLeft - 10, volumeTop + 20);

    for (let idx = 0; idx < candles.length; idx++) {
        const c = candles[idx];
        const x = marginLeft + idx * slotWidth + slotWidth / 2;
        const vHeight = (c.volume / maxVol) * (volumeHeight - 16);
        ctx.fillStyle = c.close >= c.open ? brand().upFill : brand().downFill;
        ctx.fillRect(x - candleBarWidth / 2, volumeTop + volumeHeight - vHeight, candleBarWidth, vHeight);
    }

    ctx.restore();
}

/**
 * Desenha uma curva de média móvel contínua (ignora valores ausentes)
 */
function drawOverlay(context, candles, slotWidth, marginLeft, priceToY, key, color) {
    context.strokeStyle = color;
    context.lineWidth = 2.2;
    context.beginPath();
    let started = false;
    for (let idx = 0; idx < candles.length; idx++) {
        const value = candles[idx][key];
        if (!value) continue;
        const x = marginLeft + idx * slotWidth + slotWidth / 2;
        const y = priceToY(value);
        if (!started) {
            context.moveTo(x, y);
            started = true;
        } else {
            context.lineTo(x, y);
        }
    }
    if (started) context.stroke();
}

/* ============================================================
   Interatividade do grafico: crosshair e tooltip
   ============================================================
   O crosshair acompanha o ponteiro sobre o canvas e o tooltip
   exibe OHLCV da vela mais proxima. Usa as mesmas escalas e
   margens de renderTradingChartReal para nao haver deslocamento.
   ============================================================ */

let crosshairLayer = null;

function ensureCrosshairLayer() {
    if (crosshairLayer) return crosshairLayer;
    const layer = document.createElement("div");
    layer.className = "chart-crosshair-layer";
    layer.style.position = "absolute";
    layer.style.top = canvas.offsetTop + "px";
    layer.style.left = canvas.offsetLeft + "px";
    layer.style.width = canvas.offsetWidth + "px";
    layer.style.height = canvas.offsetHeight + "px";
    layer.style.pointerEvents = "none";
    layer.style.zIndex = "40";
    const parent = canvas.parentElement;
    if (parent) {
        parent.style.position = "relative";
        parent.appendChild(layer);
    }
    crosshairLayer = layer;
    return layer;
}

function drawCrosshair(g) {
    const layer = ensureCrosshairLayer();
    if (!g || !canvas || !ctx) {
        layer.innerHTML = "";
        return;
    }
    // brand() é lazy: se a paleta ainda não foi lida, lê agora para
    // garantir que o crosshair use a cor correta no tema ativo.
    loadBrandPalette();
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const marginLeft = 68;
    const marginRight = 30;
    const marginTop = 45;
    const volumeHeight = 75;
    const chartBottom = rect.height - volumeHeight - 35;
    const chartHeight = chartBottom - marginTop;
    const plotWidth = rect.width - marginLeft - marginRight;

    const x = Math.max(marginLeft, Math.min(rect.width - marginRight, g.cursorX));
    const idx = Math.floor((x - marginLeft - slotWidthOf(g)) / slotWidthOf(g));
    const candles = g.candles;
    if (!candles || candles.length === 0) {
        layer.innerHTML = "";
        return;
    }
    const clamped = Math.max(0, Math.min(idx, candles.length - 1));
    const c = candles[clamped];

    // Linha vertical do crosshair acompanha o cursor X (mesmo comportamento do commit 75f7b61)
    const cx = Math.max(marginLeft, Math.min(rect.width - marginRight, g.cursorX));
    // brand() resolve os tokens CSS via getComputedStyle. Atributos SVG
    // (stroke/fill) NÃO resolvem var(), então interpolamos o valor real.
    const crosshairColor = brand().cyan;
    layer.innerHTML = `
        <svg width="${rect.width}" height="${rect.height}" style="display:block;position:absolute;top:0;left:0;pointer-events:none">
            <line x1="${cx}" y1="${marginTop}" x2="${cx}" y2="${chartBottom}" stroke="${crosshairColor}" stroke-width="1" stroke-dasharray="4,4"/>
            <line x1="${marginLeft}" y1="${g.priceY}" x2="${rect.width - marginRight}" y2="${g.priceY}" stroke="${crosshairColor}" stroke-width="1" stroke-dasharray="4,4"/>
            <circle cx="${cx}" cy="${g.priceY}" r="3.5" fill="${crosshairColor}"/>
        </svg>
    `;

    // Atualiza tooltip com dados da vela
    updateChartTooltip(clamped, g, x, g.priceY);
}

function slotWidthOf(g) {
    return g.slotWidth || 1;
}

function updateChartTooltip(index, g, cursorX, cursorY) {
    const tooltip = document.getElementById("chartTooltip");
    if (!tooltip || !g || !g.candles || g.candles.length === 0) return;
    const clamped = Math.max(0, Math.min(index, g.candles.length - 1));
    const c = g.candles[clamped];
    const moeda = g.moeda || "R$";

    const o = toFiniteNumber(c.open);
    const h = toFiniteNumber(c.high);
    const l = toFiniteNumber(c.low);
    const cl = toFiniteNumber(c.close);
    const v = toFiniteNumber(c.volume);

    const dateEl = document.getElementById("chartTooltipDate");
    const openEl = document.getElementById("chartTooltipOpen");
    const highEl = document.getElementById("chartTooltipHigh");
    const lowEl = document.getElementById("chartTooltipLow");
    const closeEl = document.getElementById("chartTooltipClose");
    const changeEl = document.getElementById("chartTooltipChange");
    const volumeEl = document.getElementById("chartTooltipVolume");

    const fmtPrice = (n) => n === null ? "—" : `${moeda} ${n.toFixed(2).replace(".", ",")}`;
    const fmtChange = (n) => n === null ? "—" : `${n >= 0 ? "+" : ""}${n.toFixed(2).replace(".", ",")}%`;

    if (dateEl) dateEl.textContent = c.date || "";
    if (openEl) openEl.textContent = fmtPrice(o);
    if (highEl) highEl.textContent = fmtPrice(h);
    if (lowEl) lowEl.textContent = fmtPrice(l);
    if (closeEl) closeEl.textContent = fmtPrice(cl);
    if (changeEl) {
        if (o !== null && cl !== null && o !== 0) {
            const ch = ((cl - o) / o) * 100;
            changeEl.textContent = fmtChange(ch);
            changeEl.className = ch >= 0 ? "text-green" : "text-red";
        } else {
            changeEl.textContent = "—";
            changeEl.className = "";
        }
    }
    if (volumeEl) volumeEl.textContent = v === null ? "—" : v.toLocaleString("pt-BR");

    // Posiciona dentro do stage do grafico (mesmo sistema de coordenadas do
    // canvas e do crosshair), medindo a caixa real apos atualizar o conteudo
    // e mantendo-a dentro dos limites do contenedor.
    tooltip.style.display = "block";
    tooltip.style.visibility = "hidden";
    const tw = tooltip.offsetWidth;
    const th = tooltip.offsetHeight;

    const rect = canvas ? canvas.getBoundingClientRect() : { width: 0, height: 0 };
    const container = tooltip.parentElement;
    const cw = container ? container.clientWidth : rect.width;
    const ch = container ? container.clientHeight : rect.height;
    const pad = 10;

    let tx = cursorX + 14;
    let ty = cursorY - th - 10; // acima do cursor
    if (tx + tw > cw - pad) tx = cursorX - tw - 14; // esquerda do cursor
    if (tx < pad) tx = pad;
    if (tx + tw > cw - pad) tx = Math.max(pad, cw - tw - pad);
    if (ty < pad) ty = cursorY + 14; // abaixo do cursor
    if (ty + th > ch - pad) ty = ch - th - pad;
    if (ty < pad) ty = pad;

    tooltip.style.left = `${tx}px`;
    tooltip.style.top = `${ty}px`;
    tooltip.style.visibility = "visible";
    tooltip.setAttribute("aria-hidden", "false");
}

function onChartPointerMove(event) {
    if (!canvas || !ctx) return;
    const rect = canvas.getBoundingClientRect();
    const cursorX = event.clientX - rect.left;
    const cursorY = event.clientY - rect.top;

    const dpr = window.devicePixelRatio || 1;
    const marginLeft = 68;
    const marginRight = 30;
    const marginTop = 45;
    const volumeHeight = 75;
    const chartBottom = rect.height - volumeHeight - 35;
    const chartHeight = chartBottom - marginTop;
    const plotWidth = rect.width - marginLeft - marginRight;

    // Recalcula slotWidth com base no estado atual (usa ultimo signature se disponivel)
    const cached = cacheGet(cacheKey(currentSelectedTicker));
    if (!cached || !cached.candles) return;
    const candles = cached.candles;
    const lastCandle = candles[candles.length - 1];
    const targetPrice = cached.alvo || cached.target || lastCandle.close;
    const futureSteps = 14;
    const totalSlots = candles.length + futureSteps;
    const slotWidth = plotWidth / totalSlots;

    let minPrice = Infinity, maxPrice = -Infinity;
    for (const c of candles) {
        if (c.low < minPrice) minPrice = c.low;
        if (c.high > maxPrice) maxPrice = c.high;
        if (c.wma30 && c.wma30 < minPrice) minPrice = c.wma30;
        if (c.wma30 && c.wma30 > maxPrice) maxPrice = c.wma30;
        if (c.sma200 && c.sma200 < minPrice) minPrice = c.sma200;
        if (c.sma200 && c.sma200 > maxPrice) maxPrice = c.sma200;
    }
    if (targetPrice > maxPrice) maxPrice = targetPrice;
    if (targetPrice < minPrice) minPrice = targetPrice;
    const priceMargin = (maxPrice - minPrice) * 0.10;
    minPrice -= priceMargin;
    maxPrice += priceMargin;

    const priceToY = (price) => chartBottom - ((price - minPrice) / (maxPrice - minPrice)) * chartHeight;

    // O crosshair segue o cursor (mesmo comportamento do commit 75f7b61):
    // linha X e linha Y posicionadas na coordenada bruta do ponteiro.
    drawCrosshair({
        cursorX, cursorY,
        candles,
        slotWidth,
        priceY: cursorY,
    });
}

function onChartPointerLeave() {
    const layer = document.querySelector(".chart-crosshair-layer");
    if (layer) layer.innerHTML = "";
    hideChartTooltip();
}

/** Oculta o tooltip e sincroniza o estado de acessibilidade. */
function hideChartTooltip() {
    const tooltip = document.getElementById("chartTooltip");
    if (tooltip) {
        tooltip.style.display = "none";
        tooltip.setAttribute("aria-hidden", "true");
    }
}

/**
 * Conexao e sincronizacao inicial com backend Python 3.11
 */
async function testPythonBackend() {
    const connIndicator = document.getElementById("connectionStatus");
    const connText = document.getElementById("connText");
    const baseUrl = getApiBaseUrl();

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        const res = await fetch(`${baseUrl}/api/status`, {
            signal: controller.signal,
            headers: { "Accept": "application/json" }
        });
        clearTimeout(timeoutId);

        if (res.ok) {
            const data = await res.json();
            isServerOnline = true;
            connIndicator.className = "connection-indicator online";
            connText.textContent = "Servidor Online";
            connIndicator.title = `Conectado ao Águia Trader (Python ${data.python_version}) - Ollama: ${data.ollama?.online ? "Ativo (" + data.ollama.modelo + ")" : "Offline (Modo Determinístico)"}`;

            if (data.server_time && snapshotTimestamp) {
                const dt = new Date(data.server_time);
                snapshotTimestamp.textContent = dt.toLocaleDateString("pt-BR", {
                    day: "2-digit", month: "2-digit", year: "numeric",
                    hour: "2-digit", minute: "2-digit"
                });
            }

            if (complianceDisclaimer && data.disclaimer) {
                complianceDisclaimer.textContent = data.disclaimer;
            }

            refreshBackendAssets();
            return true;
        }
        throw new Error(`HTTP ${res.status}`);
    } catch {
        isServerOnline = false;
        connIndicator.className = "connection-indicator offline";
        connText.textContent = "Servidor Offline";
        connIndicator.title = "Servidor Python 3.11 não detectado. Clique para reconectar.";
        return false;
    }
}

/**
 * Busca a lista de ações do backend Python (/api/acoes)
 * Só re-renderiza a lista quando os dados realmente mudaram.
 */
async function refreshBackendAssets(force = false) {
    const now = Date.now();
    if (!force && now - lastAssetsFetch < ASSETS_REFRESH_MS) return;
    lastAssetsFetch = now;

    try {
        const res = await fetch(`${getApiBaseUrl()}/api/acoes?modo=${modoRequisicao}`, {
            headers: { "Accept": "application/json" }
        });
        if (!res.ok) return;
        const json = await res.json();
        const list = json.dados || json.assets;
        if (!list || !list.length) return;

        const signature = list
            .map(a => `${a.ticker}:${a.price}:${a.trend}:${a.returnPct}:${a.asof}`)
            .join("|");
        if (signature === assetsSignature) return;

        assetsSignature = signature;
        ASSETS_UNIVERSE = list;
        renderStockList();
    } catch {
        // Mantém lista local em fallback silencioso
    }
}

// Configura eventos de filtro e busca
let searchDebounceTimer = null;
searchInput.addEventListener("input", (e) => {
    clearTimeout(searchDebounceTimer);
    const value = e.target.value.trim();
    searchDebounceTimer = setTimeout(() => {
        searchQuery = value;
        renderStockList();
    }, SEARCH_DEBOUNCE_MS);
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
        const cached = cacheGet(cacheKey(currentSelectedTicker));
        if (cached && cached.candles) {
            lastChartSignature = "";
            renderTradingChartReal(cached.candles, cached);
        }
    }, 80);
});

// Clique manual no indicador de status para reconectar
document.getElementById("connectionStatus")?.addEventListener("click", () => {
    const connText = document.getElementById("connText");
    connText.textContent = "Testando...";
    refreshBackendAssets(true);
    testPythonBackend();
});

// Suspende o polling quando a aba está oculta
document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
        testPythonBackend();
        refreshBackendAssets(true);
    }
});

// Theme toggle (light/dark) driven entirely by CSS tokens.
const SWAP_TARGET_SELECTOR = "#aiReasoningText, #metricCurrentPrice, #metricTargetPrice, #metricStopLoss, #metricPayoff, #badgeTargetPrice, #badgeTargetReturn, #headlineReturn, #headlineTrend, #metricPriceDiff, #metricStopDiff, #metricTargetReturn";

function aplicarTema(tema) {
    document.documentElement.setAttribute("data-theme", tema);
    try { localStorage.setItem("aguia-tema", tema); } catch (e) {}
    const sun = document.querySelector(".theme-icon.sun");
    const moon = document.querySelector(".theme-icon.moon");
    if (sun) sun.style.display = tema === "light" ? "inline" : "none";
    if (moon) moon.style.display = tema === "light" ? "none" : "inline";
}
(function initTheme() {
    let salvo = "dark";
    try {
        const stored = localStorage.getItem("aguia-tema");
        if (stored === "dark" || stored === "light") salvo = stored;
    } catch (e) {}
    aplicarTema(salvo);
    const btn = document.getElementById("themeToggle");
    if (btn) btn.addEventListener("click", () => {
        const atual = document.documentElement.getAttribute("data-theme") || "dark";
        aplicarTema(atual === "light" ? "dark" : "light");
    });
})();

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

function aplicarDadosComFade(atualizar) {
    const targets = document.querySelectorAll(SWAP_TARGET_SELECTOR);
    if (prefersReducedMotion.matches) {
        atualizar();
        return;
    }
    targets.forEach(el => el.classList.add("data-swap-out"));
    setTimeout(() => {
        atualizar();
        targets.forEach(el => {
            el.classList.add("data-swap-in");
            el.classList.remove("data-swap-out");
        });
    }, 180);
    setTimeout(() => {
        targets.forEach(el => el.classList.remove("data-swap-in"));
    }, 530);
}

// Mode bar: switching between Swing Trade and Day Trade.
function aplicarModo(modoId) {
    const def = MODES[modoId];
    if (!def) return;
    currentMode = modoId;
    currentInterval = def.intervalo;
    modoRequisicao = currentMode;
    intervaloRequisicao = currentInterval;
    document.querySelectorAll(".mode-btn").forEach(b => {
        b.classList.toggle("active", b.dataset.mode === modoId);
    });
    document.querySelectorAll(".mode-interval").forEach(i => {
        i.classList.toggle("active", i.dataset.interval === currentInterval);
    });
    const ctx = document.getElementById("modeContextLabel");
    if (ctx) {
        const text = currentMode === "day"
            ? `MODO DAY TRADE · VELAS ${currentInterval}`
            : def.contexto;
        ctx.textContent = "";
        const dot = document.createElement("span");
        dot.className = "mode-context-dot";
        const span = document.createElement("span");
        span.className = "mode-context-text";
        span.textContent = text;
        ctx.appendChild(dot);
        ctx.appendChild(span);
    }
    const search = document.getElementById("searchInput");
    if (search) search.placeholder = def.placeholder_busca || "Busque um ativo...";
    // Clear analysis cache so the next selection fetches the new mode.
    chartDataCache.clear();
    lastChartSignature = "";
    selectStock(currentSelectedTicker);
}
(function initModeBar() {
    document.querySelectorAll(".mode-btn").forEach(btn => {
        btn.addEventListener("click", () => aplicarModo(btn.dataset.mode));
    });
    document.querySelectorAll(".mode-interval").forEach(el => {
        el.addEventListener("click", () => {
            currentInterval = el.dataset.interval;
            document.querySelectorAll(".mode-interval").forEach(i => {
                i.classList.toggle("active", i.dataset.interval === currentInterval);
            });
            const ctx = document.getElementById("modeContextLabel");
            if (ctx) {
                const text = currentMode === "day"
                    ? `MODO DAY TRADE · VELAS ${currentInterval}`
                    : MODES[currentMode].contexto;
                ctx.textContent = "";
                const dot = document.createElement("span");
                dot.className = "mode-context-dot";
                const span = document.createElement("span");
                span.className = "mode-context-text";
                span.textContent = text;
                ctx.appendChild(dot);
                ctx.appendChild(span);
            }
            selectStock(currentSelectedTicker);
        });
    });
    aplicarModo(currentMode);
})();

// ============================================================
// Coreografia Splash -> App
// ------------------------------------------------------------
// A splash e a revelacao do app compartilham os mesmos tokens de
// tempo (--splash-hold, --reveal-duration, ...), definidos em
// style.css. O JS apenas le esses tokens e sincroniza as classes
// de estado no <html>, garantindo que a animacao CSS e os timers
// nunca saiam de sincronia.
//
// Sequencia visual (t = 0 no carregamento):
//   0ms      splash entra e se assenta no centro
//   5000ms   splash dissolve (scale 1 -> 1.045) e o app comeca a
//            expandir de escala 0.955 ate 1, a partir do centro
//            exato da viewport
//   5690ms   app em escala plena; splash e nodo removidos do DOM
// ============================================================

const SPLASH_TIMING_DEFAULTS = {
    hold: 5000,
    exit: 450,
    revealDelay: 70,
    revealDuration: 620,
    revealFade: 260,
};

function readSplashTiming() {
    const styles = getComputedStyle(document.documentElement);
    const read = (name, fallback) => {
        const value = parseFloat(styles.getPropertyValue(name));
        return Number.isFinite(value) ? value : fallback;
    };

    return {
        hold: read("--splash-hold", SPLASH_TIMING_DEFAULTS.hold),
        exit: read("--splash-exit", SPLASH_TIMING_DEFAULTS.exit),
        revealDelay: read("--reveal-delay", SPLASH_TIMING_DEFAULTS.revealDelay),
        revealDuration: read("--reveal-duration", SPLASH_TIMING_DEFAULTS.revealDuration),
        revealFade: read("--reveal-fade", SPLASH_TIMING_DEFAULTS.revealFade),
    };
}

function setupSplash() {
    const splash = document.getElementById("splashScreen");
    const wrapper = document.querySelector(".dashboard-wrapper");
    const root = document.documentElement;
    const timing = readSplashTiming();

    let revealed = false;
    let settled = false;

    // Origem do scale no centro EXACTO da viewport (e nao do wrapper),
    // para que a expansao "emerge" do centro da janela do navegador
    // mesmo quando o conteudo e mais alto que a tela.
    const syncRevealOrigin = () => {
        if (!wrapper) return;
        const rect = wrapper.getBoundingClientRect();
        const originY = window.innerHeight / 2 - rect.top;
        wrapper.style.transformOrigin = "50% " + originY + "px";
    };

    const reveal = () => {
        if (revealed) return;
        revealed = true;
        syncRevealOrigin();
        // Troca atomica: a classe final traz a transition, a inicial
        // traz o estado de partida. A troca num unico frame e o que
        // faz a transicao disparar sem "flash" do app em escala 1.
        root.classList.remove("app-booting");
        root.classList.add("app-revealing");
    };

    const settle = () => {
        if (settled) return;
        settled = true;
        // Remove a classe de transicao: o app volta ao estado estatico
        // e a camada de composicao dedicada e liberada.
        root.classList.remove("app-revealing");
        if (splash && splash.parentNode) {
            try { console.log('[SPLASH_REMOVED]', performance.now()); } catch(e){}
            splash.parentNode.removeChild(splash);
        }
        try { console.log('[SPLASH_EVENT]', performance.now()); window.dispatchEvent(new CustomEvent('aguia:splash-done')); } catch(e){}
    };

    const revealTimer = setTimeout(reveal, timing.hold);

    // O encerramento espera a transicao mais longa (escala OU fade),
    // para nunca remover a splash com a animacao ainda em andamento.
    const revealSpan = Math.max(timing.revealDuration, timing.revealFade);
    const settleTimer = setTimeout(
        settle,
        timing.hold + timing.revealDelay + revealSpan + 60
    );

    // Rede de seguranca: se o CSS concluir a saida antes do timer
    // (aba em segundo plano, throttling do navegador), antecipa.
    if (splash) {
        splash.addEventListener("animationend", (event) => {
            if (event.target === splash && event.animationName === "splashExit") {
                reveal();
            }
        });
    }

    // Ultimo recurso: garante que o app nunca fique invisivel.
    setTimeout(() => {
        reveal();
        settle();
    }, timing.hold + timing.exit + 3000);

    // Se algo falhar no caminho, o app e liberado imediatamente.
    window.addEventListener("error", () => {
        root.classList.remove("app-booting");
    }, { once: true });
}

// InicializaÃ§Ã£o
document.addEventListener("DOMContentLoaded", () => {
    try {
        setupSplash();
    } catch (error) {
        document.documentElement.classList.remove("app-booting");
        console.warn("Falha na coreografia da splash:", error);
        try { window.dispatchEvent(new CustomEvent('aguia:splash-done')); } catch(e){}
    }

    renderStockList();
    testPythonBackend();
    selectStock("PETR4");

    // Força um redraw do gráfico após a revelação da splash, quando o
    // canvas ainda tem largura/altura zero devido à animação de escala.
    const revealRetry = setInterval(() => {
        const cached = cacheGet(cacheKey(currentSelectedTicker));
        if (cached && cached.candles && cached.candles.length) {
            lastChartSignature = "";
            renderTradingChartReal(cached.candles, cached);
            clearInterval(revealRetry);
        }
    }, 150);
    setTimeout(() => clearInterval(revealRetry), 8000);

    // Sincronização periódica suave de status
    setInterval(() => {
        if (!document.hidden) testPythonBackend();
    }, STATUS_POLL_MS);
});
(function(){
  const btn=document.getElementById('strategyBtn');
  const modal=document.getElementById('strategyModal');
  const form=document.getElementById('strategyForm');
  if(!btn||!modal||!form) return;
  const open=()=>{modal.classList.add('open');modal.setAttribute('aria-hidden','false');};
  const close=()=>{modal.classList.remove('open');modal.setAttribute('aria-hidden','true');};
  btn.addEventListener('click',open);
  modal.addEventListener('click',(e)=>{if(e.target===modal)close();});
  document.addEventListener('keydown',(e)=>{if(e.key==='Escape')close();});
  const sel=document.getElementById('strategySelector');
  const defaults={"media_tendencia_macro_jr":{"InpTrendPeriod":20,"InpFastEMAPeriod":9,"InpSMAInstitution":50,"InpSMAMacro":200,"InpADXPeriod":14,"InpADXMinLevel":22.0,"InpBBPeriod":20,"InpBBDeviation":2.0,"InpKeltnerMult":1.5}};
  if(sel){ sel.addEventListener('change',()=>{ const d=defaults[sel.value]; if(!d) return; Object.keys(d).forEach(k=>{const inp=form.querySelector('[name="'+k+'"]'); if(inp) inp.value=d[k];}); }); }
  form.addEventListener('submit',async(e)=>{
    e.preventDefault();
    const data={strategy_id: sel?sel.value:'media_tendencia_macro_jr', params:{}};
    new FormData(form).forEach((v,k)=>{ if(k!=='strategy_id') data.params[k]=isNaN(v)?v:Number(v); });
    try{ await fetch('/api/update-strategy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}); }catch(err){console.error(err);}
    close();
  });
})();


(function(){
  // Placeholder - handlers are managed by auth integration
})();





// Cache de autenticacao para evitar chamadas repetidas
window._aguiaAuthCache = window._aguiaAuthCache || {ts:0, data:null};
window._aguiaAuthFetchPromise = window._aguiaAuthFetchPromise || null;
window._aguiaAuthFetch = window._aguiaAuthFetch || function(force){
  var now = Date.now();
  if(!force && window._aguiaAuthCache.data && now - window._aguiaAuthCache.ts < 60000){
    return Promise.resolve(window._aguiaAuthCache.data);
  }
  if(!force && window._aguiaAuthFetchPromise){
    return window._aguiaAuthFetchPromise;
  }
  var p = fetch('/api/auth/me').then(function(r){
    if(!r.ok){
      throw new Error('http_' + r.status);
    }
    return r.json();
  }).then(function(data){
    window._aguiaAuthCache = {ts: Date.now(), data: data};
    window._aguiaAuthFetchPromise = null;
    return data;
  }).catch(function(err){
    window._aguiaAuthFetchPromise = null;
    throw err;
  });
  window._aguiaAuthFetchPromise = p;
  return p;
};
try { if(!window._aguiaAuthFetchPromise && (!window._aguiaAuthCache || !window._aguiaAuthCache.data || Date.now() - window._aguiaAuthCache.ts >= 60000)) { try { window._aguiaAuthFetch(); } catch(e){} } } catch(e){}
window._aguiaAuthInvalidate = function(){
  window._aguiaAuthCache = {ts:0, data:null};
  window._aguiaAuthFetchPromise = null;
};
// Auth integration
(function(){
  const btn = document.getElementById('btnEntrarCadastro');
  const menu = document.getElementById('userDropdown');
  const nameEl = document.querySelector('#userDropdown .user-name');
  const emailEl = document.querySelector('#userDropdown .user-email');
  const avatarLg = document.querySelector('#userDropdown .user-avatar-lg');
  const pills = Array.from(document.querySelectorAll('#userDropdown .user-pill'));
  const manageBtn = pills.find(function(x){ return /Gerenciar/i.test(x.textContent||''); });
  const relBtn = pills.find(function(x){ return /Relat/i.test(x.textContent||''); });
  const secBtn = pills.find(function(x){ return /Segur/i.test(x.textContent||''); });
  const sairBtn = pills.find(function(x){ return /Sair/i.test(x.textContent||''); });

  function openMenu(){ if(menu){ menu.classList.add('open'); menu.setAttribute('aria-hidden','false'); } }
  function closeMenu(){ if(menu){ menu.classList.remove('open'); menu.setAttribute('aria-hidden','true'); } }
  function toggleMenu(e){ if(e){ try{ e.preventDefault(); e.stopPropagation(); }catch(ex){} } if(menu){ if(menu.classList.contains('open')) closeMenu(); else openMenu(); } }

  function setGuest(){
    if(nameEl) nameEl.textContent = 'Visitante';
    if(emailEl) emailEl.textContent = 'sem conta';
    if(avatarLg){ avatarLg.innerHTML=''; avatarLg.classList.remove('has-img'); }
    if(manageBtn){ manageBtn.onclick = function(e){ try{e.preventDefault();}catch(ex){} closeMenu(); if(typeof window.openAuthModal==='function') window.openAuthModal(); }; }
    if(secBtn){ secBtn.onclick = function(e){ try{e.preventDefault();}catch(ex){} closeMenu(); if(typeof window.openAuthModal==='function') window.openAuthModal(); }; }
    if(relBtn){ relBtn.onclick = function(e){ try{e.preventDefault();}catch(ex){} closeMenu(); alert('Relatórios em desenvolvimento'); }; }
    if(sairBtn){ sairBtn.textContent='Entrar / Criar conta'; sairBtn.classList.remove('danger'); sairBtn.onclick = function(e){ try{e.preventDefault();}catch(ex){} closeMenu(); if(typeof window.openAuthModal==='function') window.openAuthModal(); }; }
    if(btn){ btn.setAttribute('aria-label','Entrar / Cadastrar'); btn.onclick = toggleMenu; }
  }

  async function loadAuth(){
    try {
      var data = await (window._aguiaAuthFetch ? window._aguiaAuthFetch() : fetch('/api/auth/me').then(function(r){return r.json();}));
      if(data && data.sucesso && data.dados && data.dados.autenticado && data.dados.user){
        var u = data.dados.user;
        if(nameEl) nameEl.textContent = u.display_name || u.email_original || 'Usuário';
        if(emailEl) emailEl.textContent = u.email_original || u.email_normalized || '';
        if(avatarLg){
          avatarLg.innerHTML='';
          var img = document.createElement('img');
          img.src = '/api/auth/avatar/' + u.id + '?t=' + Date.now();
          img.style.width='100%'; img.style.height='100%'; img.style.objectFit='cover';
          avatarLg.appendChild(img);
          avatarLg.classList.add('has-img');
        }
        if(manageBtn){ manageBtn.onclick = function(e){ try{e.preventDefault();}catch(ex){} closeMenu(); window.location.href = 'conta.html'; }; }
        if(relBtn){ relBtn.onclick = function(e){ try{e.preventDefault();}catch(ex){} closeMenu(); window.location.href = 'conta.html'; }; }
        if(secBtn){ secBtn.onclick = function(e){ try{e.preventDefault();}catch(ex){} closeMenu(); window.location.href = 'conta.html'; }; }
        if(sairBtn){ sairBtn.textContent='Sair'; sairBtn.classList.add('danger'); sairBtn.onclick = async function(e){
          try{e.preventDefault();}catch(ex){} closeMenu();
          try { await fetch('/api/auth/logout',{method:'POST'}); } catch(ex){}
          location.reload();
        }; }
        if(btn){ btn.title = u.display_name || ''; btn.onclick = toggleMenu; }
        return;
      }
    } catch(e){}
    setGuest();
  }

  window.aguiaAuthSuccess = function(u){ loadAuth(); };
  window.aguiaAuthGuest = function(){ setGuest(); };

  if(btn){ btn.onclick = toggleMenu; try{btn._aguiaAuthBound=true;}catch(e){} }
  document.addEventListener('click', function(e){
    if(!menu) return;
    if(menu.contains(e.target)) return;
    if(btn && btn.contains(e.target)) return;
    closeMenu();
  });
  document.addEventListener('keydown', function(e){ if(e.key === 'Escape') closeMenu(); });

  loadAuth();
  })();
