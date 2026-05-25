# PROTOCOLO_PAPER — Simulacao sem Dinheiro Real

**ID:** `PT-001` | **Fase:** #phase/3 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Validar a operacionalidade do sistema sem risco financeiro. Paper trading e a ponte entre backtest e dinheiro real.

---

## 2. DURACAO

- **Minimo:** 1 mes (30 dias de jogos NBA)
- **Ideal:** 100 sinais gerados, o que for maior
- **Recomendado:** 60 dias para maior confiança estatística

---

## 3. FLUXO OPERACIONAL DETALHADO

### 3.1 Passo a Passo

```
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 1: GERAÇÃO DE SINAL                                         │
├─────────────────────────────────────────────────────────────────┤
│ • Motor de value processa dados em tempo real                    │
│ • Modelo XGBoost gera probabilidade                              │
│ • Meta-labeler valida edge                                       │
│ • Calibração por regime é aplicada                               │
│ • Sinal é gerado com: odds, stake, confiança                     │
│ • Timestamp de geração é registado                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 2: VALIDAÇÃO DE RISCO                                       │
├─────────────────────────────────────────────────────────────────┤
│ • Circuit breakers são verificados                               │
│ • Exposição diária é calculada                                   │
│ • Correlação com apostas existentes é verificada                 │
│ • Limite de mercado é validado                                   │
│ • Sinal é APROVADO ou REJEITADO                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 3: REGISTRO DE SINAL (PAPER)                                │
├─────────────────────────────────────────────────────────────────┤
│ • Sinal aprovado é inserido na BD como 'paper'                    │
│ • Campos registados:                                             │
│   - signal_id (UUID único)                                       │
│   - game_id, market_type, selection_id                           │
│   - signal_timestamp, signal_odds, signal_stake                  │
│   - kelly_fraction, confidence_score                             │
│   - mode = 'paper' (flag distintivo)                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 4: CAPTURA DE ODD DISPONÍVEL                                │
├─────────────────────────────────────────────────────────────────┤
│ • Sistema consulta API de odds (Betfair/Pinnacle)                │
│ • Odd disponível no momento do sinal é capturada                 │
│ • Liquidez disponível é verificada                               │
│ • Timestamp de captura é registado                               │
│ • Se API indisponível: flag para captura manual                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 5: SIMULAÇÃO DE EXECUÇÃO                                   │
├─────────────────────────────────────────────────────────────────┤
│ • Sistema simula se aposta seria preenchida:                     │
│   - Liquidez suficiente na odd alvo?                             │
│   - Mercado ainda aberto?                                        │
│   - Timeout de 60 segundos                                       │
│ • Se preenchida: execution_status = 'FILLED'                     │
│ • Se não preenchida: execution_status = 'CANCELLED_TIMEOUT'     │
│ • Odd obtida (simulada) é determinada                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 6: CAPTURA DE ODD DE FECHO                                  │
├─────────────────────────────────────────────────────────────────┤
│ • Após término do jogo, odd de fecho é capturada                 │
│ • Fonte: API histórica ou scraping                               │
│ • Timestamp de fecho é registado                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 7: DETERMINAÇÃO DE RESULTADO                               │
├─────────────────────────────────────────────────────────────────┤
│ • Resultado do jogo é obtido (API oficial)                       │
│ • Sistema determina se aposta foi ganha/perdida/void             │
│ • PnL é calculado: (stake * odds) - stake se ganha, -stake se perde│
│ • CLV_expost é calculado: (odds_obtida / odds_fecho) - 1         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 8: ANÁLISE E RELATÓRIO                                     │
├─────────────────────────────────────────────────────────────────┤
│ • Métricas agregadas são calculadas diariamente                  │
│ • Comparação com backtest é realizada                            │
│ • Divergências são identificadas                                 │
│ • Relatório é gerado automaticamente                             │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Exemplo Prático

**Sinal gerado:** Lakers vs Celtics, Moneyline Lakers, odds 2.10, stake 10€

```
1. 19:30 UTC - Sinal gerado pelo motor
2. 19:30 UTC - Validado por circuit breakers
3. 19:30:05 UTC - Registado na BD (paper mode)
4. 19:30:10 UTC - Odd disponível capturada: 2.08 (liquidez €5000)
5. 19:30:10 UTC - Simulação: FILLED (liquidez suficiente)
6. 19:30:10 UTC - Odd obtida: 2.08 (slippage -0.96%)
7. 22:00 UTC - Jogo termina (Lakers ganha)
8. 22:15 UTC - Odd de fecho capturada: 1.95
9. 22:15 UTC - PnL calculado: 10€ * 2.08 - 10€ = 10.80€
10. 22:15 UTC - CLV_expost: (2.08 / 1.95) - 1 = +6.67%
```

---

## 4. CRITERIOS DE PASSAGEM

### 4.1 Critérios Críticos (BLOCKERS)

| Criterio | Threshold | Justificacao | Acao se falhar |
|----------|-----------|--------------|----------------|
| CLV paper vs backtest | Diferenca < 1% | Se paper tem CLV muito menor, ha problema operacional | Investigar e corrigir |
| Numero de sinais | >= 100 | Significancia estatistica minima | Continuar ate threshold |
| Uptime do sistema | > 95% | Sistema deve ser confiavel | Melhorar infraestrutura |
| Tempo medio sinal -> registo | < 2 min | Operador ou sistema deve ser rapido | Otimizar pipeline |
| Sem erros criticos | 0 | Nenhum circuit breaker nao-intencional | Debug e corrigir |

### 4.2 Critérios de Qualidade (WARNINGS)

| Metrica | Target | Warning | Critical |
|---------|--------|---------|----------|
| Fill rate simulado | > 85% | < 80% | < 70% |
| Slippage medio | < 1.5% | > 2% | > 3% |
| ROI paper | > 2% | < 1% | < 0% |
| Sharpe ratio | > 0.5 | < 0.3 | < 0 |
| Max drawdown | < 20% | > 25% | > 35% |

---

## 5. RELATORIO DE SAIDA

### 5.1 Estrutura do Relatório

```python
@dataclass
class PaperTradingReport:
    # Metadados
    report_id: str
    period_start: date
    period_end: date
    generated_at: datetime
    
    # Volume
    n_signals: int
    n_bets_simulated: int
    fill_rate: float
    
    # Performance
    total_pnl: float
    roi: float
    avg_clv: float
    sharpe_ratio: float
    max_drawdown: float
    
    # Comparação com backtest
    clv_paper: float
    clv_backtest: float
    clv_divergence: float
    pnl_paper: float
    pnl_backtest_expected: float
    pnl_divergence_pct: float
    
    # Operacional
    uptime_pct: float
    avg_latency_seconds: float
    circuit_breakers_triggered: int
    errors_count: int
    
    # Decisão
    recommendation: str  # 'PROCEED', 'REVIEW', 'STOP'
    blockers: List[str]
    warnings: List[str]
    
    # Análise adicional
    market_breakdown: Dict[str, Dict]
    daily_pnl: List[Tuple[date, float]]
    clv_distribution: Dict[str, float]
```

### 5.2 Exemplo de Relatório

```
═══════════════════════════════════════════════════════════════
PAPER TRADING REPORT
═══════════════════════════════════════════════════════════════
Período: 2024-01-01 a 2024-01-31 (31 dias)
Gerado: 2024-02-01 00:00:00 UTC

───────────────────────────────────────────────────────────────
VOLUME
───────────────────────────────────────────────────────────────
Sinais gerados: 127
Apostas simuladas: 115
Fill rate: 90.6%

───────────────────────────────────────────────────────────────
PERFORMANCE
───────────────────────────────────────────────────────────────
PnL total: +245.50€
ROI: 21.3%
CLV médio: +3.2%
Sharpe ratio: 1.85
Max drawdown: -12.4%

───────────────────────────────────────────────────────────────
COMPARAÇÃO COM BACKTEST
───────────────────────────────────────────────────────────────
CLV paper: +3.2%
CLV backtest: +3.4%
Divergência: -0.2% ✓

PnL paper: +245.50€
PnL esperado: +260.00€
Divergência: -5.6% ⚠

───────────────────────────────────────────────────────────────
OPERACIONAL
───────────────────────────────────────────────────────────────
Uptime: 98.7% ✓
Latência média: 1.2s ✓
Circuit breakers: 0 ✓
Erros: 3 ⚠

───────────────────────────────────────────────────────────────
DECISÃO
───────────────────────────────────────────────────────────────
RECOMMENDATION: PROCEED ✓

BLOCKERS: Nenhum
WARNINGS:
  • Divergência de PnL > 5% (investigar slippage)
  • 3 erros de API de odds (revisar rate limiting)

───────────────────────────────────────────────────────────────
ANÁLISE POR MERCADO
───────────────────────────────────────────────────────────────
NBA Moneyline: 82 sinais, ROI 22.1%, CLV 3.4%
NBA Spread: 33 sinais, ROI 19.8%, CLV 2.8%
NBA Totals: 12 sinais, ROI 18.5%, CLV 2.9%

═══════════════════════════════════════════════════════════════
```

---

## 6. PROCEDIMENTOS DE CONTINGÊNCIA

### 6.1 Falha de Sistema

Se o sistema ficar indisponível:

1. **Imediatamente:**
   - Notificar responsável operacional
   - Iniciar registro manual em spreadsheet template
   - Capturar screenshots de sinais se possível

2. **Durante downtime:**
   - Registrar manualmente: timestamp, jogo, mercado, odds, stake
   - Capturar odds disponível manualmente
   - Documentar motivo da falha

3. **Após recuperação:**
   - Importar dados manuais para BD
   - Reconciliar com dados automáticos
   - Investigar causa raiz
   - Implementar prevenção

### 6.2 Dados Incorretos

Se dados de odds/resultados estiverem incorretos:

1. **Identificar período afetado:**
   - Verificar logs de API
   - Comparar com fontes alternativas
   - Marcar registros suspeitos

2. **Correção:**
   - Marcar sinais como 'invalid' na BD
   - Excluir do cálculo de métricas
   - Recalcular relatórios

3. **Prevenção:**
   - Implementar validação cruzada de fontes
   - Adicionar alerts para valores anómalos
   - Revisar qualidade de dados

---

## 7. BACKLOG DE IMPLEMENTAÇÃO

### 7.1 Funcionalidades Críticas

- [x] Implementar modo paper na base de dados
- [x] Criar schema de paper_trading_signals
- [ ] Implementar captura automática de odds disponível
- [ ] Implementar simulação de fill rate
- [ ] Criar script de relatório automático
- [ ] Implementar validação de resultados

### 7.2 Funcionalidades Secundárias

- [ ] Dashboard em tempo real de paper trading
- [ ] Alertas automáticos por email/Telegram
- [ ] Comparação visual paper vs backtest
- [ ] Análise de slippage por mercado
- [ ] Exportação de dados para Excel

### 7.3 Processos

- [ ] Definir processo de decisão após paper trading
- [ ] Criar checklist manual diário
- [ ] Documentar planos de contingência
- [ ] Treinar operacional no protocolo

---

## 8. PROCEDIMENTOS MANUAIS (QUANDO AUTOMAÇÃO FALHA)

### 8.1 Template de Registro Manual

Quando o sistema está offline, usar este template:

```excel
| Data | Hora UTC | Jogo | Mercado | Seleção | Odd Sinal | Odd Disp. | Stake | Liquidez | Status | Odd Obtida | Resultado | PnL | CLV | Notas |
|------|-----------|------|---------|---------|-----------|-----------|-------|----------|--------|------------|-----------|-----|-----|-------|
| 2024-01-15 | 19:30:00 | Lakers vs Celtics | Moneyline | Lakers | 2.10 | 2.08 | 10€ | 5000€ | FILLED | 2.08 | WIN | 10.80€ | 6.67% | - |
```

**Instruções de preenchimento:**
1. **Data/Hora UTC:** Registrar imediatamente quando sinal é recebido
2. **Odd Sinal:** Odd exata do sinal do sistema
3. **Odd Disp.:** Odd disponível no mercado no momento do sinal
4. **Liquidez:** Volume disponível na odd (se visível)
5. **Status:** FILLED (liquidez OK), CANCELLED (liquidez insuficiente), TIMEOUT (60s)
6. **Odd Obtida:** Odd que seria obtida (igual a Odd Disp. se FILLED)
7. **Resultado:** WIN, LOSS, VOID (após jogo)
8. **PnL:** Calcular após resultado: WIN = stake × odds - stake, LOSS = -stake
9. **CLV:** Calcular após jogo: (odd_obtida / odd_fecho) - 1
10. **Notas:** Quaisquer anomalias ou observações

### 8.2 Checklist Diário Manual

**Manhã (antes dos jogos):**
- [ ] Verificar se sistema está online
- [ ] Confirmar que APIs de odds estão acessíveis
- [ ] Verificar espaço em disco do servidor
- [ ] Revisar alertas/notificações de ontem
- [ ] Documentar qualquer anomalia

**Durante o dia (após cada sinal):**
- [ ] Confirmar que sinal foi registado
- [ ] Verificar que odd foi capturada
- [ ] Validar simulação de execução
- [ ] Registrar qualquer erro ou atraso

**Fim do dia:**
- [ ] Confirmar que todos os resultados foram atualizados
- [ ] Reconciliar PnL do dia
- [ ] Calcular métricas do dia
- [ ] Revisar logs de erros
- [ ] Gerar relatório manual se automação falhou
- [ ] Documentar lições aprendidas

### 8.3 Captura Manual de Odds

Se API de odds está indisponível:

1. **Acessar mercado na Betfair Exchange**
2. **Capturar:**
   - Odd Back (para apostas simples)
   - Odd Lay (para trading, se aplicável)
   - Liquidez disponível
   - Timestamp de captura
3. **Registrar no template manual**
4. **Tirar screenshot** como evidência (opcional mas recomendado)

**Ferramentas úteis:**
- Betfair Exchange website
- OddsPortal (para odds históricas)
- FlashScore (para resultados em tempo real)

### 8.4 Validação Manual de Resultados

Se sistema de resultados falha:

1. **Acessar fonte oficial:**
   - NBA.com para resultados oficiais
   - ESPN para resultados rápidos
   - FlashScore para resultados em tempo real

2. **Registrar resultado:**
   - Score final do jogo
   - Vencedor (se aplicável)
   - Total de pontos (para Totals)
   - Qualquer status especial (OT, cancelado, etc.)

3. **Calcular PnL manual:**
   ```
   Se aposta WIN: PnL = stake × odds_obtida - stake
   Se aposta LOSS: PnL = -stake
   Se aposta VOID: PnL = 0
   ```

4. **Calcular CLV manual:**
   ```
   CLV = (odd_obtida / odd_fecho) - 1

   Exemplo:
   Odd obtida: 2.08
   Odd fecho: 1.95
   CLV = (2.08 / 1.95) - 1 = +0.0667 = +6.67%
   ```

---

## 9. ANÁLISE AVANÇADA DE PAPER TRADING

### 9.1 Análise de Slippage por Mercado

```python
def analyze_slippage_by_market():
    """
    Analisa slippage médio por tipo de mercado
    Identifica mercados com maior dificuldade de execução
    """
    query = """
    SELECT
        market_type,
        AVG(slippage_pct) as avg_slippage,
        STDDEV(slippage_pct) as stddev_slippage,
        COUNT(*) as n_signals,
        SUM(CASE WHEN slippage_pct < -0.02 THEN 1 ELSE 0 END) as n_high_slippage
    FROM paper_trading_signals
    WHERE execution_status = 'FILLED'
    GROUP BY market_type
    ORDER BY avg_slippage ASC
    """
    results = db.execute(query)

    analysis = []
    for row in results:
        analysis.append({
            'market': row.market_type,
            'avg_slippage': row.avg_slippage,
            'stddev': row.stddev_slippage,
            'signals': row.n_signals,
            'high_slippage_pct': row.n_high_slippage / row.n_signals * 100,
            'recommendation': get_slippage_recommendation(row.avg_slippage)
        })

    return analysis

def get_slippage_recommendation(avg_slippage):
    if avg_slippage > -0.005:  # > -0.5%
        return "EXCELLENT - Mercado com execução fácil"
    elif avg_slippage > -0.015:  # > -1.5%
        return "GOOD - Execução aceitável"
    elif avg_slippage > -0.025:  # > -2.5%
        return "ACCEPTABLE - Monitorizar de perto"
    else:
        return "POOR - Considerar ajustar filtros ou evitar mercado"
```

### 9.2 Análise de CLV por Regime de Mercado

```python
def analyze_clv_by_regime():
    """
    Analisa CLV médio por diferentes regimes de mercado
    Identifica condições onde modelo performa melhor/pior
    """
    query = """
    SELECT
        regime_type,  # 'high_volatility', 'low_volatility', 'trending', etc.
        AVG(clv_expost) as avg_clv,
        STDDEV(clv_expost) as stddev_clv,
        COUNT(*) as n_signals,
        AVG(roi) as avg_roi
    FROM paper_trading_signals
    JOIN market_regimes ON paper_trading_signals.game_id = market_regimes.game_id
    WHERE execution_status = 'FILLED'
    GROUP BY regime_type
    ORDER BY avg_clv DESC
    """
    results = db.execute(query)

    analysis = []
    for row in results:
        analysis.append({
            'regime': row.regime_type,
            'avg_clv': row.avg_clv,
            'stddev': row.stddev_clv,
            'signals': row.n_signals,
            'avg_roi': row.avg_roi,
            'recommendation': get_regime_recommendation(row.avg_clv, row.n_signals)
        })

    return analysis
```

### 9.3 Análise de Timing de Sinais

```python
def analyze_signal_timing():
    """
    Analisa performance baseada no timing do sinal
    Identifica horários ótimos para execução
    """
    query = """
    SELECT
        EXTRACT(HOUR FROM signal_timestamp) as hour,
        AVG(clv_expost) as avg_clv,
        COUNT(*) as n_signals,
        AVG(slippage_pct) as avg_slippage,
        AVG(roi) as avg_roi
    FROM paper_trading_signals
    WHERE execution_status = 'FILLED'
    GROUP BY hour
    ORDER BY avg_clv DESC
    """
    results = db.execute(query)

    analysis = []
    for row in results:
        analysis.append({
            'hour_utc': int(row.hour),
            'avg_clv': row.avg_clv,
            'signals': row.n_signals,
            'avg_slippage': row.avg_slippage,
            'avg_roi': row.avg_roi
        })

    return analysis
```

### 9.4 Análise de Divergência Paper vs Backtest

```python
def analyze_paper_vs_backtest_divergence():
    """
    Analisa systematicamente onde paper diverge do backtest
    Identifica causas de discrepância
    """
    # Comparar CLV por mercado
    clv_divergence = """
    SELECT
        pt.market_type,
        AVG(pt.clv_expost) as paper_clv,
        AVG(bt.clv_expected) as backtest_clv,
        AVG(pt.clv_expost) - AVG(bt.clv_expected) as divergence
    FROM paper_trading_signals pt
    JOIN backtest_signals bt ON pt.signal_id = bt.signal_id
    GROUP BY pt.market_type
    """

    # Comparar fill rate
    fill_divergence = """
    SELECT
        COUNT(CASE WHEN pt.execution_status = 'FILLED' THEN 1 END) * 100.0 / COUNT(*) as paper_fill_rate,
        bt.expected_fill_rate as backtest_fill_rate,
        COUNT(CASE WHEN pt.execution_status = 'FILLED' THEN 1 END) * 100.0 / COUNT(*) - bt.expected_fill_rate as divergence
    FROM paper_trading_signals pt
    CROSS JOIN (SELECT expected_fill_rate FROM backtest_config LIMIT 1) bt
    """

    # Análise de slippage
    slippage_divergence = """
    SELECT
        AVG(pt.slippage_pct) as paper_slippage,
        bt.expected_slippage as backtest_slippage,
        AVG(pt.slippage_pct) - bt.expected_slippage as divergence
    FROM paper_trading_signals pt
    CROSS JOIN (SELECT expected_slippage FROM backtest_config LIMIT 1) bt
    WHERE pt.execution_status = 'FILLED'
    """

    return {
        'clv_divergence': db.execute(clv_divergence),
        'fill_divergence': db.execute(fill_divergence),
        'slippage_divergence': db.execute(slippage_divergence)
    }
```

---

## 10. INTEGRAÇÃO COM SISTEMAS EXTERNOS

### 10.1 Integração com Telegram para Notificações

```python
import requests

class PaperTradingTelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send_signal_notification(self, signal):
        """Envia notificação quando novo sinal é gerado"""
        message = f"""
📊 PAPER TRADING - NOVO SINAL

🏀 {signal.game}
📈 Mercado: {signal.market_type}
🎯 Seleção: {signal.selection}
💰 Odd: {signal.odds}
📊 Stake: {signal.stake}€
🔒 Confiança: {signal.confidence_score:.1%}
⏰ {signal.timestamp}
        """
        self._send_message(message)

    def send_execution_notification(self, signal, execution):
        """Envia notificação de execução simulada"""
        status_emoji = "✅" if execution.status == "FILLED" else "❌"
        message = f"""
{status_emoji} EXECUÇÃO SIMULADA

Sinal: {signal.signal_id}
Status: {execution.status}
Odd obtida: {execution.odds_obtained}
Slippage: {execution.slippage_pct:.2%}
        """
        self._send_message(message)

    def send_daily_summary(self, report):
        """Envia resumo diário"""
        emoji = "✅" if report.recommendation == "PROCEED" else "⚠️"
        message = f"""
{emoji} PAPER TRADING - RESUMO DIÁRIO

📅 {report.date}
📊 Sinais: {report.n_signals}
💰 PnL: {report.total_pnl:.2f}€
📈 ROI: {report.roi:.2%}
🎯 CLV: {report.avg_clv:.2%}
📉 Drawdown: {report.max_drawdown:.2%}

Decisão: {report.recommendation}
        """
        self._send_message(message)

    def _send_message(self, message):
        """Envia mensagem via Telegram API"""
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, json=data)
```

### 10.2 Integração com Dashboard em Tempo Real

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/paper/realtime')
def get_paper_realtime():
    """Endpoint para dashboard em tempo real"""
    # Métricas das últimas 24 horas
    query = """
    SELECT
        COUNT(*) as n_signals_today,
        SUM(CASE WHEN execution_status = 'FILLED' THEN 1 ELSE 0 END) as n_filled,
        AVG(clv_expost) as avg_clv,
        SUM(pnl) as total_pnl,
        AVG(slippage_pct) as avg_slippage
    FROM paper_trading_signals
    WHERE signal_timestamp >= NOW() - INTERVAL '24 hours'
    """
    metrics = db.execute_one(query)

    # Últimos 10 sinais
    recent_signals = """
    SELECT
        signal_id,
        game,
        market_type,
        signal_odds,
        execution_odds,
        pnl,
        clv_expost,
        signal_timestamp
    FROM paper_trading_signals
    ORDER BY signal_timestamp DESC
    LIMIT 10
    """
    signals = db.execute(recent_signals)

    return jsonify({
        'metrics': metrics,
        'recent_signals': signals,
        'timestamp': datetime.now().isoformat()
    })
```

### 10.3 Integração com Sistema de Alertas

```python
class PaperTradingAlertSystem:
    def __init__(self, thresholds):
        self.thresholds = thresholds
        self.notifier = TelegramNotifier(...)

    def check_and_alert(self):
        """Verifica métricas e envia alertas se necessário"""
        metrics = self.calculate_metrics()

        alerts = []

        # Verificar CLV
        if metrics['avg_clv'] < self.thresholds['min_clv']:
            alerts.append({
                'severity': 'CRITICAL',
                'message': f"CLV médio ({metrics['avg_clv']:.2%}) abaixo do threshold ({self.thresholds['min_clv']:.2%})"
            })

        # Verificar fill rate
        if metrics['fill_rate'] < self.thresholds['min_fill_rate']:
            alerts.append({
                'severity': 'WARNING',
                'message': f"Fill rate ({metrics['fill_rate']:.2%}) abaixo do threshold ({self.thresholds['min_fill_rate']:.2%})"
            })

        # Verificar drawdown
        if metrics['max_drawdown'] > self.thresholds['max_drawdown']:
            alerts.append({
                'severity': 'CRITICAL',
                'message': f"Drawdown ({metrics['max_drawdown']:.2%}) acima do threshold ({self.thresholds['max_drawdown']:.2%})"
            })

        # Enviar alertas
        for alert in alerts:
            self.notifier.send_alert(alert)

        return alerts
```

---

## 11. MELHORES PRÁTICAS E LIÇÕES APRENDIDAS

### 11.1 Do's and Don'ts

**DO:**
- ✓ Registrar meticulosamente cada sinal, mesmo se não executado
- ✓ Capturar timestamp exato de cada evento
- ✓ Validar dados de múltiplas fontes quando possível
- ✓ Revisar relatórios diariamente
- ✓ Investigar anomalias imediatamente
- ✓ Manter backup dos dados
- ✓ Documentar todos os procedimentos manuais
- ✓ Testar sistema antes de iniciar paper trading

**DON'T:**
- ✗ Ignorar sinais não executados
- ✗ Assumir que dados estão corretos sem validação
- ✗ Alterar filtros durante paper trading
- ✗ Parar paper trading prematuramente
- ✗ Comparar paper trading com backtest de forma superficial
- ✗ Usar dados de diferentes fontes sem ajuste
- ✗ Negligenciar logs de erros
- ✗ Iniciar dinheiro real sem completar paper trading

### 11.2 Lições Comuns

**Lição 1: Timing é crítico**
- O backtest assume execução instantânea
- Paper trading revela atrasos reais
- Ajustar expectativas de CLV baseado em latência real

**Lição 2: Liquidez varia muito**
- Backtest assume liquidez infinita
- Paper trading mostra liquidez real disponível
- Ajustar filtros de liquidez baseado em dados reais

**Lição 3: Odds mudam rapidamente**
- Odd sinalizada ≠ odd disponível
- Slippage é real e impacta ROI
- Implementar tolerância de slippage aceitável

**Lição 4: Erros acontecem**
- APIs falham, sistemas crasham
- Ter procedimentos manuais de backup
- Testar contingências regularmente

**Lição 5: Consistência > Perfeição**
- Sistema consistente 95% do tempo > Sistema perfeito 50% do tempo
- Focar em uptime e fiabilidade
- Aceitar pequenos erros se sistema é robusto

---

## 12. LINKS CRUZADOS

- [[21_Paper_Trading/INDEX]] ← Seção mãe
- [[21_Paper_Trading/PAPER_TRADING_SETUP]] ← Configuração e ambiente
- [[22_Real_Money_Operations/INDEX]] → Próxima fase
- [[06_Backtesting/INDEX]] → Backtest para comparação
- [[08_Risk_Management/INDEX]] → Gestão de risco aplicada
- [[47_Shadow_Betting/INDEX]] → Shadow mode multi-casa
