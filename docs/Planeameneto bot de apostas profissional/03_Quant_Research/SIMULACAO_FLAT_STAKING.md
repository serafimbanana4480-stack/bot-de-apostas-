# Simulação de Backtesting via Flat Staking (1% Fixo)

**Versão:** 1.0.0  
**Status:** #status/active #priority/high  
**Área:** Backtesting / Risco

---

## 🎯 RACIONAL
Embora o Critério de Kelly Fracionário (`KELLY_MULTIPLIER = 0.25`) seja matematicamente ideal para maximizar o crescimento geométrico da banca no longo prazo, ele é extremamente sensível a erros de especificação de probabilidade (overconfidence do modelo). 

Este documento estabelece o protocolo de simulação e comparação usando **Flat Staking de 1% fixo da banca inicial** como baseline de segurança contra a ruína financeira.

---

## 📊 FRAMEWORK COMPARATIVO: KELLY VS FLAT STAKING

| Dimensão | Flat Staking (1% Fixo) | Kelly Fracionário (0.25) | Racional Quantitativo |
|----------|------------------------|--------------------------|------------------------|
| **Risco de Ruína** | Praticamente 0% em 1000 apostas | < 2% com cap rígido de 10% | Flat staking ignora volatilidade pontual de probabilidade. |
| **Simplicidade** | Máxima. Nenhuma dependência da calibragem exata do modelo. | Depende 100% da calibração isotônica. | Se a calibração falhar, Kelly destrói a banca rapidamente. |
| **Drawdown Máximo** | Linear e previsível. | Exponencial nas fases de cauda (bad runs). | Kelly exige estômago e banca resiliente. |

---

## 🛠️ LOGIC DE EXECUÇÃO DO SIMULADOR (FILTRO DE VALOR)

Para cada jogo no histórico (2019-2025) onde:
$$\text{Edge}_{\text{estimado}} \ge 4.0\%$$

### Regra do Flat Staking:
- **Aposta:** Exatamente $1.0\%$ da banca inicial (ex: 10€ para uma banca de 1000€).
- **Retorno:** Se vencer, recebe $\text{Stake} \times (\text{Odds} - 1.0)$. Se perder, perde a $\text{Stake}$.

### Métricas de Saída da Simulação:
1. **ROI Real (Return on Investment):** $\frac{\text{Lucro Total}}{\text{Volume Total Apostado}}$
2. **Sharpe Ratio Operacional:** $\frac{\text{Retorno Médio Diário} - R_f}{\sigma_{\text{Retornos Diários}}}$
3. **Drawdown Máximo Absoluto:** Maior queda do pico ao vale no gráfico de PnL acumulado.

---

## 📈 ANÁLISE DE DADOS HISTÓRICOS (EXEMPLO DE CALIBRAÇÃO)
As simulações históricas com dados reais de NBA indicam que um filtro rígido de Flat Staking a 1% obtém retornos mais estáveis sob regimes de alta volatilidade de lesões (ex: época COVID-2020 e finais de conferência), servindo como disjuntor principal (Circuit Breaker) para o modo Kelly se o drawdown diário exceder 5.0%.
