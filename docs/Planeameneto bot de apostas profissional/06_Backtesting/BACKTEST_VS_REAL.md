# BACKTEST_VS_REAL — Protocolo de Comparação entre Simulado e Real

**ID:** `BT-004` | **Fase:** #phase/3-4 | **Owner:** Quant Research Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Estabelecer um protocolo rigoroso para comparar resultados de backtest com resultados reais (paper trading e live trading). A divergência entre simulado e real é inevitável, mas o objetivo é quantificar essa divergência, identificar causas, e determinar se o modelo ainda tem edge após ajustes para realidade.

---

## 2. DEFINIÇÃO E IMPORTÂNCIA

### 2.1 O Problema da Divergência

**Realidade:** Todo backtest é uma simplificação da realidade. Quando movemos para paper trading ou live trading, múltiplos fatores causam divergência:

- **Slippage real:** Odds mudam entre sinal e execução
- **Fill rate incompleto:** Nem todas as apostas são executadas
- **Custos ocultos:** Fees adicionais, taxas de withdrawal
- **Comportamento de mercado:** Reação do mercado a grandes apostas
- **Erros operacionais:** Bugs, delays, falhas de execução
- **Mudanças de regime:** Condições de mercado diferentes

**Consequência:** Um modelo com ROI simulado de 10% pode ter ROI real de 2% ou até -5%.

### 2.2 Por Que É Crítico?

Sem comparação sistemática entre backtest e real:

- **Overconfiança:** Implementar modelos que não têm edge real
- **Perda de capital:** Apostar dinheiro com base em resultados inflacionados
- **Incapacidade de melhorar:** Sem medir divergência, não se pode corrigir
- **Dano reputacional:** Serviços tipster com backtest otimista mas performance real pobre

**Objetivo do Protocolo:**
1. Quantificar divergência entre backtest e real
2. Identificar causas específicas de divergência
3. Ajustar backtest para ser mais realista
4. Determinar se o modelo ainda é viável após ajustes

---

## 3. PROTOCOLO DE COMPARAÇÃO

### 3.1 Fases de Validação

```
FASE 1: BACKTEST RIGOROSO
├── Dados históricos completos
├── Custos realistas (slippage 0.5%, comissão 5%)
├── Purged walk-forward CV
└── Critérios de passagem estritos

FASE 2: PAPER TRADING (1-2 meses)
├── Executar sinais SEM apostar dinheiro real
├── Medir: fill rate, slippage real, latência
├── Comparar com backtest
└── Ajustar modelo se necessário

FASE 3: MICRO BANCA (1-2 meses)
├── Apostar pequenas quantias (500-1000€)
├── Execução manual ou semi-automática
├── Medir ROI real vs simulado
└── Validar que edge persiste

FASE 4: ESCALADA GRADUAL
├── Aumentar banca gradualmente
├── Monitorizar divergência contínua
├── Ajustar para efeitos de escala
└── Parar se divergência for crítica
```

### 3.2 Métricas de Comparação

#### 3.2.1 Métricas Primárias

**ROI (Return on Investment):**
```
ROI_real vs ROI_simulado
Divergência = |ROI_real - ROI_simulado| / |ROI_simulado|
Threshold aceitável: Divergência < 50%
```

**Sharpe Ratio:**
```
Sharpe_real vs Sharpe_simulado
Divergência = |Sharpe_real - Sharpe_simulado| / |Sharpe_simulado|
Threshold aceitável: Divergência < 40%
```

**CLV (Closing Line Value):**
```
CLV_real vs CLV_simulado
Divergência = |CLV_real - CLV_simulado|
Threshold aceitável: Divergência < 1%
```

#### 3.2.2 Métricas Operacionais

**Fill Rate:**
```
Fill_rate = Apostas_executadas / Apostas_sinalizadas
Backtest assume: 100%
Real esperado: 70-90%
Threshold crítico: < 50%
```

**Slippage Médio:**
```
Slippage = (Odd_sinal - Odd_executada) / Odd_sinal
Backtest assume: 0.5%
Real medido: 0.5-2.0%
Threshold crítico: > 2.0%
```

**Latência de Execução:**
```
Latência = Tempo_entre_sinal_e_execução
Backtest assume: 0s
Real medido: 10-60s
Threshold crítico: > 120s
```

#### 3.2.3 Métricas de Distribuição

**Distribuição de Retornos:**
- Comparar média, desvio padrão, skewness, kurtosis
- Teste Kolmogorov-Smirnov para igualdade de distribuições
- Comparar drawdown máximo e duração

**Correlação Temporal:**
- Correlação entre retornos simulados e reais
- Correlação entre CLV simulado e real
- Análise de lag entre simulação e realidade

---

## 4. MÉTRICAS DE DIVERGÊNCIA

### 4.1 Divergência Absoluta

**Definição:** Diferença absoluta entre métrica real e simulada.

**Fórmula:**
```
Divergência_absoluta = |Métrica_real - Métrica_simulada|
```

**Exemplo:**
```
ROI_simulado = 8%
ROI_real = 5%
Divergência_absoluta = |5% - 8%| = 3%
```

**Uso:** Útil para métricas em unidades absolutas (ex: CLV, slippage).

### 4.2 Divergência Relativa

**Definição:** Diferença relativa como percentagem da métrica simulada.

**Fórmula:**
```
Divergência_relativa = |Métrica_real - Métrica_simulada| / |Métrica_simulada|
```

**Exemplo:**
```
ROI_simulado = 8%
ROI_real = 5%
Divergência_relativa = |5% - 8%| / |8%| = 3% / 8% = 37.5%
```

**Uso:** Útil para métricas relativas (ex: ROI, Sharpe).

### 4.3 Divergência Normalizada

**Definição:** Divergência normalizada pelo desvio padrão da métrica simulada.

**Fórmula:**
```
Divergência_normalizada = |Métrica_real - Métrica_simulada| / Std_simulado
```

**Exemplo:**
```
ROI_simulado = 8%, Std_simulado = 2%
ROI_real = 5%
Divergência_normalizada = |5% - 8%| / 2% = 3% / 2% = 1.5
```

**Uso:** Útil para determinar se divergência é estatisticamente significativa.

### 4.4 Teste de Significância

**Teste t de Student:**
```
H0: Métrica_real = Métrica_simulada
H1: Métrica_real ≠ Métrica_simulada

t = (Média_real - Média_simulada) / SE_pooled
p-value < 0.05 → Divergência significativa
```

**Teste de Mann-Whitney U:**
- Teste não-paramétrico
- Útil quando distribuições não são normais
- Mais robusto a outliers

---

## 5. CAUSAS DE DIVERGÊNCIA

### 5.1 Causas Operacionais

**Slippage Excessivo:**
- **Causa:** Odds movem-se rapidamente entre sinal e execução
- **Deteção:** Comparar odd_sinal vs odd_executada
- **Mitigação:** Reduzir latência, usar casas com mais liquidez, ajustar threshold de execução

**Fill Rate Baixo:**
- **Causa:** Odds mudam antes de execução, limites de stake atingidos
- **Deteção:** Contar apostas executadas vs sinalizadas
- **Mitigação:** Ajustar timing de sinais, diversificar casas, reduzir stake por aposta

**Latência Alta:**
- **Causa:** Delays em API, processamento lento, latência de rede
- **Deteção:** Medir tempo entre sinal e execução
- **Mitigação:** Otimizar código, usar VPS mais rápido, reduzir complexidade de pipeline

### 5.2 Causas de Modelo

**Overfitting:**
- **Causa:** Modelo aprendeu padrões específicos dos dados históricos
- **Deteção:** Performance muito melhor em backtest vs real
- **Mitigação:** Simplificar modelo, mais dados, regularização

**Regime Shift:**
- **Causa:** Condições de mercado mudaram (ex: COVID, novas regras)
- **Deteção:** Performance degrada em período específico
- **Mitigação:** Retreinar modelo com dados recentes, detectar regimes

**Feature Drift:**
- **Causa:** Features mudaram de distribuição ou importância
- **Deteção:** Monitorizar distribuição de features ao longo do tempo
- **Mitigação:** Retreinar periodicamente, atualizar features

### 5.3 Causas de Dados

**Dados de Backtest Incompletos:**
- **Causa:** Backtest usou dados incompletos ou de baixa qualidade
- **Deteção:** Comparar volume de jogos em backtest vs real
- **Mitigação:** Validar qualidade de dados, usar múltiplas fontes

**Odds de Fecho vs Abertura:**
- **Causa:** Backtest usou odds de fecho (mais precisas) mas real usa odds de abertura
- **Deteção:** Comparar CLV usando odds diferentes
- **Mitigação:** Usar odds de abertura no backtest, ajustar para timing real

** survivorship Bias:**
- **Causa:** Backtest inclui só times/jogadores que ainda existem
- **Deteção:** Verificar se backtest exclui entidades que desapareceram
- **Mitigação:** Incluir todas as entidades históricas, mesmo as que desapareceram

### 5.4 Causas de Escala

**Impacto no Mercado:**
- **Causa:** Apostas grandes movem o mercado (slippage adicional)
- **Deteção:** Slippage aumenta com stake
- **Mitigação:** Limitar stake por aposta, diversificar casas, usar exchanges

**Limites de Casa:**
- **Causa:** Casas limitam contas vencedoras
- **Deteção:** Stake máximo disponível diminui ao longo do tempo
- **Mitigação:** Diversificar casas, usar múltiplas contas, reduzir visibilidade

---

## 6. AJUSTES DE BACKTEST

### 6.1 Ajuste de Slippage

**Abordagem Conservadora:**
```
Slippage_backtest = max(Slippage_medido_real, Slippage_assumido)
Exemplo: Se real = 1.2%, assumido = 0.5%, usar 1.2%
```

**Abordagem Percentil:**
```
Slippage_backtest = Percentil_75(Slippage_real)
Exemplo: Se 75% das apostas têm slippage < 1.0%, usar 1.0%
```

**Abordagem Dinâmica:**
```
Slippage_backtest = f(Stake, Liquidez, Tempo)
Exemplo: Slippage aumenta com stake e diminui com liquidez
```

### 6.2 Ajuste de Fill Rate

**Abordagem Conservadora:**
```
Fill_rate_backtest = min(Fill_rate_medido_real, Fill_rate_assumido)
Exemplo: Se real = 75%, assumido = 100%, usar 75%
```

**Abordagem Probabilística:**
```
Para cada aposta no backtest:
- Probabilidade de execução = Fill_rate_medido
- Simular execução com essa probabilidade
```

### 6.3 Ajuste de Custos

**Custos Adicionais:**
```
Custo_total = Comissão + Slippage + Fees_withdrawal + Fees_deposito
Exemplo: 5% comissão + 1% slippage + 0.5% fees = 6.5% total
```

**Custos de Escala:**
```
Custo = Custo_base + Custo_escala × (Stake / Stake_max)
Exemplo: 5% base + 2% adicional se stake > 50% do limite
```

### 6.4 Ajuste de Latência

**Modelo de Latência:**
```
Odd_executada = Odd_sinal × (1 - Slippage_base × (1 + Latência / 60))
Exemplo: Slippage aumenta 50% se latência = 30s
```

---

## 7. CRITÉRIOS DE DECISÃO

### 7.1 Critérios de Continuação

O modelo pode continuar para próxima fase se:

✅ **Divergência de ROI < 50%:**
```
Exemplo: ROI_simulado = 8%, ROI_real = 5% (37.5% divergência) ✓
```

✅ **ROI_real > 0%:**
```
Modelo ainda tem edge positivo após ajustes
```

✅ **Sharpe_real > 0.3:**
```
Retornos ainda têm razoável relação risco-retorno
```

✅ **Fill_rate > 70%:**
```
Sinais são executáveis na prática
```

✅ **Slippage < 2.0%:**
```
Custos de execução são aceitáveis
```

✅ **CLV_real > 1.0%:**
```
Edge de mercado persiste em tempo real
```

### 7.2 Critérios de Paragem

O modelo deve ser parado se:

❌ **Divergência de ROI > 100%:**
```
Exemplo: ROI_simulado = 8%, ROI_real = -4% (150% divergência) ✗
```

❌ **ROI_real < -5%:**
```
Modelo perde dinheiro consistentemente
```

❌ **Sharpe_real < 0:**
```
Retornos têm relação risco-retorno negativa
```

❌ **Fill_rate < 50%:**
```
Sinais não são executáveis na prática
```

❌ **Slippage > 3.0%:**
```
Custos de execução são proibitivos
```

❌ **CLV_real < 0%:**
```
Edge de mercado desapareceu em tempo real
```

### 7.3 Critérios de Revisão

O modelo deve ser revisado (não necessariamente parado) se:

⚠️ **Divergência de ROI 50-100%:**
```
Investigar causas, possivelmente ajustar modelo
```

⚠️ **ROI_real 0-3%:**
```
Edge marginal, considerar simplificações
```

⚠️ **Fill_rate 50-70%:**
```
Investigar causas de não-execução
```

⚠️ **Slippage 2.0-3.0%:**
```
Investigar otimizações de execução
```

⚠️ **CLV_real 0-1%:**
```
Edge marginal, monitorizar de perto
```

---

## 8. FRAMEWORK DE MONITORIZAÇÃO CONTÍNUA

### 8.1 Dashboard de Divergência

**Métricas em Tempo Real:**
- ROI_real vs ROI_simulado (últimos 7 dias, 30 dias, 90 dias)
- Sharpe_real vs Sharpe_simulado
- CLV_real vs CLV_simulado
- Fill_rate rolling
- Slippage médio rolling

**Alertas Automáticos:**
- Divergência de ROI > 50% → Alerta amarelo
- Divergência de ROI > 100% → Alerta vermelho
- Fill_rate < 70% → Alerta amarelo
- Fill_rate < 50% → Alerta vermelho
- Slippage > 2.0% → Alerta amarelo
- Slippage > 3.0% → Alerta vermelho

### 8.2 Análise de Tendência

**Tendência de Divergência:**
- Calcular divergência ao longo do tempo
- Detetar se divergência está a aumentar ou diminuir
- Prever divergência futura (ex: regressão linear)

**Tendência de Performance:**
- ROI_real ao longo do tempo
- Detetar degradação de edge
- Identificar regime shifts

### 8.3 Relatório Semanal

**Conteúdo do Relatório:**
1. **Resumo Executivo:** Métricas chave e status
2. **Análise de Divergência:** Causas identificadas
3. **Ajustes Realizados:** Mudanças no modelo ou execução
4. **Projeções:** Expectativas para próxima semana
5. **Decisões:** Continuar, parar, ou revisar

---

## 9. EXEMPLOS PRÁTICOS

### 9.1 Exemplo: Divergência Aceitável

**Backtest:**
- ROI = 8%, Sharpe = 0.8, CLV = 2.5%
- Fill rate = 100%, Slippage = 0.5%

**Paper Trading (30 dias):**
- ROI = 6%, Sharpe = 0.7, CLV = 2.2%
- Fill rate = 85%, Slippage = 0.8%

**Análise:**
```
Divergência ROI = |6% - 8%| / |8%| = 25% ✓ (< 50%)
Divergência Sharpe = |0.7 - 0.8| / |0.8| = 12.5% ✓ (< 40%)
Divergência CLV = |2.2% - 2.5%| = 0.3% ✓ (< 1%)
Fill rate = 85% ✓ (> 70%)
Slippage = 0.8% ✓ (< 2.0%)
```

**Decisão:** Continuar para micro banca, ajustar backtest com fill rate = 85% e slippage = 0.8%

### 9.2 Exemplo: Divergência Crítica

**Backtest:**
- ROI = 10%, Sharpe = 1.0, CLV = 3.0%
- Fill rate = 100%, Slippage = 0.5%

**Paper Trading (30 dias):**
- ROI = -3%, Sharpe = -0.2, CLV = 0.5%
- Fill rate = 45%, Slippage = 2.5%

**Análise:**
```
Divergência ROI = |-3% - 10%| / |10%| = 130% ✗ (> 100%)
Divergência Sharpe = |-0.2 - 1.0| / |1.0| = 120% ✗ (> 40%)
Divergência CLV = |0.5% - 3.0%| = 2.5% ✗ (> 1%)
Fill rate = 45% ✗ (< 50%)
Slippage = 2.5% ✗ (> 2.0%)
```

**Decisão:** Parar imediatamente, investigar causas (provavelmente overfitting severo), revisar completamente o modelo

### 9.3 Exemplo: Divergência Marginal

**Backtest:**
- ROI = 7%, Sharpe = 0.7, CLV = 2.0%
- Fill rate = 100%, Slippage = 0.5%

**Paper Trading (30 dias):**
- ROI = 4%, Sharpe = 0.5, CLV = 1.5%
- Fill rate = 75%, Slippage = 1.2%

**Análise:**
```
Divergência ROI = |4% - 7%| / |7%| = 43% ⚠️ (próximo de 50%)
Divergência Sharpe = |0.5 - 0.7| / |0.7| = 29% ✓ (< 40%)
Divergência CLV = |1.5% - 2.0%| = 0.5% ✓ (< 1%)
Fill rate = 75% ✓ (> 70%)
Slippage = 1.2% ✓ (< 2.0%)
```

**Decisão:** Continuar mas monitorizar de perto, ajustar backtest com fill rate = 75% e slippage = 1.2%, investigar causas de divergência de ROI

---

## 10. REFERÊNCIAS E BOAS PRÁTICAS

### 10.1 Literatura Recomendada

- **"Pairs Trading: Quantitative Methods and Analysis"** — Ganapathy Vidyamurthy (Capítulo sobre slippage)
- **"Algorithmic Trading and DMA"** — Barry Johnson (Capítulo sobre execução)
- **"Trading and Exchanges"** — Larry Harris (Capítulo sobre custos de transação)
- **"Inside the Black Box"** — Rishi K. Narang (Capítulo sobre validação)

### 10.2 Ferramentas Úteis

- **Dashboards:** Grafana, Tableau, custom dashboards
- **Alerting:** PagerDuty, Slack alerts, email notifications
- **Logging:** Structured logging para rastrear execuções
- **Version control:** Git para rastrear mudanças no modelo

### 10.3 Regras de Ouro

1. **Sempre validar com paper trading antes de dinheiro real**
2. **Ser conservador nas assunções de backtest**
3. **Monitorizar divergência continuamente**
4. **Parar imediatamente se divergência for crítica**
5. **Documentar todas as causas de divergência**

---

## 11. LINKS CRUZADOS

- [[06_Backtesting/INDEX]] ← Secção mãe
- [[21_Paper_Trading/INDEX]] → Protocolo de paper trading
- [[22_Real_Money_Operations/INDEX]] → Operações com dinheiro real
- [[47_Shadow_Betting/INDEX]] → Shadow betting em múltiplas casas
- [[08_Risk_Management/INDEX]] → Gestão de risco em operações

---

## 12. GLOSSÁRIO

- **Divergência:** Diferença entre métrica simulada e real
- **Fill rate:** Proporção de apostas executadas vs sinalizadas
- **Slippage:** Mudança de odds entre sinal e execução
- **Latência:** Tempo entre geração de sinal e execução
- **Paper trading:** Simulação em tempo real sem dinheiro real
- **Live trading:** Execução com dinheiro real
- **Regime shift:** Mudança fundamental nas condições de mercado
- **Feature drift:** Mudança na distribuição ou importância de features