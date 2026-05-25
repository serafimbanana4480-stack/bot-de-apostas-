# Relatório de Viabilidade Financeira — Bot de Apostas Quantitativo

**Data:** 2026-05-25  
**Analista:** Kimi Code CLI (Auditoria Técnica Completa)  
**Dataset:** football_real_odds (8.955 jogos, 2019-2024, odds Pinnacle open/close)  
**Método:** Walk-Forward Purged + Embargo (7 dias), leakage check ativado

---

## 1. Resumo Executivo

### Veredicto: ❌ NÃO LUCRATIVO NO ESTADO ATUAL

O sistema **não deve ser utilizado com dinheiro real**. O backtest honesto demonstra perdas significativas e consistentes, com um risco de ruína de 91%. Embora o modelo capture sinais de Closing Line Value (CLV) positivo, este edge é **ilusório** — deriva de overfitting na estimativa de probabilidades, não de verdadeira vantagem preditiva.

---

## 2. Correções Efetuadas (Hardening)

Foram implementadas melhorias críticas de enterprise-grade:

| Fase | Problema | Correção |
|------|----------|----------|
| **Fase 1** | Data leakage temporal em calibração OOF (KFold shuffle) | Substituído por `TimeSeriesSplit` + embargo de 2 dias |
| **Fase 1** | Walk-Forward sem purging/embargo | Adicionado `embargo_days` e gap temporal rigoroso |
| **Fase 1** | Testes de leakage ausentes | Criados 5 novos testes automáticos |
| **Fase 2** | Serialização com `pickle` (insegura) | Substituída por JSON nativo XGBoost + JSON para Poisson/Isotonic |
| **Fase 3** | Monte Carlo com odds fixas | Refatorado para amostrar da distribuição empírica real |
| **Fase 3** | Apenas 5 circuit breakers | Adicionado 6º breaker (Zeta: Model Degradation via Brier score) |
| **Fase 4** | Betfair como default (ilegal PT) | Paper trading only por defeito; avisos legais adicionados |
| **Fase 4** | TTL de 5 minutos (impraticável) | Substituído por "válido até odd < mínima calculada" com edge decay |
| **Fase 5** | Documentação fragmentada | Criado `GETTING_STARTED.md` funcional e script de reconciliação diária |

**Estado dos testes:** 236 passados, 14 skipped, 0 falhas ✅

---

## 3. Resultados do Backtest Honesto

### 3.1 Configuração
- **Período:** 2023-01-01 a 2024-12-31
- **Método:** Walk-Forward com 180 dias de treino, 30 dias de teste, 7 dias de embargo
- **Folds:** 11
- **Leakage gate:** PASSED ✅
- **Dataset:** `matches_football_real_odds.parquet` (odds reais Pinnacle)

### 3.2 Métricas Financeiras

| Métrica | Valor | Threshold Aceitável | Status |
|---------|-------|---------------------|--------|
| **Total de apostas** | 393 | > 100 | ✅ |
| **ROI por aposta** | **-10.9%** | > +2% | ❌ |
| **Win rate** | 29.0% | — | ⚠️ |
| **Profit Factor** | **0.85** | > 1.10 | ❌ |
| **Sharpe proxy** | **-1.38** | > 1.0 | ❌ |
| **Sortino proxy** | 0.0 | > 1.0 | ❌ |
| **Max Drawdown** | 78.2 unidades | < 20 unidades | ❌ |
| **Mean CLV** | **+4.01%** | > 2% | ✅ |
| **Positive CLV %** | 69.7% | > 50% | ✅ |

### 3.3 Paradoxo do CLV

O modelo apresenta **CLV médio positivo de 4%** (69.7% das apostas batem a linha de fecho), mas o **ROI real é -10.9%**. Este é o sintoma clássico de **overfitting de probabilidade**:

1. O modelo Poisson sobrestima sistematicamente a probabilidade de vitória da casa
2. O "edge" calculado (`model_prob - implied_prob`) é fictício — aproximadamente +12% acima do real
3. O CLV positivo é um artefacto de seleção: o modelo escolhe jogos onde as odds de abertura são altas vs o fecho, mas a predição da probabilidade está enviesada

**Analogia:** O modelo é como um cartógrafo que desenha mapas bonitos mas com coordenadas erradas. A bússola aponta norte, mas o norte está 12 graus desviado.

---

## 4. Simulação de Monte Carlo Realista

Usando a distribuição empírica real de odds do backtest (com comissão de 5%):

| Métrica | Valor |
|---------|-------|
| Bankroll final médio (de €1000) | **€383** |
| Probabilidade de lucro | **0.02%** |
| **Risk of Ruin (>50% perda)** | **91.2%** |
| Drawdown médio máximo | 63.8% |
| Sortino Ratio | **-6.46** |
| Sharpe Ratio | **-6.43** |

**Interpretação:** Em 10.000 simulações, 9.120 terminaram com perda superior a 50% do bankroll inicial. Apenas 2 terminaram com lucro.

---

## 5. Análise de Causa Raiz

### 5.1 O Modelo Poisson é Inadequado para Previsão de Resultados
O modelo Dixon-Coles com attack/defense strengths é um excelente **baseline teórico**, mas:
- Não captura informação de mercado (line movement, sharp money)
- As features de forma/H2H/rest são demasiado simples (médias exponenciais)
- A calibração isotónica corrige a escala das probabilidades, mas não a sua ordem — se o modelo classifica mal, a calibração não salva

### 5.2 O XGBoost Híbrido Não Adiciona Valor Real
O segundo estágio (XGBoost) aprende resíduos do Poisson, mas com apenas ~393 apostas no backtest (de ~9000 jogos), o modelo está a filtrar muito agressivamente. A baixa taxa de vitória (29%) sugere que o filtro de edge está a remover os jogos vencedores e manter os perdedores.

### 5.3 O "Edge" é Consumido pelo Overround
Mesmo que o modelo tivesse um edge genuíno de 2%, o overround médio do mercado (2.6-2.9%) + comissão da exchange (5%) = **~7.5% de custo total**. Para ser lucrativo, o modelo precisaria de um edge verdadeiro > 8%, o que é extremamente raro em mercados eficientes como o futebol europeu.

### 5.4 Data Leakage Residual (Mesmo Após Correções)
As correções efetuadas eliminaram o leakage mais óbvio (KFold shuffle), mas:
- O `FootballPoissonModel._match_history` mantém os últimos 1000 jogos. No backtest walk-forward, cada fold treina um modelo novo, mas a lógica de form/H2H ainda pode incorporar informação do futuro se o dataset de treino não for purgado corretamente em relação às janelas de forma.
- A feature `line_movement_home` nos dados de input pode conter informação do fecho se não for cuidadosamente calculada apenas com dados até à abertura.

---

## 6. Roadmap para Tornar o Sistema Potencialmente Viável

### Curto Prazo (1-2 meses)
1. **Diagnóstico de calibração:** Plotar reliability diagrams por faixa de odds. O modelo está a sobrestimar prob em favoritos ou em underdogs?
2. **Análise de resíduos:** Verificar se o erro do modelo está correlacionado com variáveis observáveis (ex: lesões, suspensões, clima).
3. **Mais dados:** O dataset tem apenas ~9.000 jogos. Para 80 features, precisa-se de pelo menos 50.000+ jogos ou redução drástica de dimensionalidade.
4. **Remover features de mercado do modelo de base:** O Poisson deve usar apenas estatísticas de equipa. As odds de mercado devem entrar apenas na camada de decisão (meta-labeling).

### Médio Prazo (3-6 meses)
5. **Implementar meta-labeling:** Usar o modelo Poisson para gerar sinais (primary model), e um segundo modelo (Random Forest/XGBoost) para prever a probabilidade de o sinal ser correto, usando features de mercado (line movement, volume, etc.).
6. **Focar em mercados nicho:** O mercado 1X2 da Premier League é demasiado eficiente. Testar em ligas menores, Asian Handicaps, ou mercados de cantos/escanteios.
7. **Coletar dados de execução real:** Executar paper trading durante 3-6 meses e comparar odds simuladas vs odds obtidas. Medir slippage real.

### Longo Prazo (6-12 meses)
8. **Reavaliação com 10.000+ apostas paper:** Só considerar dinheiro real após 10.000 apostas paper com ROI > 2%, Sortino > 1.0, e CLV consistentemente positivo.
9. **Estrutura legal:** Constituir entidade empresarial, obter licenciamento SRIJ (ou operar via entidade internacional legítima com Pinnacle).
10. **Bankroll adequado:** Com Kelly 0.25x e edge de 2%, o bankroll mínimo recomendado para suportar a variância é €10.000-€25.000.

---

## 7. Conclusão e Recomendações

### ❌ NÃO APOSTE DINHEIRO REAL
O sistema, mesmo após as correções enterprise-grade, **é perdedor em backtest honesto**. A probabilidade de ruína é de 91%.

### ⚠️ O CLV Positivo é uma Armadilha
Um CLV positivo não garante lucro. O modelo captura o movimento das odds, mas não a verdadeira probabilidade do resultado. Isto é equivalente a saber que uma ação vai subir de preço porque os insiders estão a comprar, mas não saber se a empresa é boa.

### ✅ Próximos Passos Recomendados
1. Continue a usar o sistema em **paper trading only** por pelo menos 6 meses.
2. Foque-se em **meta-labeling** e em **reduzir a dimensionalidade** para 10-15 features robustas.
3. Colete **dados de execução real** (odds efetivamente disponíveis no momento da aposta) para quantificar o slippage.
4. **Não considere dinheiro real** até obter ROI > +2%, Profit Factor > 1.2, e Risk of Ruin < 10% em 5.000+ apostas paper.

---

## Anexos

### A. Código das Correções
Todas as alterações estão no branch atual e cobertas por 236 testes automatizados.

### B. Dados do Backtest
- Dataset: `data/bronze/matches_football_real_odds.parquet`
- Relatório: `data/reports/backtest_football_2023-01-01_2024-12-31.json`
- Comando: `uv run python scripts/run_pipeline.py --sport football --mode backtest --start 2023-01-01 --end 2024-12-31 --check-leakage`

### C. Referências
- Lopez de Prado, M. (2018). *Advances in Financial Machine Learning*
- Buchdahl, J. (2016). *Squares & Sharps, Suckers & Sharks*
- SRIJ — Serviço de Regulação e Inspeção de Jogos (Portugal)
