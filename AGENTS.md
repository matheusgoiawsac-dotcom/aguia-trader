# Águia Trader — agent rules

Local web dashboard with B3 (Brazil) swing-trade and day-trade ideas.
Python 3.11 backend on stdlib `http.server` + vanilla HTML/CSS/JS with Canvas. Free tools only.

## Commands (Windows, PowerShell)
- Setup: `setup.bat` (creates `.venv`, installs requirements, clones Kronos into `vendor/Kronos`)
- Run: `iniciar_servidor.bat` or `python app.py [--host H] [--port P]` -> http://127.0.0.1:8000
- Refresh data + forecasts: `python -m aguia.jobs.refresh --tf 1d [--tickers PETR4,VALE3]` (or `atualizar_dados.bat`)
- Tests: `pytest -q` (live-network tests: `pytest -m network`)

## Layout
- `app.py` thin entrypoint; code lives in `aguia/` (`config`, `db`, `calendar_b3`, `indicators`, `modes`, `icons`, `server/`, `providers/`, `forecast/`, `explain/`, `charts/`, `jobs/`)
- `config/` (`config.toml`, `universe.json`, `b3_holidays.json`), `static/` (the only directory served), `tests/`
- `vendor/Kronos/` pinned clone of github.com/shiyu-coder/Kronos (gitignored); `data/` SQLite + PNG cache (gitignored)
- Trading modes live in `aguia/modes.py` (single source of truth); `static/script.js` keeps a mirrored `MODES` registry and `tests/test_modes.py` asserts both stay in sync.
- Asset classification (icon factory) lives in `aguia/icons.py`; `static/script.js` mirrors it in `ICON_CRYPTO_MAP`, `ICON_FOREX_MAP`, `ICON_COMMODITY_MAP`, `ICON_INDEX_MAP` and `ICON_B3_SECTORS`, and `tests/test_icons.py` asserts both stay in sync.

## Invariants (never violate)
- Free stack only: no paid APIs, no API keys, no accounts, no secrets in the repo.
- No web framework, no Node/npm, no CDN scripts. Frontend stays vanilla JS + Canvas.
- Never fabricate market data outside tests and the labeled demo fixture ("SIMULADO").
- Never place or simulate orders. MT5, if ever added, is read-only market data.
- Never present output as investment advice; keep the pt-BR disclaimer on every analysis. No imperative buy/sell wording in generated text.
- Server binds to 127.0.0.1 and serves only `static/`. CORS allowlist: localhost / 127.0.0.1 on port 8000.
- UI, README and analysis text: pt-BR (numbers like `R$ 13,27`). Code, comments, commits, tests: English.
- Keep the current visual identity (dark theme, colors, eagle badge, layout).
- Icon colors come from CSS tokens only (`--icon-*`); the chart stays native Canvas (crosshair and tooltip included).
- Work only inside this directory; no destructive commands; move instead of delete.

## Gotchas
- Yahoo symbols: `PETR4.SA`. Recent yfinance can return MultiIndex columns even for one ticker; normalize. Use `auto_adjust=True`. Throttle to <= 2 req/s and retry with backoff on 429.
- Yahoo intraday history is short: 1m about 7 days, 5m to 90m about 60 days. Clamp ranges and log a warning.
- Drop the in-progress candle before any analysis.
- Kronos: `max_context` is 512 for small/base. `sample_count` averages paths, so use `sample_count=1` repeated N times to get percentiles. Verify signatures in `vendor/Kronos/model/` before use.
- Indicators: SMA200 and WMA30 are NaN until enough candles exist (never shrink the window). ATR14 uses Wilder smoothing.
- Matplotlib: set the `Agg` backend before importing pyplot and guard plotting with a global lock.
- Ollama output is never trusted: every number in generated text must exist in the facts JSON, otherwise use the deterministic template.
- Fonts: `index.html` imports Inter (400/500/600/700) and JetBrains Mono (500/700) from Google Fonts. Any new `font-weight` in `style.css` must be added to that import, or the browser silently falls back.
- The icon factory glyphs are 22x22 SVG in `static/script.js`; the palette lives in `config/brand_palette.json` and the `--icon-*` tokens (`tests/test_brand_palette.py` blocks colors outside the `:root` block).
