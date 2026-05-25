# METRICAS_E_KPIS — Métricas de Sucesso e KPIs

**ID:** `CI-003` | **Fase:** #phase/1-15 | **Owner:** Product Manager | **Status:** #status/pending

---

## 1. OBJETIVO

Definir um conjunto abrangente de métricas e KPIs (Key Performance Indicators) para monitorizar o desempenho do sistema de value betting, permitindo tomada de decisão baseada em dados e identificação de áreas de melhoria.

---

## 2. CONTEXTO

No value betting, a medição correta é crítica porque:
- Pequenas diferenças em ROI representam grandes valores monetários
- O mercado é eficiente e margens são pequenas
- Decisões erradas baseadas em métricas incorretas podem ser dispendiosas
- É necessário distinguir entre variância e tendência real

Métricas mal definidas levam a:
- Otimização para o errado
- Decisões baseadas em ruído estatístico
- Falha em identificar problemas reais
- Perda de confiança no sistema

---

## 3. HIERARQUIA DE MÉTRICAS

### 3.1 Nível 1: Métricas de Negócio (Business Metrics)

**Foco:** Resultado financeiro final

**Métricas:**
- **ROI (Return on Investment):** Lucro total / Investimento total
- **PnL (Profit and Loss):** Lucro ou prejuízo absoluto
- **CLV (Cumulative Long-term Value):** Valor acumulado esperado
- **Bankroll Growth:** Taxa de crescimento do bankroll
- **Monthly Revenue:** Receita mensal gerada

**Frequência:** Diária, Semanal, Mensal
**Acesso:** Stakeholders, Product Manager
**Ação:** Direcionamento estratégico

---

### 3.2 Nível 2: Métricas de Performance (Performance Metrics)

**Foco:** Eficiência das estratégias de aposta

**Métricas:**
- **Hit Rate:** Percentagem de apostas vencedoras
- **Average Value:** Valor médio das apostas (edge médio)
- **Yield:** Lucro por unidade apostada
- **Sharpe Ratio:** Retorno ajustado pelo risco
- **Maximum Drawdown:** Maior queda do bankroll
- **Recovery Time:** Tempo para recuperar de drawdown

**Frequência:** Diária, Semanal
**Acesso:** Product Manager, Data Analyst
**Ação:** Ajustes de estratégias

---

### 3.3 Nível 3: Métricas Operacionais (Operational Metrics)

**Foco:** Saúde e estabilidade do sistema

**Métricas:**
- **Uptime:** Percentagem de tempo online
- **Latency:** Tempo de resposta do sistema
- **Error Rate:** Percentagem de erros
- **Throughput:** Número de apostas por hora
- **API Success Rate:** Percentagem de chamadas API bem-sucedidas
- **Data Freshness:** Idade dos dados utilizados

**Frequência:** Contínua (monitorização em tempo real)
**Acesso:** DevOps, Development Team
**Ação:** Manutenção e otimização técnica

---

### 3.4 Nível 4: Métricas de Qualidade (Quality Metrics)

**Foco:** Precisão e confiabilidade dos dados/modelos

**Métricas:**
- **Prediction Accuracy:** Precisão das previsões vs realidade
- **Model Calibration:** Calibração das probabilidades
- **Backtest vs Live Performance:** Comparação backtest/produção
- **Data Quality Score:** Qualidade dos dados de entrada
- **False Positive Rate:** Apostas sinalizadas como value que não são

**Frequência:** Semanal, Mensal
**Acesso:** Data Scientists, Model Engineers
**Ação:** Melhoria de modelos e dados

---

## 4. MÉTRICAS DETALHADAS

### 4.1 ROI (Return on Investment)

**Definição:**
```
ROI = (Lucro Líquido / Investimento Total) × 100
```

**Interpretação:**
- ROI > 0: Sistema lucrativo
- ROI > 2%: Excelente para value betting
- ROI < 0: Sistema não lucrativo

**Thresholds de Alerta:**
- ROI < 0% por 7 dias: Investigar
- ROI < 0% por 30 dias: Ação crítica
- ROI < 1% por 90 dias: Revisar estratégia

**Segmentação:**
- Por desporto (futebol, ténis, basquetebol)
- Por tipo de aposta (match winner, over/under, handicaps)
- Por bookmaker
- Por período (dia da semana, hora)

---

### 4.2 Hit Rate (Taxa de Acerto)

**Definição:**
```
Hit Rate = (Apostas Vencedoras / Total de Apostas) × 100
```

**Interpretação:**
- Hit Rate esperado varia por estratégia
- Hit Rate muito alto pode indicar overfitting
- Hit Rate muito baixo pode indicar modelo fraco

**Thresholds de Alerta:**
- Desvio > 10% do esperado: Investigar
- Tendência descendente por 2 semanas: Ajustar modelo

**Relação com Odds:**
- Odds baixas: Hit rate deve ser alto
- Odds altas: Hit rate pode ser baixo mas com value alto

---

### 4.3 Average Value (Edge Médio)

**Definição:**
```
Average Value = Média de (Odds Estimadas - Odds de Mercado) / Odds de Mercado
```

**Interpretação:**
- Value > 0: Apostas têm edge positivo
- Value > 2%: Bom para value betting
- Value > 5%: Excelente mas pode indicar erro de modelo

**Thresholds de Alerta:**
- Value médio < 1%: Margem muito pequena
- Value médio > 10%: Possível erro de modelo

---

### 4.4 Sharpe Ratio

**Definição:**
```
Sharpe Ratio = (ROI - Risk-Free Rate) / Standard Deviation of ROI
```

**Interpretação:**
- Sharpe > 1: Bom
- Sharpe > 2: Excelente
- Sharpe < 1: Risco alto para o retorno

**Utilidade:**
- Compara retorno ajustado pelo risco
- Útil para comparar diferentes estratégias
- Ajuda a otimizar bankroll allocation

---

### 4.5 Maximum Drawdown

**Definição:**
```
Max Drawdown = (Pico - Vale) / Pico
```

**Interpretação:**
- Drawdown < 10%: Excelente gestão de risco
- Drawdown < 20%: Aceitável
- Drawdown > 30%: Risco alto

**Ações:**
- Se drawdown > 20%: Reduzir stake
- Se drawdown > 30%: Parar e investigar
- Calcular tempo médio de recuperação

---

### 4.6 CLV (Cumulative Long-term Value)

**Definição:**
```
CLV = Σ (Value Esperado de cada aposta)
```

**Interpretação:**
- CLV positivo: Estratégia tem edge positivo
- CLV vs PnL: Comparar esperado vs realizado
- CLV crescente: Estratégia saudável

**Utilidade:**
- Predição de longo prazo
- Validação de modelo
- Detecção de mudanças de mercado

---

### 4.7 Latency

**Definição:**
```
Latency = Tempo desde mudança de odds até execução da aposta
```

**Thresholds:**
- < 100ms: Excelente
- 100-300ms: Bom
- 300-1000ms: Aceitável
- > 1000ms: Precisa de melhoria

**Impacto:**
- Latency alta reduz value real
- Odds podem mudar antes da execução
- Perda de oportunidades

---

### 4.8 Error Rate

**Definição:**
```
Error Rate = (Erros / Total de Operações) × 100
```

**Tipos de Erros:**
- API errors (bookmaker não responde)
- Validation errors (dados inválidos)
- Execution errors (aposta falhou)
- System errors (crashes, timeouts)

**Thresholds:**
- < 1%: Excelente
- 1-5%: Aceitável
- > 5%: Investigar urgentemente

---

## 5. DASHBOARDS E MONITORIZAÇÃO

### 5.1 Dashboard Executivo (Nível 1)

**Público:** Stakeholders, Product Manager
**Atualização:** Diária
**Métricas:**
- ROI (7 dias, 30 dias, 90 dias)
- PnL total
- Bankroll atual
- CLV vs PnL
- Maximum Drawdown

**Visualizações:**
- Gráfico de linha de PnL ao longo do tempo
- Gráfico de barras de ROI por desporto
- Gauge de Sharpe Ratio

---

### 5.2 Dashboard de Performance (Nível 2)

**Público:** Product Manager, Data Analyst
**Atualização:** Contínua (quase real-time)
**Métricas:**
- Hit rate (hoje, semana, mês)
- Average value
- Yield por estratégia
- Volume de apostas
- Distribuição de odds

**Visualizações:**
- Scatter plot de value vs resultado
- Histograma de ROI por aposta
- Heatmap de performance por desporto/hora

---

### 5.3 Dashboard Operacional (Nível 3)

**Público:** DevOps, Development Team
**Atualização:** Contínua (real-time)
**Métricas:**
- Uptime
- Latency (P50, P95, P99)
- Error rate
- API success rate
- CPU/Memory usage

**Visualizações:**
- Time series de latency
- Pie chart de tipos de erro
- Grafos de dependência

---

### 5.4 Dashboard de Qualidade (Nível 4)

**Público:** Data Scientists, Model Engineers
**Atualização:** Semanal
**Métricas:**
- Prediction accuracy
- Model calibration
- Backtest vs live
- Data quality score
- Feature importance

**Visualizações:**
- Calibration curve
- Residual plots
- Feature importance bar chart

---

## 6. ALERTAS E THRESHOLDS

### 6.1 Alertas Críticos (Ação Imediata)

- ROI < 0% por 7 dias consecutivos
- Error rate > 10%
- System downtime > 1 hora
- Drawdown > 30%
- Bankroll < 50% do inicial

**Ação:** Notificação imediata, investigação urgente

---

### 6.2 Alertas de Aviso (Ação em 24h)

- ROI < 1% por 30 dias
- Hit rate desviando > 15% do esperado
- Latency P95 > 1000ms
- Error rate > 5%
- CLV vs PnL divergindo > 20%

**Ação:** Investigar no próximo dia útil

---

### 6.3 Alertas Informativos (Revisão Semanal)

- ROI entre 1-2%
- Latency P95 entre 500-1000ms
- Error rate entre 1-5%
- Mudanças em feature importance

**Ação:** Revisar na próxima retrospectiva

---

## 7. ANÁLISE DE TENDÊNCIAS

### 7.1 Detecção de Tendências

**Métodos:**
- Moving averages (7, 30, 90 dias)
- Linear regression
- Seasonal decomposition
- Change point detection

**O que procurar:**
- ROI em declínio gradual
- Latency aumentando
- Error rate em tendência ascendente
- Mudanças em hit rate por desporto

---

### 7.2 Análise de Causa-Raiz

**Quando métrica fora dos thresholds:**
1. Verificar se é variância ou tendência
2. Analisar segmentação (por desporto, bookmaker, etc.)
3. Verificar mudanças externas (regras, APIs)
4. Revisar alterações recentes no sistema
5. Validar qualidade dos dados

**Ferramentas:**
- 5 Whys
- Fishbone diagram
- Pareto analysis

---

## 8. BENCHMARKS E METAS

### 8.1 Metas de Curto Prazo (1-3 meses)

- ROI > 2%
- Hit rate dentro de ±5% do esperado
- Latency P95 < 500ms
- Error rate < 2%
- Uptime > 99%

---

### 8.2 Metas de Médio Prazo (3-12 meses)

- ROI > 3%
- Sharpe Ratio > 1.5
- Maximum Drawdown < 20%
- Latency P95 < 300ms
- Error rate < 1%

---

### 8.3 Metas de Longo Prazo (1+ anos)

- ROI > 4%
- Sharpe Ratio > 2
- Maximum Drawdown < 15%
- Latency P95 < 200ms
- Expansão para 3+ desportos

---

## 9. RELATÓRIOS

### 9.1 Relatório Diário

**Conteúdo:**
- ROI do dia
- PnL do dia
- Número de apostas
- Erros críticos
- Status do sistema

**Distribuição:** Email automático às 08:00

---

### 9.2 Relatório Semanal

**Conteúdo:**
- ROI semanal
- Comparação com semana anterior
- Hit rate por desporto
- Top 5 apostas (melhor/pior)
- Análise de tendências
- Alertas ativos

**Distribuição:** Email automático segunda-feira

---

### 9.3 Relatório Mensal

**Conteúdo:**
- ROI mensal e trimestral
- Análise detalhada de performance
- Comparação backtest vs live
- Métricas operacionais
- Recomendações de melhoria
- Plan de ação para mês seguinte

**Distribuição:** Apresentação em retrospectiva mensal

---

## 10. MELHORIA CONTÍNUA

### 10.1 Revisão de Métricas

**Trimestralmente:**
- Revisar se métricas ainda são relevantes
- Adicionar novas métricas se necessário
- Remover métricas obsoletas
- Ajustar thresholds baseados em dados históricos

---

### 10.2 Calibração de Modelos

**Mensalmente:**
- Comparar previsões vs resultados
- Ajustar modelos se systematicamente enviesados
- Validar feature importance
- Testar novos features

---

### 10.3 Automação

**Objetivos:**
- Automatizar coleta de métricas
- Automatizar alertas
- Automatizar relatórios
- Automatizar detecção de anomalias

---

## 11. LINKS CRUZADOS

- [[49_Continuous_Improvement/INDEX]] ← Secção mãe
- [[49_Continuous_Improvement/CICLO_PDCA]] → Uso de métricas no CHECK
- [[49_Continuous_Improvement/EXPERIMENTACAO]] → Métricas para A/B testing
- [[49_Continuous_Improvement/FEEDBACK_LOOPS]] → Coleta de dados
- [[49_Continuous_Improvement/RETROSPECTIVA_MENSAL]] → Revisão de métricas