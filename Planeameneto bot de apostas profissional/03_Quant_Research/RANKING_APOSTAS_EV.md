# Protocolo de Ordenação e Seleção de Apostas (Ranking EV)

**Versão:** 1.0.0  
**Status:** #status/active #priority/high  
**Área:** Quant Research / Execução

---

## 🎯 RACIONAL
Em noites de intensa atividade na NBA, o sistema pode identificar múltiplos sinais de valor em paralelo (ex: 8 a 12 jogos com valor esperado positivo). Executar todas as apostas indiscriminadamente pode levar ao sobre-dimensionamento do risco e a correlações indesejadas de carteira.

Este documento define o framework de **Ranking EV** e o seletor **Best-N** para filtrar e priorizar as apostas com maior probabilidade e maior vantagem real.

---

## 📈 FÓRMULA DO ESPERADO OPERACIONAL (EXPECTED VALUE - EV)

Para cada oportunidade de aposta $i$:
$$EV_i = (P_{i,\text{calibrada}} \times \text{Odds}_{i,\text{bookmaker}}) - 1.0$$

### Categoria de Confiança por Desvio (Z-Score do Histórico):
Comparamos o $EV_i$ atual contra a distribuição histórica de vantagens reais observadas nos testes de cross-validation:
$$\text{Z-Score}_{EV} = \frac{EV_i - \mu_{EV,\text{histórico}}}{\sigma_{EV,\text{histórico}}}$$

- **Oportunidade Premium:** $\text{Z-Score}_{EV} > 1.5$ (Alta probabilidade de edge não precificado pelo bookmaker).
- **Oportunidade Standard:** $0.0 \le \text{Z-Score}_{EV} \le 1.5$.
- **Oportunidade Rejeitada:** $\text{Z-Score}_{EV} < 0.0$ (Sem valor matemático esperado).

---

## 🛠️ MECANISMO DE SELEÇÃO BEST-N

Quando o número de sinais aprovados exceder $N$ (onde $N=4$ por noite, padrão de gerenciamento de risco da banca):

```
Sinais Candidatos (EV > 0)
       │
       ▼
Ordenar por EV Decrescente
       │
       ▼
Filtrar por Exclusão de Correlação (Max 1 time por divisão geográfica)
       │
       ▼
Selecionar as N Melhores (Best-N)
```

### Exemplo Prático de Filtragem:
Se tivermos 5 jogos identificados:
1. `BOS vs LAL` (EV: 8.5%)
2. `MIA vs MIL` (EV: 7.2%)
3. `GSW vs PHX` (EV: 5.1%)
4. `NYK vs BKN` (EV: 4.8%)
5. `DEN vs UTA` (EV: 3.2%)

Com $N=3$ selecionamosBoston, Miami e Golden State. Os restantes são guardados para fins de monitorização em paper trading, mas não recebem stakes financeiras reais.
