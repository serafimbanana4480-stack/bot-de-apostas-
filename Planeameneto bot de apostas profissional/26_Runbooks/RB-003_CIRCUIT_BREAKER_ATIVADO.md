# RB-003_CIRCUIT_BREAKER_ATIVADO — Resposta a Circuit Breaker

**ID:** `RB-003` | **Trigger:** Qualquer circuit breaker ativado | **Severidade:** CRITICAL
**Fase:** #phase/1-15 | **Owner:** Risk Manager | **Status:** #status/active

---

## 1. SINTOMA
- Alerta P1 recebido via PagerDuty
- Dashboard mostra circuit breaker "ACTIVE"
- Motor de decisão parado automaticamente

## 2. IMPACTO
- Operações de apostas pausadas
- Perda de oportunidades durante incidente
- Potencial perda financeira se não resolvido rapidamente

## 3. MITIGAÇÃO IMEDIATA (0-5 minutos)
1. Receber alerta e identificar qual circuit breaker disparou
2. Confirmar que motor de decisão está parado
3. Notificar equipa via Telegram ops_alertas: "Circuit breaker [ID] ativado"
4. Marcar Risk Manager na mensagem

## 4. DIAGNÓSTICO DETALHADO (5-30 minutos)

### 4.1 Identificar Qual Circuit Breaker Disparou

```bash
# Verificar estado dos circuit breakers
curl http://localhost:8000/api/v1/circuit-breakers/status

# Resposta esperada:
# {
#   "alpha_drawdown": "TRIGGERED",
#   "beta_consecutive_losses": "MONITORING",
#   "gamma_feed_offline": "CLOSED",
#   "delta_roi_30d": "CLOSED"
# }
```

### 4.2 Diagnóstico por Tipo de Circuit Breaker

**Alpha (Drawdown > 15%):**
```bash
# Verificar drawdown atual
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT 
    MAX(equity) as high_watermark,
    current_equity,
    (MAX(equity) - current_equity) / MAX(equity) as drawdown_pct
FROM bankroll_history;
"

# Verificar quando começou o drawdown
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT date, bankroll_end 
FROM bankroll_history 
WHERE bankroll_end = (SELECT MAX(bankroll_end) FROM bankroll_history);
"
```

**Beta (7 perdas consecutivas):**
```bash
# Verificar sequência de perdas
docker exec postgres psql -U vb_admin -d valuebetting -c "
WITH streak AS (
    SELECT result,
           ROW_NUMBER() OVER (ORDER BY execution_timestamp) -
           ROW_NUMBER() OVER (PARTITION BY result ORDER BY execution_timestamp) as grp
    FROM bets
    WHERE result IN ('win', 'loss')
    ORDER BY execution_timestamp DESC
    LIMIT 20
)
SELECT result, COUNT(*) as streak_length
FROM streak
WHERE grp = (SELECT grp FROM streak LIMIT 1)
GROUP BY result;
"
```

**Gamma (Feed offline > 5min):**
```bash
# Verificar última ingestão de odds
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT MAX(ingested_at) as last_ingestion 
FROM raw_odds;
"

# Verificar logs do pipeline
docker logs --tail 50 data-pipeline | grep -i "error\|timeout\|connection"
```

**Delta (ROI < -5% em 30 dias):**
```bash
# Calcular ROI dos últimos 30 dias
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT 
    SUM(pnl) / SUM(stake_executed) as roi_30d,
    COUNT(*) as n_bets,
    AVG(clv) as avg_clv
FROM bets
WHERE execution_timestamp >= NOW() - INTERVAL '30 days'
AND result IN ('win', 'loss');
"
```

---

## 5. RESOLUÇÃO DETALHADA (30-60 minutos)

### 5.1 Alpha — Drawdown > 15%

**Ação:**
1. **Reduzir stakes 50%** (ajustar Kelly fraction de 0.5 para 0.25)
2. **Verificar CLV** dos últimos 7 dias:
   - Se CLV > 0: drawdown é variação estatística normal, manter reduzido
   - Se CLV < 0: modelo degradado, agendar retreino urgente
3. **Documentar** decisão no canal de ops
4. **Agendar** revisão em 48 horas

```python
# Reduzir stakes no sistema
from risk_management import KellyCalculator

kelly = KellyCalculator()
kelly.set_global_fraction(0.25)  # Reduzir para quarter Kelly
logger.critical("Circuit breaker Alpha: Kelly reduzido para 0.25")
```

**Critério de Reset:**
- Drawdown recuperou para < 10% OU
- 48 horas passaram com CLV positivo e drawdown estável

### 5.2 Beta — 7 Perdas Consecutivas

**Ação:**
1. **Verificar CLV** das apostas perdidas
2. **Se CLV médio > 0:** variação estatística, continuar com stakes reduzidas (Kelly 0.25)
3. **Se CLV médio < 0:** investigar degradação de modelo
4. **Reset:** Após 3 vitórias consecutivas OU após 24h com CLV positivo

### 5.3 Gamma — Feed Offline > 5min

**Ação:**
1. **Verificar** se feed está online: `curl https://api.betfair.com/exchange/betting/rest/v1.0/listEventTypes/`
2. **Se feed online:** reset circuit breaker, continuar operações
3. **Se feed offline:**
   - Verificar credenciais Betfair
   - Verificar rate limiting
   - Verificar conectividade de rede
   - Se não resolver em 15 min: parar operações até feed voltar

### 5.4 Delta — ROI < -5% em 30 dias

**Ação:**
1. **Analisar** métricas de qualidade:
   - ROC-AUC dos últimos 7 dias
   - Feature drift (PSI)
   - Calibration drift (ECE)
2. **Se métricas saudáveis:** variação estatística, continuar com stakes reduzidas
3. **Se métricas degradadas:**
   - Parar operações
   - Agendar retreino urgente
   - Usar modelo anterior (rollback) se disponível

---

## 6. VERIFICAÇÃO PÓS-RESOLUÇÃO (5-10 minutos)

```bash
# 1. Circuit breaker em estado MONITORING ou CLOSED
curl http://localhost:8000/api/v1/circuit-breakers/status | grep -v TRIGGERED

# 2. Sinais estão a ser gerados novamente
curl http://localhost:8000/api/v1/signals/recent | jq '.signals | length'
# Esperado: > 0 (se há jogos)

# 3. Stakes estão reduzidas (se Alpha/Beta)
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT AVG(kelly_fraction) FROM bets 
WHERE execution_timestamp >= NOW() - INTERVAL '1 hour';
"
# Esperado: <= 0.25 (se reduzido)

# 4. Sem erros nos logs
docker logs --tail 20 api | grep -i "error\|circuit" || echo "Sem erros"
```

**Critérios de Passagem:**
- [ ] Circuit breaker não está TRIGGERED
- [ ] Motor de decisão gera sinais (se mercado aberto)
- [ ] Stakes estão dentro dos limites definidos
- [ ] Logs não mostram erros críticos

---

## 7. PREVENÇÃO

### 7.1 Monitorização Proativa

```yaml
# prometheus.yml
rules:
  - alert: CircuitBreakerApproachingAlpha
    expr: (bankroll_high_watermark - current_equity) / bankroll_high_watermark > 0.12
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Drawdown a 12%, próximo de 15% (Alpha)"
      runbook_url: "https://wiki.internal/RB-003"

  - alert: CircuitBreakerApproachingBeta
    expr: consecutive_losses > 5
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "5 perdas consecutivas, próximo de 7 (Beta)"
```

### 7.2 Revisões Regulares

- **Diária:** Verificar estado de todos os circuit breakers
- **Semanal:** Analisar métricas que se aproximaram dos thresholds
- **Mensal:** Revisar se thresholds ainda são adequados

---

## 8. ESCALADA

| Tempo | Ação | Destino |
|-------|------|---------|
| 0 min | Alerta disparado | Risk Manager (Telegram) |
| 15 min | Se não resolvido | Operations Lead |
| 30 min | Se não resolvido | CTO |
| 60 min | Se drawdown > 20% | Declarar incidente maior |

---

## 9. LINKS CRUZADOS

- [[25_SOPs/SOP-004_Resposta_Circuit_Breaker]] → SOP detalhado
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Detalhes técnicos
- [[08_Risk_Management/DRAWDOWN_CONTROL]] → Controle de drawdown
- [[33_Alerting/THRESHOLDS_ALERTAS]] → Thresholds de alertas