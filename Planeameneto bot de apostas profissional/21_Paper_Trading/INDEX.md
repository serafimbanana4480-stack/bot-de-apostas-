# 21_Paper_Trading — INDEX

**ID:** `SEC-21` | **Fase:** #phase/3 | **Owner:** Principal Quant Engineer | **Status:** #status/complete

---

## 1. OBJETIVO

Validar a operacionalidade do sistema sem risco financeiro. O paper trading mede se o processo completo (sinais → execução simulada → resultados) funciona como o backtest prevê, antes de arriscar dinheiro real.

**Regra:** Paper trading NÃO é opcional. É a ponte entre backtest e dinheiro real.

---

## 2. NOTAS FUNDAMENTAIS

- [[PROTOCOLO_PAPER]] — Como simular apostas sem execução real
- [[PAPER_TRADING_SETUP]] — Configuração, ambiente, ferramentas e validação
- [[DIVERGENCIA_BACKTEST]] — Como medir e analisar diferenças entre simulado e paper
- [[LATENCIA_PAPER]] — Medir se o atraso operacional muda as odds obtidas
- [[METRICAS_PAPER]] — Quais métricas validam a prontidão para dinheiro real

---

## 3. PROTOCOLO DE PAPER TRADING

### 3.1 Fluxo Operacional Detalhado

```
┌─────────────────────────────────────────────────────────────────┐
│ FASE 1: GERAÇÃO DE SINAL                                         │
├─────────────────────────────────────────────────────────────────┤
│ 1. Motor de value gera sinal (mesma lógica de produção)          │
│ 2. Sistema valida filtros de risco (circuit breakers)            │
│ 3. Sinal é aprovado/rejeitado automaticamente                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 2: REGISTRO DE SINAL                                         │
├─────────────────────────────────────────────────────────────────┤
│ 1. Sinal aprovado é registado na BD como 'paper'                 │
│ 2. Timestamp de geração é registado                              │
│ 3. Odd sinalizada é capturada                                    │
│ 4. Stake recomendado (Kelly) é calculado                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 3: CAPTURA DE ODD                                           │
├─────────────────────────────────────────────────────────────────┤
│ 1. Odd disponível é capturada em tempo real (se API disponível)  │
│ 2. Odd de fecho é capturada após o jogo                          │
│ 3. Histórico de odds é registado para análise de slippage        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 4: DETERMINAÇÃO DE RESULTADO                                │
├─────────────────────────────────────────────────────────────────┤
│ 1. Resultado do jogo é determinado após o jogo                   │
│ 2. Sistema verifica se a aposta seria preenchida                 │
│ 3. Odd obtida (simulada) é determinada                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 5: CÁLCULO DE PnL                                           │
├─────────────────────────────────────────────────────────────────┤
│ 1. PnL simulado é calculado baseado em odd obtida                │
│ 2. CLV_expost é calculado (odd obtida vs odd fecho)              │
│ 3. Métricas de risco são atualizadas                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 6: ANÁLISE E COMPARAÇÃO                                     │
├─────────────────────────────────────────────────────────────────┤
│ 1. Comparação: paper PnL vs backtest PnL esperado                │
│ 2. Análise de divergência CLV                                    │
│ 3. Identificação de problemas operacionais                       │
│ 4. Geração de relatório diário                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Duração e Volume

| Parâmetro | Valor Mínimo | Valor Ideal | Justificação |
|-----------|--------------|-------------|--------------|
| Duração | 30 dias | 60 dias | Ciclo completo de NBA |
| Sinais | 100 | 200 | Significância estatística |
| Jogos por dia | 3-5 | 5-8 | Cobertura de variabilidade |
| Horários | Variados | Variados | Diferentes fusos horários |

**Duração mínima:** 1 mês (30 dias de jogos NBA) ou 100 sinais, o que for maior.

---

## 4. CRITÉRIOS DE PASSAGEM PARA MICRO BANCA

### 4.1 Thresholds Críticos

| Critério | Threshold | Justificação |
|----------|-----------|--------------|
| CLV paper vs backtest | Diferença < 1% | Se paper tem CLV muito menor, há problema operacional |
| Número de sinais | ≥ 100 | Significância estatística mínima |
| Uptime do sistema | > 95% | Sistema deve ser confiável |
| Tempo médio sinal → registo | < 2 min | Operador ou sistema deve ser rápido |
| Sem erros críticos | 0 | Nenhum circuit breaker não-intencional |

### 4.2 Métricas Secundárias (Monitorização)

| Métrica | Target | Ação se abaixo do target |
|---------|--------|---------------------------|
| Fill rate simulado | > 85% | Revisar filtros de liquidez |
| Slippage médio | < 1.5% | Revisar timing de execução |
| ROI paper | > 2% | Investigar modelo se < 0% |
| Sharpe ratio | > 0.5 | Revisar gestão de risco |
| Max drawdown | < 20% | Revisar Kelly fraction |

### 4.3 Processo de Decisão

```
SE todos os critérios CRÍTICOS forem satisfeitos:
    → APROVADO para Micro Banca
    → Iniciar preparação de Fase 4
SENÃO:
    → IDENTIFICAR problema específico
    → CORRIGIR problema
    → REINICIAR paper trading por 30 dias
```

---

## 5. GESTÃO DE DADOS DO PAPER TRADING

### 5.1 Schema de Base de Dados

```sql
CREATE TABLE paper_trading_signals (
    id SERIAL PRIMARY KEY,
    signal_id VARCHAR(50) UNIQUE NOT NULL,
    game_id VARCHAR(50) NOT NULL,
    market_type VARCHAR(20) NOT NULL,
    selection_id VARCHAR(50) NOT NULL,
    bet_type VARCHAR(20) NOT NULL,
    
    -- Sinal
    signal_timestamp TIMESTAMP NOT NULL,
    signal_odds DECIMAL(10,4) NOT NULL,
    signal_stake DECIMAL(10,2) NOT NULL,
    kelly_fraction DECIMAL(5,4) NOT NULL,
    
    -- Execução simulada
    execution_timestamp TIMESTAMP,
    execution_odds DECIMAL(10,4),
    execution_status VARCHAR(20), -- 'FILLED', 'CANCELLED', 'REJECTED'
    slippage_pct DECIMAL(5,4),
    
    -- Resultado
    closing_odds DECIMAL(10,4),
    game_result VARCHAR(20),
    pnl DECIMAL(10,2),
    clv_expost DECIMAL(5,4),
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_paper_signals_game ON paper_trading_signals(game_id);
CREATE INDEX idx_paper_signals_date ON paper_trading_signals(signal_timestamp);
```

### 5.2 Relatórios Diários

Relatório automático gerado às 23:59 UTC:

```python
class DailyPaperReport:
    date: date
    total_signals: int
    filled_bets: int
    fill_rate: float
    total_pnl: float
    roi: float
    avg_clv: float
    avg_slippage: float
    max_drawdown: float
    uptime_pct: float
    errors: List[str]
    recommendation: str  # 'PROCEED', 'REVIEW', 'STOP'
```

---

## 6. VIGILÂNCIA OPERACIONAL

### 6.1 Monitorização em Tempo Real

| Componente | Métrica | Alerta se | Ação |
|------------|---------|-----------|------|
| Motor de value | Sinais/hora | < 50% do esperado | Verificar pipeline de dados |
| Base de dados | Latência de escrita | > 500ms | Verificar performance |
| API de odds | Taxa de sucesso | < 95% | Verificar quota/limite |
| Sistema geral | Uptime | < 95% | Investigar downtime |

### 6.2 Checklist Diário (Manual)

- [ ] Verificar se todos os sinais foram registados
- [ ] Confirmar que resultados foram atualizados
- [ ] Revisar erros nos logs
- [ ] Validar que PnL está coerente
- [ ] Verificar métricas de CLV
- [ ] Documentar anomalias

---

## 7. RISCOS E MITIGAÇÃO

### 7.1 Riscos Comuns

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Dados incompletos | Média | Alto | Redundância de fontes |
| Erro de modelo | Baixa | Crítico | Validação cruzada |
| Falha de sistema | Baixa | Alto | Backup manual |
| Viés operacional | Média | Médio | Automatização máxima |

### 7.2 Planos de Contingência

**Se o sistema ficar offline:**
1. Registar sinais manualmente em spreadsheet
2. Capturar odds manualmente
3. Atualizar resultados manualmente
4. Reconciliar quando sistema voltar

**Se dados estiverem incorretos:**
1. Identificar período afetado
2. Marcar sinais como 'invalid'
3. Excluir do cálculo de métricas
4. Investigar causa raiz

---

## 8. CONFIGURAÇÃO E SETUP

### 8.1 Ambiente de Paper Trading

**Requisitos de Sistema:**
- Python 3.9+
- PostgreSQL 14+
- Redis 7+ (para cache de odds)
- 4GB RAM mínimo
- 20GB armazenamento

**Variáveis de Ambiente:**
```bash
# Paper Trading Mode
PAPER_TRADING_ENABLED=true
PAPER_TRADING_MODE=full  # 'full' ou 'validation'

# APIs (mesmas que produção, mas sem execução real)
ODDS_API_KEY=xxx
ODDS_API_RATE_LIMIT=1000/hour

# Base de Dados
DB_HOST=localhost
DB_NAME=bot_apostas_paper
DB_USER=bot_user
DB_PASSWORD=xxx

# Notificações
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
NOTIFICATION_LEVEL=info  # 'debug', 'info', 'warning', 'error'
```

### 8.2 Script de Inicialização

```bash
#!/bin/bash
# init_paper_trading.sh

# 1. Verificar ambiente
python3 check_environment.py

# 2. Criar base de dados paper (se não existe)
python3 create_paper_db.py

# 3. Validar schema
python3 validate_schema.py

# 4. Testar conexões
python3 test_connections.py

# 5. Iniciar serviços
docker-compose up -d postgres redis
python3 paper_trading_engine.py --mode=full --log-level=info

# 6. Verificar status
python3 status_check.py
```

### 8.3 Validação Pré-Paper Trading

**Checklist de Setup:**
- [ ] Base de dados criada e schema validado
- [ ] APIs de odds configuradas e testadas
- [ ] Motor de value carregado com modelo mais recente
- [ ] Circuit breakers configurados
- [ ] Sistema de notificações testado
- [ ] Script de relatório diário configurado
- [ ] Backup automatizado ativado
- [ ] Logging configurado com níveis apropriados

**Teste de Smoke (5 minutos):**
```bash
# Executar teste de smoke
python3 smoke_test.py

# Output esperado:
# ✓ Database connection: OK
# ✓ API connection: OK
# ✓ Model loading: OK
# ✓ Signal generation: OK (3 signals in 60s)
# ✓ Data storage: OK
# ✓ Notification: OK
```

---

## 9. AUTOMAÇÃO DE PAPER TRADING

### 9.1 Motor de Paper Trading

```python
class PaperTradingEngine:
    def __init__(self, config):
        self.mode = config.mode  # 'full' ou 'validation'
        self.signal_generator = SignalGenerator()
        self.odd_capture = OddCapture()
        self.result_processor = ResultProcessor()
        self.db = PaperTradingDB()

    def run_continuous(self):
        """Executa continuamente, processando sinais em tempo real"""
        while True:
            try:
                # 1. Gerar sinais
                signals = self.signal_generator.generate()

                # 2. Para cada sinal
                for signal in signals:
                    # Validar filtros de risco
                    if self.validate_risk(signal):
                        # Registar sinal
                        self.db.register_signal(signal, mode='paper')

                        # Capturar odd disponível
                        odd_available = self.odd_capture.capture(signal)

                        # Simular execução
                        execution = self.simulate_execution(signal, odd_available)

                        # Atualizar registo
                        self.db.update_execution(signal.id, execution)

            except Exception as e:
                log_error(e)
                send_alert(f"Paper trading error: {e}")

            time.sleep(60)  # Verificar a cada minuto

    def simulate_execution(self, signal, odd_available):
        """Simula se a aposta seria preenchida"""
        # Verificar liquidez
        if odd_available.liquidity < signal.stake * 2:
            return ExecutionStatus.CANCELLED_LIQUIDITY

        # Verificar se odd é aceitável
        slippage = (odd_available.value / signal.odds) - 1
        if slippage < -0.02:  # >2% de slippage negativo
            return ExecutionStatus.CANCELLED_SLIPPAGE

        # Simular timeout de 60 segundos
        if self.check_timeout(signal.timestamp):
            return ExecutionStatus.CANCELLED_TIMEOUT

        # Preenchida
        return ExecutionStatus.FILLED, odd_available.value
```

### 9.2 Cron Jobs Automatizados

```bash
# Crontab para paper trading

# Minuto a minuto: verificar sinais
* * * * * cd /path/to/bot && python3 paper_trading_engine.py --check-signals >> /var/log/paper/signals.log 2>&1

# A cada 5 minutos: capturar odds
*/5 * * * * cd /path/to/bot && python3 odd_capture.py --paper-mode >> /var/log/paper/odds.log 2>&1

# A cada 10 minutos: atualizar resultados de jogos finalizados
*/10 * * * * cd /path/to/bot && python3 result_processor.py --paper-mode >> /var/log/paper/results.log 2>&1

# Diariamente às 23:59: gerar relatório
59 23 * * * cd /path/to/bot && python3 daily_report.py --paper-mode >> /var/log/paper/daily_report.log 2>&1

# Semanalmente às 00:00 domingo: backup de BD
0 0 * * 0 pg_dump bot_apostas_paper > /backups/paper/paper_$(date +\%Y\%m\%d).sql
```

### 9.3 Monitorização Automática

```python
class PaperTradingMonitor:
    def __init__(self):
        self.alert_thresholds = {
            'fill_rate': 0.85,
            'clv_avg': 0.015,
            'roi': 0.02,
            'drawdown': 0.20,
            'uptime': 0.95
        }

    def check_metrics(self):
        """Verifica métricas e envia alertas se necessário"""
        metrics = self.calculate_metrics()

        alerts = []
        if metrics['fill_rate'] < self.alert_thresholds['fill_rate']:
            alerts.append(f"ALERTA: Fill rate {metrics['fill_rate']:.2%} < {self.alert_thresholds['fill_rate']:.2%}")

        if metrics['clv_avg'] < self.alert_thresholds['clv_avg']:
            alerts.append(f"ALERTA: CLV médio {metrics['clv_avg']:.2%} < {self.alert_thresholds['clv_avg']:.2%}")

        if metrics['roi'] < self.alert_thresholds['roi']:
            alerts.append(f"ALERTA: ROI {metrics['roi']:.2%} < {self.alert_thresholds['roi']:.2%}")

        if metrics['drawdown'] > self.alert_thresholds['drawdown']:
            alerts.append(f"CRÍTICO: Drawdown {metrics['drawdown']:.2%} > {self.alert_thresholds['drawdown']:.2%}")

        if alerts:
            self.send_alerts(alerts)

    def calculate_metrics(self):
        """Calcula métricas dos últimos 7 dias"""
        # Implementação de cálculo de métricas
        pass
```

---

## 10. TROUBLESHOOTING GUIDE

### 10.1 Problemas Comuns e Soluções

**Problema: Sinais não são gerados**
- Sintoma: Zero sinais por > 2 horas
- Causas possíveis:
  - Pipeline de dados offline
  - API de odds com erro
  - Modelo não carregado
- Solução:
  ```bash
  # Verificar status do pipeline
  python3 check_pipeline_status.py

  # Testar API de odds
  python3 test_odds_api.py

  # Recarregar modelo
  python3 reload_model.py
  ```

**Problema: Fill rate muito baixo (< 70%)**
- Sintoma: Muitas apostas marcadas como CANCELLED
- Causas possíveis:
  - Filtros de liquidez muito restritivos
  - Timeout muito curto
  - API de odds com atraso
- Solução:
  - Ajustar filtros de liquidez (reduzir de 2x para 1.5x)
  - Aumentar timeout de 60s para 90s
  - Verificar latência da API de odds

**Problema: CLV inconsistente com backtest**
- Sintoma: CLV paper < CLV backtest - 2%
- Causas possíveis:
  - Odd sinalizada diferente de backtest
  - Timing de captura de odd diferente
  - Dados de odds diferentes
- Solução:
  - Verificar fonte de odds no backtest vs paper
  - Ajustar timestamp de captura de odd
  - Validar que odds são da mesma fonte

**Problema: Sistema offline**
- Sintoma: Uptime < 90%
- Causas possíveis:
  - Servidor desligado
  - Falha de rede
  - Processo crashado
- Solução:
  ```bash
  # Verificar se processo está a correr
  ps aux | grep paper_trading

  # Reiniciar processo
  systemctl restart paper-trading

  # Verificar logs
  tail -f /var/log/paper/engine.log
  ```

### 10.2 Diagnóstico Rápido

```bash
#!/bin/bash
# diagnose_paper.sh

echo "=== DIAGNÓSTICO DE PAPER TRADING ==="
echo ""

echo "1. Status do Sistema:"
systemctl status paper-trading
echo ""

echo "2. Conexões:"
python3 test_connections.py
echo ""

echo "3. Últimos sinais:"
python3 last_signals.py --count=5
echo ""

echo "4. Métricas dos últimos 7 dias:"
python3 metrics_report.py --days=7
echo ""

echo "5. Erros recentes:"
tail -20 /var/log/paper/errors.log
echo ""

echo "6. Espaço em disco:"
df -h
echo ""

echo "=== FIM DO DIAGNÓSTICO ==="
```

### 10.3 Logs e Debugging

**Níveis de Log:**
- DEBUG: Informação detalhada para desenvolvimento
- INFO: Informação operacional normal
- WARNING: Situações anormais mas não críticas
- ERROR: Erros que requerem atenção
- CRITICAL: Erros que pararam o sistema

**Localização de Logs:**
```
/var/log/paper/
├── engine.log          # Motor principal
├── signals.log         # Geração de sinais
├── execution.log       # Simulação de execução
├── results.log         # Processamento de resultados
├── errors.log          # Erros apenas
└── alerts.log          # Alertas enviados
```

**Comandos úteis:**
```bash
# Ver logs em tempo real
tail -f /var/log/paper/engine.log

# Procurar erros
grep ERROR /var/log/paper/*.log

# Contar sinais por dia
grep "Signal generated" /var/log/paper/signals.log | wc -l

# Ver performance do sistema
grep "Processing time" /var/log/paper/engine.log | tail -10
```

---

## 11. INTEGRAÇÃO COM OUTROS SISTEMAS

### 11.1 Integração com Shadow Betting

O paper trading pode ser executado em paralelo com shadow mode multi-casa:

```
Sinal → Paper Trading (simulação simples)
       → Shadow Betting (simulação multi-casa)
       → Comparação de CLV
```

**Benefícios:**
- Validação do edge em múltiplas casas
- Identificação da melhor casa para execução real
- Redução do risco de viés de fonte única

### 11.2 Integração com Telegram Bot

O sistema de paper trading pode enviar notificações via Telegram:

```python
def send_paper_notification(signal, result):
    """Envia notificação de paper trading via Telegram"""
    message = f"""
📊 PAPER TRADING SIGNAL

🏀 Jogo: {signal.game}
💰 Odd: {signal.odds} → {result.odds_obtained}
📊 Stake: {signal.stake}€
✅ Resultado: {result.outcome}
💵 PnL: {result.pnl}€
📈 CLV: {result.clv:.2%}
    """

    telegram_bot.send_message(message)
```

### 11.3 Integração com Dashboard

Métricas de paper trading podem ser visualizadas em tempo real:

```python
# API endpoint para dashboard
@app.route('/api/paper/metrics')
def get_paper_metrics():
    metrics = {
        'total_signals': db.count_signals(mode='paper'),
        'fill_rate': db.calculate_fill_rate(mode='paper'),
        'avg_clv': db.calculate_avg_clv(mode='paper'),
        'roi': db.calculate_roi(mode='paper'),
        'drawdown': db.calculate_drawdown(mode='paper'),
        'last_7_days': db.get_metrics_last_7_days(mode='paper')
    }
    return jsonify(metrics)
```

---

## 12. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[06_Backtesting/INDEX]] → Backtest que o paper valida
- [[22_Real_Money_Operations/INDEX]] → Próxima fase após paper
- [[08_Risk_Management/INDEX]] → Gestão de risco aplicada ao paper
- [[47_Shadow_Betting/INDEX]] → Shadow mode (comparação multi-casa)
- [[PROTOCOLO_PAPER]] → Protocolo detalhado de paper trading
