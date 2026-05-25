# VARIANCE_SHARPE_RATIO — Medida de Performance Ajustada ao Risco

**ID:** `QUANT-015` | **Fase:** #phase/2-6 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Explicar o conceito de Sharpe Ratio e Variance, e como estas métricas são usadas para avaliar a qualidade de um sistema de value betting para além do ROI simples.

---

## 2. VARIÂNCIA (VOLATILIDADE)

### 2.1 Definição

Variância mede o quão dispersos são os retornos em torno da média.

```
Variância = (1/n) × Σ (r_i - r_média)²
```

Onde:
- r_i = retorno da aposta i
- r_média = retorno médio de todas as apostas
- n = número de apostas

### 2.2 Desvio Padrão

```
Desvio Padrão (σ) = √Variância
```

### 2.3 Interpretação

- **Alta variância:** Retornos muito irregulares, ganhos grandes seguidos de perdas grandes
- **Baixa variância:** Retornos mais consistentes, previsíveis

**Exemplo:**
- Sistema A: ROI 10% com σ = 30% (muito arriscado)
- Sistema B: ROI 5% com σ = 5% (mais consistente)

Sistema B é preferível apesar de ROI menor, porque é mais previsível.

---

## 3. SHARPE RATIO

### 3.1 Definição

Sharpe Ratio é uma métrica de performance ajustada ao risco. Mede o retorno por unidade de risco.

```
Sharpe = (R_média - R_livre_de_risco) / σ
```

Onde:
- R_média = retorno médio do sistema
- R_livre_de_risco = retorno de um investimento sem risco (ex: 0% para apostas)
- σ = desvio padrão dos retornos

### 3.2 Simplificado para Apostas

Como não temos "livre de risco" em apostas (o dinheiro está sempre em risco):

```
Sharpe = ROI_médio / σ
```

### 3.3 Interpretação

| Sharpe Ratio | Classificação | Significado |
|--------------|--------------|-------------|
| < 0.3 | Ruim | Retorno não compensa o risco |
| 0.3 - 0.5 | Aceitável | Retorno marginalmente compensa risco |
| 0.5 - 0.7 | Bom | Retorno bem compensa risco |
| > 0.7 | Excelente | Retorno muito compensa risco |
| > 1.0 | Excepcional | Retorno excepcionalmente compensa risco |

---

## 4. CÁLCULO PRÁTICO

### 4.1 Exemplo Numérico

```
Apostas: 100
Retornos individuais: [+0.05, -0.10, +0.15, -0.05, +0.20, ...]
ROI médio: +0.05 (5%)
Desvio padrão: 0.10 (10%)

Sharpe = 0.05 / 0.10 = 0.5
```

### 4.2 Sharpe Rolling

Sharpe é tipicamente calculado em janelas deslizantes:
- Sharpe 50 apostas: últimas 50 apostas
- Sharpe 100 apostas: últimas 100 apostas
- Sharpe rolling: média móvel com janela fixa

Isto permite monitorizar se o sistema está a manter consistência ao longo do tempo.

---

## 5. VARIÂNCIA EM SISTEMAS DE APOSTAS

### 5.1 Fontes de Variância

1. **Variância de Mercado:** Odds mudam, resultados são aleatórios
2. **Variância de Modelo:** Modelo comete erros de previsão
3. **Variância de Execução:** Slippage, fill rate imperfeito
4. **Variância de Stake:** Tamanhos de aposta variam

### 5.2 Como Reduzir Variância

1. **Diversificação:** Apostar em múltiplos jogos, mercados
2. **Sizing consistente:** Usar Kelly fracionado (não full Kelly)
3. **Filtros de qualidade:** Meta-labeling para reduzir apostas de baixa confiança
4. **Limites de exposição:** Máximo por jogo, por dia, total

---

## 6. SHARPE RATIO NO CONTEXTO DE VALUE BETTING

### 6.1 Target vs. Aceitável

**Target:** Sharpe > 0.5
**Aceitável inicial:** Sharpe > 0.3
**Excelente:** Sharpe > 0.7

### 6.2 Comparação com Outras Classes de Ativos

- **Índices S&P 500:** Sharpe ~0.4-0.6
- **Hedge Funds:** Sharpe ~1.0-2.0
- **Value Betting systems bons:** Sharpe 0.5-1.0

Um Sharpe de 0.5-0.7 é competitivo com fundos profissionais.

### 6.3 Limitações

Sharpe assume:
- Retornos são normalmente distribuídos (nem sempre verdade)
- Volatilidade é constante (muda ao longo do tempo)
- Sem correlação temporal (apostas podem estar autocorrelacionadas)

Por isso, Sharpe deve ser usado em conjunto com outras métricas.

---

## 7. MÉTRICAS COMPLEMENTARES

### 7.1 Sortino Ratio

Variante do Sharpe que usa apenas downside deviation (volatilidade negativa).

```
Sortino = ROI_médio / σ_downside
```

Onde σ_downside é calculado apenas com retornos negativos.

**Vantagem:** Penaliza apenas perdas, não ganhos extremos.

### 7.2 Calmar Ratio

```
Calmar = ROI_anual / Max_Drawdown
```

**Interpretação:** Quanto ROI anual por unidade de drawdown máximo.

### 7.3 Omega Ratio

```
Omega = (Ganhos acima de threshold) / (Perdas abaixo de threshold)
```

**Vantagem:** Captura assimetria de retornos (preferência por ganhos grandes).

---

## 8. MONITORIZAÇÃO EM PRODUÇÃO

### 8.1 Dashboard

Painel "Risk-Adjusted Performance" com:
- Sharpe Ratio rolling 50/100/500
- Sortino Ratio rolling
- Drawdown atual vs. histórico
- Comparação com target (Sharpe > 0.5)

### 8.2 Alertas

- Sharpe 50 < 0.3 por 7 dias → Warning
- Sharpe 100 < 0.3 por 14 dias → Critical (investigar)
- Sharpe tendência decrescente → Investigar drift

---

## 9. OTIMIZAÇÃO DE SHARPE RATIO

### 9.1 Aumentar Retorno

- Melhorar modelo (mais edge)
- Encontrar mais oportunidades (mais apostas)
- Otimizar thresholds de entrada

### 9.2 Reduzir Variância

- Meta-labeling (filtro de qualidade)
- Diversificação (mais jogos, mercados)
- Stake sizing mais conservador
- Limites de exposição

### 9.3 Trade-off

Muitas vezes, reduzir variância (filtros mais rigorosos) reduz também retorno. Otimizar Sharpe é encontrar o equilíbrio.

---

## 10. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]] ← Fundamentos estatísticos
- [[06_Backtesting/INDEX]] → Validação de Sharpe no backtest
- [[36_KPIs/INDEX]] → KPIs financeiros incluindo Sharpe