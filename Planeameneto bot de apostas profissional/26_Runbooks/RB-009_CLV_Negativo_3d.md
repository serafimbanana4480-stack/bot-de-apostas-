# RB-009 — CLV Negativo por 3 Dias

**ID:** `RB-009` | **Severidade:** High | **Status:** #status/active

---

## 1. SINTOMAS

- CLV médio < -2% por 3 dias consecutivos
- ROI negativo sustentado
- Modelo não está encontrando edge

---

## 2. DIAGNÓSTICO

```sql
-- Check CLV recente
SELECT 
  DATE(bet_time) as date,
  AVG(clv) as avg_clv,
  COUNT(*) as num_bets,
  SUM(pnl) as total_pnl
FROM bets
WHERE bet_time >= NOW() - INTERVAL '7 days'
GROUP BY DATE(bet_time)
ORDER BY date DESC;
```

---

## 3. RESOLUÇÃO

1. Pausar novas apostas temporariamente
2. Investigar drift de features
3. Verificar se odds reference mudou
4. Verificar se mercado mudou (ex: nova temporada)
5. Se necessário, re-treinar modelo
6. Validar em backtest antes de retomar

---

## 4. VERIFICAÇÃO

- CLV volta a positivo em backtest recente
- Modelo validado
- Apostas retomadas com sucesso

---

## 5. LINKS CRUZADOS

- [[26_Runbooks/INDEX]] ← Secção mãe
- [[37_CLV_Analytics/INDEX]] → Análise CLV
