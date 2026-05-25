# 37_CLV_Analytics — INDEX

**ID:** `SEC-37` | **Fase:** #phase/4-15 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Analisar o CLV (Closed Line Value) em profundidade: por regime, por mercado, por dia, e ao longo do tempo. Identificar onde o edge é mais forte e onde está a degradar-se.

---

## 2. DIMENSÕES DE ANÁLISE

| Dimensão | Porque Importa | Ficheiro |
|----------|----------------|----------|
| Regime (favorito/equilibrado/underdog) | Calibração difere por regime | [[CLV_POR_REGIME]] |
| Casa vs Fora | Contexto altera eficiência | [[CLV_CASA_FORA]] |
| Dia da semana | Padrões de mercado | [[CLV_DIA_SEMANA]] |
| Back-to-back | Fadiga física | [[CLV_BACK_TO_BACK]] |
| Mês da época | Ritmo de jogo muda | [[CLV_MES_EPOCA]] |
| Mercado (ML vs Spread) | Eficiência relativa | [[CLV_POR_MERCADO]] |

---

## 3. DECOMPOSIÇÃO DE PnL

```
PnL_total = PnL_skill + PnL_luck + PnL_execution

PnL_skill = turnover * CLV_teorico * (1 - comissao)
PnL_execution = turnover * (CLV_real - CLV_teorico) * (1 - comissao)
PnL_luck = PnL_total - PnL_skill - PnL_execution
```

**Objetivo:** Maximizar PnL_skill (edge real). Minimizar diferença entre CLV_real e CLV_teorico (slippage).

---

## 4. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[03_Quant_Research/INDEX]] → Fundamentos de CLV
- [[36_KPIs/INDEX]] → KPIs que incluem CLV
