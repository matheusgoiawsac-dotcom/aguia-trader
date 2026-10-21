# Águia Trader - Dashboard & Trade Ideas B3

Plataforma quantitativa de análise técnica e ideias de trade baseada no modelo estatístico **SMA 200 + WMA 30 + ATR 14 + IA Local**, com design de alta fidelidade visual, tela escura (*dark mode*), gráfico de candlesticks com projeção futura de 14 períodos e seleção interativa do universo de ações da B3.

---

## 🎨 Características Visuais e Funcionais

1. **Cabeçalho Principal**:
   - Identidade visual **Águia Trader**.
   - Badge de versão `Fase 3 • Normalizado`.
   - Subtítulo técnico: `Motor estatístico SMA 200 + WMA 30 + ATR 14 + IA Local (Águia Trader)`.
   - Snapshot com data/hora em tempo real e indicador de status da API Python 3.11.

2. **Coluna Lateral Esquerda (Universo de Ações)**:
   - Contagem e catálogo do universo da B3 (`ASAI3`, `ANIM3`, `ARML3`, `AURE3`, `PETR4`, `VALE3`, `WEGE3`, etc.).
   - Campo de busca em tempo real (`Buscar ação (ex: PETR4)...`).
   - Filtros de tendência: `Todos`, `Alta`, `Baixa`, `Neutro`.
   - Cards estilizados com destaque de borda azul e brilho para o ativo ativo no gráfico.

3. **Coluna Principal (Gráfico Quantitativo & Projeção 14D)**:
   - Barra de legendas: *Preço (Fechamento)*, *WMA 30*, *SMA 200*, *Projeção 14D (Alvo + Banda ATR)*.
   - Headline dinâmico: `ASAI3 | Águia Trader (+5.17%): ALTA (BULLISH)`.
   - Banner flutuante com alvo e recomendação.
   - **Motor Gráfico em HTML5 Canvas**:
     - Candlesticks japoneses (altas em verde, baixas em vermelho).
     - Curva amarela para **WMA 30** (Média Ponderada).
     - Curva azul para **SMA 200** (Média Simples de Longo Prazo).
     - Faixa translúcida sombreada para a **Projeção de 14 períodos à frente**.
     - Rótulo de alvo na linha de projeção (`Alvo 14D: R$ 13.96`).
     - Subpainel de volume com escala vertical `x 10⁶`.
     - Marca d'água no canto inferior direito com o selo **Águia Trader**.

4. **Painel de Métricas & Racional de IA**:
   - Cards com Preço Atual, Variação diária, Alvo Projetado 14D, Stop Loss e Relação Risco x Retorno (*Payoff*).
   - Racional do modelo algorítmico contextualizado para cada papel.

---

## 🚀 Como Executar

### Opção 1: Via Servidor Python 3.11 (Recomendado)

No PowerShell / Terminal:
```powershell
python app.py
```
Acesse no seu navegador:
```
http://localhost:8000
```

### Opção 2: Abertura Direta do Front-end
Você também pode abrir o arquivo `index.html` diretamente no seu navegador favorito dando um duplo clique. O script possui suporte completo a execução local autônoma.
