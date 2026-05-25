# RB-002 — Modelo com Valores Estranhos

**ID:** `RB-002` | **Severidade:** High | **Status:** #status/active

---

## 1. SINTOMAS

- Probabilidades fora do range [0, 1]
- Stake negativo ou extremamente alto
- CLV > 50% ou < -50%

---

## 2. DIAGNÓSTICO

```sql
-- Check probabilidades inválidas
SELECT * FROM predictions 
WHERE probability < 0 OR probability > 1
ORDER BY prediction_time DESC LIMIT 100;

-- Check stakes inválidos
SELECT * FROM bets 
WHERE stake <= 0 OR stake > 1000
ORDER BY bet_time DESC LIMIT 100;
```

---

## 3. RESOLUÇÃO

1. Identificar origem do problema
2. Verificar features de input
3. Verificar versão do modelo
4. Se bug no modelo, rollback para versão anterior
5. Se drift de dados, investigar pipeline

---

## 4. VERIFICAÇÃO

- Valores dentro de ranges normais
- Modelo estável em backtest

---

## 5. LINKS CRUZADOS

- [[26_Runbooks/INDEX]] ← Secção mãe
