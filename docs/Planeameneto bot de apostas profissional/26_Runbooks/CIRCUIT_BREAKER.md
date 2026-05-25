# CIRCUIT_BREAKER — Runbook de Circuit Breaker

**ID:** `RB-CB` | **Severidade:** High | **Status:** #status/active

---

## 1. SINTOMAS

- Circuit breaker ativado automaticamente
- Apostas pausadas
- Drawdown acelerado detetado

---

## 2. DIAGNÓSTICO

```sql
-- Check drawdown atual
SELECT 
  current_bankroll,
  peak_bankroll,
  (current_bankroll - peak_bankroll) / peak_bankroll as drawdown_pct
FROM bankroll_history
ORDER BY date DESC LIMIT 1;

-- Check sequência de perdas
SELECT COUNT(*) as consecutive_losses
FROM bets
WHERE pnl < 0
AND bet_time >= (
  SELECT MAX(bet_time) FROM bets WHERE pnl >= 0
);
```

---

## 3. RESOLUÇÃO

1. Verificar drawdown atual
2. Identificar causa das perdas
3. Decidir: pausar ou reduzir stake
4. Se pausar, investigar modelo
5. Se reduzir stake, implementar redução
6. Monitorizar recuperação
7. Desativar circuit breaker quando estável

---

## 4. VERIFICAÇÃO

- Drawdown estabilizado
- Stake ajustado aplicado
- Sistema pronto para retomar

---

## 5. LINKS CRUZADOS

- [[26_Runbooks/INDEX]] ← Secção mãe
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Circuit breakers
