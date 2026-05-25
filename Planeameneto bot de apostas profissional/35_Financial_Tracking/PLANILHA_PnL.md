# PLANILHA_PnL — Tracking Financeiro

**ID:** `FT-001` | **Fase:** #phase/4 | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. ESTRUTURA DA PLANILHA

| Coluna | Descricao |
|--------|-----------|
| date | Data da aposta |
| game_id | ID do jogo |
| market | Moneyline / Spread |
| selection | Equipa apostada |
| odd_signal | Odd recomendada |
| odd_executed | Odd realmente obtida |
| slippage | (odd_executed - odd_signal) / odd_signal |
| stake | Valor apostado |
| result | Win / Loss |
| pnl | Profit ou Loss |
| commission | Comissao paga |
| net_pnl | pnl - commission |
| clv | (odd_executed / odd_close) - 1 |
| bankroll | Banca apos aposta |

---

## 2. RELATORIOS

### Diario
```sql
SELECT 
    DATE_TRUNC('day', date) as dia,
    COUNT(*) as n_apostas,
    SUM(stake) as turnover,
    SUM(net_pnl) as pnl,
    SUM(net_pnl) / SUM(stake) as roi
FROM bets
GROUP BY 1
ORDER BY 1 DESC;
```

### Semanal
```sql
SELECT 
    DATE_TRUNC('week', date) as semana,
    AVG(clv) as clv_medio,
    SUM(net_pnl) / SUM(stake) as roi
FROM bets
GROUP BY 1;
```

---

## 3. BACKLOG

- [ ] Criar tabela `bets` na base de dados
- [ ] Implementar geracao automatica de relatorios
- [ ] Documentar processo de reconciliacao

---

## 4. LINKS CRUZADOS

- [[35_Financial_Tracking/INDEX]] ← Secao mae
- [[02_Business_Model/INDEX]] → Modelo de negocio
