/**
 * Ãguia Trader - Dashboard Quantitativo & Motor GrÃ¡fico B3
 * IntegraÃ§Ã£o com API Python 3.11, Yahoo Finance, Indicadores e IA Local.
 */

// Universo inicial de aÃ§Ãµes B3 monitoradas (somente fallback offline, rotulado como SIMULADO)
// Lista imutÃ¡vel: ASSETS_UNIVERSE Ã© a cÃ³pia de trabalho, substituÃ­da pela API quando online.
const ASSETS_FALLBACK_B3 = [
    { ticker: "ASAI3", price: 13.27, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 5.17, target: 13.96, stop: 12.65, payoff: "1.11 : 1", dayVar: "+0.85%", simulado: true },
    { ticker: "ANIM3", price: 5.29, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.46, target: 5.53, stop: 5.08, payoff: "1.14 : 1", dayVar: "+1.15%", simulado: true },
    { ticker: "ARML3", price: 6.48, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 5.45, target: 6.83, stop: 6.18, payoff: "1.17 : 1", dayVar: "+0.62%", simulado: true },
    { ticker: "AURE3", price: 15.59, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.53, target: 16.30, stop: 14.95, payoff: "1.11 : 1", dayVar: "+0.32%", simulado: true },
    { ticker: "PETR4", price: 38.45, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 3.80, target: 39.91, stop: 37.10, payoff: "1.08 : 1", dayVar: "+1.42%", simulado: true },
    { ticker: "VALE3", price: 61.20, trend: "BAIXA", trendText: "BAIXA (BEARISH)", returnPct: -2.75, target: 59.52, stop: 62.60, payoff: "1.20 : 1", dayVar: "-0.95%", simulado: true },
    { ticker: "ITUB4", price: 34.80, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.10, target: 36.23, stop: 33.60, payoff: "1.19 : 1", dayVar: "+0.78%", simulado: true },
    { ticker: "BBAS3", price: 27.60, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 3.95, target: 28.69, stop: 26.70, payoff: "1.21 : 1", dayVar: "+0.55%", simulado: true },
    { ticker: "BBDC4", price: 14.90, trend: "NEUTRO", trendText: "LATERAL (NEUTRAL)", returnPct: 0.67, target: 15.00, stop: 14.60, payoff: "0.33 : 1", dayVar: "+0.10%", simulado: true },
    { ticker: "WEGE3", price: 52.80, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 6.25, target: 56.10, stop: 50.40, payoff: "1.38 : 1", dayVar: "+1.85%", simulado: true },
    { ticker: "MGLU3", price: 8.90, trend: "BAIXA", trendText: "BAIXA (BEARISH)", returnPct: -5.40, target: 8.42, stop: 9.35, payoff: "1.07 : 1", dayVar: "-2.10%", simulado: true },
    { ticker: "PRIO3", price: 44.50, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.85, target: 46.66, stop: 42.80, payoff: "1.27 : 1", dayVar: "+0.90%", simulado: true },
    { ticker: "RENT3", price: 54.30, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.20, target: 56.58, stop: 52.40, payoff: "1.20 : 1", dayVar: "+0.60%", simulado: true },
    { ticker: "EMBR3", price: 49.80, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 5.60, target: 52.59, stop: 47.90, payoff: "1.47 : 1", dayVar: "+1.95%", simulado: true },
    { ticker: "GGBR4", price: 21.15, trend: "NEUTRO", trendText: "LATERAL (NEUTRAL)", returnPct: 0.45, target: 21.25, stop: 20.80, payoff: "0.28 : 1", dayVar: "+0.05%", simulado: true },
    { ticker: "CSNA3", price: 12.40, trend: "BAIXA", trendText: "BAIXA (BEARISH)", returnPct: -3.80, target: 11.93, stop: 12.85, payoff: "1.04 : 1", dayVar: "-1.30%", simulado: true },
    { ticker: "SUZB3", price: 58.70, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 4.30, target: 61.22, stop: 56.90, payoff: "1.40 : 1", dayVar: "+0.70%", simulado: true },
    { ticker: "JBSS3", price: 35.10, trend: "ALTA", trendText: "ALTA (BULLISH)", returnPct: 3.70, target: 36.40, stop: 34.10, payoff: "1.30 : 1", dayVar: "+0.45%", simulado: true }
];

// ============================================================
// Registro de Modos (espelho de aguia/modes.py)
// ------------------------------------------------------------
// O backend Ã© a fonte da verdade e expÃµe o catÃ¡logo em
// /api/modos. Este espelho mantÃ©m a interface funcional antes da
// primeira resposta da API (e permite renderizar a barra de modos
// imediatamente). tests/test_modes.py garante que os dois lados
// permaneÃ§am em sincronia.
// ============================================================
const MODES = {
    swing: {
        id: "swing",
        label: "Swing Trade",
        hint: "Velas DiÃ¡rias Â· 14D",
        contexto: "Modo Swing Trade â€¢ GrÃ¡fico DiÃ¡rio 14D",
        timeframe: "1d",
        intervalo: "1d",
        horizonte: 14,
        moeda: "R$",
        rotulo_alvo: "Alvo Projetado (14D)",
        rotulo_stop: "Stop Loss Sugerido",
        rotulo_payoff: "RelaÃ§Ã£o Risco x Retorno",
        rotulo_sub_alvo: "de projeÃ§Ã£o",
        rotulo_sub_stop: "de risco",
        rotulo_projecao: "ProjeÃ§Ã£o 14D (Alvo + Banda ATR)",
        placeholder_busca: "Buscar aÃ§Ã£o (ex: PETR4)...",
        indicadores: ["SMA 200", "WMA 30", "ATR 14"],
        foco: "continuidade de tendÃªncia de mÃ©dio prazo",
    },
    day: {
        id: "day",
        label: "Day Trade",
        hint: "Intraday Â· Rompimentos",
        contexto: "Modo Day Trade â€¢ Velas IntradiÃ¡rias",
        timeframe: "5m",
        intervalo: "5m",
        horizonte: 12,
        moeda: "US$",
        rotulo_alvo: "Alvo Intradia",
        rotulo_stop: "Stop Intradia",
        rotulo_payoff: "Risco x Retorno da SessÃ£o",
        rotulo_sub_alvo: "de projeÃ§Ã£o intradiÃ¡ria",
        rotulo_sub_stop: "de risco na sessÃ£o",
        rotulo_projecao: "ProjeÃ§Ã£o Intradia (Alvo + Banda ATR)",
        placeholder_busca: "Buscar ativo (ex: SPY)...",
        indicadores: ["Rompimentos", "ATR 14", "Volume"],
        foco: "rompimentos e volatilidade imediata",
    },
};

const INTERVALOS_DAY = ["5m", "15m", "1h"];
const MODO_PADRAO = "swing";

// Universo intradiÃ¡rio de fallback (rotulado como SIMULADO)
const ASSETS_FALLBACK_DAY = [
    { ticker: "SPY", rotulo: "S&P 500", price: 645.10, trend: "NEUTRO", trendText: "LATERAL (NEUTRAL)", returnPct: 0.42, target: 649.80, stop: 637.20, payoff: "1.02 : 1", dayVar: "+0.21%", simulado: true },
    { ticker: "DIA", rotulo: "Dow Jones", price: 438.75, trend: "NEUTRO", trendText: "LATERAL (NEUTRAL)", returnPct: 0.18, target: 440.90, stop: 434.60, payoff: "0.34 : 1", dayVar: "+0.09%", simulado: true },
    { ticker: "GC=F", rotulo: "Ouro", price: 2678.40, trend: "NEUTRO", trendText: "LATERAL (NEUTRAL)", returnPct: 0.31, target: 2694.60, stop: 2652.90, payoff: "0.51 : 1", dayVar: "+0.15%", simulado: true },
    { ticker: "BTC-USD", rotulo: "Bitcoin", price: 68420.00, trend: "NEUTRO", trendText: "LATERAL (NEUTRAL)", returnPct: 0.55, target: 68810.00, stop: 67840.00, payoff: "0.39 : 1", dayVar: "+0.27%", simulado: true },
];

// Estado da AplicaÃ§Ã£o
let ASSETS_UNIVERSE = ASSETS_FALLBACK_B3.map(asset => ({ ...asset }));
let currentSelectedTicker = "PETR4";
let currentFilter = "TODOS";
let searchQuery = "";
let currentMode = MODO_PADRAO;
let currentInterval = MODES[MODO_PADRAO].intervalo;
let currentCurrency = MODES[MODO_PADRAO].moeda;

// Cache LRU de payloads de anÃ¡lise (Map preserva a ordem de inserÃ§Ã£o)
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
let chartGeometry = null;
let chartHoverIndex = null;

// ============================================================
// Troca Fluida de Dados
// ------------------------------------------------------------
// A troca de ativo passa por um fade curto (esmaece -> aplica ->
// devolve) para eliminar o "estalo" da troca seca de valores.
// O efeito usa apenas opacity/transform (compostor-friendly) e
// Ã© desligado quando o usuÃ¡rio prefere menos movimento.
// ============================================================
const SWAP_FADE_OUT_MS = 150;
const SWAP_TARGET_SELECTOR = "#chartPanel, #assetHeader, #quantGrid .quant-card, #reasoningPanel";
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

/**
 * Espera um nÃºmero de milissegundos
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Prepara a entrada do painel: reinicia a animaÃ§Ã£o de fade
 */
function playSwapIn(targets) {
    targets.forEach(el => {
        if (el.dataset.swapBound !== "1") {
            el.addEventListener("animationend", event => {
                if (event.target === el && event.animationName === "dataSwapFade") {
                    el.classList.remove("data-swap-in");
                }
            });
            el.dataset.swapBound = "1";
        }
        el.classList.add("data-swap-in");
    });
}

/**
 * Aplica a atualizaÃ§Ã£o de dados com fade suave entre ativos
 */
async function aplicarDadosComFade(update) {
    const targets = Array.from(document.querySelectorAll(SWAP_TARGET_SELECTOR));

    if (prefersReducedMotion.matches || targets.length === 0) {
        update();
        return;
    }

    targets.forEach(el => el.classList.add("data-swap-out"));
    await sleep(SWAP_FADE_OUT_MS);
    update();
    targets.forEach(el => {
        el.classList.remove("data-swap-out");
    });
    playSwapIn(targets);
}

// ============================================================
// Paleta da Marca
// ------------------------------------------------------------
// Os tokens sÃ£o lidos de :root (static/style.css) em runtime, de
// modo que o grÃ¡fico em Canvas usa exatamente as mesmas cores do
// resto do sistema. Alterar um token em style.css repinta o
// dashboard inteiro â€” nÃ£o existe cor duplicada no JavaScript.
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

// ============================================================
// Fabrica Dinamica de Icones Cyber/Neon (SVG)
// ------------------------------------------------------------
// Cada ativo recebe um icone vetorial de 22x22px gerado em runtime:
// nada de emoji do sistema, nada de imagem externa, nada de CDN.
// A paleta vem dos tokens CSS (--icon-*), portanto o icone acompanha
// o tema e o halo neon e definido em um unico token.
//
// getAssetIconSVG(ticker, categoria) -> markup SVG inline
// ============================================================

const ICON_CATEGORIAS = {
    CRIPTO: "cripto",
    FOREX: "forex",
    COMMODITY: "commodity",
    INDICE: "indice",
    B3: "b3",
};

// Glifos vetoriais: o conteudo usa `currentColor` (a cor vem do
// wrapper) ou tokens --icon-* quando o icone e bicolor.
const ICON_GLYPHS = {
    // ------------------------------------------------------------ cripto
    btc: {
        color: "var(--icon-orange)",
        markup: `
            <circle cx="11" cy="11" r="9" fill="currentColor" opacity="0.15"/>
            <circle cx="11" cy="11" r="9" fill="none" stroke="currentColor" stroke-width="1.5"/>
            <path d="M9.4 6.4h3.2a2.3 2.3 0 0 1 0 4.6H9.4z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
            <path d="M9.4 11h3.6a2.3 2.3 0 0 1 0 4.6H9.4z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
            <path d="M10.6 4.6v12.8M12.8 4.6v12.8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        `,
    },
    eth: {
        color: "var(--icon-purple)",
        markup: `
            <path d="M11 2.4 5.8 10.8 11 13.9l5.2-3.1z" fill="var(--icon-purple)"/>
            <path d="M11 15.1 5.8 12l5.2 7.4 5.2-7.4z" fill="var(--icon-cyan)" opacity="0.9"/>
        `,
    },
    sol: {
        color: "var(--icon-green)",
        markup: `
            <path d="M8.2 4.6h9.2l-2.1 2.8H6.1z" fill="currentColor"/>
            <path d="M6.1 9h9.2l-2.1 2.8H4z" fill="currentColor" opacity="0.85"/>
            <path d="M4 13.4h9.2l-2.1 2.8H1.9z" fill="currentColor" opacity="0.7"/>
        `,
    },
    usdt: {
        color: "var(--icon-green)",
        markup: `
            <circle cx="11" cy="11" r="9" fill="none" stroke="currentColor" stroke-width="1.5"/>
            <path d="M7.4 8.4h7.2M11 8.4v6.2" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
            <path d="M8.2 15.8h5.6" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" opacity="0.55"/>
        `,
    },
    usdc: {
        color: "var(--icon-cyan)",
        markup: `
            <circle cx="11" cy="11" r="9" fill="none" stroke="currentColor" stroke-width="1.5"/>
            <path d="M13.4 9.1a2.7 2.7 0 1 0 0 4.2H9a2.7 2.7 0 1 1 0-4.2h2.6" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <path d="M11.3 7.1v8.2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        `,
    },
    bnb: {
        color: "var(--icon-gold)",
        markup: `
            <path d="M11 3.2 18.8 11 11 18.8 3.2 11z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M11 6.6 15.4 11 11 15.4 6.6 11z" fill="currentColor" opacity="0.85"/>
        `,
    },
    xrp: {
        color: "var(--icon-cyan)",
        markup: `
            <path d="M4.4 5.6 11 12.2l6.6-6.6M4.4 16.4 11 9.8l6.6 6.6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        `,
    },
    ada: {
        color: "var(--icon-cyan)",
        markup: `
            <circle cx="11" cy="11" r="7.8" fill="none" stroke="currentColor" stroke-width="1.4" stroke-dasharray="1.1 2.7" stroke-linecap="round"/>
            <circle cx="11" cy="11" r="2.3" fill="currentColor"/>
        `,
    },
    doge: {
        color: "var(--icon-gold)",
        markup: `
            <path d="M8 5.6h3.4a5.4 5.4 0 0 1 0 10.8H8z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
            <path d="M8 5.6v10.8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
        `,
    },
    avax: {
        color: "var(--icon-orange)",
        markup: `
            <path d="M11 3.4 19.4 18.6H2.6z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
            <path d="M11 10.6 14.2 16.4H7.8z" fill="currentColor" opacity="0.75"/>
        `,
    },

    // ------------------------------------------------------------ forex
    usd: {
        color: "var(--icon-cyan)",
        markup: `
            <rect x="3" y="3" width="16" height="16" rx="4.6" fill="currentColor" opacity="0.14"/>
            <rect x="3" y="3" width="16" height="16" rx="4.6" fill="none" stroke="currentColor" stroke-width="1.4"/>
            <path d="M13.2 9.3a2.6 2.6 0 1 0 0 3.8H9a2.6 2.6 0 1 1 0-3.8h2.5M11.2 7.2v8" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        `,
    },
    eur: {
        color: "var(--icon-cyan)",
        markup: `
            <circle cx="11" cy="11" r="9" fill="none" stroke="currentColor" stroke-width="1.4" opacity="0.5"/>
            <text x="11" y="15.2" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="11" font-weight="700" fill="currentColor">â‚¬</text>
        `,
    },
    gbp: {
        color: "var(--icon-green)",
        markup: `
            <circle cx="11" cy="11" r="9" fill="none" stroke="currentColor" stroke-width="1.4" opacity="0.5"/>
            <text x="11" y="15.2" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="11" font-weight="700" fill="currentColor">Â£</text>
        `,
    },
    brl: {
        color: "var(--icon-green)",
        markup: `
            <circle cx="11" cy="11" r="9" fill="none" stroke="currentColor" stroke-width="1.4" opacity="0.5"/>
            <text x="11" y="15" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="9" font-weight="700" fill="currentColor">R$</text>
        `,
    },

    // --------------------------------------------------------- commodities
    gold: {
        color: "var(--icon-gold)",
        markup: `
            <path d="M2.9 15.1 5.7 10h10.6l2.8 5.1z" fill="currentColor" opacity="0.9"/>
            <path d="M5.7 10 8.1 5.4h5.8l2.4 4.6z" fill="currentColor" opacity="0.55"/>
            <path d="M4.8 12.6h12.4" stroke="currentColor" stroke-width="0.9" opacity="0.4"/>
        `,
    },
    silver: {
        color: "var(--icon-silver)",
        markup: `
            <path d="M2.9 15.1 5.7 10h10.6l2.8 5.1z" fill="currentColor" opacity="0.75"/>
            <path d="M5.7 10 8.1 5.4h5.8l2.4 4.6z" fill="currentColor" opacity="0.45"/>
        `,
    },
    copper: {
        color: "var(--icon-orange)",
        markup: `
            <circle cx="11" cy="11" r="6.6" fill="none" stroke="currentColor" stroke-width="2.4"/>
            <circle cx="11" cy="11" r="2.4" fill="none" stroke="currentColor" stroke-width="1.3" opacity="0.7"/>
        `,
    },
    oil: {
        color: "var(--icon-orange)",
        markup: `
            <path d="M11 3.1c3.5 4.2 5.3 6.6 5.3 9.1a5.3 5.3 0 0 1-10.6 0c0-2.5 1.8-4.9 5.3-9.1z" fill="currentColor" opacity="0.9"/>
            <path d="M9.4 12.4a1.9 1.9 0 0 0 1.9 1.9" fill="none" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" opacity="0.7"/>
        `,
    },
    corn: {
        color: "var(--icon-gold)",
        markup: `
            <path d="M11 3.4c3.3 1.7 4.7 4.5 4.7 7.5 0 3.6-2.1 6.5-4.7 7.6-2.6-1.1-4.7-4-4.7-7.6 0-3 1.4-5.8 4.7-7.5z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
            <path d="M8.8 8.6h4.4M8.4 11.4h5.2M8.8 14.2h4.4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        `,
    },
    soy: {
        color: "var(--icon-green)",
        markup: `
            <ellipse cx="9" cy="12.6" rx="3.3" ry="4.1" transform="rotate(-22 9 12.6)" fill="currentColor" opacity="0.9"/>
            <ellipse cx="13.3" cy="9.9" rx="2.9" ry="3.6" transform="rotate(22 13.3 9.9)" fill="currentColor" opacity="0.6"/>
        `,
    },

    // ------------------------------------------------------------ indices
    indexChart: {
        color: "var(--icon-cyan)",
        markup: `
            <path d="M3.4 15.8 8.2 10.4l3 3 6.4-7.2" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="17.6" cy="6.2" r="1.6" fill="currentColor"/>
            <path d="M3.4 18.4h15.2" stroke="currentColor" stroke-width="0.9" opacity="0.35"/>
        `,
    },
    indexBars: {
        color: "var(--icon-green)",
        markup: `
            <rect x="4.2" y="11.4" width="3" height="6" rx="1.1" fill="currentColor" opacity="0.6"/>
            <rect x="9.5" y="7.8" width="3" height="9.6" rx="1.1" fill="currentColor" opacity="0.82"/>
            <rect x="14.8" y="4.4" width="3" height="13" rx="1.1" fill="currentColor"/>
        `,
    },
    indexArrow: {
        color: "var(--icon-purple)",
        markup: `
            <path d="M3.4 16.6 9 11l3.2 3.2 4.8-5.6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M13.8 7.8h3.8v3.8" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3.4 18.6h15.2" stroke="currentColor" stroke-width="0.9" opacity="0.35"/>
        `,
    },
    indexIbovespa: {
        color: "var(--icon-green)",
        markup: `
            <path d="M3.4 15 8 10.2l3 2.8 6.2-6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="17.4" cy="6.6" r="1.5" fill="currentColor"/>
        `,
    },

    // ------------------------------------------------------- setores B3
    bank: {
        color: "var(--icon-cyan)",
        markup: `
            <path d="M2.9 8.6 11 4.2l8.1 4.4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M5.2 10.6v4.2M8.7 10.6v4.2M13.3 10.6v4.2M16.8 10.6v4.2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M3.4 17.4h15.2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
        `,
    },
    energy: {
        color: "var(--icon-gold)",
        markup: `
            <path d="M12.8 2.6 6.2 12.4h4.2L9.2 19.4l6.6-9.8h-4.2z" fill="currentColor" opacity="0.92"/>
        `,
    },
    mining: {
        color: "var(--icon-silver)",
        markup: `
            <path d="M11 2.8 17.4 9 11 19.2 4.6 9z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M4.6 9h12.8M11 2.8 8.3 9 11 19.2 13.7 9z" fill="currentColor" opacity="0.22" stroke="currentColor" stroke-width="1" stroke-linejoin="round"/>
        `,
    },
    retail: {
        color: "var(--icon-green)",
        markup: `
            <path d="M4.8 7.6h12.4l-1.1 10.2H5.9z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M8.2 7.6V6.1a2.8 2.8 0 0 1 5.6 0v1.5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        `,
    },
    health: {
        color: "var(--icon-cyan)",
        markup: `
            <path d="M2.8 11.2h3.4l1.8-5.2 3 10.4 2.2-6.2 1.6 3h4.4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
        `,
    },
};

// Ticker -> glifo, por categoria
const ICON_CRYPTO_MAP = {
    "BTC-USD": "btc",
    "ETH-USD": "eth",
    "SOL-USD": "sol",
    "USDT-USD": "usdt",
    "USDC-USD": "usdc",
    "BNB-USD": "bnb",
    "XRP-USD": "xrp",
    "ADA-USD": "ada",
    "DOGE-USD": "doge",
    "AVAX-USD": "avax",
};

const ICON_FOREX_MAP = {
    "USDBRL=X": "usd",
    "BRL=X": "brl",
    "DXY": "usd",
    "USD=X": "usd",
    "EURUSD=X": "eur",
    "GBPUSD=X": "gbp",
    "USDJPY=X": "usd",
    "USDCAD=X": "usd",
};

const ICON_COMMODITY_MAP = {
    "GC=F": "gold",
    "XAUUSD=X": "gold",
    "SI=F": "silver",
    "XAGUSD=X": "silver",
    "HG=F": "copper",
    "CL=F": "oil",
    "BZ=F": "oil",
    "ZC=F": "corn",
    "ZS=F": "soy",
};

const ICON_INDEX_MAP = {
    "^GSPC": "indexChart",
    "SPY": "indexChart",
    "^DJI": "indexBars",
    "DIA": "indexBars",
    "^IXIC": "indexArrow",
    "QQQ": "indexArrow",
    "^BVSP": "indexIbovespa",
};

// Setores da B3: banco, energia, mineraÃ§Ã£o, varejo/alimentaÃ§Ã£o e saÃºde/educaÃ§Ã£o
const ICON_B3_SECTORS = [
    { glyph: "bank", tickers: ["ITUB4", "BBDC4", "BBAS3", "BPSA3", "BRSR6", "ITSA4", "SANB11", "B3SA3", "CMIG4", "BBTC", "BPAC11", "BANC11", "BRBI11", "PSBB11", "BMEB3"] },
    { glyph: "energy", tickers: ["PETR4", "PETR3", "PRIO3", "RPRL3", "VBBR3", "EQTL3", "OSBR3", "CSAN3", "LOGG3", "DMMO3"] },
    { glyph: "mining", tickers: ["VALE3", "GGBR4", "MMX3", "BRAD3", "BRAP4", "AGL3", "CSNA3", "VAMO3", "USIM5", "PARIM3"] },
    { glyph: "retail", tickers: ["MGLU3", "LREN3", "ABEV3", "MRVE3", "JBSS3", "SUZB3", "CASH3", "PETZ3", "BHIA3", "SOMA3", "RADL3", "AZUL3", "KLBN3", "ASAI3", "AURE3", "RENT3"] },
    { glyph: "health", tickers: ["RDOR3", "FLRY3", "HSML3", "PSSA3", "COGN3", "YDUQ3", "VERO3", "CURA3", "APIM3", "OPM3", "PFGC3", "ANIM3"] },
];

/**
 * Embrulha o glifo em um SVG inline responsivo de 22x22
 * `color` ja vem como referencia completa de token (ex.: var(--icon-cyan))
 */
function wrapIconSVG(markup, color) {
    return `<svg class="asset-icon" viewBox="0 0 22 22" width="22" height="22" aria-hidden="true" focusable="false" style="color: ${color}">${markup}</svg>`;
}

/**
 * Icone universal: disco escuro com borda ciano neon e as duas
 * primeiras letras do ticker em JetBrains Mono.
 */
function fallbackIconSVG(ticker) {
    const letters = (String(ticker || "").toUpperCase().replace(/[^A-Z0-9]/g, "") || "??").slice(0, 2);
    return wrapIconSVG(`
        <circle cx="11" cy="11" r="9" fill="var(--icon-fallback-bg)" stroke="var(--icon-cyan)" stroke-width="1.5"/>
        <text x="11" y="14.6" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="9" font-weight="700" fill="var(--icon-cyan)">${letters}</text>
    `, "var(--icon-cyan)");
}

/**
 * Detecta a categoria do ativo a partir do ticker
 */
function detectarCategoriaIcone(ticker) {
    const t = String(ticker || "").trim().toUpperCase();

    if (ICON_CRYPTO_MAP[t]) return ICON_CATEGORIAS.CRIPTO;
    if (ICON_COMMODITY_MAP[t]) return ICON_CATEGORIAS.COMMODITY;
    if (ICON_FOREX_MAP[t] || /^[A-Z]{3}USD=X$/.test(t)) return ICON_CATEGORIAS.FOREX;
    if (ICON_INDEX_MAP[t] || t.startsWith("^")) return ICON_CATEGORIAS.INDICE;
    return ICON_CATEGORIAS.B3;
}

/**
 * Resolve o glifo de um ticker dentro de uma categoria
 */
function resolveIconGlyph(ticker, categoria) {
    const t = String(ticker || "").trim().toUpperCase();

    if (categoria === ICON_CATEGORIAS.CRIPTO) return ICON_CRYPTO_MAP[t] || null;
    if (categoria === ICON_CATEGORIAS.FOREX) return ICON_FOREX_MAP[t] || "usd";
    if (categoria === ICON_CATEGORIAS.COMMODITY) return ICON_COMMODITY_MAP[t] || null;
    if (categoria === ICON_CATEGORIAS.INDICE) return ICON_INDEX_MAP[t] || "indexChart";

    // B3: setor primeiro, fallback universal depois
    const setor = ICON_B3_SECTORS.find(entrada => entrada.tickers.includes(t));
    return setor ? setor.glyph : null;
}

/**
 * Fabrica de icones: devolve o markup SVG do icone do ativo.
 *
 * @param {string} ticker     Simbolo do ativo (ex: "PETR4", "BTC-USD")
 * @param {string} [categoria] "cripto" | "forex" | "commodity" | "indice" | "b3"
 * @returns {string} Markup SVG inline (22x22)
 */
function getAssetIconSVG(ticker, categoria) {
    const cat = categoria || detectarCategoriaIcone(ticker);
    const glyphKey = resolveIconGlyph(ticker, cat);
    const glyph = glyphKey ? ICON_GLYPHS[glyphKey] : null;

    if (!glyph) return fallbackIconSVG(ticker);
    return wrapIconSVG(glyph.markup, glyph.color);
}

// Elementos do DOM
const stockListContainer = document.getElementById("stockListContainer");
const searchInput = document.getElementById("searchInput");
const filterPills = document.querySelectorAll(".filter-pill:not(#btn-estrategia):not(#btn-estrategia-config)");
const universeCount = document.getElementById("universeCount");
const btnEstrategia = document.getElementById("btn-estrategia");
const btnEstrategiaConfig = document.getElementById("btn-estrategia-config");
const macroJrModal = document.getElementById("macroJrModal");
const macroJrBackdrop = document.getElementById("macroJrBackdrop");
const macroJrClose = document.getElementById("macroJrClose");
const macroJrCancel = document.getElementById("macroJrCancel");
const macroJrApply = document.getElementById("macroJrApply");

let macroJrAtivo = false;
let macroJrResultados = [];

const headlineTicker = document.getElementById("headlineTicker");
const headlineReturn = document.getElementById("headlineReturn");
const headlineTrend = document.getElementById("headlineTrend");
const chartHeadlineIcon = document.getElementById("chartHeadlineIcon");
const dataSourceBadge = document.getElementById("dataSourceBadge");

// Tooltip de leitura do grafico (crosshair + OHLCV)
const chartTooltip = document.getElementById("chartTooltip");
const chartTooltipDate = document.getElementById("chartTooltipDate");
const chartTooltipOpen = document.getElementById("chartTooltipOpen");
const chartTooltipHigh = document.getElementById("chartTooltipHigh");
const chartTooltipLow = document.getElementById("chartTooltipLow");
const chartTooltipClose = document.getElementById("chartTooltipClose");
const chartTooltipChange = document.getElementById("chartTooltipChange");
const chartTooltipVolume = document.getElementById("chartTooltipVolume");

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
const metricTargetLabel = document.getElementById("metricTargetLabel");
const metricStopLabel = document.getElementById("metricStopLabel");
const metricPayoffLabel = document.getElementById("metricPayoffLabel");
const aiReasoningText = document.getElementById("aiReasoningText");
const rationaleSource = document.getElementById("rationaleSource");
const complianceDisclaimer = document.getElementById("complianceDisclaimer");
const snapshotTimestamp = document.getElementById("snapshotTimestamp");

// Barra de modos (Day Trade / Swing Trade)
const modeSwitch = document.getElementById("modeSwitch");
const modeContextLabel = document.getElementById("modeContextLabel");
const modeIntervals = document.getElementById("modeIntervals");
const legendProjectionLabel = document.getElementById("legendProjectionLabel");
const themeToggle = document.getElementById("themeToggle");

const canvas = document.getElementById("tradingChartCanvas");
const ctx = canvas ? canvas.getContext("2d") : null;

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
 * FormataÃ§Ã£o de moeda no padrÃ£o brasileiro (R$ 13,27)
 * A moeda acompanha o modo ativo: R$ no Swing Trade (B3) e
 * US$ no Day Trade (ativos globais).
 */
function formatarMoeda(valor, moeda) {
    if (valor === null || valor === undefined || isNaN(valor)) return `${moeda || currentCurrency} â€”`;
    const simbolo = moeda || currentCurrency;
    return `${simbolo} ${valor.toFixed(2).replace(".", ",")}`;
}

/**
 * FormataÃ§Ã£o de porcentagem no padrÃ£o brasileiro (+5,17%)
 */
function formatarPorcentagem(valor) {
    if (valor === null || valor === undefined || isNaN(valor)) return "â€”%";
    const sinal = valor >= 0 ? "+" : "";
    return `${sinal}${valor.toFixed(2).replace(".", ",")}%`;
}

/**
 * Retorna a definicao do modo ativo (com fallback seguro)
 */
function modoAtivo() {
    return MODES[currentMode] || MODES[MODO_PADRAO];
}

/**
 * Aplica os rotulos do modo (cards de metrica, legenda e busca)
 * em todos os elementos que descrevem o horizonte de analise.
 * O rotulo de contexto pertence a barra de modos (ver atualizarBarraModos).
 */
function aplicarRotulosModo(modoId) {
    const definicao = MODES[modoId] || MODES[MODO_PADRAO];

    if (metricTargetLabel) metricTargetLabel.textContent = definicao.rotulo_alvo;
    if (metricStopLabel) metricStopLabel.textContent = definicao.rotulo_stop;
    if (metricPayoffLabel) metricPayoffLabel.textContent = definicao.rotulo_payoff;
    if (legendProjectionLabel) legendProjectionLabel.textContent = definicao.rotulo_projecao;
    if (searchInput) searchInput.placeholder = definicao.placeholder_busca;
}

/**
 * Atualiza a barra de modos (thumb, estado ativo e pilulas de intervalo)
 */
function atualizarBarraModos() {
    const definicao = modoAtivo();

    if (modeSwitch) {
        modeSwitch.dataset.active = currentMode;
        modeSwitch.querySelectorAll(".mode-switch__btn").forEach(btn => {
            const ativo = btn.dataset.mode === currentMode;
            btn.classList.toggle("is-active", ativo);
            btn.setAttribute("aria-selected", ativo ? "true" : "false");
        });
    }

    if (modeIntervals) {
        const intraday = currentMode === "day";
        modeIntervals.hidden = !intraday;
        modeIntervals.querySelectorAll(".interval-pill").forEach(pill => {
            pill.classList.toggle("is-active", intraday && pill.dataset.interval === currentInterval);
        });
    }

    if (modeContextLabel) {
        modeContextLabel.textContent = currentMode === "day"
            ? `Modo Day Trade â€¢ Velas ${currentInterval.toUpperCase()}`
            : definicao.contexto;
    }
}

/**
 * Universo de fallback (rotulado como SIMULADO) para o modo informado
 * Sempre parte das listas imutaveis: ASSETS_UNIVERSE pode ter sido
 * substituida pela API do modo anterior.
 */
function fallbackUniverso(modoId) {
    const base = modoId === "day" ? ASSETS_FALLBACK_DAY : ASSETS_FALLBACK_B3;
    return base.map(asset => ({ ...asset }));
}

/**
 * Troca o modo de operacao (Swing Trade / Day Trade) e recarrega os dados
 */
async function aplicarModo(modoId, intervalo) {
    const novoModo = MODES[modoId] ? modoId : MODO_PADRAO;
    const trocouDeModo = novoModo !== currentMode;

    currentMode = novoModo;
    currentInterval = novoModo === "day"
        ? (intervalo || (INTERVALOS_DAY.includes(currentInterval) ? currentInterval : MODES.day.intervalo))
        : MODES.swing.intervalo;
    currentCurrency = MODES[currentMode].moeda;

    atualizarBarraModos();
    aplicarRotulosModo(currentMode);

    // Universo local de fallback acompanha o modo
    if (trocouDeModo) {
        ASSETS_UNIVERSE = fallbackUniverso(currentMode);
        assetsSignature = "";
        lastAssetsFetch = 0;
        renderStockList();
    }

    // O universo definitivo vem da API (ou do fallback, se offline)
    await refreshBackendAssets(true);

    // O ticker selecionado pode nao existir no universo do novo modo
    const existeNoUniverso = ASSETS_UNIVERSE.some(a => a.ticker === currentSelectedTicker);
    if (!existeNoUniverso && ASSETS_UNIVERSE.length) {
        currentSelectedTicker = ASSETS_UNIVERSE[0].ticker;
    }

    await selectStock(currentSelectedTicker);
}

/**
 * Alterna o tema visual (escuro <-> claro) e repinta o grafico em Canvas
 */
function aplicarTema(tema) {
    const root = document.documentElement;
    const novoTema = tema === "light" ? "light" : "dark";

    root.setAttribute("data-theme", novoTema);

    if (themeToggle) {
        themeToggle.setAttribute("aria-pressed", novoTema === "light" ? "true" : "false");
        themeToggle.title = novoTema === "light"
            ? "Tema claro ativo. Clique para o tema escuro."
            : "Tema escuro ativo. Clique para o tema claro.";
    }

    try {
        localStorage.setItem("aguia-tema", novoTema);
    } catch (e) { /* localStorage indisponivel: o tema dura apenas a sessao */ }

    // A paleta do Canvas vem dos tokens CSS: recarrega e redesenha
    loadBrandPalette();
    lastChartSignature = "";
    const cached = cacheGet(currentSelectedTicker);
    if (cached && cached.candles) {
        renderTradingChartReal(cached.candles, cached);
    } else if (canvas && ctx) {
        // Sem dados em cache: lava o canvas com o novo fundo do tema
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        ctx.save();
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.fillStyle = brand().bgMain;
        ctx.fillRect(0, 0, rect.width, rect.height);
        ctx.restore();
    }
}

/**
 * Aplica o icone vetorial do ativo no titulo do grafico
 */
function aplicarIconeHeadline(ticker, categoria) {
    if (!chartHeadlineIcon) return;
    chartHeadlineIcon.innerHTML = getAssetIconSVG(ticker, categoria);
}

/**
 * Registra os eventos da barra de modos e do alternador de tema
 */
function setupControles() {
    if (modeSwitch) {
        modeSwitch.querySelectorAll(".mode-switch__btn").forEach(btn => {
            btn.addEventListener("click", () => {
                if (btn.dataset.mode === currentMode) return;
                aplicarModo(btn.dataset.mode);
            });
        });
    }

    if (modeIntervals) {
        modeIntervals.querySelectorAll(".interval-pill").forEach(pill => {
            pill.addEventListener("click", () => {
                if (currentMode !== "day" || pill.dataset.interval === currentInterval) return;
                currentInterval = pill.dataset.interval;
                atualizarBarraModos();
                selectStock(currentSelectedTicker);
            });
        });
    }

    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            const atual = document.documentElement.getAttribute("data-theme");
            aplicarTema(atual === "light" ? "dark" : "light");
        });
    }

    // Modal EstratÃ©gia MACRO JR
    if (btnEstrategiaConfig && macroJrModal) {
        btnEstrategiaConfig.addEventListener("click", () => macroJrModal.classList.add("active"));
    }
    const fecharMacro = () => macroJrModal && macroJrModal.classList.remove("active");
    if (macroJrClose) macroJrClose.addEventListener("click", fecharMacro);
    if (macroJrCancel) macroJrCancel.addEventListener("click", fecharMacro);
    if (macroJrBackdrop) macroJrBackdrop.addEventListener("click", fecharMacro);

    if (macroJrApply) {
        macroJrApply.addEventListener("click", async () => {
            const params = {
                InpTrendPeriod: parseInt(document.getElementById("mj-trend")?.value) || 20,
                InpFastEMAPeriod: parseInt(document.getElementById("mj-fast")?.value) || 9,
                InpSMAInstitution: parseInt(document.getElementById("mj-sma50")?.value) || 50,
                InpSMAMacro: parseInt(document.getElementById("mj-sma200")?.value) || 200,
                InpADXPeriod: parseInt(document.getElementById("mj-adx")?.value) || 14,
                InpADXMinLevel: Math.max(25.0, parseFloat(document.getElementById("mj-adxmin")?.value) || 25.0),
                InpBBPeriod: parseInt(document.getElementById("mj-bb")?.value) || 20,
                InpBBDeviation: parseFloat(document.getElementById("mj-bbdev")?.value) || 2.0,
                InpKeltnerMult: parseFloat(document.getElementById("mj-kelt")?.value) || 1.5,
            };
            if (macroJrModal) macroJrModal.classList.remove("active");
            await aplicarMacroAoAtivoAtual(params);
            macroJrAtivo = true;
            if (btnEstrategia) btnEstrategia.classList.add("active");
        });
    }

    if (btnEstrategia) {
        btnEstrategia.addEventListener("click", () => {
            if (macroJrModal) {
                macroJrModal.classList.add("active");
            }
        });
    }

    // Crosshair e tooltip flutuante do grafico
    if (canvas) {
        canvas.addEventListener("pointermove", onChartPointerMove);
        canvas.addEventListener("pointerleave", onChartPointerLeave);
        canvas.addEventListener("pointercancel", onChartPointerLeave);
    }
}

/**
 * Cache LRU: leitura promove o item e descarta o mais antigo quando cheio
 * A chave inclui modo e intervalo: o mesmo ticker em Swing Trade e em
 * Day Trade (5m) sÃ£o sÃ©ries diferentes e nÃ£o podem colidir.
 */
function cacheKey(ticker) {
    return `${currentMode}|${currentInterval}|${ticker}`;
}

function cacheGet(ticker) {
    const key = cacheKey(ticker);
    if (!chartDataCache.has(key)) return null;
    const data = chartDataCache.get(key);
    chartDataCache.delete(key);
    chartDataCache.set(key, data);
    return data;
}

function cacheSet(ticker, data) {
    const key = cacheKey(ticker);
    if (chartDataCache.has(key)) chartDataCache.delete(key);
    chartDataCache.set(key, data);
    while (chartDataCache.size > MAX_CACHE_ENTRIES) {
        chartDataCache.delete(chartDataCache.keys().next().value);
    }
}

/**
 * ConstrÃ³i o card de uma aÃ§Ã£o sem interpolar HTML (conteÃºdo do servidor)
 */
function createStockCard(asset) {
    const card = document.createElement("div");
    card.className = `stock-card-item ${asset.ticker === currentSelectedTicker ? "selected" : ""}`;
    card.dataset.ticker = asset.ticker;

    const returnVal = asset.returnPct || 0;
    const returnSign = returnVal >= 0 ? "+" : "";
    const returnClass = returnVal > 0 ? "positive" : (returnVal < 0 ? "negative" : "neutral");
    const priceFormatted = typeof asset.price === "number" ? formatarMoeda(asset.price) : (asset.price ? `R$ ${asset.price}` : "â€”");

    const left = document.createElement("div");
    left.className = "stock-card-left";

    const iconEl = document.createElement("span");
    iconEl.className = "stock-card-icon";
    iconEl.innerHTML = getAssetIconSVG(asset.ticker, asset.categoria);

    const tickerEl = document.createElement("span");
    tickerEl.className = "stock-ticker";
    tickerEl.textContent = asset.rotulo || asset.ticker;
    if (asset.rotulo && asset.rotulo !== asset.ticker) {
        tickerEl.title = asset.ticker;
    }

    const priceEl = document.createElement("span");
    priceEl.className = "stock-price";
    priceEl.textContent = priceFormatted;

    left.append(tickerEl, priceEl);

    if (asset.simulado && !asset.macroJr) {
        const simEl = document.createElement("span");
        simEl.className = "stock-simulated";
        simEl.textContent = "SIMULADO";
        simEl.title = "ReferÃªncia de demonstraÃ§Ã£o: sem dados de mercado reais";
        left.append(simEl);
    }
    if (asset.macroJr) {
        const mjEl = document.createElement("span");
        mjEl.className = "stock-simulated";
        mjEl.textContent = "MACRO JR";
        mjEl.title = "Filtrado pela EstratÃ©gia MACRO JR";
        left.append(mjEl);
    }

    const right = document.createElement("div");
    right.className = "stock-card-right";

    const badge = document.createElement("span");
    badge.className = `trend-badge ${asset.trend}`;
    badge.textContent = asset.trend === "ALTA" ? "ALTA" : (asset.trend === "BAIXA" ? "BAIXA" : asset.trend);

    if (!asset.macroJr) {
        const ret = document.createElement("span");
        ret.className = `stock-return ${returnClass}`;
        ret.textContent = `${returnSign}${returnVal.toFixed(2).replace(".", ",")}%`;
        right.append(badge, ret);
    } else {
        right.append(badge);
    }
    card.append(left, right);

    card.addEventListener("click", () => selectStock(asset.ticker));
    return card;
}

/**
 * Renderiza a lista de aÃ§Ãµes na barra lateral esquerda ('AÃ§Ãµes')
 */
function renderStockList() {
    if (!stockListContainer) return;
    const prevScroll = stockListContainer.scrollTop;
    stockListContainer.textContent = "";

    let sourceList = ASSETS_UNIVERSE;
    if (macroJrAtivo && macroJrResultados.length > 0) {
        // Mapear resultados para formato da lista
        const map = new Map(macroJrResultados.map(r => [r.ticker, r]));
        sourceList = ASSETS_UNIVERSE.filter(a => map.has(a.ticker)).map(a => {
            const r = map.get(a.ticker);
            return {
                ...a,
                trend: r.sinal_label, // ALTA ou BAIXA
                trendText: r.sinal_label === "ALTA" ? "ALTA (BULLISH)" : "BAIXA (BEARISH)",
                macroJr: true,
                sinalMacro: r.sinal_label,
            };
        });
        // Adicionar os que nÃ£o estÃ£o em ASSETS_UNIVERSE mas vieram do resultado
        const existentes = new Set(sourceList.map(x => x.ticker));
        for (const r of macroJrResultados) {
            if (!existentes.has(r.ticker)) {
                sourceList.push({
                    ticker: r.ticker,
                    rotulo: r.rotulo || r.ticker,
                    categoria: r.categoria,
                    setor: r.setor,
                    price: r.preco,
                    trend: r.sinal_label,
                    trendText: r.sinal_label === "ALTA" ? "ALTA (BULLISH)" : "BAIXA (BEARISH)",
                    returnPct: 0,
                    target: r.preco,
                    stop: r.preco,
                    payoff: "â€”",
                    dayVar: "â€”",
                    simulado: true,
                    macroJr: true,
                });
            }
        }
    }

    const needle = searchQuery.toLowerCase();
    const filtered = sourceList.filter(item => {
        const matchesSearch = item.ticker.toLowerCase().includes(needle)
            || String(item.rotulo || "").toLowerCase().includes(needle);
        if (macroJrAtivo) {
            return matchesSearch;
        }
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
 * Seleciona uma aÃ§Ã£o, aciona a API em background e atualiza dinamicamente todo o painel
 */
async function selectStock(ticker) {
    currentSelectedTicker = ticker;

    // Modo vigente no momento do pedido: uma resposta de outro modo
    // (troca disparada no meio do fetch) e descartada.
    const modoRequisicao = currentMode;
    const intervaloRequisicao = currentInterval;

    // Atualiza destaque imediato na lista lateral
    document.querySelectorAll(".stock-card-item").forEach(el => {
        el.classList.toggle("selected", el.dataset.ticker === ticker);
    });

    headlineTicker.textContent = ticker;
    aplicarIconeHeadline(ticker);

    // Se jÃ¡ temos os dados em cache de memÃ³ria recente, renderiza imediatamente
    const cached = cacheGet(ticker);
    if (cached) {
        await aplicarDadosComFade(() => {
            if (currentSelectedTicker !== ticker || modoRequisicao !== currentMode) return;
            aplicarDadosAnalise(cached);
        });
        return;
    }

    // Exibe estado de carregamento suave
    setLoadingState(true);
    metricPriceDiff.textContent = currentMode === "day" ? "Carregando intraday..." : "Carregando B3...";
    metricTargetReturn.textContent = "Calculando...";
    if (metricStopDiff) metricStopDiff.textContent = "Calculando...";
    aiReasoningText.textContent = "Consultando cotaÃ§Ãµes e calculando projeÃ§Ã£o estatÃ­stica...";

    const baseUrl = getApiBaseUrl();

    // Cancela a requisiÃ§Ã£o anterior: apenas a Ãºltima seleÃ§Ã£o Ã© relevante
    if (analysisController) analysisController.abort();
    analysisController = new AbortController();

    try {
        const params = new URLSearchParams({
            ticker: ticker,
            modo: modoRequisicao,
            intervalo: intervaloRequisicao,
        });
        const res = await fetch(`${baseUrl}/api/dados?${params.toString()}`, {
            signal: analysisController.signal,
            headers: { "Accept": "application/json" }
        });
        if (res.ok) {
            const json = await res.json();
            if (json.sucesso && json.dados) {
                const dados = json.dados;

                await aplicarDadosComFade(() => {
                    if (currentSelectedTicker !== ticker || modoRequisicao !== currentMode) return;
                    cacheSet(ticker, dados);
                    aplicarDadosAnalise(dados);

                    // Atualiza o ativo na lista local para refletir a nova cotaÃ§Ã£o
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
                });
                return;
            }
        }
        throw new Error(`Falha na resposta: HTTP ${res.status}`);
    } catch (err) {
        if (err && err.name === "AbortError") return;
        // Fallback em caso de falha de conexÃ£o: utiliza dados estÃ¡ticos locais
        const fallback = ASSETS_UNIVERSE.find(a => a.ticker === ticker) || ASSETS_UNIVERSE[0];
        await aplicarDadosComFade(() => {
            if (currentSelectedTicker !== ticker || modoRequisicao !== currentMode) return;
            aplicarDadosFallback(fallback);
        });
    } finally {
        setLoadingState(false);
    }
}

/**
 * Aplica os dados reais recebidos da API ao painel e ao grÃ¡fico
 */
function aplicarDadosAnalise(dados) {
    setLoadingState(false);

    // O servidor devolve o modo do payload: os rotulos seguem os dados,
    // nunca o estado local do botao.
    const modoPayload = MODES[dados.modo] ? dados.modo : currentMode;
    const definicao = MODES[modoPayload] || MODES[MODO_PADRAO];
    currentCurrency = dados.moeda || definicao.moeda;
    if (modoPayload !== currentMode) {
        currentMode = modoPayload;
        atualizarBarraModos();
    }
    aplicarRotulosModo(currentMode);

    headlineReturn.textContent = `(${formatarPorcentagem(dados.projecao_pct)})`;
    headlineReturn.className = dados.projecao_pct >= 0 ? "text-green" : "text-red";
    headlineTrend.textContent = dados.tendencia_texto;

    badgeTrendAction.textContent = dados.tendencia_texto;
    badgeTargetPrice.textContent = formatarMoeda(dados.alvo, currentCurrency);
    badgeTargetReturn.textContent = formatarPorcentagem(dados.projecao_pct);

    floatingTargetBadge.className = `target-floating-badge ${
        dados.tendencia === "ALTA" ? "badge-bullish" : (dados.tendencia === "BAIXA" ? "badge-bearish" : "badge-neutral")
    }`;

    metricCurrentPrice.textContent = formatarMoeda(dados.preco, currentCurrency);
    metricPriceDiff.textContent = `${dados.variacao_dia} hoje`;

    metricTargetPrice.textContent = formatarMoeda(dados.alvo, currentCurrency);
    metricTargetReturn.textContent = `${formatarPorcentagem(dados.projecao_pct)} ${definicao.rotulo_sub_alvo}`;
    metricTargetPrice.className = `quant-card-val ${dados.projecao_pct >= 0 ? "text-green" : "text-red"}`;

    metricStopLoss.textContent = formatarMoeda(dados.stop, currentCurrency);
    if (metricStopDiff) {
        metricStopDiff.textContent = `${dados.risco_pct?.toFixed(2).replace(".", ",")}% ${definicao.rotulo_sub_stop}`;
    }

    metricPayoff.textContent = dados.payoff;
    aiReasoningText.textContent = dados.resumo;
    aplicarIconeHeadline(dados.ticker || currentSelectedTicker, dados.categoria);

    if (rationaleSource) {
        rationaleSource.textContent = dados.fonte_resumo === "ollama"
            ? "Ollama Local + Ãguia Trader"
            : "Motor EstatÃ­stico Ãguia Trader";
    }
    if (complianceDisclaimer && dados.disclaimer) {
        complianceDisclaimer.textContent = dados.disclaimer;
    }
    if (dataSourceBadge) {
        dataSourceBadge.hidden = false;
    }

    // Renderiza o grÃ¡fico Canvas com candles reais
    if (dados.candles && dados.candles.length > 0) {
        renderTradingChartReal(dados.candles, dados);
    }
}

/**
 * Fallback determinÃ­stico caso o backend esteja offline
 */
function aplicarDadosFallback(asset) {
    setLoadingState(false);

    const definicao = modoAtivo();
    currentCurrency = definicao.moeda;

    const sign = asset.returnPct >= 0 ? "+" : "";
    headlineReturn.textContent = `(${sign}${asset.returnPct.toFixed(2)}%)`;
    headlineReturn.className = asset.returnPct >= 0 ? "text-green" : "text-red";
    headlineTrend.textContent = asset.trendText;

    badgeTrendAction.textContent = asset.trendText;
    badgeTargetPrice.textContent = formatarMoeda(asset.target, currentCurrency);
    badgeTargetReturn.textContent = `${sign}${asset.returnPct.toFixed(2)}%`;

    floatingTargetBadge.className = `target-floating-badge ${
        asset.trend === "ALTA" ? "badge-bullish" : (asset.trend === "BAIXA" ? "badge-bearish" : "badge-neutral")
    }`;

    metricCurrentPrice.textContent = formatarMoeda(asset.price, currentCurrency);
    metricPriceDiff.textContent = `${asset.dayVar} hoje`;

    metricTargetPrice.textContent = formatarMoeda(asset.target, currentCurrency);
    metricTargetReturn.textContent = `${sign}${asset.returnPct.toFixed(2)}% ${definicao.rotulo_sub_alvo}`;
    metricTargetPrice.className = `quant-card-val ${asset.returnPct >= 0 ? "text-green" : "text-red"}`;

    metricStopLoss.textContent = formatarMoeda(asset.stop, currentCurrency);
    if (metricStopDiff) {
        metricStopDiff.textContent = `4,67% ${definicao.rotulo_sub_stop}`;
    }
    metricPayoff.textContent = asset.payoff;

    aiReasoningText.textContent =
        `O ativo ${asset.rotulo || asset.ticker} apresenta configuraÃ§Ã£o tÃ©cnica acompanhada pelo modelo quantitativo. ` +
        `ProjeÃ§Ã£o estatÃ­stica baseada em ${definicao.horizonte} perÃ­odos com bandas de controle delimitadas pelo ATR 14.`;

    if (dataSourceBadge) {
        dataSourceBadge.hidden = false;
    }
}

/**
 * RenderizaÃ§Ã£o de Candlesticks Reais no HTML5 Canvas
 *
 * A cena e dividida em duas etapas: `renderTradingChartReal` calcula a
 * geometria (precos, margens, slots) e a guarda em `chartGeometry`;
 * `drawChartScene` desenha a cena e, por cima, o crosshair da posicao
 * do cursor. Assim o hover redesenha sem recalcular a escala.
 */
function renderTradingChartReal(candles, asset) {
    if (!canvas || !ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) return;

    const lastCandle = candles[candles.length - 1];
    const signature = `${currentMode}|${currentInterval}|${asset.ticker}|${asset.alvo}|${Math.round(rect.width)}x${Math.round(rect.height)}|${dpr}|${candles.length}|${lastCandle.close}`;
    if (signature === lastChartSignature) return;
    lastChartSignature = signature;

    const targetWidth = Math.round(rect.width * dpr);
    const targetHeight = Math.round(rect.height * dpr);
    if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
        canvas.width = targetWidth;
        canvas.height = targetHeight;
    }

    const width = rect.width;
    const height = rect.height;

    // Margens
    const marginLeft = 68;
    const marginRight = 30;
    const marginTop = 45;
    const volumeHeight = 75;
    const chartBottom = height - volumeHeight - 35;
    const chartHeight = chartBottom - marginTop;
    const plotWidth = width - marginLeft - marginRight;

    const futureSteps = modoAtivo().horizonte;
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

    chartGeometry = {
        dpr, width, height,
        marginLeft, marginRight, marginTop, volumeHeight,
        chartBottom, chartHeight, plotWidth, slotWidth, candleBarWidth,
        minPrice, maxPrice, priceToY,
        candles, asset, targetPrice, futureSteps, totalSlots,
        isBull: (asset.tendencia || asset.trend) === "ALTA",
    };

function drawMacroJrOverlay(data) {
    const g = chartGeometry;
    if (!g || !ctx || !data) return;
    const { dpr, width, height, marginLeft, plotWidth, priceToY, candles, slotWidth } = g;
    
    ctx.save();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    
    const x = marginLeft + (candles.length - 1) * slotWidth + slotWidth / 2 + 10;
    const color = data.sinal === 0 ? '#00ffa6' : (data.sinal === 1 ? '#ff3b6b' : '#ffcc4d');
    
    // Entry line
    const yEntry = priceToY(data.entry);
    ctx.strokeStyle = '#09ffff';
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(x, yEntry);
    ctx.lineTo(width - 40, yEntry);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#09ffff';
    ctx.font = "11px 'JetBrains Mono', monospace";
    ctx.textAlign = "left";
    ctx.fillText(`ENTRY ${currentCurrency} ${data.entry.toFixed(2).replace('.',',')}`, width - 38, yEntry + 4);
    
    // Stop Loss
    const ySL = priceToY(data.stop_loss);
    ctx.strokeStyle = '#ff3b6b';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x, ySL);
    ctx.lineTo(width - 40, ySL);
    ctx.stroke();
    ctx.fillStyle = '#ff3b6b';
    ctx.fillText(`SL ${currentCurrency} ${data.stop_loss.toFixed(2).replace('.',',')}`, width - 38, ySL + 4);
    
    // Take Profits
    const tps = [data.take_profit_1, data.take_profit_2, data.take_profit_3];
    const tpColors = ['#00ffa6', '#22c55e', '#34d399'];
    tps.forEach((tp, i) => {
        const yTP = priceToY(tp);
        ctx.strokeStyle = tpColors[i] || '#00ffa6';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x, yTP);
        ctx.lineTo(width - 40, yTP);
        ctx.stroke();
        ctx.fillStyle = tpColors[i] || '#00ffa6';
        ctx.fillText(`TP${i+1} ${currentCurrency} ${tp.toFixed(2).replace('.',',')}`, width - 38, yTP + 4);
    });
    
    // Bias label
    ctx.fillStyle = color;
    ctx.font = "bold 12px 'Inter', sans-serif";
    ctx.fillText(`MACRO JR | ${data.bias} | ${data.sinal_label} | ADX ${data.adx}`, marginLeft + 10, 25);
    
    ctx.restore();
}
 * e, quando existe, o crosshair da posicao do cursor.
 */
function drawChartScene() {
    const g = chartGeometry;
    if (!g || !ctx) return;

    const {
        dpr, width, height, marginLeft, marginRight, marginTop, volumeHeight,
        chartBottom, chartHeight, slotWidth, candleBarWidth, minPrice, maxPrice,
        priceToY, candles, asset, targetPrice, isBull, futureSteps, totalSlots,
    } = g;

    ctx.save();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // Fundo (tema corrente)
    ctx.fillStyle = brand().bgMain;
    ctx.fillRect(0, 0, width, height);

    // 1. Grade horizontal e eixos de preÃ§o (Y-Axis) formatados com 2 decimais
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

        ctx.fillText(`${currentCurrency} ${p.toFixed(2).replace(".", ",")}`, marginLeft - 10, y + 4);
    }

    // 2. Faixa sombreada de ProjeÃ§Ã£o
    const projStartX = marginLeft + candles.length * slotWidth;
    const projWidth = futureSteps * slotWidth;

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

    // Linha vertical divisÃ³ria da projeÃ§Ã£o
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

        // RÃ³tulos de datas no eixo X (a cada 12 candles)
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

    // 6. ProjeÃ§Ã£o Tracejada atÃ© o Alvo
    const lastX = marginLeft + (candles.length - 1) * slotWidth + slotWidth / 2;
    const lastPriceY = priceToY(candles[candles.length - 1].close);
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
    ctx.fillText(`Alvo: ${currentCurrency} ${targetPrice.toFixed(2).replace(".", ",")}`, targetX - 95, targetY - 10);

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

    // 8. Crosshair (eixos X e Y) na vela sob o cursor
    drawCrosshair(g);

    ctx.restore();
}

/**
 * Desenha o crosshair: linha vertical na vela e linha horizontal no
 * preÃ§o de fechamento, com o rÃ³tulo do preÃ§o no eixo.
 */
function drawCrosshair(g) {
    if (chartHoverIndex === null) return;
    const candle = g.candles[chartHoverIndex];
    if (!candle) return;

    const x = g.marginLeft + chartHoverIndex * g.slotWidth + g.slotWidth / 2;
    const y = g.priceToY(candle.close);

    ctx.save();
    ctx.setLineDash([3, 3]);
    ctx.lineWidth = 1;
    ctx.strokeStyle = brand().cyan;

    ctx.beginPath();
    ctx.moveTo(x, g.marginTop);
    ctx.lineTo(x, g.chartBottom);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(g.marginLeft, y);
    ctx.lineTo(g.width - g.marginRight, y);
    ctx.stroke();

    ctx.setLineDash([]);

    // Marcador no fechamento da vela
    ctx.fillStyle = candle.close >= candle.open ? brand().up : brand().down;
    ctx.beginPath();
    ctx.arc(x, y, 3.4, 0, Math.PI * 2);
    ctx.fill();

    // RÃ³tulo do preÃ§o no eixo Y
    const label = `${currentCurrency} ${candle.close.toFixed(2).replace(".", ",")}`;
    ctx.font = "10px 'JetBrains Mono', monospace";
    const labelWidth = ctx.measureText(label).width + 10;
    ctx.fillStyle = brand().cyan;
    ctx.fillRect(g.width - g.marginRight, y - 8, labelWidth, 16);
    ctx.fillStyle = brand().bgMain;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(label, g.width - g.marginRight + 5, y);
    ctx.textBaseline = "alphabetic";

    ctx.restore();
}

/**
 * Formata a data/hora da vela conforme o modo ativo
 */
function formatarDataVela(dateStr) {
    if (!dateStr) return "â€”";
    const texto = String(dateStr);
    const [data, hora] = texto.split("T");
    const dataBr = data.split("-").reverse().join("/");
    if (!hora) return dataBr;
    const horaCurta = hora.slice(0, 5);
    return currentMode === "day" ? `${dataBr} ${horaCurta}` : dataBr;
}

/**
 * Formata o preÃ§o de uma vela na moeda do modo ativo
 */
function formatarPrecoVela(valor) {
    if (valor === null || valor === undefined || isNaN(valor)) return "â€”";
    return `${currentCurrency} ${Number(valor).toFixed(2).replace(".", ",")}`;
}

/**
 * Atualiza o tooltip flutuante com os dados da vela sob o cursor
 */
function updateChartTooltip(index, g, cursorX, cursorY) {
    const candle = g.candles[index];
    if (!candle || !chartTooltip) return;

    const variacao = candle.open ? ((candle.close - candle.open) / candle.open) * 100 : 0;

    if (chartTooltipDate) chartTooltipDate.textContent = formatarDataVela(candle.date);
    if (chartTooltipOpen) chartTooltipOpen.textContent = formatarPrecoVela(candle.open);
    if (chartTooltipHigh) chartTooltipHigh.textContent = formatarPrecoVela(candle.high);
    if (chartTooltipLow) chartTooltipLow.textContent = formatarPrecoVela(candle.low);
    if (chartTooltipClose) chartTooltipClose.textContent = formatarPrecoVela(candle.close);
    if (chartTooltipVolume) chartTooltipVolume.textContent = Number(candle.volume || 0).toLocaleString("pt-BR");

    if (chartTooltipChange) {
        const sinal = variacao >= 0 ? "+" : "";
        chartTooltipChange.textContent = `${sinal}${variacao.toFixed(2)}%`;
        chartTooltipChange.className = `chart-tooltip__value ${variacao >= 0 ? "text-green" : "text-red"}`;
    }

    chartTooltip.hidden = false;

    const stage = canvas.parentElement;
    const stageW = stage ? stage.clientWidth : g.width;
    const stageH = stage ? stage.clientHeight : g.height;
    const tipW = chartTooltip.offsetWidth || 190;
    const tipH = chartTooltip.offsetHeight || 150;

    let left = cursorX + 20;
    if (left + tipW > stageW - 8) left = cursorX - tipW - 20;
    left = Math.max(8, Math.min(left, stageW - tipW - 8));

    let top = cursorY - tipH / 2;
    top = Math.max(8, Math.min(top, stageH - tipH - 8));

    chartTooltip.style.left = `${left}px`;
    chartTooltip.style.top = `${top}px`;
}

/**
 * Esconde o tooltip flutuante
 */
function hideChartTooltip() {
    if (chartTooltip) chartTooltip.hidden = true;
}

/**
 * Rastreia o cursor sobre o canvas: define a vela ativa, redesenha o
 * crosshair e move o tooltip.
 */
function onChartPointerMove(event) {
    const g = chartGeometry;
    if (!g || !canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const dentro = x >= g.marginLeft - 8 && x <= g.width - g.marginRight + 8
        && y >= g.marginTop - 12 && y <= g.chartBottom + 12;

    if (!dentro) {
        onChartPointerLeave();
        return;
    }

    const index = Math.max(0, Math.min(g.candles.length - 1, Math.floor((x - g.marginLeft) / g.slotWidth)));

    if (index !== chartHoverIndex) {
        chartHoverIndex = index;
        drawChartScene();
    }

    updateChartTooltip(index, g, x, y);
}

/**
 * Saida do cursor: remove o crosshair e o tooltip
 */
function onChartPointerLeave() {
    if (chartHoverIndex === null) return;
    chartHoverIndex = null;
    hideChartTooltip();
    drawChartScene();
}

/**
 * Desenha uma curva de mÃ©dia mÃ³vel contÃ­nua (ignora valores ausentes)
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

/**
 * ConexÃ£o e sincronizaÃ§Ã£o inicial com backend Python 3.11
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
            connText.textContent = "Servidor Ativo e Online";
            connIndicator.title = `Conectado ao Ãguia Trader (Python ${data.python_version}) - Ollama: ${data.ollama?.online ? "Ativo (" + data.ollama.modelo + ")" : "Offline (Modo DeterminÃ­stico)"}`;

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
        connText.textContent = "Offline (Local)";
        connIndicator.title = "Servidor Python 3.11 nÃ£o detectado. Clique para reconectar.";
        return false;
    }
}

/**
 * Busca a lista de aÃ§Ãµes do backend Python (/api/acoes)
 * SÃ³ re-renderiza a lista quando os dados realmente mudaram.
 */
async function refreshBackendAssets(force = false) {
    const now = Date.now();
    if (!force && now - lastAssetsFetch < ASSETS_REFRESH_MS) return;
    lastAssetsFetch = now;

    const modo = currentMode;

    try {
        const res = await fetch(`${getApiBaseUrl()}/api/acoes?modo=${modo}`, {
            headers: { "Accept": "application/json" }
        });
        if (!res.ok) return;
        const json = await res.json();
        const list = json.dados || json.assets;
        if (!list || !list.length) return;

        // Resposta de outro modo (troca disparada durante o fetch): ignora
        if (modo !== currentMode) return;

        const signature = list
            .map(a => `${a.ticker}:${a.price}:${a.trend}:${a.returnPct}:${a.asof}`)
            .join("|");
        if (signature === assetsSignature) return;

        assetsSignature = signature;
        ASSETS_UNIVERSE = list;
        renderStockList();
    } catch {
        // MantÃ©m lista local em fallback silencioso
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
        const cached = cacheGet(currentSelectedTicker);
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

// Suspende o polling quando a aba estÃ¡ oculta
document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
        testPythonBackend();
        refreshBackendAssets(true);
    }
});

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
        if (splash && splash.parentNode) splash.parentNode.removeChild(splash);
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
    }

    renderStockList();
    setupControles();
    atualizarBarraModos();
    aplicarRotulosModo(currentMode);
    if (themeToggle) {
        themeToggle.setAttribute(
            "aria-pressed",
            document.documentElement.getAttribute("data-theme") === "light" ? "true" : "false"
        );
    }
    testPythonBackend();
    selectStock("PETR4");

    // SincronizaÃ§Ã£o periÃ³dica suave de status
    setInterval(() => {
        if (!document.hidden) testPythonBackend();
    }, STATUS_POLL_MS);
});

