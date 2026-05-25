# 45_Bookmaker Analysis — INDEX

**ID:** `SEC-45` | **Fase:** #phase/3-6 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Analisar as características de cada casa de apostas: odds oferecidas, liquidez, velocidade de ajuste, comissões, e fiabilidade. Identificar a melhor casa para cada mercado e fase.

---

## 2. NOTAS FUNDAMENTAIS

- [[BOOKMAKER_COMPARISON]] — Comparação detalhada de casas (exchanges, sharp books, soft books)
- [[LIQUIDEZ_ODDS]] — Análise de liquidez, odds e métricas por casa
- [[SHARP_MONEY_TRACKING]] — Rastreamento de sharp money e movimentos de linha
- [[SOFT_BOOKS_ANALYSIS]] — Análise de soft books vs sharp books
- [[ARBITRAGEM_BOOKMAKERS]] — Estratégias de arbitragem entre bookmakers
- [[LINE_SHOPPING]] — Estratégias de line shopping (encontrar melhor linha)
- [[GESTAO_MULTIPLAS_CONTAS]] — Gestão de contas em múltiplos bookmakers
- [[RISCOS_LIMITACAO]] — Riscos de limitação/banimento e mitigação
- [[DIVERSIFICACAO_CONTAS]] — Estratégias de diversificação de contas

---

## 3. CASAS ANALISADAS

| Casa | Tipo | Liquidez NBA | Comissão | API | Notas |
|------|------|--------------|----------|-----|-------|
| Betfair Exchange | Exchange | Alta | 5% | Sim | Escolha principal |
| Pinnacle | Sharp | Muito alta | ~2% | Limitada | Referência de odds |
| Smarkets | Exchange | Média | 2% | Sim | Alternativa |
| Matchbook | Exchange | Baixa | 1.5% | Sim | Niche |

---

## 4. ESTRUTURA DE DOCUMENTAÇÃO

### 4.1 Documentação Existente
- **BOOKMAKER_COMPARISON.md (BA-001):** Comparação completa de casas de apostas com análise detalhada de exchanges, sharp books e soft books
- **LIQUIDEZ_ODDS.md (BK-001):** Análise de liquidez, overround, slippage e velocidade de ajuste por casa
- **SHARP_MONEY_TRACKING.md (BA-002):** Rastreamento de sharp money, line movement e indicadores de CLV

### 4.2 Documentação Criada
- **SOFT_BOOKS_ANALYSIS.md (BK-002):** Análise comparativa entre soft books e sharp books, estratégias para cada tipo
- **ARBITRAGEM_BOOKMAKERS.md (BK-003):** Estratégias de arbitragem (surebets), deteção de oportunidades e gestão de riscos
- **LINE_SHOPPING.md (BK-004):** Técnicas sistemáticas para encontrar a melhor odd entre múltiplas casas
- **GESTAO_MULTIPLAS_CONTAS.md (BK-005):** Gestão de bankroll, alocação de apostas e rotação de contas
- **RISCOS_LIMITACAO.md (BK-006):** Métodos de deteção de limitação, estratégias de mitigação e planos de contingência
- **DIVERSIFICACAO_CONTAS.md (BK-007):** Estratégias de diversificação por tipo, geografia e jurisdição

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[47_Shadow_Betting/INDEX]] → Simulação multi-casa
- [[08_Risk_Management/INDEX]] → Gestão de risco
- [[09_Execution_System/INDEX]] → Sistema de execução
- [[44_Exchange_Execution/INDEX]] → Execução em exchanges
