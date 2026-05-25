# RB-009_CLV_NEGATIVO — Resposta a CLV Negativo por 3 Dias

**ID:** `RB-009` | **Trigger:** CLV negativo por 3 dias | **Severidade:** HIGH
**Fase:** #phase/1-15 | **Owner:** ML Engineer | **Status:** #status/active

---

## 1. SINTOMA
- Alerta P2 de CLV negativo por 3 dias consecutivos
- CLV médio dos últimos 3 dias < 0%
- Circuit breaker Gamma pode disparar

## 2. IMPACTO
- Modelo pode estar degradado
- Sinais podem não ter edge real
- Perda financeira se continuar

## 3. MITIGAÇÃO IMEDIATA (0-5 minutos)
1. Verificar CLV dos últimos 3 dias
2. Verificar CLV dos últimos 7 e 30 dias
3. Se CLV 30 dias também negativo: problema sério
4. Notificar equipa: "CLV negativo por 3 dias, a investigar"

## 4. DIAGNÓSTICO DETALHADO (5-15 minutos)

### 4.1 Calcular CLV por Período

```bash
# CLV dos últimos 3, 7 e 30 dias
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT 
    '3 dias' as periodo,
    AVG(clv) as clv_medio,
    COUNT(*) as n_apostas,
    SUM(pnl) / SUM(stake_executed) as roi
FROM bets
WHERE execution_timestamp >= NOW() - INTERVAL '3 days'
AND result IN ('win', 'loss')

UNION ALL

SELECT 
    '7 dias',
    AVG(clv),
    COUNT(*),
    SUM(pnl) / SUM(stake_executed)
FROM bets
WHERE execution_timestamp >= NOW() - INTERVAL '7 days'
AND result IN ('win', 'loss')

UNION ALL

SELECT 
    '30 dias',
    AVG(clv),
    COUNT(*),
    SUM(pnl) / SUM(stake_executed)
FROM bets
WHERE execution_timestamp >= NOW() - INTERVAL '30 days'
AND result IN ('win', 'loss');
"
```

### 4.2 Analisar Breakdown por Mercado

```bash
# CLV por tipo de mercado
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT 
    market_type,
    AVG(clv) as clv,
    COUNT(*) as n,
    SUM(pnl) / SUM(stake_executed) as roi
FROM bets
WHERE execution_timestamp >= NOW() - INTERVAL '7 days'
AND result IN ('win', 'loss')
GROUP BY market_type
ORDER BY clv;
"
```

### 4.3 Verificar Métricas do Modelo

```bash
# Verificar AUC e calibração (requer logging de predições)
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT 
    DATE_TRUNC('day', prediction_timestamp) as dia,
    AVG(ABS(prediction_prob - actual_result)) as calibration_error,
    COUNT(*) as n
FROM model_predictions
WHERE prediction_timestamp >= NOW() - INTERVAL '7 days'
GROUP BY 1
ORDER BY 1;
"
```

### 4.4 Matriz de Causas

| Padrão | Causa Provável | Verificação |
|--------|---------------|-------------|
| CLV 3d < 0, CLV 30d > 0 | Variação de curto prazo | Verificar sequência de perdas |
| CLV 3d < 0, CLV 30d < 0 | Problema estrutural | Verificar AUC, drift |
| CLV < 0 em Moneyline, CLV > 0 em Spread | Bias de mercado | Breakdown por mercado |
| CLV < 0 em B2B | Modelo sub-ajusta B2B | Verificar feature is_back_to_back |
| CLV degradou gradualmente | Drift de conceito | Verificar PSI, prediction drift |

---

## 5. RESOLUÇÃO DETALHADA (15-30 minutos)

### 5.1 Caso: Variação de Curto Prazo (CLV 30d > 0)

**Ação:**
1. Reduzir stakes para 50% (Kelly 0.25)
2. Continuar monitorizando CLV diariamente
3. Se CLV 7d voltar a positivo: voltar ao Kelly normal
4. Documentar: "CLV negativo por variância, modelo saudável"

### 5.2 Caso: Problema Estrutural (CLV 30d < 0)

**Ação:**
1. **Parar operações** imediatamente
2. Verificar AUC do modelo nos últimos 7 dias
3. Verificar feature drift (PSI)
4. Se AUC < 0.55 OU PSI > 0.25: modelo degradado

```bash
# Verificar feature drift
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT 
    feature_name,
    psi_value,
    CASE 
        WHEN psi_value > 0.25 THEN 'CRITICAL'
        WHEN psi_value > 0.10 THEN 'WARNING'
        ELSE 'OK'
    END as status
FROM feature_drift_monitoring
WHERE monitoring_date = CURRENT_DATE;
"
```

### 5.3 Caso: Bias de Mercado

**Ação:**
1. Se CLV negativo apenas em Moneyline:
   - Ajustar threshold de edge para Moneyline (aumentar edge_min)
   - Ou parar de apostar Moneyline temporariamente
2. Se CLV negativo em underdogs:
   - Verificar se modelo está overconfident em underdogs
   - Recalibrar probabilidades para regime "underdog"

### 5.4 Caso: Degradação de Modelo

**Ação:**
1. Agendar retreino urgente
2. Usar modelo anterior (rollback) se disponível
3. Shadow mode até retreino concluído

```bash
# Rollback para modelo anterior
mlflow models serve -m "models:/nba_value_model/Production" --port 5001
# Verificar versão anterior
# Atualizar API
```

---

## 6. VERIFICAÇÃO PÓS-RESOLUÇÃO (5-10 minutos)

```bash
# 1. CLV dos últimos 3 dias está a melhorar
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT AVG(clv) as clv_3d
FROM bets
WHERE execution_timestamp >= NOW() - INTERVAL '3 days'
AND result IN ('win', 'loss');
"
# Esperado: > -0.01 (tendência de recuperação)

# 2. Stakes reduzidas (se aplicável)
docker exec postgres psql -U vb_admin -d valuebetting -c "
SELECT AVG(kelly_fraction) 
FROM bets 
WHERE execution_timestamp >= NOW() - INTERVAL '1 day';
"
# Esperado: <= 0.25

# 3. Sem erros de modelo nos logs
docker logs --tail 20 api | grep -i "model\|drift\|degrad" || echo "Sem erros"
```

**Critérios de Passagem:**
- [ ] CLV 3d não está a piorar (tendência plana ou positiva)
- [ ] Stakes ajustadas ao nível de risco
- [ ] Modelo AUC > 0.55 (se testado)
- [ ] Sem alertas de drift ativos

---

## 7. PREVENÇÃO

```yaml
# prometheus.yml
rules:
  - alert: CLVTrendingNegative
    expr: avg_over_time(clv_1d[3d]) < -0.02
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "CLV trending negative"
      runbook_url: "https://wiki.internal/RB-009"

  - alert: CLVCriticalNegative
    expr: avg_over_time(clv_1d[7d]) < -0.03
    for: 1h
    labels:
      severity: high
    annotations:
      summary: "CLV negative for 7 days"
```

---

## 8. ESCALADA

| Condição | Ação | Destino |
|----------|------|---------|
| CLV 3d < 0 | Investigar | ML Engineer |
| CLV 7d < 0 | Escalar | Operations Lead |
| CLV 14d < 0 | Parar operações | CTO |
| AUC < 0.55 | Retreino urgente | ML Engineer |

---

## 9. LINKS CRUZADOS

- [[03_Quant_Research/CLV_CLOSED_LINE_VALUE]] → Detalhes de CLV
- [[05_Machine_Learning/MONITORIZACAO_DRIFT]] → Deteção de drift
- [[05_Machine_Learning/MODEL_REGISTRY]] → Rollback de modelo
- [[26_Runbooks/RB-003_CIRCUIT_BREAKER_ATIVADO]] → Circuit breaker