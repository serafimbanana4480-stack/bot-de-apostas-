# VAL-001 — Validação de Dados Brutos

**ID:** `VAL-001` | **Fase:** #phase/4 | **Owner:** Data Engineer | **Status:** #status/in_progress

---

## 1. OBJETIVO

Definir estratégias e procedimentos para validar a qualidade e integridade dos dados brutos obtidos das APIs externas (NBA API e Betfair API) antes de serem processados pelo pipeline ETL. A validação de dados brutos é a primeira linha de defesa contra dados corruptos que podem comprometer todo o sistema de betting.

---

## 2. CONTEXTO

Os dados brutos são o alicerce de todo o sistema de value betting. Dados corruptos ou inválidos podem levar a:
- Features incorretas
- Predictions erradas
- Apostas com valor falso
- Perdas financeiras significativas

A validação deve ocorrer imediatamente após a ingestão dos dados, antes de qualquer transformação ou processamento adicional.

---

## 3. ESCOPO

Este documento abrange a validação de dados brutos de:
- **NBA API**: Jogos, estatísticas de jogadores, estatísticas de equipas
- **Betfair API**: Odds, volumes de mercado, profundidade do mercado

---

## 4. VALIDAÇÃO NBA API

### 4.1. Validação de Jogos

**Campos obrigatórios:**
- game_id: Identificador único do jogo
- game_date: Data do jogo (não pode ser futuro para jogos passados)
- home_team_id: Identificador da equipa da casa
- away_team_id: Identificador da equipa visitante
- status: Estado do jogo (scheduled, in_progress, finished)

**Regras de negócio:**
1. home_team_id ≠ away_team_id (evitar jogos contra si mesmo)
2. game_date não pode ser anterior a 2015 (data mínima histórica)
3. game_date não pode ser superior a +7 dias a partir de hoje (para jogos agendados)
4. status deve estar no conjunto permitido: ["scheduled", "in_progress", "finished", "postponed", "cancelled"]
5. Para jogos finished: home_score e away_score devem ser não-null e ≥ 0

**Validações estatísticas:**
1. home_score deve estar entre 0 e 200 (NBA record)
2. away_score deve estar entre 0 e 200 (NBA record)
3. season deve ser um valor válido (formato: "2023-24", "2024-25")
4. game_type deve estar em ["regular", "preseason", "playoff"]

### 4.2. Validação de Estatísticas de Jogadores

**Campos obrigatórios:**
- player_id: Identificador único do jogador
- game_id: Identificador do jogo
- team_id: Identificador da equipa

**Regras de negócio:**
1. player_id deve existir na tabela de jogadores
2. game_id deve existir na tabela de jogos
3. team_id deve corresponder a home_team_id ou away_team_id do jogo
4. minutes_played deve estar entre 0 e 48 (tempo máximo NBA)
5. segundos_played deve estar entre 0 e 2880 (48 minutos × 60 segundos)

**Validações estatísticas:**
1. field_goals_made ≤ field_goals_attempted
2. free_throws_made ≤ free_throws_attempted
3. three_pointers_made ≤ three_pointers_attempted
4. field_goal_percentage ∈ [0.0, 1.0]
5. free_throw_percentage ∈ [0.0, 1.0]
6. points deve estar entre 0 e 100 (recorde individual)
7. rebounds deve estar entre 0 e 55 (recorde individual)
8. assists deve estar entre 0 e 30 (recorde individual)

**Validações de integridade:**
1. player_id deve ser consistente com team_id (jogador não pode mudar de equipa no mesmo jogo)
2. game_date da estatística deve corresponder a game_date do jogo
3. Não pode haver duplicatas (player_id + game_id deve ser único)

### 4.3. Validação de Estatísticas de Equipas

**Campos obrigatórios:**
- team_id: Identificador da equipa
- game_id: Identificador do jogo

**Regras de negócio:**
1. team_id deve existir na tabela de equipas
2. game_id deve existir na tabela de jogos
3. team_id deve corresponder a home_team_id ou away_team_id do jogo
4. team_type deve estar em ["home", "away"]

**Validações estatísticas:**
1. field_goals_made ≤ field_goals_attempted
2. free_throws_made ≤ free_throws_attempted
3. three_pointers_made ≤ three_pointers_attempted
4. field_goal_percentage ∈ [0.0, 1.0]
5. free_throw_percentage ∈ [0.0, 1.0]
6. total_points deve corresponder à soma de pontos dos jogadores da equipa (tolerância ±2)
7. total_rebounds deve corresponder à soma de rebounds dos jogadores da equipa (tolerância ±2)

---

## 5. VALIDAÇÃO BETFAIR API

### 5.1. Validação de Odds

**Campos obrigatórios:**
- market_id: Identificador único do mercado
- selection_id: Identificador da seleção
- odd: Valor da odd decimal
- timestamp: Momento da captura da odd

**Regras de negócio:**
1. odd deve ser > 1.0 (odd mínima válida)
2. odd deve ser < 1000.0 (odd máxima razoável)
3. timestamp deve ser < game_date + 2h (pré-jogo ou in-game)
4. market_id deve seguir o formato Betfair (ex: "1.12345678")
5. selection_id deve seguir o formato Betfair (ex: "12345678")

**Validações estatísticas:**
1. Para moneyline: odds home + odds away deve estar entre 1.9 e 2.3 (margem da casa)
2. Para spread: odds spread devem estar entre 1.8 e 2.1
3. Para totals: odds over/under devem estar entre 1.8 e 2.1
4. Odd não pode ter mais de 2 casas decimais (precisão)

**Validações temporais:**
1. timestamp não pode ser futuro
2. timestamp deve ser ≥ game_date - 7 dias (janela de odds)
3. Para jogos in_progress: timestamp deve ser ≤ now (não capturar odds futuras)

### 5.2. Validação de Volume de Mercado

**Campos obrigatórios:**
- market_id: Identificador do mercado
- total_matched: Volume total apostado
- timestamp: Momento da captura

**Regras de negócio:**
1. total_matched deve ser ≥ 0
2. total_matched deve ser < 10.000.000 (limite razoável para NBA)
3. timestamp deve ser < game_date + 2h

**Validações estatísticas:**
1. total_matched deve aumentar monotonamente ao longo do tempo
2. Para jogos regulares: total_matched típico entre 50.000 e 500.000
3. Para playoffs: total_matched típico entre 200.000 e 2.000.000
4. Valores extremos devem ser sinalizados (> 3 desvios padrão da média)

### 5.3. Validação de Profundidade do Mercado

**Campos obrigatórios:**
- market_id: Identificador do mercado
- selection_id: Identificador da seleção
- price: Nível de preço
- size: Volume disponível a esse preço
- side: Lado do mercado (back ou lay)

**Regras de negócio:**
1. price deve ser > 1.0
2. price deve ser < 1000.0
3. size deve ser ≥ 0
4. side deve estar em ["back", "lay"]
5. Para lay: price deve ser > price do back correspondente

**Validações de integridade:**
1. A soma de sizes a diferentes preços deve aproximar total_matched
2. O spread entre back e lay deve ser razoável (< 5% para mercados líquidos)
3. Não pode haver gaps excessivos entre níveis de preço consecutivos

---

## 6. TRATAMENTO DE FALHAS

### 6.1. Classificação de Severidade

**CRITICAL:**
- Dados que causam falha imediata do pipeline
- Exemplo: game_id null, odd ≤ 1.0
- Ação: Rejeitar batch, notificar imediatamente

**HIGH:**
- Dados que podem comprometer decisões de betting
- Exemplo: home_team_id = away_team_id, score > 200
- Ação: Rejeitar registro, logar erro, continuar com restante do batch

**MEDIUM:**
- Dados suspeitos mas potencialmente válidos
- Exemplo: volume extremamente alto, outlier estatístico
- Ação: Flag para revisão manual, permitir processamento com alerta

**LOW:**
- Dados com qualidade subótima mas não críticos
- Exemplo: timestamp ligeiramente fora da janela
- Ação: Logar warning, permitir processamento

### 6.2. Estratégias de Recuperação

**Retry:**
- Para falhas transitórias (timeout, rate limit)
- Máximo 3 tentativas com backoff exponencial
- Intervalo: 1s, 5s, 30s

**Fallback:**
- Para dados críticos indisponíveis
- Usar última versão válida conhecida
- Flag como "stale data" para downstream

**Quarantine:**
- Para dados com problemas não críticos
- Armazenar em tabela separada para análise
- Não processar no pipeline principal

---

## 7. MONITORIZAÇÃO

### 7.1. Métricas de Qualidade

**Taxa de Sucesso:**
- % de registros que passam todas as validações
- Target: > 99%
- Alerta se < 95%

**Taxa de Erros por Tipo:**
- Contagem de erros por regra de validação
- Identificar regras mais problemáticas
- Tendência ao longo do tempo

**Volume de Dados:**
- Número de registros processados por API
- Alerta se volume cair > 50% em relação à média
- Detectar falhas de ingestão

**Latência de Ingestão:**
- Tempo entre disponibilidade na API e ingestão no sistema
- Target: < 5 minutos
- Alerta se > 15 minutos

### 7.2. Dashboard de Qualidade

**Componentes:**
1. Taxa de sucesso em tempo real (última hora)
2. Top 10 erros mais frequentes (últimas 24h)
3. Volume de dados por fonte (NBA vs Betfair)
4. Latência de ingestão por API
5. Mapa de calor de falhas por hora do dia

**Frequência de atualização:**
- Métricas em tempo real: atualização a cada 5 minutos
- Tendências: atualização a cada hora
- Relatórios diários: gerados às 00:00 UTC

---

## 8. REFERÊNCIAS CRUZADAS

- [[31_Data_Validation/INDEX]] ← Secção mãe
- [[04_Data_Engineering/INDEX]] → Pipeline de ingestão de dados
- [[14_APIs/INDEX]] → Configuração das APIs externas
- [[15_Database/INDEX]] → Schema de tabelas brutas

---

## 9. HISTÓRICO DE ALTERAÇÕES

| Data | Versão | Alteração | Autor |
|------|--------|-----------|-------|
| 2024-XX-XX | 1.0 | Criação inicial do documento | Data Engineer |