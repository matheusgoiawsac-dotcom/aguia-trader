# Águia Trader — Dashboard & Trade Ideas B3

Plataforma quantitativa de análise de dados e projeções estatísticas para ações da B3 (Brasil), baseada no modelo **SMA 200 + WMA 30 + ATR 14 + Kronos + Ollama Local**. Construída sobre Python 3.11 nativo e front-end responsivo em HTML5 Canvas vanilla no padrão *Dark Mode* de plataformas financeiras de elite.

> **Aviso de Isenção (Compliance)**:
> Análise experimental gerada por modelo estatístico. Não constitui recomendação de investimento. Sem backtest validado. As projeções refletem exclusivamente probabilidades numéricas e não garantem retornos futuros.

---

## 🦅 Arquitetura do Sistema

```text
Águia Trader/
├── app.py                      # Ponto de entrada fino (servidor ThreadingHTTPServer)
├── config/                     # Configurações TOML, universo de 18 ativos B3 e feriados B3
│   ├── config.toml
│   ├── universe.json
│   ├── b3_holidays.json
│   └── brand_palette.json       # Paleta da marca (fonte única de verdade do design system)
├── aguia/
│   ├── config.py               # Leitor stdlib tomllib + helpers de timeframe
│   ├── brand.py                # Carregador dos tokens de marca (config/brand_palette.json)
│   ├── modes.py                # Registro de modos (Swing Trade / Day Trade) e catálogo da API
│   ├── db.py                   # SQLite WAL, pool por thread e upserts idempotentes
│   ├── calendar_b3.py          # Calendário e horários oficiais da bolsa B3
│   ├── indicators.py           # Cálculos numéricos de SMA 200, WMA 30 e ATR 14 (Wilder)
│   ├── providers/
│   │   └── yfinance_provider.py# Provedor B3 via Yahoo Finance (rate-limit, multi-index, filtros)
│   ├── forecast/
│   │   ├── kronos_engine.py    # Motor Kronos Time-Series Foundation Model e FakePredictor
│   │   └── signals.py          # Classificador estatístico de setups (ALTA, BAIXA, NEUTRO)
│   ├── explain/
│   │   ├── ollama.py           # Cliente Ollama local (timeout curto, cache, circuit breaker)
│   │   └── validator.py        # Validador numérico estrito anti-alucinação para IA (tolerância 0.5%)
│   ├── charts/
│   │   └── png_export.py       # Exportação headless de gráficos via mplfinance (lock global)
│   ├── server/
│   │   ├── handler.py          # Handler HTTP seguro (sandbox 127.0.0.1, static-only, CORS)
│   │   └── routes.py           # Rotas REST (/api/acoes, /api/dados, /api/modos, /api/status_ollama)
│   └── jobs/
│       └── refresh.py          # CLI de atualização e sincronização de dados B3
├── static/                     # Interface Web Vanilla (HTML5, CSS3, Canvas, JS)
│   ├── index.html
│   ├── style.css               # Design system em :root (tokens) + tema claro + componentes
│   ├── script.js               # Dashboard + gráfico Canvas (lê os tokens do CSS)
│   ├── logo.webp / logo.png    # Logotipo otimizado (256px)
│   ├── favicon.png             # Favicon 64px
│   └── components/             # Componentes visuais reutilizáveis
│       ├── logo-hero.css       # Camadas neon/elétricas do logo (CSS puro)
│       ├── logo-hero.fragment.html # Markup canônico do componente logo-hero
│       └── logo-hero.html      # Preview isolada: /components/logo-hero.html
└── tests/                      # Suite com 176 testes automatizados (pytest)
    ├── conftest.py             # Marcadores de rede e fixtures compartilhadas
    ├── test_brand_palette.py   # Paridade do design system (JSON <-> CSS <-> SVG <-> Python)
    ├── test_splash_choreography.py # Coreografia da splash e da revelação do app
    ├── test_logo_hero.py       # Contrato do componente logo-hero (markup, CSS, performance)
    ├── test_ui_polish.py       # Contrato do refinamento visual (vidro, fade, scrollbar, tabular)
    ├── test_modes.py           # Contrato dos modos (registro do backend <-> espelho do front-end)
    └── fixtures/
        └── demo_analysis.json  # Fixture de demonstração rotulada como SIMULADO
```

> Os módulos também aceitam a configuração de `config/config.toml` como fonte única de
> verdade (janela do Yahoo Finance por timeframe, origens CORS, cache estático, etc).

---

## 🎨 Design System da Marca

A identidade visual deriva do logo **ÁGUIA TRADER Cibernética** (azul elétrico + ciano +
teal neon sobre preto). A paleta vive em **`config/brand_palette.json`** e é espelhada por:

| Camada | Onde a paleta é consumida |
| :--- | :--- |
| Tokens CSS | `:root` em `static/style.css` — **nenhuma cor hardcoded fora do bloco de tokens** |
| Dashboard | `static/index.html` + `static/style.css` (componentes, estados, animações) |
| Gráfico Canvas | `static/script.js` lê os tokens via `getComputedStyle` em runtime |
| Gráfico PNG | `aguia/charts/png_export.py` lê a paleta via `aguia/brand.py` |
| Emblema SVG | Sprite `#eagle-mark` em `static/index.html`, apenas com cores da paleta |

**Regras do sistema**

- Superfícies derivam do preto/azul-marinho do logo (`--bg-main`, `--bg-card`, ...).
- Acentos usam a rampa `--brand-blue` → `--brand-cyan` → `--brand-teal`.
- Semântica: **Alta = teal da marca** (`--color-green`), **Baixa = coral neon** (`--color-red`),
  **SMA 200 = azul**, **WMA 30 = âmbar**.
- Variações translúcidas usam `color-mix(in srgb, var(--token) N%, transparent)`.
- `tests/test_brand_palette.py` garante que as quatro representações nunca divirjam.

### Componente `logo-hero` (camadas neon/elétricas)

O logo da marca é reutilizado como base de um componente **CSS + SVG puro** (sem imagem
extra, sem CDN, sem JS). Ele já veste a splash e pode ser reaproveitado em qualquer
tela.

| Arquivo | Papel |
| :--- | :--- |
| `static/components/logo-hero.fragment.html` | Markup canônico (fonte única de verdade) |
| `static/components/logo-hero.css` | Estilos, camadas e keyframes do componente |
| `static/components/logo-hero.html` | Preview isolada em `/components/logo-hero.html` |

**Camadas** (PNG na base, efeitos por cima): `__base` (z1) → `__aura` (z2) →
`__fx` (z3). O overlay SVG desenha o anel sensor com arco viajante, circuitos
internos, o olho com luminescência, candles ascendentes e faíscas elétricas,
com a geometria medida sobre o artwork real de 256×256.

**Performance**: só `opacity`, `transform` e `stroke-dashoffset` são animados.
`filter`/`box-shadow` são estáticos e o brilho que acompanha o movimento do arco
é feito com traço duplicado (glow largo + núcleo fino), evitando re-rasterização
por quadro. O componente usa `contain: layout style` + `isolation: isolate` e
respeita `prefers-reduced-motion: reduce`.

`tests/test_logo_hero.py` garante que a cópia do markup na splash nunca diverge do
fragmento canônico, que nenhuma animação usa propriedades custosas e que todas as
cores vêm da paleta da marca.

### Refinamento visual (estilo terminal / TradingView Pro)

| Recurso | Onde |
| :--- | :--- |
| Glassmorphism com borda em gradiente | Cards de métricas (`.quant-card`) e bloco de Resumo (`.reasoning-card`) |
| Brilho ciano no hover | `rgba(0, 240, 255, 0.15)` calculado via token `--glow-cyan-hover` (sem cor hardcoded) |
| Transições suaves | Lista lateral de ações (`.stock-card-item`) e filtros (`.filter-pill`): `transition: all 0.25s ease-in-out` |
| Fade fluido entre ativos | `.data-swap-out` / `.data-swap-in` + `aplicarDadosComFade()` em `static/script.js` |
| Pulsação de status | `.connection-indicator.online .conn-dot::after` com `@keyframes connPing` |
| Scrollbar ultrafina | Tokens `--scrollbar-*` + `scrollbar-width`/`scrollbar-color` e fallback `::-webkit-scrollbar` |
| Alinhamento numérico | `font-variant-numeric: tabular-nums` no `body` e nos elementos de preço/variação |
| Status do servidor | `Servidor Ativo e Online` no cabeçalho, com pulso ciano quando a API responde |

`tests/test_ui_polish.py` garante que nenhum desses efeitos seja perdido em
refatorações futuras.

### Tipografia (Inter + JetBrains Mono)

Duas famílias,each uma com um papel:

| Família | Papel | Pesos |
| :--- | :--- | :--- |
| **Inter** | Interface: títulos, rótulos, botões, textos | 400, 500, 600, 700 |
| **JetBrains Mono** | Todos os números: preços, variações, alvos, stop, payoff, tooltip | 500, 700 |

A divisão é estrutural: qualquer valor numérico usa `var(--font-mono)` com
`font-variant-numeric: tabular-nums`, então as casas decimais não "dançam" quando
o preço muda. `tests/test_icons.py` garante que nenhuma regra peça um peso que a
importação do Google Fonts não provide.

### Tema claro (Light Cyber / Slate Clean)

O dashboard alterna entre o tema **escuro** (padrão) e um tema **claro** pelo
botão Lua/Sol no cabeçalho. A escolha é gravada em `localStorage` (`aguia-tema`) e
aplicada antes da primeira pintura, evitando qualquer *flash* de tema.

| Peça | Como funciona |
| :--- | :--- |
| Tokens | O tema claro é um override de `:root[data-theme="light"]`: nenhuma cor hardcoded fora do bloco de tokens |
| Superfícies | Tokens de filete, chip e texto sobre fundo neutro (`--hairline`, `--surface-chip`, `--text-on-surface`) trocam de valor entre os temas |
| Gráfico Canvas | O JS relê os tokens via `getComputedStyle` e redesenha o canvas ao trocar de tema |
| Splash | Herda os tokens: a tela de carregamento acompanha o tema ativo |

### Modos de operação (Swing Trade / Day Trade)

A barra de modos acima do layout alterna entre dois universos e horizontes de
análise. O registro vive em **`aguia/modes.py`** (fonte única de verdade) e é
espelhado no front-end (`MODES` em `static/script.js`).

| Modo | Universo | Vela | Horizonte | Moeda | Foco |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **Swing Trade** | 18 ativos da B3 | Diária (`1d`) | 14 períodos | `R$` | Continuidade de tendência |
| **Day Trade** | `SPY`, `DIA`, `GC=F`, `BTC-USD` | Intraday (`5m`, `15m`, `1h`) | 12 períodos | `US$` | Rompimentos e volatilidade |

Trocar de modo realinha universe, rótulos dos cards (alvo, stop, payoff), legenda
do gráfico, moeda, projeção do canvas e o texto de **Dicas Operacionais** — todos
derivam do mesmo registro, então interface e backend nunca discordam.
`tests/test_modes.py` garante que o espelho do front-end nunca divirja do backend.

### Fábrica de ícones Cyber/Neon (SVG)

Cada ativo recebe um **ícone vetorial de 22×22 px**, desenhado em runtime: nada
de emoji do sistema, nada de imagem externa, nada de CDN. O backend classifica o
ticker e publica `categoria` + `setor` em cada payload (`/api/acoes`, `/api/dados`);
o front-end escolhe o glifo e o pinta com tokens CSS, então o ícone acompanha o
tema e o halo neon vive em um único token (`--icon-glow`).

| Família | Glifos | Cor (token) |
| :--- | :--- | :--- |
| Cripto | `btc`, `eth`, `sol`, `usdt`, `usdc`, `bnb`, `xrp`, `ada`, `doge`, `avax` | laranja, roxo, verde, ciano, ouro |
| Forex | `usd`, `brl`, `eur`, `gbp` | ciano |
| Commodity | `gold`, `silver`, `copper`, `oil`, `corn`, `soy` | ouro, prata |
| Índice | `indexChart`, `indexBars`, `indexArrow`, `indexIbovespa` | ciano |
| Setores B3 | `bank`, `energy`, `mining`, `retail`, `health` | ciano, laranja, ouro, verde, roxo |
| Universal | iniciais do ticker em `JetBrains Mono` sobre disco ciano | ciano |

O registro vive em **`aguia/icons.py`** (fonte única de verdade) e é espelhado no
front-end (`ICON_CRYPTO_MAP`, `ICON_FOREX_MAP`, `ICON_COMMODITY_MAP`,
`ICON_INDEX_MAP`, `ICON_B3_SECTORS` em `static/script.js`).
`tests/test_icons.py` garante que backend e front-end nunca divirjam, que todo
glifo referenciado existe e que toda cor vem de token declarado.

### Gráfico interativo (crosshair + tooltip)

O canvas ganhou leitura de valores por cursor, sem biblioteca externa:

| Recurso | Como funciona |
| :--- | :--- |
| Crosshair | `drawCrosshair(g)` desenha as linhas de preço e de tempo sobre o último ponto |
| Tooltip OHLCV | `updateChartTooltip(index, g, cursorX, cursorY)` mostra data, abertura, máxima, mínima, fechamento, variação e volume |
| Posicionamento | O tooltip segue o cursor e se inverte quando encosta na borda do gráfico |
| Saída do cursor | `onChartPointerLeave()` remove o crosshair e esconde o tooltip |
| Estilo | Vidro com `backdrop-filter: blur()`, tipografia mono nos números |

---

## ⚡ Comandos Rápidos (Windows / PowerShell)

### 1. Iniciar o Servidor
```powershell
.\iniciar_servidor.bat
# Ou diretamente:
.\.venv\Scripts\python.exe app.py
# Porta/host alternativos (o padrão vem de config/config.toml):
.\.venv\Scripts\python.exe app.py --port 8080
```
Acesse no navegador: **`http://127.0.0.1:8000`**

### 2. Atualizar Dados de Mercado B3
```powershell
.\atualizar_dados.bat
# Ou via CLI com parâmetros:
.\.venv\Scripts\python.exe -m aguia.jobs.refresh --tf 1d --tickers PETR4,VALE3,ITUB4
```

### 3. Executar Testes Automatizados
```powershell
.\.venv\Scripts\python.exe -m pytest -q
# Somente os testes que exigem rede externa (Yahoo Finance):
.\.venv\Scripts\python.exe -m pytest -q -m network
```
*(176 testes cobrem indicadores, segurança de servidor, banco SQLite WAL, integração de dados, IA, coreografia da splash, o componente visual `logo-hero`, o refinamento visual do dashboard e o contrato dos modos de operação. Testes de rede são ignorados automaticamente quando a rede externa está indisponível).*

---

## 📊 Endpoints REST Disponíveis

| Endpoint | Método | Descrição | Envelope de Resposta |
| :--- | :---: | :--- | :--- |
| `/api/status` | `GET` | Status operacional do servidor, versão Python e IA | JSON padrão |
| `/api/status_ollama` | `GET` | Probe de conectividade do Ollama local (`11434`) | `{"sucesso": bool, "dados": ...}` |
| `/api/modos` | `GET` | Catálogo dos modos (rótulos, horizontes, universos, intervalos) | `{"sucesso": true, "dados": {...}}` |
| `/api/acoes?modo=swing\|day` | `GET` | Universo monitorado do modo (B3 ou ativos globais) | `{"sucesso": true, "assets": [...]}` |
| `/api/dados?ticker=PETR4&modo=swing&intervalo=1d` | `GET` | Dados em tempo real, candles OHLCV, projeção e dicas operacionais | `{"sucesso": true, "dados": {...}}` |
| `/api/analise?ticker=PETR4` | `GET` | Atalho retrocompatível para `/api/dados` no modo Swing Trade | `{"sucesso": true, "dados": {...}}` |
| `/api/chart.png?ticker=PETR4`| `GET` | Renderização headless PNG do gráfico de candlesticks | `image/png` binário |

---

## 🛡️ Invariantes de Segurança e Confiabilidade

1. **Stack 100% Gratuita**: Nenhuma chave de API paga, contas de terceiros ou credenciais requeridas.
2. **Isolamento de Rede Local**: O servidor escuta estritamente em `127.0.0.1:8000` e rejeita qualquer tentativa de travessia de diretório (`Path Traversal`).
3. **Resiliência a Falhas (Fallback Determinístico)**: Caso o Ollama esteja offline, o sistema gera instantaneamente uma análise técnica baseada na convergência entre as médias e volatilidade ATR 14.
4. **Validação Anti-Alucinação**: Qualquer número emitido pela IA que divirja em mais de 0,5% dos fatos estatísticos calculados é descartado e substituído pelo racional determinístico.
5. **Compatibilidade com Electron**: Código JavaScript desacoplado, sem frameworks externos ou bundlers, pronto para empacotamento via Electron ou uso em navegador.

---

## ⚡ Desempenho e Uso de Recursos

| Camada | Técnica |
| :--- | :--- |
| Servidor | HTTP/1.1 com *keep-alive*, `gzip`, `ETag`/`304` e cache em memória dos arquivos estáticos |
| Banco | Pool de conexões SQLite por thread, DDL executado uma única vez, índice redundante removido, consultas em `JOIN` único (sem N+1) |
| APIs | Cache de payload de análise (60s), cache de status do Ollama (5s) e *circuit breaker* de 30s quando o daemon está fora do ar |
| Indicadores | WMA 30 e ATR 14 vetorizados em NumPy (sem callback Python por linha) |
| Front-end | Logotipo de 1,6 MB para 12 KB (WebP), fontes não bloqueantes, cache LRU do payload, *debounce* de busca e cancelamento de requisições obsoletas |
| Componente `logo-hero` | Camadas neon em CSS/SVG puro: só `opacity`/`transform`/`stroke-dashoffset` animados, `filter` estático, brilho por traço duplicado, `contain: layout style` e `prefers-reduced-motion` |
| Interface | Fade de troca de ativo com `opacity`/`transform` (sem repaint de layout), status pulsante em `opacity`/`transform`, borda de gradiente em vez de `border-width` animável |
| Dados | Janela do Yahoo Finance definida em `config.toml` e limitada para intervalos intradiários |
