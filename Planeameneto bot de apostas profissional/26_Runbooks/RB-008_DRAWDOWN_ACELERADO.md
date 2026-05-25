# RB-008_DRAWDOWN_ACELERADO — Resposta a Drawdown Acelerado

**ID:** `RB-008` | **Trigger:** Drawdown > 10% em 48h | **Severidade:** CRITICAL
**Fase:** #phase/1-15 | **Owner:** Risk Manager | **Status:** #status/active

---

## 1. SINTOMA
- Alerta P1 de drawdown acelerado
- Drawdown aumentou > 10% em 48 horas
- Circuit breaker Alpha pode estar prestes a disparar

## 2. IMPACTO
- Perda financeira acelerada
- Risco de circuit breaker Alpha disparar (drawdown > 15%)
- Potencial perda de confiança de subscritores

## 3. MITIGAÇÃO IMEDIATA (0-5 minutos)
1. Verificar drawdown atual
2. Verificar sequência de perdas
3. Se drawdown > 15%: circuit breaker Alpha já disparou → seguir RB-003
4. Se drawdown 10-15%: continuar com este runbook

## 4. DIAGNÓSTICO DETALHADO (5-15 minutos)

### 4.1 Calcular Drawdown

```bash
# Drawdown atual
docker exec postgres psql -U vb_admin -d valuebetting -c "
WITH daily AS (
    SELECT date, bankroll_end,
           MAX(bankroll_end) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as hwm
    FROM bankroll_history
    WHERE date >= NOW() - INTERVAL '7 days'
)
SELECT 
    date,
    bankroll_end,
    hwm,
    (hwm - bankroll_end) / hwm as drawdown_pct
FROM daily
ORDER BY date DESC
LIMIT 5;
"
```

### 4.2 Analisar Causa

```bash
# Últimas 20 apostas com detalhes
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT 
    bet_id,
    result,
    pnl,
    stake_executed,
    clv,
    execution_timestamp
FROM bets
ORDER BY execution_timestamp DESC
LIMIT 20;
"

# CLV médio dos últimos 7 dias
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT AVG(clv) as clv_7d, COUNT(*) as n_bets
FROM bets
WHERE execution_timestamp >= NOW() - INTERVAL '7 days'
AND result IN ('win', 'loss');
"
```

### 4.3 Matriz de Causas

| Padrão | Causa Provável | Verificação |
|--------|---------------|-------------|
| CLV > 0 mas perdas | Variância estatística | Verificar sequência de perdas |
| CLV < 0 | Modelo degradado | Verificar AUC, PSI, ECE |
| Stake alto + perdas grandes | Overbetting | Verificar se stakes aumentaram |
| Slippage alto | Execução ruim | Verificar slippage médio |
| Perdas em B2B/underdog | Bias de mercado | Verificar breakdown por mercado |

---

## 5. RESOLUÇÃO DETALHADA (15-30 minutos)

### 5.1 Caso: Sequência de Perdas com CLV Positivo

**Ação:**
1. Reduzir stakes para 50% do Kelly normal (de 0.5 para 0.25)
2. Continuar monitorizando CLV a cada 24h
3. Se CLV permanecer > 0 por 72h: voltar ao Kelly normal
4. Documentar no canal de ops: "Drawdown por variância, CLV saudável"

```python
# Implementação
from risk_management import DrawdownController

controller = DrawdownController()
controller.set_kelly_fraction(0.25)  # Reduzir stakes
controller.enable_close_monitoring(interval_hours=6)
```

### 5.2 Caso: Perdas Grandes Individuais

**Ação:**
1. Identificar apostas com perda > 2x stake média
2. Investigar:
   - Odd de fecho muito diferente da odd executada?
   - Jogo teve circunstâncias especiais (lesão, overtime)?
   - Stake foi maior que o normal?
3. Se stake foi excessiva: ajustar limites hard cap
4. Se odd de fecho muito diferente: verificar slippage e timing

### 5.3 Caso: Aumento de Stake

**Ação:**
1. Verificar histórico de stakes:
```bash
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT DATE_TRUNC('week', execution_timestamp) as semana,
       AVG(stake_executed) as stake_medio,
       STDDEV(stake_executed) as stake_std
FROM bets
GROUP BY 1
ORDER BY 1 DESC
LIMIT 4;
"
```
2. Se stake aumentou > 50% vs média: reduzir para nível anterior
3. Investigar por que stakes aumentaram (Kelly full? Banca maior?)

### 5.4 Caso: Degradação de Modelo

**Ação:**
1. Verificar métricas de qualidade do modelo:
```bash
# Verificar AUC dos últimos 7 dias (requer MLflow ou logging)
curl http://localhost:8000/api/v1/model/metrics?days=7
```
2. **Se AUC < 0.55 OU PSI > 0.2:**
   - Parar operações imediatamente
   - Agendar retreino urgente
   - Usar modelo anterior (rollback) se disponível em MLflow
3. **Se ECE > 0.10:** Recalibrar modelo

```bash
# Rollback para modelo anterior (se disponível)
mlflow models serve -m "models:/nba_value_model/Production" --port 5001
# Atualizar API para usar modelo anterior
```

---

## 6. VERIFICAÇÃO PÓS-RESOLUÇÃO (5-10 minutos)

```bash
# 1. Drawdown estabilizou ou recuperou
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT (hwm - bankroll_end) / hwm as drawdown_pct
FROM (
    SELECT MAX(bankroll_end) as hwm, 
           (SELECT bankroll_end FROM bankroll_history ORDER BY date DESC LIMIT 1) as bankroll_end
    FROM bankroll_history
) x;
"
# Esperado: < 10% (se reduzimos stakes e drawdown estabilizou)

# 2. Stakes estão reduzidas
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT AVG(kelly_fraction) as kelly_atual
FROM bets
WHERE execution_timestamp >= NOW() - INTERVAL '1 hour';
"
# Esperado: <= 0.25

# 3. CLV positivo nos últimos 3 dias
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT AVG(clv) as clv_3d
FROM bets
WHERE execution_timestamp >= NOW() - INTERVAL '3 days'
AND result IN ('win', 'loss');
"
# Esperado: > 0
```

**Critérios de Passagem:**
- [ ] Drawdown estabilizou (não aumentou nas últimas 6h)
- [ ] Stakes reduzidas para nível defensivo
- [ ] CLV positivo nos últimos 3 dias (se modelo saudável)
- [ ] Nenhum erro de modelo nos logs

---

## 7. PREVENÇÃO

### 7.1 Alertas Precoces

```yaml
# prometheus.yml
rules:
  - alert: DrawdownApproaching10
    expr: (bankroll_hwm - current_bankroll) / bankroll_hwm > 0.10
    for: 1m
    labels:
      severity: high
    annotations:
      summary: "Drawdown atingiu 10%"
      runbook_url: "https://wiki.internal/RB-008"

  - alert: ConsecutiveLossesIncreasing
    expr: consecutive_losses > 4
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "4 perdas consecutivas"
```

### 7.2 Revisões Regulares

- **Diária:** Verificar drawdown e CLV
- **Semanal:** Analisar padrões de perdas
- **Mensal:** Revisar se limites de drawdown são adequados

---

## 8. ESCALADA

| Condição | Ação | Destino |
|----------|------|---------|
| Drawdown > 15% | Circuit breaker Alpha | RB-003 |
| Drawdown > 20% | Incidente maior | CTO + todos |
| Não resolvido em 24h | Escalar | CTO |
| Modelo degradado | Retreino urgente | ML Engineer |

---

## 9. LINKS CRUZADOS

- [[08_Risk_Management/DRAWDOWN_CONTROL]] → Controle de drawdown
- [[08_Risk_Management/KELLY_FRACIONADO]] → Gestão de stake
- [[26_Runbooks/RB-003_CIRCUIT_BREAKER_ATIVADO]] → Circuit breaker Alpha
- [[05_Machine_Learning/MONITORIZACAO_DRIFT]] → Monitorização de modelo