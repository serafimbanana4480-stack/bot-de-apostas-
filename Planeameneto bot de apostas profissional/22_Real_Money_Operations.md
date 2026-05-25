# 22_REAL_MONEY_OPERATIONS — Índice de Operações com Dinheiro Real

**ID:** `SEC-22` | **Fase:** #phase/4+ | **Owner:** Operations Lead | **Status:** #status/pending  
**Última Atualização:** `2026-05-13`

---

## PROPÓSITO

Esta secção documenta todos os processos, protocolos e decisões relacionados com operações reais de apostas — desde a micro-banca inicial até à escala de banca.

**⚠️ ATENÇÃO: Nenhuma aposta real antes de:**
1. Shadow mode completo (Fase 3) com CLV > 2% consistente
2. Paper trading validado (Fase 3)
3. Aprovação explícita do Chief Systems Architect

---

## DOCUMENTOS DESTA SECÇÃO

| Ficheiro | Descrição | Fase |
|----------|-----------|------|
| [[22_Real_Money_Operations/INDEX]] | Índice completo, protocolos e pré-requisitos | 4 |
| [[22_Real_Money_Operations/MICRO_BANCA_PROTOCOL]] | Protocolo micro-banca 500-1000€, gestão e tracking | 4 |

---

## FASES DE OPERAÇÃO COM DINHEIRO REAL

```
FASE 4 (Mês 4): Micro-banca 500-1000€ na Betfair
    └── Máx 2% por aposta, máx 12% por dia
    └── Tracking rigoroso de divergência backtest vs real
    └── Stop loss: -20% banca → pausar automático

FASE 5 (Mês 5): Estabilização
    └── Ajuste de parâmetros com dados reais
    └── Lançamento tipster com resultados verificáveis

FASE 8 (Mês 9-12): Escala de banca
    └── 2.000€ → 5.000€ → 10.000€
    └── Apenas se ROI real > 3% com significância estatística
```

---

## LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Índice mestre
- [[08_Risk_Management/INDEX]] → Kelly, drawdown, circuit breakers
- [[09_Execution_System/INDEX]] → Execução de apostas
- [[21_Paper_Trading/INDEX]] → Paper trading (pré-dinheiro real)
- [[47_Shadow_Betting/INDEX]] → Shadow mode (pré-dinheiro real)
- [[35_Financial_Tracking/INDEX]] → Tracking financeiro e PnL
