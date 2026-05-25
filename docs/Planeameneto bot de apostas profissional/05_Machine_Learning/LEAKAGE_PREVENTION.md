# LEAKAGE_PREVENTION — Prevenção de Look-Ahead Bias

**ID:** `ML-004` | **Fase:** #phase/1-2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar um sistema sistemático de prevenção de leakage (look-ahead bias) no pipeline de machine learning. Leakage ocorre quando informações do futuro são inadvertidamente incluídas no treino do modelo, causando performance inflada em backtest que não se traduz em performance real. O objetivo é garantir que todas as features usadas no treino são estritamente pré-jogo, ou seja, conhecidas antes do início de cada jogo. Prevenção de leakage é crítica porque leakage pode fazer modelos parecerem lucrativos em backtest quando na realidade não têm edge real.

---

## 2. DEFINIÇÃO DE LEAKAGE

Leakage é o uso de informações que não estariam disponíveis no momento da predição. Em contexto de apostas NBA, leakage ocorre quando o modelo usa dados que só seriam conhecidos após o início do jogo ou após o seu término.

**Exemplo de Leakage:**
- Usar o resultado final do jogo como feature para prever o resultado do jogo (trivial)
- Usar estatísticas do jogo em tempo real (pontos no 1º quarto) para prever resultado final
- Usar odds de fechamento (closing odds) como feature para prever resultado
- Usar notícias de lesões que só foram anunciadas após o início do jogo

**Exemplo Sem Leakage:**
- Usar estatísticas da equipe nas últimas 10 temporadas
- Usar histórico de head-to-head entre equipes
- Usar odds de abertura (opening odds) que são conhecidas antes do jogo
- Usar notícias de lesões anunciadas antes do jogo

---

## 3. TIPOS DE LEAKAGE

### 3.1 Target Leakage

**Definição:** Usar estatísticas do próprio jogo como features para prever o target do mesmo jogo.

**Exemplo:** Usar pontos marcados no jogo como feature para preder quem ganha o jogo.

**Problema:** O modelo aprende que mais pontos = vitória, o que é trivial e não generaliza.

**Como Evitar:**
- Usar apenas dados pré-jogo (estatísticas históricas, não do jogo atual)
- Validar que todas as features são agregadas sobre jogos anteriores
- Nunca usar box score do jogo atual como feature

### 3.2 Temporal Leakage

**Definição:** Embaralhar dados temporais, permitindo que o modelo aprenda com dados do futuro.

**Exemplo:** Misturar jogos de 2024 na treino e jogos de 2023 na validação.

**Problema:** O modelo pode aprender padrões temporais que não existiam no momento da predição.

**Como Evitar:**
- Ordenar dados estritamente por data
- Usar walk-forward cross-validation (não random cross-validation)
- Aplicar embargo entre treino e validação (ex: 7 dias de gap)
- Nunca embaralhar dados temporais

### 3.3 Look-Ahead em Features

**Definição:** Usar dados que ainda não estariam disponíveis no momento da predição.

**Exemplo:** Usar notícias de lesões anunciadas 1 hora antes do jogo, mas o modelo é treinado como se as notícias fossem conhecidas 24 horas antes.

**Problema:** O modelo assume acesso a informações que não teria em produção.

**Como Evitar:**
- Validar timestamp de conhecimento de cada feature (`known_at_timestamp`)
- Garantir que `known_at_timestamp <= game_date` para todas as features
- Documentar quando cada feature se torna disponível
- Implementar audit automático de timestamps

### 3.4 Selection Bias

**Definição:** Filtrar dados de forma que apenas jogos "fáceis" ou específicos sejam incluídos no treino.

**Exemplo:** Incluir apenas jogos onde a diferença de skill é grande, ignorando jogos equilibrados.

**Problema:** O modelo não generaliza para todos os jogos em produção, apenas para um subconjunto específico.

**Como Evitar:**
- Incluir TODOS os jogos disponíveis no período de treino
- Não filtrar por qualidade de sinal ou edge
- Documentar qualquer exclusão e justificar
- Validar que distribuição de dados em treino corresponde à distribuição em produção

### 3.5 Survivorship Bias

**Definição:** Ignorar jogos cancelados, adiados ou que não foram completados.

**Exemplo:** Remover jogos cancelados do dataset de treino.

**Problema:** O modelo assume que todos os jogos ocorrem, o que não é verdade em produção.

**Como Evitar:**
- Incluir jogos cancelados no dataset (com flag indicando cancelamento)
- Documentar taxa de cancelamento no período de treino
- Validar que modelo lida corretamente com jogos cancelados em produção
- Considerar impacto de cancelamentos na estratégia de execução

---

## 4. AUDIT AUTOMATIZADO

### 4.1 Função de Audit de Leakage

```python
def audit_leakage(df_features, game_date_col='game_date'):
    """
    Verifica que nenhuma feature tem data de conhecimento > game_date.
    
    Args:
        df_features: DataFrame com features e timestamps
        game_date_col: Nome da coluna com data do jogo
    
    Returns:
        True se não houver leakage, levanta ValueError se houver
    
    Raises:
        ValueError: Se leakage for detetado em qualquer feature
    """
    violations = []
    
    for col in df_features.columns:
        # Pular colunas de timestamp
        if col.endswith('_known_at') or col.endswith('_timestamp'):
            continue
        
        # Se a feature tiver um timestamp associado, validar
        known_at_col = f"{col}_known_at"
        if known_at_col in df_features.columns:
            mask = df_features[known_at_col] > df_features[game_date_col]
            if mask.any():
                violations.append({
                    'feature': col,
                    'n_violations': mask.sum(),
                    'max_lead_hours': (df_features.loc[mask, known_at_col] - 
                                       df_features.loc[mask, game_date_col]).dt.total_seconds().max() / 3600
                })
    
    if violations:
        violation_summary = "\n".join([
            f"- {v['feature']}: {v['n_violations']} violações, max lead: {v['max_lead_hours']:.2f}h"
            for v in violations
        ])
        raise ValueError(f"LEAKAGE DETECTADO em {len(violations)} features!\n{violation_summary}")
    
    return True
```

### 4.2 Validação de Features Individuais

Para cada nova feature, validar:

**Timestamp de Conhecimento:**
- Quando esta feature se torna disponível?
- O timestamp está corretamente documentado?
- O timestamp é anterior ao game_date para todas as observações?

**Fonte de Dados:**
- De onde vem esta feature?
- A fonte é confiável?
- A fonte está disponível em produção?

**Relevância Temporal:**
- Esta feature era conhecida antes do jogo em todos os casos?
- Há casos onde a feature só se torna disponível após o início do jogo?

### 4.3 Integração com CI/CD

Implementar audit de leakage como parte do pipeline de CI/CD:

1. **Pré-Treino:** Executar audit de leakage no dataset de treino
2. **Pré-Validação:** Executar audit no dataset de validação
3. **Pré-Produção:** Executar audit no dataset de produção
4. **Contínuo:** Executar audit em novos dados diariamente

Se leakage for detetado, o pipeline deve falhar e notificar a equipa.

---

## 5. CHECKLIST PRÉ-TREINO

Antes de treinar qualquer modelo, verificar:

**Disponibilidade Temporal:**
- [ ] Todas as features são conhecidas antes do início do jogo?
- [ ] Nenhuma feature usa box score do próprio jogo?
- [ ] Timestamps de conhecimento estão documentados para todas as features?

**Ordenação Temporal:**
- [ ] Dados estão ordenados cronologicamente?
- [ ] Não há embaralhamento de dados temporais?
- [ ] Embargo entre treino e validação está aplicado?

**Seleção de Dados:**
- [ ] Todos os jogos disponíveis estão incluídos (sem filtrar)?
- [ ] Jogos cancelados estão incluídos (com flag)?
- [ ] Não há seleção baseada em qualidade de sinal ou edge?

**Target:**
- [ ] O target é determinado APÓS o jogo (resultado final)?
- [ ] O target não é usado como feature?
- [ ] O target não está disponível antes do jogo?

---

## 6. DOCUMENTAÇÃO DE FEATURES

Para cada feature no modelo, documentar:

**Nome da Feature:** Nome único e descritivo

**Descrição:** O que a feature representa

**Timestamp de Conhecimento:** Quando esta feature se torna disponível (ex: "24h antes do jogo", "ao momento do tip-off")

**Fonte de Dados:** De onde vem a feature (ex: "NBA API", "Estatísticas históricas")

**Risco de Leakage:** Avaliação de risco (baixo/médio/alto)

**Validação:** Como validar que não há leakage (ex: "verificar que known_at <= game_date")

**Exemplo:**
```
Feature: home_team_win_pct_last_10
Descrição: Percentagem de vitórias da equipe visitante nos últimos 10 jogos
Timestamp de Conhecimento: 24h antes do jogo
Fonte: NBA API (estatísticas históricas)
Risco de Leakage: Baixo
Validação: Verificar que data das estatísticas <= game_date - 24h
```

---

## 7. MONITORIZAÇÃO CONTÍNUA

### 7.1 Monitorização em Produção

Monitorizar continuamente por sinais de leakage em produção:

- Verificar que timestamps de features estão corretos
- Validar que novas features não introduzem leakage
- Alertar se timestamps inconsistentes são detetados

### 7.2 Revisão Periódica

Revisar periodicamente (mensalmente/trimestralmente):

- Todas as features estão ainda livres de leakage?
- Há novas fontes de dados que introduzem risco?
- A documentação está atualizada?
- O audit de leakage está a funcionar corretamente?

---

## 8. BACKLOG TÉCNICO

- [ ] Implementar audit leakage como parte do CI/CD
- [ ] Criar testes unitários para cada feature individual
- [ ] Documentar decision log quando novas features são adicionadas
- [ ] Criar dashboard de monitorização de timestamps
- [ ] Implementar alertas automáticos quando leakage é detetado
- [ ] Criar sistema de versionamento de features com timestamps
- [ ] Implementar validação de features em produção

---

## 9. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]] ← Secção mãe
- [[06_Backtesting/LEAKAGE_TEMPORAL]] → Detalhes de prevenção temporal
- [[04_Data_Engineering/VALIDACAO_DADOS]] → Validação de dados
- [[06_Backtesting/WALK_FORWARD_CV]] → Cross-validation temporal
