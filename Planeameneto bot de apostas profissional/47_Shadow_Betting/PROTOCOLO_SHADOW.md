# PROTOCOLO_SHADOW — Simulacao Multi-Casa

**ID:** `SH-001` | **Fase:** #phase/3 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Simular apostas em 3+ casas sem execucao real para medir o True CLV e validar que o edge existe independentemente da casa.

---

## 2. CASAS SIMULADAS

| Casa | Fonte Odds | Razao |
|------|-----------|-------|
| Pinnacle | Kaggle / Repositorios publicos | Referencia mundial |
| Betfair Exchange | API oficial | Exchange real (usado em prod) |
| Casa tradicional X | Scraping limitado | Mercado mais lento (odds mais faceis) |

---

## 3. FLUXO

```
1. Sinal aprovado pelo motor de value
2. Sistema regista odd disponivel em cada casa
3. Apos o jogo, recolhe odd de fecho em cada casa
4. Calcula CLV_expost para cada casa
5. Relatorio: True CLV = media ponderada
```

---

## 4. METRICAS

| Metrica | Target | Interpretacao |
|---------|--------|---------------|
| True CLV medio | > 1.5% | Edge real existe |
| Dispersao de CLV | < 2% | Edge e robusto entre casas |
| Fill rate simulado | > 80% | Apostas seriam executaveis |
| Slippage shadow vs backtest | < 1% | Backtest nao e otimista |

---

## 5. BACKLOG

- [ ] Implementar simulacao para 3 casas
- [ ] Criar relatorio diario automatico
- [ ] Documentar diferencas entre casas

---

## 6. LINKS CRUZADOS

- [[47_Shadow_Betting/INDEX]] ← Secao mae
- [[03_Quant_Research/CLV_CLOSED_LINE_VALUE]] → Definicao de CLV
