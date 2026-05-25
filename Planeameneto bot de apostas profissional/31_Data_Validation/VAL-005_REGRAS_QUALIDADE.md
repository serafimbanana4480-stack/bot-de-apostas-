# VAL-005 — Regras de Qualidade de Dados

**ID:** `VAL-005` | **Fase:** #phase/4 | **Owner:** Data Engineer | **Status:** #status/in_progress

---

## 1. OBJETIVO

Definir o conjunto completo de regras de qualidade de dados que devem ser aplicadas em todas as etapas do pipeline. As regras são divididas em regras de negócio (baseadas em conhecimento do domínio de betting) e regras estatísticas (baseadas em propriedades estatísticas dos dados).

---

## 2. CONTEXTO

As regras de qualidade são a implementação concreta da validação de dados. Cada regra define:
- Uma condição que deve ser satisfeita
- A severidade da violação (CRITICAL, HIGH, MEDIUM, LOW)
- A ação a tomar quando a regra é violada
- A justificativa para a regra

As regras são aplicadas automaticamente pelo pipeline de validação, mas também podem ser usadas manualmente para auditoria de qualidade.

---

## 3. REGRAS DE NEGÓCIO

### 3.1. Regras para Tabela de Jogos (games)

| ID | Regra | Descrição | Severidade | Ação |
|----|-------|-----------|------------|------|
| BN-G-001 | game_id não null | Identificador único obrigatório | CRITICAL | Rejeitar registro |
| BN-G-002 | game_date não null | Data do jogo obrigatória | CRITICAL | Rejeitar registro |
| BN-G-003 | game_date não futuro (para jogos finished) | Jogos terminados não podem ter data futura | CRITICAL | Rejeitar registro |
| BN-G-004 | game_date ≥ 2015-01-01 | Data mínima histórica | HIGH | Rejeitar registro |
| BN-G-005 | home_team_id ≠ away_team_id | Equipa não pode jogar contra si mesma | CRITICAL | Rejeitar registro |
| BN-G-006 | home_team_id não null | Equipa da casa obrigatória | CRITICAL | Rejeitar registro |
| BN-G-007 | away_team_id não null | Equipa visitante obrigatória | CRITICAL | Rejeitar registro |
| BN-G-008 | status ∈ {scheduled, in_progress, finished, postponed, cancelled} | Estado válido | CRITICAL | Rejeitar registro |
| BN-G-009 | home_score ≥ 0 (se não null) | Pontuação não pode ser negativa | CRITICAL | Rejeitar registro |
| BN-G-010 | away_score ≥ 0 (se não null) | Pontuação não pode ser negativa | CRITICAL | Rejeitar registro |
| BN-G-011 | home_score ≤ 200 (se não null) | Pontuação dentro de limites razoáveis | HIGH | Flag para revisão |
| BN-G-012 | away_score ≤ 200 (se não null) | Pontuação dentro de limites razoáveis | HIGH | Flag para revisão |
| BN-G-013 | season formato válido (YYYY-YY) | Formato de temporada válido | HIGH | Rejeitar registro |
| BN-G-014 | game_type ∈ {regular, preseason, playoff} | Tipo de jogo válido | HIGH | Rejeitar registro |

### 3.2. Regras para Tabela de Odds (odds)

| ID | Regra | Descrição | Severidade | Ação |
|----|-------|-----------|------------|------|
| BN-O-001 | market_id não null | Identificador de mercado obrigatório | CRITICAL | Rejeitar registro |
| BN-O-002 | selection_id não null | Identificador de seleção obrigatório | CRITICAL | Rejeitar registro |
| BN-O-003 | odd não null | Valor da odd obrigatório | CRITICAL | Rejeitar registro |
| BN-O-004 | odd > 1.0 | Odd mínima válida | CRITICAL | Rejeitar registro |
| BN-O-005 | odd < 1000.0 | Odd máxima razoável | HIGH | Flag para revisão |
| BN-O-006 | odd ≤ 2 casas decimais | Precisão adequada | LOW | Arredondar |
| BN-O-007 | timestamp não null | Timestamp obrigatório | CRITICAL | Rejeitar registro |
| BN-O-008 | timestamp ≤ now | Timestamp não pode ser futuro | CRITICAL | Rejeitar registro |
| BN-O-009 | timestamp ≥ game_date - 7 dias | Janela temporal razoável | HIGH | Flag para revisão |
| BN-O-010 | timestamp < game_date + 2h | Odds pré-jogo ou in-game | CRITICAL | Rejeitar registro |
| BN-O-011 | market_id formato Betfair | Formato válido de market_id | HIGH | Rejeitar registro |
| BN-O-012 | selection_id formato Betfair | Formato válido de selection_id | HIGH | Rejeitar registro |
| BN-O-013 | market ∈ {moneyline_home, moneyline_away, spread_home, spread_away, total_over, total_under} | Mercado válido | CRITICAL | Rejeitar registro |
| BN-O-014 | odds home + odds away ∈ [1.9, 2.3] (moneyline) | Margem de mercado razoável | MEDIUM | Flag para revisão |

### 3.3. Regras para Tabela de Estatísticas de Jogadores (player_stats)

| ID | Regra | Descrição | Severidade | Ação |
|----|-------|-----------|------------|------|
| BN-P-001 | player_id não null | Identificador de jogador obrigatório | CRITICAL | Rejeitar registro |
| BN-P-002 | game_id não null | Identificador de jogo obrigatório | CRITICAL | Rejeitar registro |
| BN-P-003 | team_id não null | Identificador de equipa obrigatório | CRITICAL | Rejeitar registro |
| BN-P-004 | player_id existe na tabela de jogadores | Integridade referencial | CRITICAL | Rejeitar registro |
| BN-P-005 | game_id existe na tabela de jogos | Integridade referencial | CRITICAL | Rejeitar registro |
| BN-P-006 | team_id ∈ {home_team_id, away_team_id do jogo} | Jogador pertence a uma das equipas | CRITICAL | Rejeitar registro |
| BN-P-007 | minutes_played ∈ [0, 48] | Tempo máximo NBA | CRITICAL | Rejeitar registro |
| BN-P-008 | seconds_played ∈ [0, 2880] | Tempo máximo em segundos | CRITICAL | Rejeitar registro |
| BN-P-009 | field_goals_made ≤ field_goals_attempted | Consistência lógica | CRITICAL | Rejeitar registro |
| BN-P-010 | free_throws_made ≤ free_throws_attempted | Consistência lógica | CRITICAL | Rejeitar registro |
| BN-P-011 | three_pointers_made ≤ three_pointers_attempted | Consistência lógica | CRITICAL | Rejeitar registro |
| BN-P-012 | field_goal_percentage ∈ [0.0, 1.0] | Percentagem válida | CRITICAL | Rejeitar registro |
| BN-P-013 | free_throw_percentage ∈ [0.0, 1.0] | Percentagem válida | CRITICAL | Rejeitar registro |
| BN-P-014 | points ∈ [0, 100] | Pontos dentro de limites razoáveis | HIGH | Flag para revisão |
| BN-P-015 | rebounds ∈ [0, 55] | Rebotes dentro de limites razoáveis | HIGH | Flag para revisão |
| BN-P-016 | assists ∈ [0, 30] | Assistências dentro de limites razoáveis | HIGH | Flag para revisão |
| BN-P-017 | (player_id, game_id) único | Sem duplicatas | CRITICAL | Remover duplicata |

### 3.4. Regras para Tabela de Estatísticas de Equipas (team_stats)

| ID | Regra | Descrição | Severidade | Ação |
|----|-------|-----------|------------|------|
| BN-T-001 | team_id não null | Identificador de equipa obrigatório | CRITICAL | Rejeitar registro |
| BN-T-002 | game_id não null | Identificador de jogo obrigatório | CRITICAL | Rejeitar registro |
| BN-T-003 | team_id existe na tabela de equipas | Integridade referencial | CRITICAL | Rejeitar registro |
| BN-T-004 | game_id existe na tabela de jogos | Integridade referencial | CRITICAL | Rejeitar registro |
| BN-T-005 | team_id ∈ {home_team_id, away_team_id do jogo} | Equipa é home ou away | CRITICAL | Rejeitar registro |
| BN-T-006 | team_type ∈ {home, away} | Tipo de equipa válido | CRITICAL | Rejeitar registro |
| BN-T-007 | field_goals_made ≤ field_goals_attempted | Consistência lógica | CRITICAL | Rejeitar registro |
| BN-T-008 | free_throws_made ≤ free_throws_attempted | Consistência lógica | CRITICAL | Rejeitar registro |
| BN-T-009 | three_pointers_made ≤ three_pointers_attempted | Consistência lógica | CRITICAL | Rejeitar registro |
| BN-T-010 | field_goal_percentage ∈ [0.0, 1.0] | Percentagem válida | CRITICAL | Rejeitar registro |
| BN-T-011 | free_throw_percentage ∈ [0.0, 1.0] | Percentagem válida | CRITICAL | Rejeitar registro |
| BN-T-012 | total_points ≈ soma de player_pts (tolerância ±2) | Consistência com jogador | MEDIUM | Flag para revisão |
| BN-T-013 | total_rebounds ≈ soma de player_reb (tolerância ±2) | Consistência com jogador | MEDIUM | Flag para revisão |
| BN-T-014 | (team_id, game_id) único | Sem duplicatas | CRITICAL | Remover duplicata |

### 3.5. Regras para Tabela de Features (features)

| ID | Regra | Descrição | Severidade | Ação |
|----|-------|-----------|------------|------|
| BN-F-001 | feature_id não null | Identificador de feature obrigatório | CRITICAL | Rejeitar registro |
| BN-F-002 | game_id não null | Identificador de jogo obrigatório | CRITICAL | Rejeitar registro |
| BN-F-003 | computed_at não null | Timestamp de computação obrigatório | CRITICAL | Rejeitar registro |
| BN-F-004 | computed_at < game_date | Anti-leakage temporal | CRITICAL | Rejeitar registro |
| BN-F-005 | feature_value não null (para features críticas) | Features críticas obrigatórias | CRITICAL | Rejeitar registro |
| BN-F-006 | feature_name ∈ lista de features válidas | Feature conhecida | HIGH | Rejeitar registro |
| BN-F-007 | rolling_avg ∈ [min_histórico, max_histórico] | Dentro de limites históricos | MEDIUM | Flag para revisão |
| BN-F-008 | rolling_avg não varia > 50% entre períodos | Suavidade temporal | MEDIUM | Flag para revisão |
| BN-F-009 | percentagem ∈ [0.0, 1.0] | Percentagem válida | CRITICAL | Rejeitar registro |

### 3.6. Regras para Tabela de Predictions (predictions)

| ID | Regra | Descrição | Severidade | Ação |
|----|-------|-----------|------------|------|
| BN-PD-001 | prediction_id não null | Identificador de prediction obrigatório | CRITICAL | Rejeitar registro |
| BN-PD-002 | game_id não null | Identificador de jogo obrigatório | CRITICAL | Rejeitar registro |
| BN-PD-003 | model_id não null | Identificador de modelo obrigatório | CRITICAL | Rejeitar registro |
| BN-PD-004 | predicted_at não null | Timestamp de prediction obrigatório | CRITICAL | Rejeitar registro |
| BN-PD-005 | predicted_at < game_date | Anti-leakage temporal | CRITICAL | Rejeitar registro |
| BN-PD-006 | probability ∈ [0.0, 1.0] | Probabilidade válida | CRITICAL | Rejeitar registro |
| BN-PD-007 | probability ∉ (0.01, 0.99) para evitar extremos | Evitar overconfidence | HIGH | Flag para revisão |
| BN-PD-008 | spread ∈ [-30, 30] | Spread dentro de limites razoáveis | CRITICAL | Rejeitar registro |
| BN-PD-009 | total ∈ [180, 260] | Total dentro de limites razoáveis | CRITICAL | Rejeitar registro |
| BN-PD-010 | P(home) + P(away) = 1.0 ± 0.01 | Consistência home-away | CRITICAL | Rejeitar registro |
| BN-PD-011 | P(over) + P(under) = 1.0 ± 0.01 | Consistência over/under | CRITICAL | Rejeitar registro |
| BN-PD-012 | EV ∈ [-20%, +30%] | EV dentro de limites razoáveis | CRITICAL | Rejeitar registro |

### 3.7. Regras para Tabela de Apostas (bets)

| ID | Regra | Descrição | Severidade | Ação |
|----|-------|-----------|------------|------|
| BN-B-001 | bet_id não null | Identificador de aposta obrigatório | CRITICAL | Rejeitar registro |
| BN-B-002 | game_id não null | Identificador de jogo obrigatório | CRITICAL | Rejeitar registro |
| BN-B-003 | prediction_id não null | Identificador de prediction obrigatório | CRITICAL | Rejeitar registro |
| BN-B-004 | stake > 0 | Stake positivo | CRITICAL | Rejeitar registro |
| BN-B-005 | odd_taken > 1.0 | Odd mínima válida | CRITICAL | Rejeitar registro |
| BN-B-006 | placed_at não null | Timestamp de aposta obrigatório | CRITICAL | Rejeitar registro |
| BN-B-007 | placed_at < game_date | Aposta pré-jogo | CRITICAL | Rejeitar registro |
| BN-B-008 | market ∈ lista de mercados válidos | Mercado válido | CRITICAL | Rejeitar registro |
| BN-B-009 | selection ∈ lista de seleções válidas | Seleção válida | CRITICAL | Rejeitar registro |
| BN-B-010 | stake ≤ bankroll × 0.05 | Limite de stake (5% do bankroll) | HIGH | Rejeitar aposta |

---

## 4. REGRAS ESTATÍSTICAS

### 4.1. Regras de Missing Values

| ID | Regra | Descrição | Severidade | Ação |
|----|-------|-----------|------------|------|
| ES-M-001 | Missing rate < 0.1% para features críticas | Alta completude | CRITICAL | Rejeitar batch |
| ES-M-002 | Missing rate < 5% para features importantes | Completude aceitável | HIGH | Investigar |
| ES-M-003 | Missing rate < 20% para features opcionais | Completude mínima | MEDIUM | Documentar |
| ES-M-004 | Missing rate não aumentou > 50% vs semana anterior | Estabilidade de completude | MEDIUM | Investigar tendência |

### 4.2. Regras de Outliers

| ID | Regra | Descrição | Severidade | Ação |
|----|-------|-----------|------------|------|
| ES-O-001 | Outlier rate < 5% para todas as features | Taxa de outliers aceitável | HIGH | Investigar se > 10% |
| ES-O-002 | Valores > 3 desvios padrão flag para revisão | Outliers extremos | MEDIUM | Flag para revisão |
| ES-O-003 | Valores < Q1 - 1.5×IQR ou > Q3 + 1.5×IQR são outliers leves | Definição IQR | MEDIUM | Flag para revisão |
| ES-O-004 | Valores < Q1 - 3×IQR ou > Q3 + 3×IQR são outliers extremos | Definição IQR extremo | HIGH | Investigar |

### 4.3. Regras de Distribuição

| ID | Regra | Descrição | Severidade | Ação |
|----|-------|-----------|------------|------|
| ES-D-001 | PSI < 0.1 para features críticas | Sem drift significativo | HIGH | Alertar se > 0.25 |
| ES-D-002 | KS test p-value > 0.05 para features críticas | Distribuição estável | HIGH | Alertar se < 0.01 |
| ES-D-003 | Skewness ∈ [-1, 1] para rolling averages | Distribuição aproximadamente normal | MEDIUM | Flag para revisão |
| ES-D-004 | Kurtosis ∈ [-2, 2] para rolling averages | Distribuição sem caudas pesadas | MEDIUM | Flag para revisão |
| ES-D-005 | Variação de média < 10% entre meses | Estabilidade intra-temporada | MEDIUM | Alertar se > 20% |

### 4.4. Regras de Calibração

| ID | Regra | Descrição | Severidade | Ação |
|----|-------|-----------|------------|------|
| ES-C-001 | Brier Score < 0.25 | Calibração aceitável | HIGH | Recalibrar se > 0.3 |
| ES-C-002 | ECE < 0.05 | Erro de calibração baixo | HIGH | Recalibrar se > 0.1 |
| ES-C-003 | Log Loss < 0.6 | Qualidade de probabilidade | HIGH | Re-treinar se > 0.7 |
| ES-C-004 | Diferença P vs win rate < 5% por bin | Calibração por bin | MEDIUM | Ajustar se > 10% |
| ES-C-005 | Brier Score aumentou < 20% vs baseline | Estabilidade de calibração | HIGH | Alertar se > 20% |

### 4.5. Regras de Performance

| ID | Regra | Descrição | Severidade | Ação |
|----|-------|-----------|------------|------|
| ES-P-001 | Accuracy moneyline > 55% | Performance mínima moneyline | HIGH | Re-treinar se < 50% |
| ES-P-002 | Accuracy spread > 52% | Performance mínima spread | HIGH | Re-treinar se < 48% |
| ES-P-003 | MAE spread < 5 pontos | Erro médio aceitável | HIGH | Alertar se > 7 |
| ES-P-004 | MAE totals < 7 pontos | Erro médio aceitável | HIGH | Alertar se > 10 |
| ES-P-005 | RMSE < 1.5 × MAE | Sem outliers excessivos | MEDIUM | Investigar se > 2× |
| ES-P-006 | R² > 0.1 | Explicabilidade mínima | MEDIUM | Alertar se < 0.05 |
| ES-P-007 | Accuracy não caiu > 10% vs baseline | Estabilidade de performance | HIGH | Re-treinar se > 10% |

### 4.6. Regras de Consistência

| ID | Regra | Descrição | Severidade | Ação |
|----|-------|-----------|------------|------|
| ES-CS-001 | team_total_pts ≈ soma de player_pts (±2) | Consistência equipa-jogador | MEDIUM | Flag para revisão |
| ES-CS-002 | team_fg_pct ≈ team_fg_made / team_fg_attempted (±0.01) | Consistência de cálculo | MEDIUM | Flag para revisão |
| ES-CS-003 | spread prediction ≈ conversão(P(vitória)) (±10%) | Consistência spread-prob | MEDIUM | Flag para revisão |
| ES-CS-004 | total prediction ≈ home_pts + away_pts (±5) | Consistência total-components | MEDIUM | Flag para revisão |
| ES-CS-005 | EV calculado ≈ EV prediction (±1%) | Consistência de EV | HIGH | Alertar se > 5% |

---

## 5. IMPLEMENTAÇÃO DAS REGRAS

### 5.1. Framework de Validação

**Opção 1: Great Expectations**
- Framework open-source para validação de dados
- Suporta suites de expectativas
- Integração com pipelines (Prefect, Airflow)
- Dashboard automático de validação

**Opção 2: Validação Customizada**
- Implementação própria com Pandas/SQL
- Maior flexibilidade
- Requer mais manutenção
- Dashboard customizado necessário

**Recomendação:**
- Começar com Great Expectations para regras padrão
- Implementar validação customizada para regras específicas de domínio
- Combinação de ambos para máxima cobertura

### 5.2. Estrutura de Suites de Validação

**Suite de Dados Brutos:**
- Inclui todas as regras BN-*
- Executada após ingestão de dados
- Falha CRITICAL para pipeline

**Suite de Features:**
- Inclui regras BN-F-* e ES-* para features
- Executada após feature engineering
- Falha CRITICAL para features críticas

**Suite de Predictions:**
- Inclui regras BN-PD-* e ES-* para predictions
- Executada após inferência
- Falha CRITICAL para predictions inválidas

**Suite de Apostas:**
- Inclui regras BN-B-*
- Executada antes de colocar aposta
- Falha CRITICAL bloqueia aposta

### 5.3. Configuração de Thresholds

**Thresholds globais:**
- Taxa de sucesso mínima: 95%
- Taxa de erro máxima: 5%
- Latência máxima de validação: 30 segundos por batch

**Thresholds por tabela:**
- games: 99% sucesso
- odds: 98% sucesso
- player_stats: 97% sucesso
- team_stats: 97% sucesso
- features: 95% sucesso
- predictions: 99% sucesso

**Thresholds dinâmicos:**
- Ajustados automaticamente com base em histórico
- Usam rolling window de 7 dias
- Alertam se threshold violado 3 vezes consecutivas

---

## 6. MANUTENÇÃO DAS REGRAS

### 6.1. Revisão Periódica

**Frequência:**
- Revisão mensal de todas as regras
- Revisão quinzenal de regras críticas
- Revisão ad-hoc quando mudanças no domínio

**Processo de revisão:**
1. Analisar taxas de violação de cada regra
2. Identificar regras com alta taxa de falsos positivos
3. Ajustar thresholds ou remover regras obsoletas
4. Adicionar novas regras para problemas recorrentes
5. Documentar todas as alterações

### 6.2. Versionamento de Regras

**Controlo de versões:**
- Cada regra tem versão (ex: BN-G-001 v1.2)
- Alterações documentadas com motivo
- Histórico completo mantido
- Rollback possível se necessário

**Ambientes:**
- Dev: Regras relaxadas para desenvolvimento
- Staging: Regras iguais a produção
- Produção: Regras estritas aplicadas

### 6.3. Documentação de Regras

**Metadados obrigatórios:**
- ID único
- Descrição clara
- Justificativa de negócio
- Severidade
- Ação recomendada
- Data de criação
- Autor
- Histórico de alterações

**Documentação acessível:**
- Catálogo de regras no dashboard
- Documentação técnica detalhada
- Exemplos de violações
- Guias de resolução

---

## 7. REFERÊNCIAS CRUZADAS

- [[31_Data_Validation/INDEX]] ← Secção mãe
- [[VAL-001_VALIDACAO_DADOS_BRUTOS]] → Regras para dados brutos
- [[VAL-002_VALIDACAO_FEATURES]] → Regras para features
- [[VAL-003_VALIDACAO_PREDICTIONS]] → Regras para predictions
- [[04_Data_Engineering/INDEX]] → Pipeline que aplica regras

---

## 8. HISTÓRICO DE ALTERAÇÕES

| Data | Versão | Alteração | Autor |
|------|--------|-----------|-------|
| 2024-XX-XX | 1.0 | Criação inicial do documento | Data Engineer |