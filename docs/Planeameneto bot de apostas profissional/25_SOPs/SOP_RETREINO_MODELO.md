# SOP_RETREINO_MODELO — Procedimento Operacional Padrão

**ID:** `SOP-005` | **Fase:** #phase/6 | **Owner:** ML Engineer | **Status:** #status/active
**Última Revisão:** 2024-05-13 | **Próxima Revisão:** 2024-08-13

---

## 1. OBJETIVO

Estabelecer um procedimento padronizado para o retreino do modelo de Machine Learning utilizado no sistema de value betting NBA. Este SOP garante que o modelo é retreinado de forma consistente, com dados de qualidade, e que o novo modelo é validado rigorosamente antes de ser colocado em produção, minimizando o risco de degradação de performance.

---

## 2. APLICAÇÃO

**Quando executar:**
- **Retreino programado:** Mensalmente (primeira segunda-feira de cada mês)
- **Retreino reativo:** Quando métricas de performance do modelo degradam (AUC < 0.55, drift detetado)
- **Retreino pós-incidente:** Após incidente que afetou qualidade dos dados ou do modelo
- **Retreino experimental:** Quando testando novas features ou arquiteturas

**Responsável:**
- ML Engineer (execução técnica)
- Data Engineer (preparação de dados)
- Risk Manager (aprovação de deploy)

**Duração estimada:**
- Preparação de dados: 2-4 horas
- Execução do retreino: 4-8 horas
- Validação: 2-4 horas
- Total: 8-16 horas (dependendo do tamanho do dataset)

---

## 3. PRÉ-REQUISITOS

### 3.1. Acesso e Ferramentas
- [ ] Acesso ao ambiente de treinamento (GPU/CPU)
- [ ] Acesso à base de dados PostgreSQL
- [ ] Acesso ao repositório de código (Git)
- [ ] Acesso ao Model Registry (MLflow ou similar)
- [ ] Acesso ao sistema de monitorização de modelos
- [ ] Acesso ao Jupyter Notebook ou ambiente Python

### 3.2. Conhecimentos Necessários
- Familiaridade com o pipeline de ML do sistema
- Conhecimento de técnicas de validação (walk-forward CV, purged CV)
- Capacidade de interpretar métricas de performance (AUC, calibração, feature importance)
- Conhecimento de técnicas de deteção de drift

### 3.3. Estado do Sistema
- [ ] Pipeline de dados está funcional
- [ ] Base de dados tem dados suficientes para retreino (mínimo 6 meses)
- [ ] Ambiente de treinamento tem recursos disponíveis
- [ ] Não há jobs críticos a correr no ambiente de produção

---

## 4. CRITÉRIOS DE RETREINO

### 4.1. Critérios de Performance

| Métrica | Threshold Normal | Threshold Alerta | Ação |
|---------|------------------|------------------|------|
| AUC (últimos 30 dias) | > 0.58 | < 0.55 | Considerar retreino |
| AUC (últimos 7 dias) | > 0.56 | < 0.53 | Considerar retreino urgente |
| Calibração (Brier score) | < 0.15 | > 0.20 | Considerar retreino |
| Feature drift (KS test) | < 0.1 | > 0.2 | Considerar retreino |
| Target drift (KS test) | < 0.1 | > 0.2 | Considerar retreino |

### 4.2. Critérios Temporais

- **Retreino programado:** Mensal (primeira segunda-feira)
- **Retreino trimestral:** Obrigatório, independentemente de performance
- **Retreino pós-offseason:** Após offseason NBA (setembro)
- **Retreino pós-mudança de regras:** Se NBA mudar regras significativamente

### 4.3. Critérios de Dados

- **Volume mínimo:** Pelo menos 1.000 jogos na base de treinamento
- **Recência:** Dados dos últimos 12 meses (com peso maior para últimos 6 meses)
- **Qualidade:** Menos de 5% de valores missing, menos de 2% de outliers
- **Balanceamento:** Taxa de vitória esperada entre 45-55%

---

## 5. PROCEDIMENTO DETALHADO

### 5.1. Fase 1: Preparação (1-2 horas)

**Objetivo:** Preparar ambiente, dados, e configuração para o retreino.

**Passos:**

1. **Agendar retreino:**
   - [ ] Notificar equipa com 3 dias de antecedência (se retreino programado)
   - [ ] Verificar que não há conflitos com outros jobs críticos
   - [ ] Agendar janela de manutenção se necessário (ver MANUTENCAO_PROGRAMADA)

2. **Preparar ambiente:**
   - [ ] Atualizar dependências: `pip install -r requirements.txt --upgrade`
   - [ ] Verificar disponibilidade de GPU/CPU
   - [ ] Limpar diretórios temporários
   - [ ] Verificar espaço em disco (mínimo 50GB livre)

3. **Backup do modelo atual:**
   - [ ] Exportar modelo atual para Model Registry
   - [ ] Guardar versão atual como "production_backup"
   - [ ] Documentar versão atual (ID, data, métricas)

4. **Preparar configuração:**
   - [ ] Criar ficheiro de configuração para o retreino
   - [ ] Definir hiperparâmetros (ou usar otimização automática)
   - [ ] Definir período de dados para treinamento
   - [ ] Definir período de dados para validação

### 5.2. Fase 2: Extração e Preparação de Dados (2-3 horas)

**Objetivo:** Extrair dados da base de dados e prepará-los para treinamento.

**Passos:**

1. **Extração de dados:**
   ```sql
   -- Extrair dados de jogos
   SELECT 
       game_id,
       game_date,
       home_team,
       away_team,
       final_score,
       home_score,
       away_score,
       venue,
       season
   FROM games
   WHERE game_date BETWEEN '[data_inicio]' AND '[data_fim]'
   ORDER BY game_date;
   
   -- Extrair features de jogadores
   SELECT 
       game_id,
       player_id,
       player_name,
       team,
       minutes,
       points,
       rebounds,
       assists,
       -- outras features
   FROM player_stats
   WHERE game_date BETWEEN '[data_inicio]' AND '[data_fim]';
   
   -- Extrair odds históricas
   SELECT 
       game_id,
       market,
       selection,
       closing_odds,
       opening_odds,
       timestamp
   FROM historical_odds
   WHERE game_date BETWEEN '[data_inicio]' AND '[data_fim]';
   ```

2. **Limpeza de dados:**
   - [ ] Remover duplicatas
   - [ ] Tratar valores missing (imputação ou remoção)
   - [ ] Remover outliers (usar IQR ou z-score)
   - [ ] Verificar consistência dos dados
   - [ ] Documentar decisões de limpeza

3. **Feature engineering:**
   - [ ] Calcular features derivadas (médias móveis, ratios, etc.)
   - [ ] Criar features temporais (dia da semana, mês, etc.)
   - [ ] Normalizar/standardizar features numéricas
   - [ ] Encode features categóricas
   - [ ] Documentar novas features criadas

4. **Split de dados:**
   - [ ] Dividir dados em treinamento e validação
   - [ ] Usar split temporal (não random split)
   - [ ] Exemplo: treinamento com dados até 30 dias atrás, validação com últimos 30 dias
   - [ ] Garantir que não há leakage (ver LEAKAGE_PREVENTION)

5. **Validação de qualidade:**
   - [ ] Verificar distribuição de features
   - [ ] Verificar balanceamento de classes
   - [ ] Verificar correlações entre features
   - [ ] Detetar multicolinearidade
   - [ ] Documentar descobertas

### 5.3. Fase 3: Execução do Retreino (4-8 horas)

**Objetivo:** Treinar o modelo com os dados preparados.

**Passos:**

1. **Configurar treinamento:**
   - [ ] Definir tipo de modelo (XGBoost, LightGBM, etc.)
   - [ ] Definir hiperparâmetros iniciais
   - [ ] Configurar cross-validation (walk-forward ou purged)
   - [ ] Configurar early stopping
   - [ ] Configurar logging

2. **Executar treinamento:**
   ```python
   # Exemplo pseudocódigo
   from xgboost import XGBClassifier
   from sklearn.model_selection import TimeSeriesSplit
   
   # Configurar modelo
   model = XGBClassifier(
       n_estimators=1000,
       max_depth=6,
       learning_rate=0.01,
       subsample=0.8,
       colsample_bytree=0.8,
       random_state=42
   )
   
   # Configurar cross-validation temporal
   tscv = TimeSeriesSplit(n_splits=5)
   
   # Treinar com cross-validation
   for train_idx, val_idx in tscv.split(X_train):
       X_train_fold, X_val_fold = X_train[train_idx], X_train[val_idx]
       y_train_fold, y_val_fold = y_train[train_idx], y_train[val_idx]
       
       model.fit(
           X_train_fold, y_train_fold,
           eval_set=[(X_val_fold, y_val_fold)],
           early_stopping_rounds=50,
           verbose=False
       )
   
   # Treinar modelo final com todos os dados
   model.fit(X_train, y_train)
   ```

3. **Otimização de hiperparâmetros (opcional):**
   - [ ] Se usando Optuna ou similar: configurar search space
   - [ ] Definir número de trials (ex: 100)
   - [ ] Definir métrica de otimização (AUC, log loss, etc.)
   - [ ] Executar otimização
   - [ ] Guardar melhores hiperparâmetros

4. **Monitorizar treinamento:**
   - [ ] Monitorizar logs de treinamento
   - [ ] Verificar que não há overfitting (treino vs validação)
   - [ ] Verificar que treinamento está a progredir
   - [ ] Se treinamento estagnou: ajustar hiperparâmetros

5. **Guardar modelo:**
   - [ ] Exportar modelo para ficheiro (pickle, joblib, etc.)
   - [ ] Registar modelo no Model Registry
   - [ ] Guardar metadata (hiperparâmetros, métricas, data)
   - [ ] Guardar artefactos (features usadas, preprocessing pipeline)

### 5.4. Fase 4: Validação (2-4 horas)

**Objetivo:** Validar que o novo modelo é superior ou igual ao modelo atual.

**Passos:**

1. **Validação no conjunto de validação:**
   - [ ] Fazer predições no conjunto de validação
   - [ ] Calcular métricas de performance:
     - AUC
     - Accuracy
     - Precision
     - Recall
     - F1-score
     - Log loss
     - Brier score (calibração)
   - [ ] Comparar com modelo atual

2. **Análise de calibração:**
   - [ ] Gerar reliability diagram
   - [ ] Calcular Brier score
   - [ ] Comparar calibração com modelo atual
   - [ ] Se calibração pobre: considerar calibração isotônica (ver CALIBRACAO_ISOTONICA)

3. **Análise de feature importance:**
   - [ ] Calcular feature importance (SHAP values, gain, etc.)
   - [ ] Comparar com feature importance do modelo atual
   - [ ] Verificar se features importantes mudaram drasticamente
   - [ ] Investigar se mudança é justificada

4. **Backtesting:**
   - [ ] Executar backtesting com novo modelo (ver BACKTESTING)
   - [ ] Usar walk-forward cross-validation
   - [ ] Calcular métricas de backtesting:
     - ROI simulado
     - Drawdown máximo
     - Sharpe ratio
     - Taxa de acerto
   - [ ] Comparar com backtesting do modelo atual

5. **Deteção de drift:**
   - [ ] Comparar distribuição de predições novo vs atual
   - [ ] Executar KS test para deteção de drift
   - [ ] Verificar se há drift significativo
   - [ ] Se drift: investigar causa

6. **Critérios de aprovação:**
   - [ ] AUC novo >= AUC atual - 0.01 (tolerância pequena)
   - [ ] Calibração nova <= calibração atual + 0.02
   - [ ] ROI simulado novo >= ROI simulado atual - 0.5%
   - [ ] Drawdown simulado novo <= drawdown simulado atual + 2%
   - [ ] Não há drift significativo nas predições

### 5.5. Fase 5: Decisão e Documentação (1-2 horas)

**Objetivo:** Decidir se aprovar novo modelo e documentar processo.

**Passos:**

1. **Comparar modelos:**
   - Criar tabela comparativa:
   
   | Métrica | Modelo Atual | Modelo Novo | Diferença | Status |
   |---------|--------------|-------------|-----------|--------|
   | AUC | 0.58 | 0.59 | +0.01 | ✅ |
   | Calibração | 0.14 | 0.13 | -0.01 | ✅ |
   | ROI simulado | 3.5% | 3.8% | +0.3% | ✅ |
   | Drawdown | 12% | 11% | -1% | ✅ |

2. **Tomar decisão:**
   - Se todos os critérios de aprovação são cumpridos: **APROVAR**
   - Se alguns critérios não são cumpridos mas melhoria é marginal: **APROVAR COM RESERVAS**
   - Se critérios críticos não são cumpridos: **REJEITAR**

3. **Documentar retreino:**
   - [ ] Criar relatório de retreino
   - [ ] Incluir: data, período de dados, hiperparâmetros, métricas, comparações
   - [ ] Incluir gráficos de performance
   - [ ] Incluir análise de feature importance
   - [ ] Guardar relatório no Model Registry

4. **Notificar equipa:**
   - [ ] Enviar resumo para canal ops_documentacao
   - [ ] Se modelo aprovado: notificar que deploy está agendado
   - [ ] Se modelo rejeitado: documentar motivos e próxima ação

---

## 6. PROCEDIMENTO DE EMERGÊNCIA

### 6.1. Se Retreino Falha

**Passos:**
1. Verificar logs de erro
2. Identificar causa (dados, código, recursos)
3. Se problema de dados: corrigir dados, reiniciar retreino
4. Se problema de código: corrigir código, reiniciar retreino
5. Se problema de recursos: alocar mais recursos ou reduzir dataset
6. Se não for possível resolver: manter modelo atual, documentar falha

### 6.2. Se Novo Modelo Pior que Atual

**Passos:**
1. Investigar causa (overfitting, dados ruins, hiperparâmetros)
2. Se overfitting: ajustar regularização, reduzir complexidade
3. Se dados ruins: investigar qualidade dos dados
4. Se hiperparâmetros: ajustar ou usar otimização
5. Se não for possível melhorar: rejeitar modelo, manter atual

### 6.3. Se Retreino Demora Muito

**Passos:**
1. Verificar uso de recursos (CPU/GPU, memória)
2. Se recursos insuficientes: alocar mais ou reduzir dataset
3. Se código ineficiente: otimizar código
4. Se dataset muito grande: amostrar dados ou usar incremental learning
5. Se não for possível acelerar: agendar retreino para janela mais longa

---

## 7. TABELAS DE REFERÊNCIA

### 7.1. Hiperparâmetros Típicos (XGBoost)

| Hiperparâmetro | Valor Típico | Range |
|----------------|--------------|-------|
| n_estimators | 500-1000 | 100-2000 |
| max_depth | 4-8 | 3-10 |
| learning_rate | 0.01-0.1 | 0.001-0.3 |
| subsample | 0.7-0.9 | 0.5-1.0 |
| colsample_bytree | 0.7-0.9 | 0.5-1.0 |
| min_child_weight | 1-5 | 1-10 |
| gamma | 0-0.5 | 0-1 |
| reg_alpha | 0-1 | 0-10 |
| reg_lambda | 1-2 | 0.5-5 |

### 7.2. Métricas de Performance

| Métrica | Descrição | Valor Alvo | Mínimo Aceitável |
|---------|-----------|------------|------------------|
| AUC | Área sob a curva ROC | > 0.60 | > 0.55 |
| Accuracy | Taxa de acerto | > 0.55 | > 0.50 |
| Log Loss | Logarithmic loss | < 0.65 | < 0.70 |
| Brier Score | Calibração | < 0.15 | < 0.20 |
| ROI Simulado | Return on Investment simulado | > 3% | > 1% |
| Sharpe Ratio | Risco ajustado | > 1.0 | > 0.5 |

### 7.3. Tempos Estimados

| Atividade | Dataset Pequeno (< 1000 jogos) | Dataset Médio (1000-5000 jogos) | Dataset Grande (> 5000 jogos) |
|-----------|--------------------------------|----------------------------------|--------------------------------|
| Extração de dados | 30 minutos | 1 hora | 2 horas |
| Limpeza de dados | 1 hora | 2 horas | 4 horas |
| Feature engineering | 1 hora | 2 horas | 4 horas |
| Treinamento | 1 hora | 3 horas | 8 horas |
| Validação | 1 hora | 2 horas | 4 horas |
| **TOTAL** | **4.5 horas** | **10 horas** | **22 horas** |

---

## 8. CHECKLIST FINAL

Antes de considerar retreino concluído, verificar:

- [ ] Dados extraídos e limpos
- [ ] Features criadas e validadas
- [ ] Modelo treinado com sucesso
- [ ] Modelo guardado no Model Registry
- [ ] Validação concluída
- [ ] Métricas calculadas e comparadas
- [ ] Decisão tomada (aprovar/rejeitar)
- [ ] Relatório de retreino criado
- [ ] Equipa notificada
- [ ] Se aprovado: deploy agendado (ver SOP-006)

---

## 9. MÉTRICAS DE SUCESSO

| Métrica | Threshold | Ação se não cumprido |
|---------|-----------|---------------------|
| Taxa de sucesso do retreino | > 90% | Investigar falhas |
| Tempo de retreino | < 12 horas | Otimizar processo |
| Melhoria de AUC médio | > 0.005 | Revisar estratégia |
| Taxa de aprovação de modelos | > 70% | Ajustar critérios |
| Tempo entre retreinos | 30 dias | Agendar melhor |

---

## 10. RISCOS E MITIGAÇÃO

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|------------|
| Overfitting | Alto (performance pobre em produção) | Médio | Cross-validation rigoroso, early stopping |
| Dados de baixa qualidade | Alto (modelo ruim) | Médio | Validação de dados, limpeza rigorosa |
| Retreino demorado | Médio (atraso no deploy) | Baixa | Otimização de código, recursos adequados |
- Modelo pior que atual | Médio (deploy desnecessário) | Baixa | Validação rigorosa, comparação com atual |
- Drift não detetado | Alto (performance degrada) | Médio | Monitorização contínua, deteção de drift |

---

## 11. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
- [[05_Machine_Learning/INDEX]] → Documentação de ML
- [[05_Machine_Learning/WALK_FORWARD_CV]] → Cross-validation temporal
- [[05_Machine_Learning/CALIBRACAO_ISOTONICA]] → Calibração de modelo
- [[05_Machine_Learning/OPTUNA_TUNING]] → Otimização de hiperparâmetros
- [[06_Backtesting/INDEX]] → Backtesting
- [[11_MLOps/INDEX]] → MLOps
- [[30_Model_Registry/INDEX]] → Model Registry