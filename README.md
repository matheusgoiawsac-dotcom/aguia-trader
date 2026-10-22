# Águia Trader — Dashboard & Trade Ideas B3

Plataforma quantitativa de análise de dados e projeções estatísticas para ações da B3 (Brasil), baseada no modelo **SMA 200 + WMA 30 + ATR 14 + Kronos + Ollama Local**. Construída sobre Python 3.11 nativo e front-end responsivo em HTML5 Canvas vanilla no padrão *Dark Mode* de plataformas financeiras de elite.

> **Aviso de Isenção (Compliance)**:
> Análise experimental gerada por modelo estatístico. Não constitui recomendação de investimento. Sem backtest validado. As projeções refletem exclusivamente probabilidades numéricas e não garantem retornos futuros.

---

## 🦅 Arquitetura do Sistema

```text
Águia Trader/
├── app.py                      # Ponto de entrada fino (< 40 linhas, servidor ThreadingHTTPServer)
├── config/                     # Configurações TOML, universo de 18 ativos B3 e feriados B3
├── aguia/
│   ├── config.py               # Leitor stdlib tomllib
│   ├── db.py                   # Banco de dados SQLite WAL e upserts idempotentes
│   ├── calendar_b3.py          # Calendário e horários oficiais da bolsa B3
│   ├── indicators.py           # Cálculos numéricos de SMA 200, WMA 30 e ATR 14 (Wilder)
│   ├── providers/
│   │   └── yfinance_provider.py# Provedor B3 via Yahoo Finance (rate-limit, multi-index, filtros)
│   ├── forecast/
│   │   ├── kronos_engine.py    # Motor Kronos Time-Series Foundation Model e FakePredictor
│   │   └── signals.py          # Classificador estatístico de setups (ALTA, BAIXA, NEUTRO)
│   ├── explain/
│   │   └── validator.py        # Validador numérico estrito anti-alucinação para IA (tolerância 0.5%)
│   ├── charts/
│   │   └── png_export.py       # Exportação headless de gráficos via mplfinance (lock global)
│   ├── server/
│   │   ├── handler.py          # Handler HTTP seguro (sandbox 127.0.0.1, static-only, CORS)
│   │   └── routes.py           # Rotas REST (/api/acoes, /api/analise, /api/status_ollama, etc.)
│   └── jobs/
│       └── refresh.py          # CLI de atualização e sincronização de dados B3
├── integracao_ollama.py        # Integração HTTP com Ollama local e fallback determinístico
├── static/                     # Interface Web Vanilla (HTML5, CSS3, Canvas, JS)
│   ├── index.html
│   ├── style.css
│   └── script.js
└── tests/                      # Suite com 42 testes automatizados (pytest)
```

---

## ⚡ Comandos Rápidos (Windows / PowerShell)

### 1. Iniciar o Servidor
```powershell
.\iniciar_servidor.bat
# Ou diretamente:
.\.venv\Scripts\python.exe app.py
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
```
*(Todos os 42 testes cobrem indicadores, segurança de servidor, banco SQLite WAL, integração de dados e IA).*

---

## 📊 Endpoints REST Disponíveis

| Endpoint | Método | Descrição | Envelope de Resposta |
| :--- | :---: | :--- | :--- |
| `/api/status` | `GET` | Status operacional do servidor, versão Python e IA | JSON padrão |
| `/api/status_ollama` | `GET` | Probe de conectividade do Ollama local (`11434`) | `{"sucesso": bool, "dados": ...}` |
| `/api/acoes` | `GET` | Universo completo de 18 ativos monitorados da B3 | `{"sucesso": true, "assets": [...]}` |
| `/api/analise?ticker=PETR4` | `GET` | Dados em tempo real, 65 candles OHLCV, projeção e resumo | `{"sucesso": true, "dados": {...}}` |
| `/api/chart.png?ticker=PETR4`| `GET` | Renderização headless PNG do gráfico de candlesticks | `image/png` binário |

---

## 🛡️ Invariantes de Segurança e Confiabilidade

1. **Stack 100% Gratuita**: Nenhuma chave de API paga, contas de terceiros ou credenciais requeridas.
2. **Isolamento de Rede Local**: O servidor escuta estritamente em `127.0.0.1:8000` e rejeita qualquer tentativa de travessia de diretório (`Path Traversal`).
3. **Resiliência a Falhas (Fallback Determinístico)**: Caso o Ollama esteja offline, o sistema gera instantaneamente uma análise técnica baseada na convergência entre as médias e volatilidade ATR 14.
4. **Validação Anti-Alucinação**: Qualquer número emitido pela IA que divirja em mais de 0,5% dos fatos estatísticos calculados é descartado e substituído pelo racional determinístico.
5. **Compatibilidade com Electron**: Código JavaScript desacoplado, sem frameworks externos ou bundlers, pronto para empacotamento via Electron ou uso em navegador.
