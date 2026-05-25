# LEAKAGE TEMPORAL — Detecção, Prevenção e Auditoria

**ID:** `BT-001` | **Fase:** #phase/2 | **Owner:** Quant Research Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar todos os tipos de leakage temporal que podem invalidar um backtest, fornecer métodos sistemáticos de deteção, estabelecer protocolos de prevenção e criar um framework de auditoria contínua. **Leakage é a causa #1 de backtests enganosos** — um modelo com leakage aparenta ter edge quando na realidade está apenas a "olhar para o futuro".

---

## 2. DEFINIÇÃO E IMPORTÂNCIA

### 2.1 O Que É Leakage Temporal?

Leakage temporal ocorre quando informação do futuro é acidentalmente incorporada no conjunto de treino ou validação, permitindo que o modelo "veja" o resultado antes de fazer a predição. Em backtesting de apostas desportivas, isto é particularmente insidioso porque:

- **Otimista por definição:** Um modelo com leakage terá sempre performance melhor que a realidade
- **Difícil de detetar:** O leakage pode ser subtil e escondido em features aparentemente inocentes
- **Catastrófico em produção:** Um modelo com leakage passará no backtest mas perderá dinheiro consistentemente

### 2.2 Por Que É Crítico?

Na indústria de hedge funds e quant trading, estima-se que **70-80% das estratégias que falham em produção sofriam de leakage não detetado**. O custo de implementar uma estratégia com leakage inclui:

- Desenvolvimento de infraestrutura (APIs, databases, sistemas de execução)
- Perda de capital real (apostas com edge negativo)
- Dano reputacional (se for um serviço tipster)
- Tempo perdido que poderia ser investido em estratégias válidas

---

## 3. TIPOS DE LEAKAGE

### 3.1 Target Leakage (Leakage do Alvo)

**Definição:** O target ou variável dependente contém informação que não estaria disponível no momento da predição.

**Exemplos Comuns em Apostas:**
- Usar estatísticas do jogo que estamos a prever (ex: pontos totais do jogo para preder o vencedor)
- Incluir resultado de jogos que aconteceram no mesmo dia mas antes do jogo em questão
- Usar odds de fecho quando só teríamos acesso a odds de abertura

**Como Deteção:**
1. Listar todas as features e o target
2. Para cada feature, perguntar: "Quando é que esta informação estaria disponível?"
3. Verificar se alguma feature depende do resultado do jogo em si
4. Cross-reference com timestamps dos dados

**Exemplo Prático:**
```
❌ INCORRETO:
Feature: "Pontos marcados pelo time no jogo"
Target: "Vitória do time"
Problema: Os pontos marcados só são conhecidos APÓS o jogo

✅ CORRETO:
Feature: "Média de pontos marcados nos últimos 10 jogos"
Target: "Vitória do time"
OK: Esta média é calculada com dados históricos anteriores ao jogo
```

### 3.2 Temporal Leakage (Leakage Temporal)

**Definição:** Informação de períodos futuros "vaza" para períodos passados através de operações de agregação ou normalização.

**Exemplos Comuns:**
- Normalização de features usando estatísticas globais (média, desvio padrão) calculadas em todo o dataset
- Rolling windows que incluem dados futuros
- Imputation de missing values usando média global
- Standardization usando parâmetros calculados em todo o dataset

**Como Deteção:**
1. Verificar todas as operações de pré-processamento
2. Identificar operações que usam dados de múltiplos períodos
3. Confirmar que a normalização é feita dentro de cada fold de validação cruzada
4. Usar purged cross-validation para garantir separação temporal

**Exemplo Prático:**
```
❌ INCORRETO:
# Normalização global antes de split temporal
X_normalized = (X - X.mean()) / X.std()
X_train, X_test = split_temporal(X_normalized, y)

✅ CORRETO:
# Normalização dentro de cada fold
for fold in folds:
    X_train_fold, X_test_fold = get_fold_data(fold)
    mean_train, std_train = X_train_fold.mean(), X_train_fold.std()
    X_train_normalized = (X_train_fold - mean_train) / std_train
    X_test_normalized = (X_test_fold - mean_train) / std_train
```

### 3.3 Look-Ahead Bias em Features

**Definição:** Features que usam dados que só estariam disponíveis após o momento de decisão.

**Exemplos Comuns em Apostas NBA:**
- Usar estatísticas de "últimos 5 jogos" quando o 5º jogo ainda não aconteceu
- Incluir injury reports que só foram publicados após o tip-off
- Usar odds de closing line quando só teríamos odds de opening line
- Features calculadas com dados de jogos que ainda não terminaram

**Como Deteção:**
1. Criar um "audit trail" para cada feature: timestamp da feature vs timestamp do jogo
2. Verificar se feature_timestamp < game_timestamp para todas as observações
3. Usar embargo periods explicitamente
4. Simular tempo real: processar dados sequencialmente como se fosse produção

**Exemplo Prático:**
```
❌ INCORRETO:
Feature: "Forma dos últimos 5 jogos" (calculada no dia do jogo)
Problema: Se o jogo é às 20:00, e a feature inclui um jogo das 19:00,
          há look-ahead porque esse jogo ainda não terminou

✅ CORRETO:
Feature: "Forma dos últimos 5 jogos completos" (calculada no dia anterior)
Embargo: 2 dias entre o último jogo usado e o jogo a prever
```

### 3.4 Data Leakage via Selection Bias

**Definição:** O conjunto de dados é filtrado de forma que introduz bias temporal, removendo observações que teriam estado disponíveis em produção.

**Exemplos Comuns:**
- Remover jogos sem odds disponíveis (mas que teriam estado disponíveis em tempo real)
- Filtrar por "apostas executadas" quando em produção não saberíamos quais seriam executadas
- Usar survivorship bias (só incluir times/jogadores que ainda estão ativos)

**Como Deteção:**
1. Comparar número de jogos no backtest vs número de jogos históricos totais
2. Verificar se algum filtro remove jogos que teriam estado disponíveis
3. Simular o processo de seleção de apostas SEM olhar para o resultado
4. Documentar todos os filtros aplicados e justificar cada um

### 3.5 Slippage Otimista

**Definição:** Assumir custos de transação irrealisticamente baixos, levando a ROI inflacionado.

**Exemplos Comuns:**
- Assumir execução sempre na odd exata do sinal
- Ignorar slippage por movimento de odds entre sinal e execução
- Subestimar comissões ou fees
- Assumir 100% de fill rate (todas as apostas executadas)

**Como Deteção:**
1. Sensitivity analysis: testar com diferentes níveis de slippage (0.5%, 1%, 2%)
2. Comparar com dados de paper trading quando disponíveis
3. Usar custos conservadores (pessimistas) no backtest principal
4. Documentar todas as assunções sobre custos

---

## 4. MÉTODOS DE DETEÇÃO

### 4.1 Audit Trail de Features

Cada feature deve ter documentação explícita de:

```markdown
## Feature Audit Template

**Nome:** `rolling_points_last_5`
**Descrição:** Média de pontos marcados nos últimos 5 jogos
**Data Source:** API de estatísticas NBA
**Known At:** 24h antes do jogo (após último jogo do time)
**Leakage Risk:** Baixo
**Validation:**
- [ ] Feature timestamp < Game timestamp para 100% das observações
- [ ] Não depende de resultado do jogo atual
- [ ] Não usa dados de jogos futuros
```

### 4.2 Temporal Consistency Check

Implementar validação automatizada:

1. **Timestamp Validation:** Verificar que todas as features têm timestamp <= game timestamp
2. **Embargo Validation:** Verificar que existe período mínimo (ex: 2 dias) entre último dado usado e jogo
3. **Rolling Window Validation:** Verificar que janelas móveis não incluem dados futuros
4. **Normalization Validation:** Verificar que normalização é feita dentro de folds

### 4.3 Correlation Analysis

Leakage muitas vezes manifesta-se como correlação anormalmente alta com o target:

- Correlação > 0.9 com target é sinal de alerta
- Feature importance extremamente alta (> 80%) pode indicar leakage
- Comparar correlações em treino vs validação (leakage tende a ser estável)

### 4.4 Randomization Test

Permutar o target e verificar se features ainda têm poder preditivo:

1. Permutar aleatoriamente os labels (resultados dos jogos)
2. Treinar modelo com dados permutados
3. Se performance ainda é alta, há leakage no feature engineering
4. Modelo com dados permutados deve ter performance próxima de random (50% accuracy)

---

## 5. PROTOCOLO DE PREVENÇÃO

### 5.1 Purged Cross-Validation com Embargo

**Conceito:** Validar o modelo de forma estritamente temporal, removendo dados próximos da fronteira entre treino e validação.

**Implementação:**
- Janela de treino: 36 meses deslizante
- Janela de validação: 1 mês
- Embargo: 2 dias mínimo entre treino e validação
- Folds: 12 (um por mês de validação)

**Por Que Funciona:**
- Garante que o modelo nunca vê dados do futuro
- Embargo previne leakage de features com "memória" (ex: rolling averages)
- Simula o processo real de treino em produção

### 5.2 Feature Engineering Temporal

**Regras de Ouro:**

1. **Só usar dados conhecidos antes do jogo**
   - Timestamp da feature deve ser documentado
   - Implementar verificação automatizada de timestamps

2. **Normalização dentro de folds**
   - Nunca normalizar globalmente antes do split temporal
   - Calcular parâmetros de normalização só no set de treino

3. **Embargo explícito**
   - Definir período mínimo (ex: 2 dias) entre último dado usado e predição
   - Implementar verificação automatizada de embargo

4. **Documentação completa**
   - Cada feature tem "known_at_timestamp" documentado
   - Audit trail mantido para todas as transformações

### 5.3 Pipeline de Validação

```
1. PREPARAÇÃO
   ├── Ingerir dados com timestamps explícitos
   ├── Criar audit trail para cada feature
   └── Documentar todas as transformações

2. SPLIT TEMPORAL
   ├── Dividir dados em treino/validação/teste por tempo
   ├── Aplicar embargo entre folds
   └── Verificar ordenação temporal

3. FEATURE ENGINEERING
   ├── Calcular features dentro de cada fold
   ├── Normalizar usando só dados de treino
   └── Verificar timestamps vs game timestamps

4. VALIDAÇÃO
   ├── Temporal consistency check
   ├── Correlation analysis
   ├── Randomization test
   └── Feature importance stability

5. AUDIT FINAL
   ├── Revisar manualmente top 10 features
   ├── Verificar todas as assunções
   └── Documentar todas as decisões
```

---

## 6. AUDITORIA CONTÍNUA

### 6.1 Checklist de Audit

Antes de aprovar um backtest para produção:

**Dados:**
- [ ] Todos os dados têm timestamps explícitos
- [ ] Timestamps são consistentes (sem timezones misturados)
- [ ] Dados estão ordenados temporalmente
- [ ] Não há dados duplicados ou sobrepostos

**Features:**
- [ ] Cada feature tem "known_at_timestamp" documentado
- [ ] Feature timestamp < game timestamp para 100% das observações
- [ ] Normalização feita dentro de folds
- [ ] Nenhuma feature depende do resultado do jogo atual
- [ ] Embargo aplicado corretamente

**Validação:**
- [ ] Purged CV implementado com embargo
- [ ] Folds são estritamente temporais
- [ ] Randomization test passa (modelo permutado ≈ random)
- [ ] Correlações com target são razoáveis (< 0.9)
- [ ] Feature importance é estável across folds

**Custos:**
- [ ] Slippage incluído (mínimo 0.5%)
- [ ] Comissão incluída (5% para Betfair)
- [ ] Fill rate realista (< 100%)
- [ ] Sensitivity analysis realizada

### 6.2 Automatização

Implementar scripts automatizados que:

1. Validam timestamps automaticamente
2. Detetam correlações anormais
3. Executam randomization test
4. Geram relatório de audit
5. Bloqueiam backtests que não passam

### 6.3 Peer Review

Todo backtest deve ser revisto por outro quant que:

- Verifica manualmente as top 5 features
- Questiona todas as assunções
- Confirma que o pipeline é reproduzível
- Valida que não há leakage óbvio

---

## 7. EXEMPLOS PRÁTICOS

### 7.1 Caso de Estudo: Feature Problemática

**Feature Proposta:** "Média de pontos dos últimos 5 jogos"

**Análise de Leakage:**
```
✅ CORRETO se:
- Calculada 24h antes do jogo
- Usa só jogos completos
- Tem embargo de 2 dias após último jogo usado

❌ INCORRETO se:
- Calculada no dia do jogo (pode incluir jogo em andamento)
- Usa jogos que ainda não terminaram
- Não tem embargo
```

### 7.2 Caso de Estudo: Normalização Errada

**Cenário:** Normalizar features usando média e desvio padrão globais

**Problema:**
```python
❌ INCORRETO:
X_normalized = (X - X.mean()) / X.std()
# Isso usa informação de TODO o dataset, incluindo futuro
```

**Solução:**
```python
✅ CORRETO:
for fold in folds:
    X_train, X_test = get_fold_data(fold)
    mean_train, std_train = X_train.mean(), X_train.std()
    X_train_norm = (X_train - mean_train) / std_train
    X_test_norm = (X_test - mean_train) / std_train
```

### 7.3 Caso de Estudo: Embargo Violado

**Cenário:** Usar estatísticas dos últimos 5 jogos, sendo o último jogo ontem

**Problema:**
- Sem embargo, o modelo pode "aprender" padrões muito recentes
- Em produção, o dado mais recente pode não estar disponível a tempo
- Leakage subtil: o modelo está a usar informação muito fresca

**Solução:**
- Implementar embargo de 2 dias
- Só usar jogos completos até 2 dias antes da predição
- Documentar explicitamente o período de embargo

---

## 8. REFERÊNCIAS E BOAS PRÁTICAS

### 8.1 Literatura Recomendada

- **"Advances in Financial Machine Learning"** — Marcos Lopez de Prado (Capítulo 7 sobre Cross-Validation)
- **"Evidence-Based Technical Analysis"** — David Aronson (Capítulo sobre Data Snooping)
- **"Pseudo-Mathematics and Financial Charlatanism"** — Bailey et al. (Sobre overfitting e leakage)

### 8.2 Ferramentas Úteis

- **Temporal validation splits:** sklearn's TimeSeriesSplit
- **Leakage detection:** Feature importance analysis, correlation matrices
- **Audit automation:** Custom scripts para validar timestamps
- **Version control:** Git para rastrear mudanças no pipeline

### 8.3 Regras de Ouro

1. **Nunca confiar num backtest sem audit de leakage**
2. **Se algo parece bom demais para ser verdade, provavelmente é leakage**
3. **Documentar tudo: assunções, transformações, timestamps**
4. **Ser conservador: assumir pior cenário para custos**
5. **Peer review é obrigatório para backtests críticos**

---

## 9. LINKS CRUZADOS

- [[06_Backtesting/INDEX]] ← Secção mãe
- [[06_Backtesting/PURGED_CV]] → Implementação de CV temporal
- [[06_Backtesting/OVERFITTING_TESTS]] → Testes complementares de robustez
- [[05_Machine_Learning/INDEX]] → Feature engineering e modelagem
- [[04_Data_Engineering/INDEX]] → Ingestão e validação de dados

---

## 10. GLOSSÁRIO

- **Leakage:** Informação do futuro acidentalmente incorporada no treino
- **Look-ahead bias:** Viés introduzido por usar dados futuros
- **Embargo:** Período de separação entre treino e validação
- **Purged CV:** Cross-validation temporal com remoção de dados próximos da fronteira
- **Timestamp:** Marca temporal que indica quando a informação estava disponível
- **Audit trail:** Documentação completa da origem e transformação de dados