# PIPELINE_PROPS — Player Props NBA

**ID:** `PP-001` | **Fase:** #phase/6 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Expandir para mercados de Player Props (pontos, ressaltos, assistencias) com pipeline dedicado.

---

## 2. MERCADOS

| Mercado | Descricao | Dados Necessarios |
|---------|-----------|-------------------|
| PTS Over/Under | Pontos do jogador | Box scores historicos |
| REB Over/Under | Ressaltos | Box scores historicos |
| AST Over/Under | Assistencias | Box scores historicos |
| PRA (PTS+REB+AST) | Combinado | Box scores historicos |

---

## 3. FEATURES ESPECIFICAS

```python
player_features = {
    "pts_last5": float,      # Media pontos ultimos 5
    "pts_vs_opponent": float, # Historico contra esta equipa
    "minutes_last5": float,   # Minutos jogados (proxy para uso)
    "usage_rate": float,      # Taxa de uso da posse
    "is_starter": bool,       # Titular ou suplente
    "opponent_def_rating": float, # Rating defensivo adversario
}
```

---

## 4. CHALLENGES

- Dados mais esparsos (jogador pode nao jogar)
- Mercados mais iliquidos (slippage maior)
- Lesoes tem impacto direto

---

## 5. BACKLOG

- [ ] Implementar ingestao de box scores a nivel de jogador
- [ ] Construir modelo de previsao de props
- [ ] Validar com backtest dedicado

---

## 6. LINKS CRUZADOS

- [[42_Player_Props/INDEX]] ← Secao mae
- [[05_Machine_Learning/INDEX]] → Modelos
