# WALK_FORWARD_IMPLEMENTACAO — Implementação Detalhada de Purged Walk-Forward CV

**ID:** `BT-005` | **Fase:** #phase/2 | **Owner:** Quant Research Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar a implementação detalhada de Purged Walk-Forward Cross-Validation com embargo periods, o padrão ouro para validação temporal de modelos de apostas desportivas. Este documento foca-se na teoria, fluxo de trabalho e justificações, não em código específico.

---

## 2. DEFINIÇÃO E IMPORTÂNCIA

### 2.1 O Que É Walk-Forward Cross-Validation?

**Definição:** Método de validação cruzada onde o modelo é treinado em janelas de dados históricos e testado em períodos futuros, simulando o processo real de treino e predição em produção.

**Características Principais:**
- **Estritamente temporal:** Dados de treino sempre precedem dados de teste
- **Deslizante:** Janela de treino move-se forward no tempo
- **Purged:** Remove dados próximos da fronteira entre treino e teste
- **Com embargo:** Período de separação explícito entre treino e teste

### 2.2 Por Que Walk-Forward é Superior?

**vs K-Fold CV Clássico:**
- K-Fold embaralha dados, destruindo estrutura temporal
- K-Fold permite leakage temporal (treino vê futuro)
- Walk-Fold preserva ordem temporal, simulando produção

**vs Hold-Out Simples:**
- Hold-out usa apenas um split (treino vs teste)
- Hold-out não valida estabilidade temporal
- Walk-Forward valida múltiplos períodos, mais robusto

**vs Rolling Window:**
- Rolling window mantém tamanho fixo de treino
- Walk-Forward pode usar janela crescente ou fixa
- Walk-Forward com purge é mais rigoroso

### 2.3 Por Que é Crítico em Apostas Desportivas?

**Estrutura Temporal:** Dados de apostas são intrinsecamente temporais:
- Jogos acontecem em sequência
- Odds mudam ao longo do tempo
- Regimes de mercado evoluem (ex: pré-COVID vs pós-COVID)

**Risco de Leakage:** CV clássica causaria leakage porque:
- Modelo treinaria em jogos futuros
- Feature engineering usaria estatísticas globais
- Normalização contaminaria dados de teste

**Validação Realista:** Walk-Forward simula produção:
- Treinar em dados históricos
- Predizer jogos futuros
- Atualizar modelo periodicamente

---

## 3. ARQUITETURA DO WALK-FORWARD

### 3.1 Estrutura de Janelas

**Parâmetros do Projeto:**
```
Janela de treino: 36 meses (3 épocas)
Janela de validação: 12 meses (1 época)
Janela de teste: 12 meses (1 época)
Embargo: 2 dias
Folds: 12 (um por mês de validação)
```

**Visualização:**
```
Épocas: 2018-19 | 2019-20 | 2020-21 | 2021-22 | 2022-23
         Tr       Tr       Tr       Val      Test
         |_________|_________|___|___|_______|
                   |_________|___|___|_______|
                             |___|___|_______|

Tr = Treino (36 meses)
Val = Validação (12 meses)
Test = Teste (12 meses, hold-out final)
___ = Embargo (2 dias entre folds)
```

### 3.2 Fluxo de Dados

```
DADOS HISTÓRICOS (5 épocas)
│
├── FOLD 1
│   ├── Treino: 2018-19, 2019-20, 2020-21 (36 meses)
│   ├── Embargo: últimos 2 dias do treino
│   ├── Validação: 2021-22, mês 1
│   └── Teste: Não usado neste fold
│
├── FOLD 2
│   ├── Treino: 2019-20, 2020-21, 2021-22 mês 1-11 (36 meses)
│   ├── Embargo: últimos 2 dias do treino
│   ├── Validação: 2021-22, mês 2
│   └── Teste: Não usado neste fold
│
├── ...
│
├── FOLD 12
│   ├── Treino: 2020-21, 2021-22 meses 1-10, 2022-23 mês 1-2 (36 meses)
│   ├── Embargo: últimos 2 dias do treino
│   ├── Validação: 2022-23, mês 3
│   └── Teste: Não usado neste fold
│
└── HOLD-OUT FINAL
    ├── Treino: 2018-19, 2019-20, 2020-21, 2021-22 (48 meses)
    ├── Embargo: últimos 2 dias do treino
    └── Teste: 2022-23 (12 meses, NUNCA usado para tuning)
```

### 3.3 Divisão 3:1:1

**Justificativa:**
- **3 épocas treino:** Dados suficientes para aprender padrões robustos
- **1 época validação:** Período suficiente para tuning de hiperparâmetros
- **1 época teste:** Avaliação final sem qualquer tuning

**Proporção 3:1:1 vs Alternativas:**

| Proporção | Vantagens | Desvantagens | Uso Recomendado |
|-----------|-----------|--------------|-----------------|
| **3:1:1** | Balanceado, suficiente treino | Menos dados de teste | ✅ Padrão |
| 4:1:0 | Mais treino, menos validação | Sem teste final | ❌ Não recomendado |
| 2:1:1 | Mais teste | Menos treino (overfitting) | ⚠️ Dados limitados |
| 3:0.5:1.5 | Mais teste | Validação curta | ⚠️ Tuning limitado |

---

## 4. PURGED CV COM EMBARGO

### 4.1 O Que É Purging?

**Definição:** Remoção de dados do conjunto de treino que estão muito próximos temporalmente dos dados de validação/teste.

**Por Que Purging é Necessário:**
- **Features com memória:** Rolling averages, momentum features usam dados históricos
- **Overlapping information:** Dados próximos podem ter informação correlacionada
- **Leakage subtil:** Mesmo sem olhar para o futuro, features podem "vazar" informação

**Exemplo:**
```
Jogo A: 2022-01-15
Jogo B: 2022-01-16 (validação)
Feature para Jogo B: "Média últimos 5 jogos"

Sem purging:
- Feature usa Jogo A (2022-01-15) que está no treino
- Isso é leakage porque Jogo A está muito próximo de Jogo B

Com purging (embargo 2 dias):
- Remover Jogo A do treino se estiver a 2 dias de Jogo B
- Feature só usa jogos até 2022-01-13
```

### 4.2 O Que É Embargo?

**Definição:** Período de separação explícito entre o último dado usado no treino e o primeiro dado de validação/teste.

**Parâmetro do Projeto:** Embargo = 2 dias

**Justificativa de 2 Dias:**
- **NBA:** Jogos quase diários, 2 dias = ~2-3 jogos de separação
- **Features com memória:** Rolling averages de 5 jogos precisam de ~5 dias de separação
- **Pragmático:** Balance entre rigor e quantidade de dados

**Alternativas e Trade-offs:**

| Embargo | Vantagens | Desvantagens | Uso |
|---------|-----------|--------------|-----|
| **0 dias** | Máximo de dados | Leakage alto | ❌ Nunca |
| 1 dia | Mais dados | Algum leakage | ⚠️ Apenas se urgente |
| **2 dias** | Balanceado | Leve perda de dados | ✅ Padrão |
| 5 dias | Menos leakage | Perda significativa de dados | ⚠️ Se features de longo prazo |
| 10 dias | Mínimo leakage | Perda severa de dados | ❌ Excessivo |

### 4.3 Implementação Conceitual

**Algoritmo:**
```
Para cada fold i:
1. Definir janela de treino [T_inicio, T_fim]
2. Definir janela de validação [V_inicio, V_fim]
3. Aplicar embargo:
   - Remover dados de treino em [V_inicio - embargo, V_inicio]
   - Remover dados de treino em [V_fim, V_fim + embargo]
4. Treinar modelo em treino purgado
5. Validar em validação (não purgada)
6. Guardar métricas
```

**Visualização:**
```
Treino:     [====================]
Embargo:           [==]
Validação:               [====]
Embargo:                     [==]
Treino próximo:                   [====================]
```

---

## 5. FLUXO DE TRABALHO DETALHADO

### 5.1 Preparação de Dados

**Passo 1: Ingerir Dados Históricos**
- 5 épocas completas de NBA (2018-19 a 2022-23)
- Validar integridade (sem missing values, timestamps consistentes)
- Ordenar por data (ascendente)
- Remover duplicatas

**Passo 2: Feature Engineering Temporal**
- Calcular features usando SÓ dados anteriores ao jogo
- Documentar "known_at_timestamp" para cada feature
- Validar que feature_timestamp < game_timestamp

**Passo 3: Divisão Temporal**
- Dividir dados em treino/validação/teste por tempo
- Treino: 2018-19, 2019-20, 2020-21
- Validação: 2021-22 (12 folds, 1 mês cada)
- Teste: 2022-23 (hold-out final)

**Passo 4: Validação de Integridade**
- Verificar ordenação temporal
- Verificar que não há overlapping entre folds
- Verificar que embargo é aplicado corretamente

### 5.2 Execução de Walk-Forward

**Para cada fold (1 a 12):**

**1. Setup do Fold:**
```
Fold i:
- Treino: épocas anteriores + meses anteriores de validação
- Validação: mês i de 2021-22
- Embargo: 2 dias antes e depois da validação
```

**2. Purging:**
```
Remover do treino:
- Jogos em [validação_inicio - 2 dias, validação_inicio]
- Jogos em [validação_fim, validação_fim + 2 dias]
```

**3. Feature Engineering no Fold:**
```
- Calcular features usando SÓ dados de treino purgado
- Normalizar features usando estatísticas de treino purgado
- NÃO usar dados de validação em qualquer transformação
```

**4. Treinamento:**
```
- Treinar modelo em treino purgado
- Tunar hiperparâmetros usando validação (se aplicável)
- Guardar modelo e hiperparâmetros
```

**5. Validação:**
```
- Aplicar modelo a dados de validação
- Calcular métricas (ROI, Sharpe, CLV, etc.)
- Guardar predições e métricas
```

**6. Iteração:**
```
- Mover janela de treino forward
- Repetir para próximo fold
```

### 5.3 Agregação de Resultados

**Métricas por Fold:**
- ROI, Sharpe, CLV para cada fold
- Feature importance para cada fold
- Número de apostas para cada fold
- Distribuição de retornos para cada fold

**Métricas Agregadas:**
- **Média:** Média das métricas across folds
- **Desvio padrão:** Variabilidade across folds
- **Mínimo/Máximo:** Range de performance
- **Percentis:** 25th, 50th (mediana), 75th percentis

**Estabilidade:**
- Coeficiente de variação (CV = std/mean)
- % de folds com performance positiva
- Correlação de métricas entre folds adjacentes

---

## 6. HOLD-OUT FINAL

### 6.1 Propósito

**Por Que Hold-Out Separado?**
- **Tuning em validação:** Hiperparâmetros são tunados nos 12 folds
- **Avaliação final:** Teste é NUNCA usado para tuning
- **Simulação de produção:** Teste simula deployment real

**Regra de Ouro:**
> "O conjunto de teste é sagrado. NUNCA use o teste para tuning, feature selection, ou qualquer decisão de modelo."

### 6.2 Implementação

**Treino para Teste:**
```
- Usar TODOS os dados de treino + validação (48 meses)
- Aplicar embargo de 2 dias antes do teste
- Treinar modelo final com hiperparâmetros ótimos
```

**Validação no Teste:**
```
- Usar época 2022-23 (12 meses)
- NÃO aplicar purging no teste
- Calcular métricas finais
- Comparar com validação
```

**Critérios de Passagem:**
- Teste deve ter performance similar à validação
- Gap entre validação e teste < 30%
- Teste deve passar todos os critérios mínimos (ROI > 5%, etc.)

---

## 7. MÉTRICAS E VALIDAÇÃO

### 7.1 Métricas por Fold

**Métricas de Performance:**
- ROI (Return on Investment)
- Sharpe Ratio
- CLV (Closing Line Value)
- Brier Score
- ECE (Expected Calibration Error)
- Número de apostas
- Max drawdown

**Métricas de Estabilidade:**
- Feature importance (top 10 features por fold)
- Correlação de features entre folds
- Distribuição de predições por fold

**Métricas de Calibração:**
- Reliability diagrams por fold
- Histograma de probabilidades por fold
- Calibration slope e intercept por fold

### 7.2 Análise de Estabilidade

**Feature Importance Stability:**
```
Para cada fold:
1. Calcular feature importance (SHAP ou gain)
2. Ranking das top 10 features
3. Comparar ranking entre folds

Critério:
- Top 5 features consistentes em ≥ 8 dos 12 folds
- Correlação de ranking > 0.6 entre folds adjacentes
```

**Performance Stability:**
```
Para cada métrica (ROI, Sharpe, CLV):
1. Calcular média e desvio padrão across folds
2. Calcular coeficiente de variação (CV = std/mean)
3. Contar folds com performance positiva

Critério:
- CV(ROI) < 0.5
- ≥ 8 de 12 folds com ROI > 0
- ≥ 10 de 12 folds com Sharpe > 0
```

**Temporal Consistency:**
```
1. Plotar métricas ao longo do tempo (folds)
2. Detetar tendências (degradação ou melhoria)
3. Identificar regime shifts (mudanças abruptas)

Critério:
- Sem tendência negativa forte
- Sem regime shifts não explicados
```

### 7.3 Validação Final

**Comparação Validação vs Teste:**
```
Métrica | Validação (média) | Teste | Gap
--------|-------------------|-------|-----
ROI     | 7.2%              | 5.8%  | 19% ✓
Sharpe  | 0.75              | 0.62  | 17% ✓
CLV     | 2.3%              | 2.1%  | 9% ✓

Critério: Gap < 30% para todas as métricas
```

**Critérios de Passagem Finais:**
- ✅ Teste ROI > 5%
- ✅ Teste Sharpe > 0.5
- ✅ Teste CLV > 2.0%
- ✅ Gap validação-teste < 30%
- ✅ Estabilidade across folds (CV < 0.5)
- ✅ Feature importance consistente

---

## 8. OTIMIZAÇÕES E VARIATIONS

### 8.1 Janela Crescente vs Fixa

**Janela Fixa (Rolling Window):**
```
Fold 1: Treino 36 meses
Fold 2: Treino 36 meses (desliza)
Fold 3: Treino 36 meses (desliza)
...
```

**Vantagens:**
- Modelo sempre usa mesmo volume de dados
- Mais consistência de performance
- Menor risco de regime shift antigo

**Desvantagens:**
- Perde dados históricos importantes
- Menos dados nos folds finais

**Janela Crescente (Expanding Window):**
```
Fold 1: Treino 36 meses
Fold 2: Treino 37 meses (adiciona 1 mês)
Fold 3: Treino 38 meses (adiciona 1 mês)
...
```

**Vantagens:**
- Usa todos os dados disponíveis
- Mais dados nos folds finais
- Potencialmente melhor performance

**Desvantagens:**
- Volume de dados varia entre folds
- Pode incluir dados muito antigos (regime shift)

**Recomendação:** Janela fixa (rolling) para consistência

### 8.2 Número de Folds

**Trade-offs:**

| Folds | Vantagens | Desvantagens |
|-------|-----------|--------------|
| 6 | Validação rápida | Menos granularidade |
| **12** | Balanceado | ✅ Padrão |
| 24 | Mais granularidade | Mais lento, folds menores |
| 52 | Semanal | Muito lento, folds muito pequenos |

**Recomendação:** 12 folds (mensal) para NBA

### 8.3 Tamanho do Embargo

**Depende de:**
- **Frequência de jogos:** NBA tem jogos quase diários
- **Features com memória:** Rolling averages precisam de separação
- **Liquidez:** Mercados mais líquidos toleram embargo menor

**Recomendação:**
- **NBA:** 2 dias (padrão)
- **NFL:** 7 dias (jogos semanais)
- **Tênis:** 1 dia (torneios diários)

---

## 9. BOAS PRÁTICAS

### 9.1 Antes da Execução

**Validação de Dados:**
- Verificar integridade dos dados (sem missing, timestamps corretos)
- Ordenar dados temporalmente
- Validar que não há overlapping entre folds

**Documentação:**
- Documentar todos os parâmetros (janela treino, validação, embargo)
- Documentar justificativa para escolha de parâmetros
- Criar diagrama visual da estrutura de folds

**Reproducibilidade:**
- Fixar random seeds
- Versionar código e dados
- Guardar configuração exata de cada execução

### 9.2 Durante a Execução

**Logging:**
- Log progresso de cada fold
- Log métricas intermediárias
- Log quaisquer erros ou warnings

**Checkpointing:**
- Guardar estado após cada fold
- Permitir retomar de fold específico
- Guardar modelos treinados

**Validação em Tempo Real:**
- Monitorizar performance de cada fold
- Detetar anomalias (folds com performance muito diferente)
- Parar se algo estiver errado

### 9.3 Após a Execução

**Análise de Resultados:**
- Calcular métricas agregadas
- Analisar estabilidade across folds
- Comparar validação vs teste

**Documentação:**
- Documentar resultados completos
- Documentar decisões baseadas em resultados
- Guardar artefatos (modelos, predições, métricas)

**Revisão:**
- Peer review dos resultados
- Validação de que não houve leakage
- Aprovação para próxima fase

---

## 10. EXEMPLOS PRÁTICOS

### 10.1 Exemplo: Estrutura Completa

**Dados:** 5 épocas NBA (2018-19 a 2022-23) = ~6000 jogos

**Parâmetros:**
- Janela treino: 36 meses (~3600 jogos)
- Janela validação: 1 mês (~100 jogos)
- Embargo: 2 dias (~2-3 jogos)
- Folds: 12

**Estrutura:**
```
Fold 1:
- Treino: 2018-19, 2019-20, 2020-21 (3600 jogos)
- Embargo: últimos 2 jogos de 2021-04
- Validação: 2021-11 (95 jogos)
- Resultado: ROI = 7.5%, Sharpe = 0.8

Fold 2:
- Treino: 2019-20, 2020-21, 2021-11 (3695 jogos)
- Embargo: últimos 2 jogos de 2021-12
- Validação: 2021-12 (92 jogos)
- Resultado: ROI = 6.8%, Sharpe = 0.7

...

Fold 12:
- Treino: 2020-21, 2021-22 meses 1-10, 2022-23 mês 1-2 (3580 jogos)
- Embargo: últimos 2 jogos de 2022-10
- Validação: 2022-10 (88 jogos)
- Resultado: ROI = 5.2%, Sharpe = 0.6

Teste Final:
- Treino: 2018-19, 2019-20, 2020-21, 2021-22 (4800 jogos)
- Embargo: últimos 2 jogos de 2022-10
- Teste: 2022-23 (1230 jogos)
- Resultado: ROI = 5.8%, Sharpe = 0.62
```

**Análise:**
```
Validação (média 12 folds):
- ROI = 6.5%, Std = 1.2%, CV = 0.18 ✓
- Sharpe = 0.72, Std = 0.15, CV = 0.21 ✓
- 11 de 12 folds com ROI > 0 ✓

Teste vs Validação:
- Gap ROI = |5.8% - 6.5%| / 6.5% = 11% ✓ (< 30%)
- Gap Sharpe = |0.62 - 0.72| / 0.72 = 14% ✓ (< 30%)

Conclusão: Modelo estável e generaliza bem
```

### 10.2 Exemplo: Problema de Estabilidade

**Resultado:**
```
Fold 1: ROI = 12%, Sharpe = 1.2
Fold 2: ROI = 8%, Sharpe = 0.9
Fold 3: ROI = -3%, Sharpe = -0.4
Fold 4: ROI = 15%, Sharpe = 1.5
Fold 5: ROI = -5%, Sharpe = -0.6
...
```

**Análise:**
```
Validação:
- ROI = 2.5%, Std = 8.5%, CV = 3.4 ✗ (> 0.5)
- 6 de 12 folds com ROI > 0 ✗ (< 8)
- Muita variabilidade entre folds
```

**Diagnóstico:**
- Modelo muito instável
- Possivelmente overfitted a regimes específicos
- Feature importance provavelmente inconsistente

**Ação:**
- Simplificar modelo
- Reduzir complexidade de features
- Aumentar janela de treino
- Considerar detecção de regimes

---

## 11. REFERÊNCIAS E BOAS PRÁTICAS

### 11.1 Literatura Recomendada

- **"Advances in Financial Machine Learning"** — Marcos Lopez de Prado (Capítulo 7 sobre Cross-Validation)
- **"Financial Machine Learning"** — Lopez de Prado (Capítulo sobre Purged K-Fold)
- **"Evidence-Based Technical Analysis"** — David Aronson (Capítulo sobre validação)
- **"Machine Learning for Asset Managers"** — Lopez de Prado (Capítulo sobre backtesting)

### 11.2 Ferramentas Úteis

- **Scikit-learn:** TimeSeriesSplit (base, não purged)
- **Custom implementations:** Purged K-Fold com embargo
- **MLfinlab:** Biblioteca específica para finance com purged CV
- **Version control:** Git para rastrear configurações

### 11.3 Regras de Ouro

1. **Nunca usar K-Fold clássico em dados temporais**
2. **Sempre aplicar purging e embargo**
3. **Nunca usar teste para tuning**
4. **Validar estabilidade across folds**
5. **Documentar todos os parâmetros e decisões**

---

## 12. LINKS CRUZADOS

- [[06_Backtesting/INDEX]] ← Secção mãe
- [[06_Backtesting/PURGED_CV]] → Documentação complementar de purged CV
- [[06_Backtesting/LEAKAGE_TEMPORAL]] → Detecção de leakage temporal
- [[05_Machine_Learning/INDEX]] → Modelagem e feature engineering
- [[03_Quant_Research/INDEX]] → Fundamentos estatísticos

---

## 13. GLOSSÁRIO

- **Walk-Forward CV:** Validação cruzada temporal com janelas deslizantes
- **Purged CV:** CV com remoção de dados próximos da fronteira
- **Embargo:** Período de separação explícito entre treino e validação
- **Fold:** Uma iteração de validação cruzada
- **Hold-out:** Conjunto de dados separado para avaliação final
- **Rolling Window:** Janela de tamanho fixo que desliza no tempo
- **Expanding Window:** Janela que cresce ao incluir mais dados
- **Temporal leakage:** Viés introduzido por usar dados futuros
- **Regime shift:** Mudança fundamental nas condições de mercado
- **Feature importance:** Importância relativa de cada feature no modelo