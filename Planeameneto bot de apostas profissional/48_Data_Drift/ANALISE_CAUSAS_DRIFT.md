# ANALISE_CAUSAS_DRIFT — Investigação e Diagnóstico

**ID:** `DRIFT-006` | **Fase:** #phase/6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Fornecer metodologia estruturada para investigar as causas raiz quando drift é detetado, permitindo decisões informadas sobre ações corretivas apropriadas.

---

## 2. CONTEXTO

Detetar drift é apenas o primeiro passo. Para responder eficazmente, é necessário entender:
- **Por que** o drift ocorreu
- **O que** está a causar o drift
- **Como** mitigar o impacto
- **Se** é uma mudança temporária ou permanente

Sem análise de causas, a equipa pode:
- Retreinar desnecessariamente (custo, tempo)
- Ignorar problemas reais (perdas financeiras)
- Aplicar soluções incorretas (agravar problema)

---

## 3. FRAMEWORK DE ANÁLISE

### 3.1 5 Whys (5 Porquês)

Metodologia para chegar à causa raiz fazendo perguntas "por que" sucessivas.

**Exemplo:**
1. Por que drift foi detetado na feature odds_home?
   - Porque a média das odds aumentou de 2.10 para 2.45.
2. Por que a média das odds aumentou?
   - Porque as odds dos jogos da Premier League aumentaram.
3. Por que as odds da Premier League aumentaram?
   - Porque há mais incerteza devido a lesões de jogadores chave.
4. Por que há mais lesões?
   - Porque o calendário está mais congestionado.
5. Por que o calendário está congestionado?
   - Porque a UEFA adicionou uma nova competição europeia.

**Causa raiz:** Nova competição europeia → calendário congestionado → mais lesões → odds mais altas → drift.

### 3.2 Fishbone Diagram (Ishikawa)

Diagrama de causa e efeito para categorizar possíveis causas.

**Categorias principais:**
- **Pessoas:** Mudanças na equipa, treinamento
- **Processos:** Mudanças no pipeline de dados
- **Tecnologia:** Mudanças no sistema, bugs
- **Dados:** Mudanças na fonte de dados
- **Ambiente:** Mudanças externas (regras, mercado)
- **Métodos:** Mudanças na metodologia de modelagem

### 3.3 Causal Graph

Grafo direcionado que mostra relações causais entre variáveis.

**Aplicação:**
- Mapear como mudanças em uma variável afetam outras
- Identificar caminhos causais para drift
- Distinguir correlação de causalidade

---

## 4. TIPOS DE CAUSAS

### 4.1 Causas Técnicas

Problemas relacionados com a infraestrutura e implementação.

**Exemplos:**
- **Bug na coleta de dados:** Script falha, parsing incorreto
- **Mudança no schema:** API retorna dados diferentes
- **Problema de qualidade:** Missing values, outliers, duplicados
- **Erro de deploy:** Versão incorreta do modelo em produção
- **Timeout/latência:** Dados incompletos devido a timeouts

**Sintomas:**
- Drift súbito (não gradual)
- Afeta apenas uma fonte de dados
- Padrões não naturais nos dados

**Investigação:**
- Verificar logs de ETL
- Validar schema dos dados
- Comparar counts de registros
- Verificar timestamps

### 4.2 Causas de Dados

Mudanças nos dados de entrada que não são bugs.

**Exemplos:**
- **Mudança na fonte:** Bookmaker muda API
- **Nova feature:** Fonte adiciona novo campo
- **Feature removida:** Fonte remove campo existente
- **Mudança de unidades:** Odds passam de decimal para fracional
- **Mudança de formato:** Data de DD/MM/YYYY para MM/DD/YYYY

**Sintomas:**
- Drift correlacionado com mudança na fonte
- Padrões consistentes com mudança documentada
- Afeta features específicas

**Investigação:**
- Verificar changelog da fonte de dados
- Contactar suporte da fonte
- Validar formato dos dados
- Comparar com documentação

### 4.3 Causas Externas

Mudanças no ambiente externo ao sistema.

**Exemplos:**
- **Mudança de regras:** VAR no futebol, novas regras da NBA
- **Eventos externos:** Pandemias, scandals, greves
- **Mudanças sazonais:** Férias, internacional breaks
- **Mudanças competitivas:** Novas equipas, novas ligas
- **Mudanças de mercado:** Bookmakers ajustam estratégias

**Sintomas:**
- Drift gradual ou em etapas
- Afeta múltiplas features correlacionadas
- Correlacionado com eventos externos conhecidos

**Investigação:**
- Verificar calendário de eventos
- Pesquisar notícias do desporto
- Analisar padrões sazonais históricos
- Comparar com outras fontes de dados

### 4.4 Causas de Modelo

Problemas relacionados com o modelo de ML.

**Exemplos:**
- **Overfitting:** Modelo aprende ruído, não padrão
- **Underfitting:** Modelo demasiado simples
- **Concept drift:** Relação feature-target mudou
- **Feature importance mudou:** Features relevantes mudaram
- **Interações mudaram:** Interações entre features mudaram

**Sintomas:**
- Drift em performance sem drift em features
- Feature importance muda significativamente
- Resíduos mostram padrões

**Investigação:**
- Analisar métricas de validação
- Comparar feature importance
- Analisar resíduos
- Validar em holdout set

---

## 5. PROCEDIMENTO DE INVESTIGAÇÃO

### 5.1 Fase 1: Triagem Rápida (15 min)

**Objetivo:** Determinar se é urgente e qual tipo de causa.

**Checklist:**
- [ ] Verificar se drift é CRITICAL
- [ ] Verificar se afeta apostas em tempo real
- [ ] Verificar se há múltiplas features com drift
- [ ] Verificar se há correlação com eventos recentes
- [ ] Verificar se há erros nos logs

**Decisão:**
- Se CRITICAL + afeta apostas → Ação imediata (pausar)
- Se não crítico → Continuar para Fase 2

### 5.2 Fase 2: Análise Preliminar (1h)

**Objetivo:** Identificar tipo provável de causa.

**Passos:**
1. **Visualizar dados:** Histogramas, time series
2. **Verificar logs:** ETL, API, sistema
3. **Comparar períodos:** Antes vs depois do drift
4. **Correlacionar eventos:** Verificar eventos externos
5. **Validar qualidade:** Missing values, outliers

**Output:** Hipótese preliminar da causa (técnica/dados/externa/modelo)

### 5.3 Fase 3: Análise Profunda (4h)

**Objetivo:** Confirmar causa raiz.

**Passos específicos por tipo:**

**Causa técnica:**
- Reproduzir bug em ambiente de dev
- Verificar código de ETL
- Testar API da fonte de dados
- Validar schema

**Causa de dados:**
- Contactar fonte de dados
- Documentar mudanças
- Validar formato
- Testar parsing

**Causa externa:**
- Pesquisar notícias
- Analisar calendário
- Comparar com anos anteriores
- Validar com especialistas do domínio

**Causa de modelo:**
- Revalidar modelo em holdout
- Analisar feature importance
- Testar retraining
- Comparar com baseline

**Output:** Causa raiz confirmada com evidência

### 5.4 Fase 4: Recomendação (1h)

**Objetivo:** Propor ação corretiva.

**Template de relatório:**
```
# Relatório de Análise de Drift

## Resumo
- Tipo de drift: Feature Drift
- Severidade: HIGH
- Data de deteção: 2024-01-15
- Causa raiz: Mudança de API do bookmaker X

## Evidência
- Drift detetado nas odds_home (PSI=0.25)
- Correlacionado com changelog do bookmaker (2024-01-14)
- Outras features não afetadas

## Impacto
- Apostas com odds do bookmaker X podem ter EV incorreto
- ~15% do volume de apostas afetado

## Recomendação
1. Atualizar parser de dados do bookmaker X
2. Retreinar modelo com dados corrigidos
3. Monitorizar drift por 7 dias

## Timeline
- Correção do parser: 2h
- Retraining: 4h
- Monitorização: 7 dias
```

---

## 6. FERRAMENTAS DE ANÁLISE

### 6.1 Visualização

**Ferramentas:**
- **Matplotlib/Seaborn:** Histogramas, time series
- **Plotly:** Dashboards interativos
- **Grafana:** Monitorização em tempo real
- **Tableau/PowerBI:** Exploração de dados

**Visualizações úteis:**
- Histogramas comparativos (ref vs atual)
- Time series de métricas
- Scatter plots de features
- Correlation heatmaps
- Boxplots por segmento

### 6.2 Análise Estatística

**Ferramentas:**
- **SciPy:** Testes estatísticos (KS, Chi-square)
- **Statsmodels:** Regressão, análise de séries temporais
- **Pandas:** Manipulação de dados
- **NumPy:** Cálculos numéricos

**Análises úteis:**
- Testes de hipótese
- Análise de correlação
- Decomposição de séries temporais
- Detecção de outliers

### 6.3 Logging e Monitoring

**Ferramentas:**
- **ELK Stack:** Logs centralizados
- **Prometheus:** Métricas de sistema
- **Grafana:** Dashboards de monitorização
- **Sentry:** Error tracking

**Logs úteis:**
- Logs de ETL
- Logs de API calls
- Logs de predições
- Logs de erros

---

## 7. DOCUMENTAÇÃO

### 7.1 Registro de Incidentes

Cada incidente de drift deve ser documentado:

**Campos obrigatórios:**
- ID do incidente
- Data e hora de deteção
- Tipo de drift
- Severidade
- Causa raiz
- Impacto
- Ação tomada
- Responsável
- Status

**Armazenamento:**
- Sistema de ticket (Jira, GitHub Issues)
- Repositório de documentação
- Base de conhecimento

### 7.2 Base de Conhecimento

Criar base de conhecimento com:
- Causas comuns de drift
- Padrões recorrentes
- Soluções padrão
- Lições aprendidas

**Benefícios:**
- Resolução mais rápida de incidentes futuros
- Redução de duplicação de esforço
- Melhoria contínua do processo

---

## 8. PREVENÇÃO

### 8.1 Monitorização Proativa

Implementar monitorização para detetar causas antes que causem drift:

- Monitorizar changelogs de fontes de dados
- Monitorizar métricas de qualidade de dados
- Monitorizar performance do sistema
- Monitorizar notícias do desporto

### 8.2 Testes de Regressão

Implementar testes para detetar regressões:

- Testes de schema de dados
- Testes de qualidade de dados
- Testes de performance de modelo
- Testes de integração

### 8.3 Documentação de Fontes

Manter documentação atualizada de:
- APIs de fontes de dados
- Schema de dados
- Mudanças esperadas
- Contatos de suporte

---

## 9. MELHORIAS FUTURAS

- [ ] Implementar auto-diagnóstico de causas usando ML
- [ ] Adicionar integração com sistemas de ticket automático
- [ ] Desenvolver knowledge graph de causas de drift
- [ ] Implementar análise preditiva de drift
- [ ] Adicionar colaboração em tempo real para investigação

---

## 10. LINKS CRUZADOS

- [[48_Data_Drift/INDEX]] ← Secção mãe
- [[48_Data_Drift/DETECAO_FEATURE_DRIFT]] → Detecção de feature drift
- [[48_Data_Drift/DETECAO_PREDICTION_DRIFT]] → Detecção de prediction drift
- [[48_Data_Drift/DETECAO_TARGET_DRIFT]] → Detecção de target drift
- [[48_Data_Drift/DETECAO_CONCEPT_DRIFT]] → Detecção de concept drift
- [[48_Data_Drift/MITIGACAO_DRIFT]] → Resposta a drift
- [[11_MLOps/INDEX]] → Operações de MLOps