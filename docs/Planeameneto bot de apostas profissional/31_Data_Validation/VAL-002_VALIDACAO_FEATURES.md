# VAL-002 — Validação de Features

**ID:** `VAL-002` | **Fase:** #phase/5 | **Owner:** Data Engineer | **Status:** #status/in_progress

---

## 1. OBJETIVO

Definir estratégias e procedimentos para validar a qualidade e integridade das features geradas pelo pipeline de feature engineering. Features são a entrada dos modelos de ML, e a sua qualidade impacta diretamente a precisão das predictions e a rentabilidade do sistema de betting.

---

## 2. CONTEXTO

As features são derivadas dos dados brutos através de transformações estatísticas e computações complexas. Erros no feature engineering podem introduzir:
- **Data leakage**: Features que contêm informação do futuro
- **Missing values**: Features obrigatórias com valores nulos
- **Outliers**: Valores extremos que distorcem o modelo
- **Distribuições anormais**: Features com distribuições inconsistentes ao longo do tempo

A validação de features deve ocorrer após o feature engineering e antes do treino/inferência dos modelos.

---

## 3. ESCOPO

Este documento abrange a validação de:
- **Features de rolling averages**: Médias móveis de estatísticas
- **Features de momentum**: Tendências de desempenho recente
- **Features de matchup**: Comparação entre equipas/jogadores
- **Features de contexto**: Fatores externos (dias de descanso, viagem, etc.)
- **Features de eficiência**: Métricas avançadas (offensive rating, defensive rating)

---

## 4. VALIDAÇÃO DE MISSING VALUES

### 4.1. Classificação de Features por Obrigatoriedade

**Features Críticas (não podem ser null):**
- team_id, player_id, game_id (chaves primárias)
- game_date (temporal)
- team_rolling_avg_pts_last_5 (features principais de rolling)
- player_rolling_avg_pts_last_5 (features principais de rolling)
- home_team_id, away_team_id (identificação de matchup)

**Features Importantes (podem ser null com justificativa):**
- team_rolling_avg_pts_last_10 (para jogos recentes na temporada)
- player_rest_days (para rookies ou jogadores novos)
- team_travel_distance (quando geolocalização indisponível)

**Features Opcionais (null aceitável):**
- advanced_metrics (quando dados insuficientes)
- situational_stats (para situações raras)

### 4.2. Regras de Missing Values

**Para features críticas:**
1. Missing rate deve ser < 0.1%
2. Se missing > 0.1%, rejeitar batch inteiro
3. Investigar causa raiz imediatamente

**Para features importantes:**
1. Missing rate deve ser < 5%
2. Se missing > 5%, logar warning e investigar
3. Implementar imputação se missing > 1%

**Para features opcionais:**
1. Missing rate pode ser até 20%
2. Documentar justificativa para missing
3. Considerar remoção se missing > 30%

### 4.3. Estratégias de Imputação

**Imputação por média/mediana:**
- Aplicável para features numéricas com distribuição normal
- Usar média se outlier rate < 5%
- Usar mediana se outlier rate ≥ 5%

**Imputação por valor fixo:**
- Para features categóricas: usar categoria "unknown"
- Para flags binárias: usar valor 0 (false)
- Para contadores: usar valor 0

**Imputação por regressão:**
- Para features com correlação forte (> 0.7) com outras features
- Usar modelo simples de regressão linear
- Documentar features usadas na imputação

**Imputação por forward fill:**
- Para time series (rolling averages)
- Usar último valor válido conhecido
- Limitar a 3 períodos consecutivos

---

## 5. VALIDAÇÃO DE OUTLIERS

### 5.1. Definição de Outliers

**Método IQR (Interquartile Range):**
- Outlier leve: valor < Q1 - 1.5×IQR ou valor > Q3 + 1.5×IQR
- Outlier extremo: valor < Q1 - 3×IQR ou valor > Q3 + 3×IQR

**Método Z-Score:**
- Outlier leve: |z-score| > 2
- Outlier extremo: |z-score| > 3

**Método de domínio:**
- Baseado em conhecimento do domínio (ex: pontos não podem ser negativos)

### 5.2. Regras por Tipo de Feature

**Features de pontuação (pts, reb, ast):**
- Bounds: [0, 100] para jogadores, [0, 200] para equipas
- Outlier extremo se > 3 desvios padrão da média
- Investigar se outlier é erro ou performance legítima

**Features de percentagem (fg_pct, ft_pct, etc.):**
- Bounds: [0.0, 1.0]
- Outlier se < 0.2 ou > 0.8 para médias de temporada
- Investigar se outlier é erro ou performance extrema

**Features de rolling averages:**
- Deve estar entre min e max histórico da feature
- Não pode variar > 50% entre períodos consecutivos
- Outlier se variação > 3 desvios padrão da variação média

**Features de eficiência (offensive rating, defensive rating):**
- Bounds: [80, 140] para equipas NBA
- Outlier se < 90 ou > 130
- Investigar contexto (jogo atípico, overtime)

### 5.3. Tratamento de Outliers

**Verificação manual:**
- Para outliers extremos em features críticas
- Investigar registro original nos dados brutos
- Confirmar se é erro ou valor legítimo

**Winsorização:**
- Para outliers leves em features importantes
- Capar em 1º ou 99º percentil
- Documentar percentis usados

**Remoção:**
- Para outliers confirmados como erros
- Remover registro ou feature
- Logar motivo da remoção

**Flagging:**
- Para outliers legítimos mas extremos
- Adicionar flag feature_is_outlier
- Permitir processamento com alerta

---

## 6. VALIDAÇÃO DE DISTRIBUIÇÕES

### 6.1. Detecção de Drift de Distribuição

**KS Test (Kolmogorov-Smirnov):**
- Comparar distribuição atual vs distribuição histórica
- p-value < 0.05 indica drift significativo
- Alertar se drift detectado em features críticas

**Population Stability Index (PSI):**
- PSI < 0.1: sem drift
- PSI 0.1-0.25: drift leve
- PSI > 0.25: drift significativo
- Recalcular modelo se PSI > 0.25 em features importantes

### 6.2. Validação de Distribuição por Feature

**Features de rolling averages:**
- Distribuição deve ser aproximadamente normal
- Skewness deve estar entre -1 e 1
- Kurtosis deve estar entre -2 e 2

**Features de percentagem:**
- Distribuição deve ser centrada em torno da média histórica
- Não deve ter bimodalidade (indica subpopulações)

**Features de contexto (rest days, travel):**
- Distribuição deve refletir calendário da NBA
- Deve ter padrões sazonais esperados

### 6.3. Validação de Consistência Temporal

**Consistência intra-temporada:**
- Distribuição deve ser estável dentro da mesma temporada
- Variação de média < 10% entre meses
- Alertar se variação > 20%

**Consistência inter-temporadas:**
- Média pode variar entre temporadas (evolução do jogo)
- Mas distribuição geral deve manter forma similar
- Investigar mudanças drásticas de regras ou formato

**Consistência por fase da temporada:**
- Regular season vs playoffs podem ter distribuições diferentes
- Documentar diferenças esperadas
- Validar separadamente se necessário

---

## 7. VALIDAÇÃO DE DATA LEAKAGE

### 7.1. Regras Temporais

**Regra anti-leakage principal:**
- computed_at (momento da computação da feature) < game_date
- Se computed_at >= game_date, rejeitar imediatamente

**Janela de computação:**
- Features de rolling: usar apenas dados até game_date - 1 dia
- Não usar dados do próprio jogo ou jogos futuros
- Para features de pre-game: usar dados até tip-off - 1 hora

### 7.2. Validação de Causalidade

**Features dependentes de resultados:**
- Confirmar que features não usam resultados de jogos futuros
- Ex: team_win_rate deve usar apenas jogos anteriores
- Ex: player_form deve usar apenas estatísticas anteriores

**Features baseadas em odds:**
- Odds devem ser do momento anterior ao jogo
- Não usar odds de closing line em features de pre-game
- Documentar timestamp das odds usadas

### 7.3. Validação de Look-ahead Bias

**Verificação de timestamp:**
- Confirmar que todas as fontes têm timestamp < game_date
- Para dados de API: usar timestamp de ingestão
- Para dados computados: usar timestamp de computação

**Verificação de lógica:**
- Revisar código de feature engineering
- Confirmar que não há acesso a dados futuros
- Testar com dados históricos conhecidos

---

## 8. VALIDAÇÃO DE INTEGRIDADE

### 8.1. Consistência de Chaves

**Chaves primárias:**
- game_id, team_id, player_id devem ser não-null
- Devem existir nas tabelas de referência
- Devem seguir formatos definidos

**Chaves estrangeiras:**
- team_id deve existir na tabela de equipas
- player_id deve existir na tabela de jogadores
- game_id deve existir na tabela de jogos

**Unicidade:**
- (game_id, team_id) deve ser único para features de equipa
- (game_id, player_id) deve ser único para features de jogador
- Não pode haver duplicatas

### 8.2. Consistência de Valores Relacionados

**Somas e agregações:**
- team_total_pts deve aproximar soma de player_pts (tolerância ±2)
- team_fg_pct deve ser consistente com team_fg_made / team_fg_attempted
- Alertar se discrepância > 5%

**Relações entre features:**
- home_team_rolling_avg_pts + away_team_rolling_avg_pts deve aproximar totals_line
- player_usage_rate × team_possessions deve aproximar player_possessions
- Validar relações físicas/estatísticas esperadas

### 8.3. Consistência de Flags e Estados

**Flags binárias:**
- is_home_game deve ser true para home_team, false para away_team
- is_back_to_back deve ser consistente com rest_days
- is_overtime deve ser true se minutes > 48

**Estados categóricos:**
- team_conference deve ser "East" ou "West"
- player_position deve estar em ["PG", "SG", "SF", "PF", "C"]
- Valores devem ser consistentes com tabelas de referência

---

## 9. MONITORIZAÇÃO

### 9.1. Métricas de Qualidade de Features

**Taxa de Missing Values:**
- % de missing por feature
- Target: < 1% para features críticas
- Alerta se > 5%

**Taxa de Outliers:**
- % de outliers por feature
- Target: < 5%
- Alerta se > 10%

**PSI (Population Stability Index):**
- PSI por feature vs distribuição base
- Target: < 0.1
- Alerta se > 0.25

**KS Test p-value:**
- p-value por feature vs distribuição histórica
- Target: > 0.05
- Alerta se < 0.05

### 9.2. Dashboard de Features

**Componentes:**
1. Taxa de missing values por feature (heatmap)
2. Distribuição de features críticas (histogramas)
3. PSI ao longo do tempo (line charts)
4. Top 10 features com maior drift
5. Correlação entre features (matrix)

**Frequência de atualização:**
- Em tempo real: após cada batch de features
- Tendências: atualização a cada hora
- Relatórios: diários e semanais

---

## 10. REFERÊNCIAS CRUZADAS

- [[31_Data_Validation/INDEX]] ← Secção mãe
- [[05_Machine_Learning/INDEX]] → Modelos que usam estas features
- [[32_Feature_Store/INDEX]] → Armazenamento de features
- [[48_Data_Drift/INDEX]] → Monitorização de drift de dados

---

## 11. HISTÓRICO DE ALTERAÇÕES

| Data | Versão | Alteração | Autor |
|------|--------|-----------|-------|
| 2024-XX-XX | 1.0 | Criação inicial do documento | Data Engineer |