# EXP-004 — Arbitrage Detection

**ID:** `EXP-004` | **Fase:** #phase/9-12 | **Owner:** Product Manager / Strategy Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar sistema de deteção de arbitragem (surebets) entre múltiplas casas de apostas, identificando oportunidades de lucro garantido através da discrepância de odds entre diferentes bookmakers.

---

## 2. CONTEXTO

Arbitragem em apostas desportivas consiste em apostar em todos os resultados possíveis de um evento em diferentes casas de apostas, garantindo lucro independentemente do resultado.

**Características da Arbitragem:**
- **Lucro garantido**: Não depende do resultado do evento
- **Margem tipicamente pequena**: 0.5% - 3% por aposta
- **Curta duração**: Oportunidades duram segundos a minutos
- **Alta frequência**: Requer monitorização contínua
- **Risco de limitação**: Casas podem limitar ou banir contas

**Por que considerar arbitragem:**
- Fluxo de caixa previsível
- Menor variância que value betting tradicional
- Pode complementar estratégias de value betting
- Útil para gerir bankroll durante períodos de drawdown

**Por que NÃO ser o foco principal:**
- Margens pequenas requerem volume alto
- Requer capital em múltiplas casas
- Alto risco de limitação de contas
- Complexidade operacional significativa
- Menor potencial de escala que value betting

---

## 3. MECÂNICA DE ARBITRAGEM

### 3.1 Conceito Básico

Para um evento com 2 resultados (ex: Moneyline NBA):
```
Odds Casa A: Equipa A @ 2.10
Odds Casa B: Equipa B @ 1.95

Arbitragem existe se: (1/2.10) + (1/1.95) < 1
Cálculo: 0.476 + 0.513 = 0.989 < 1 ✓

Lucro garantido: (1 - 0.989) = 1.1%
```

### 3.2 Tipos de Arbitragem

**Arbitragem Simples (2-way):**
- Moneyline em desportos com 2 resultados
- Ex: NBA, MLB, NHL, Ténis

**Arbitragem 3-way:**
- Desportos com empate possível
- Ex: Futebol (1X2), NHL (com empate na regulação)

**Arbitragem Multi-casa:**
- Requer 3+ casas para cobrir todos os resultados
- Ex: Futebol com over/under

**Arbitragem Cross-Market:**
- Combina diferentes mercados do mesmo evento
- Ex: Moneyline + Handicap para criar arbitragem

**Arbitragem de Live Betting:**
- Oportunidades durante o evento
- Mais voláteis, margens maiores
- Requer execução extremamente rápida

### 3.3 Cálculo de Stake Distribution

Para distribuir stakes corretamente:
```
Stake Resultado A = (Probabilidade Implícita A / Soma) * Bankroll
Stake Resultado B = (Probabilidade Implícita B / Soma) * Bankroll

Onde Probabilidade Implícita = 1 / Odds
```

---

## 4. ARQUITETURA DO SISTEMA

### 4.1 Componentes Principais

**Data Collection Layer:**
- Scraping/API de múltiplas casas de apostas
- Normalização de odds (decimal, american, fractional)
- Deduplicação de eventos
- Sincronização temporal (timestamps)

**Processing Layer:**
- Matching de eventos entre casas
- Cálculo de probabilidades implícitas
- Deteção de arbitragem em tempo real
- Cálculo de stake distribution
- Filtragem de oportunidades (margem mínima)

**Execution Layer:**
- Priorização de oportunidades
- Execução simultânea em múltiplas casas
- Verificação de execução bem-sucedida
- Handling de erros e odds changes

**Risk Management Layer:**
- Monitorização de limites de apostas
- Gestão de bankroll por casa
- Detecção de odds stale
- Proteção contra erros de cálculo

### 4.2 Fluxo de Dados

```
1. Coleta de odds de todas as casas (freq: 1-5 seg)
2. Normalização e matching de eventos
3. Cálculo de probabilidades implícitas
4. Deteção de arbitragem (margem > threshold)
5. Validação de oportunidade (liquidez, limites)
6. Cálculo de stake distribution
7. Execução simultânea em todas as casas
8. Verificação e confirmação
9. Logging e monitorização
```

### 4.3 Requisitos de Latência

- **Coleta de odds**: < 1 segundo
- **Processamento**: < 500ms
- **Detecção**: < 200ms
- **Execução**: < 2 segundos total
- **Latência total**: < 5 segundos ideal

---

## 5. REQUISITOS DE DADOS

### 5.1 Casas de Apostas Necessárias

**Casas Principais (liquidez alta):**
- Betfair (Exchange)
- Pinnacle
- Bet365
- William Hill
- Unibet

**Casas Secundárias (edge hunting):**
- 888Sport
- Betway
- Ladbrokes
- Coral
- Bwin

*Nota: Mínimo de 5-7 casas para oportunidades frequentes*

### 5.2 Dados Necessários

- **Odds em tempo real**: Todas as casas, freq: 1-5 seg
- **Limites de apostas**: Por casa, por evento
- **Eventos matching**: Identificador único por evento
- **Timestamps**: Precisão de milissegundos
- **Liquidez**: Volume disponível em cada odd

### 5.3 Fontes de Dados

- **Betfair API**: Exchange data, streaming
- **Pinnacle API**: Odds e limites
- **Scraping**: Para casas sem API (último recurso)
- **Aggregators**: OddsPortal, Flash Odds (verificar TOS)

---

## 6. ALGORITMOS DE DETEÇÃO

### 6.1 Algoritmo Básico

```python
def detect_arbitrage(event_odds):
    """
    event_odds: dict {outcome: {bookmaker: odds}}
    """
    best_odds = {}
    for outcome in event_odds:
        best_odds[outcome] = max(event_odds[outcome].values())

    total_implied = sum(1/odds for odds in best_odds.values())

    if total_implied < 1:
        arbitrage_margin = (1 - total_implied) * 100
        return {
            'margin': arbitrage_margin,
            'best_combination': best_odds,
            'stake_distribution': calculate_stakes(best_odds)
        }
    return None
```

### 6.2 Algoritmo Otimizado (Multi-Casa)

Para maximizar margem:
```python
def find_optimal_arbitrage(event_odds):
    """
    Encontra combinação ótima de casas para maximizar margem
    Considerando limites de apostas e liquidez
    """
    best_combinations = []
    for combination in generate_combinations(event_odds):
        margin = calculate_margin(combination)
        if margin > threshold:
            stake_dist = calculate_stakes(combination, limits)
            if validate_execution(stake_dist):
                best_combinations.append({
                    'margin': margin,
                    'combination': combination,
                    'stakes': stake_dist
                })

    return sorted(best_combinations, key=lambda x: x['margin'], reverse=True)[0]
```

### 6.3 Filtragem de Oportunidades

**Filtros de Qualidade:**
- Margem mínima: 0.5% - 1% (ajustável)
- Liquidez total: > $100 (para evitar limites baixos)
- Tempo até início: > 5 minutos (evitar eventos iminentes)
- Número de casas: ≥ 2 (preferencialmente ≥ 3)
- Odds variance: Não aceitar outliers extremos (possível erro)

**Filtros de Risco:**
- Evitar odds stale (verificar se odds mudaram recentemente)
- Verificar limites de apostas por casa
- Verificar regras específicas (ex: overtime rules)
- Evitar eventos com alta probabilidade de cancelamento

---

## 7. GESTÃO DE RISCOS

### 7.1 Riscos Operacionais

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Odds change durante execução | Alta | Médio | Execução simultânea, timeout curto |
| Evento cancelado | Baixa | Alto | Verificar regras, evitar eventos arriscados |
| Erro de matching | Média | Alto | Validação cruzada, manual review |
| Falha de API | Média | Médio | Múltiplas fontes, retry logic |
| Stake rejeitada | Média | Médio | Verificar limites antes, stake adjustment |

### 7.2 Riscos de Conta

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Limitação de conta | Muito Alta | Alto | Stake sizing conservador, rotação de contas |
| Banimento de conta | Alta | Muito Alto | Comportamento "normal", evitar padrões |
| KYC/Verificação | Média | Médio | Manter documentação atualizada |
| Fechamento de contas | Média | Alto | Diversificar casas, não concentrar |

### 7.3 Estratégias de Mitigação

**Stake Sizing:**
- Limitar stakes a % pequena do bankroll por casa
- Ajustar stakes baseado em limites da casa
- Evitar apostas máximas frequentes

**Comportamento:**
- Misturar arbitragem com apostas "normais"
- Evitar padrões óbvios (sempre apostar em arbitragens)
- Diversificar tipos de apostas
- Apostar ocasionalmente em eventos sem valor

**Gestão de Contas:**
- Múltiplas contas por casa (se permitido)
- Rotação de contas
- Manter perfil de apostador "recreativo"

---

## 8. IMPLEMENTAÇÃO

### 8.1 Fase 1: MVP (2-3 meses)

- Integração com 3-5 casas principais
- Sistema de coleta de odds em tempo real
- Algoritmo básico de deteção
- Execução manual inicial
- Documentação de oportunidades

### 8.2 Fase 2: Automatização (2-3 meses)

- Execução automática
- Sistema de matching de eventos robusto
- Filtros de qualidade implementados
- Monitorização de performance
- Gestão de bankroll por casa

### 8.3 Fase 3: Otimização (contínuo)

- Adicionar mais casas
- Algoritmos avançados de otimização
- Live betting arbitrage
- Cross-market arbitrage
- Machine learning para previsão de oportunidades

---

## 9. MÉTRICAS E MONITORIZAÇÃO

### 9.1 Métricas Chave

- **Oportunidades/dia**: Número de arbitragens detetadas
- **Oportunidades executadas**: % de oportunidades executadas com sucesso
- **Margem média**: Lucro médio por arbitragem
- **Volume total**: Valor total apostado
- **Lucro total**: Lucro acumulado
- **ROI**: Return on investment
- **Taxa de sucesso**: % de arbitragens lucrativas (deveria ser ~100%)

### 9.2 Monitorização

- **Alertas**: Oportunidades acima de threshold
- **Dashboards**: Visualização de oportunidades em tempo real
- **Logging**: Detalhes de cada oportunidade e execução
- **Performance tracking**: Por casa, por desporto, por período

---

## 10. CUSTOS E INVESTIMENTO

### 10.1 Custos Iniciais

- **Capital**: Mínimo $5K-$10K distribuído por 5-7 casas
- **Infraestrutura**: Servidor para scraping/processing
- **Desenvolvimento**: 2-3 meses de desenvolvimento
- **API subscriptions**: Casas que cobram por acesso

### 10.2 Custos Recorrentes

- **Infraestrutura**: $50-$200/mês (servidor, bandwidth)
- **API subscriptions**: $100-$500/mês
- **Manutenção**: Tempo contínuo para updates e debugging

### 10.3 Retorno Esperado

- **Margem por aposta**: 0.5% - 3%
- **Oportunidades/dia**: 5-20 (dependendo do número de casas)
- **Volume/dia**: $500-$2,000
- **Lucro/dia**: $5-$60
- **Lucro/mês**: $150-$1,800

*Nota: Retornos são conservadores e dependem de número de casas e capital*

---

## 11. DEPENDÊNCIAS

- **Contas em múltiplas casas**: Mínimo 5-7 casas
- **Capital**: Bankroll distribuído por casas
- **API access**: Acesso programático às casas
- **Infraestrutura**: Servidor com capacidade de scraping
- **Desenvolvimento**: Tempo para implementação
- **Conhecimento legal**: Verificar legalidade na jurisdição

---

## 12. CRITÉRIOS DE SUCESSO

- [ ] Sistema deteta ≥ 10 oportunidades/dia
- [ ] Margem média ≥ 1%
- [ ] Taxa de execução bem-sucedida ≥ 90%
- [ ] ROI positivo consistente
- [ ] Sem limitações de contas após 3 meses
- [ ] Sistema automatizado em produção
- [ ] Monitorização ativa implementada
- [ ] Documentação completa

---

## 13. BACKLOG

- [ ] Pesquisar e selecionar 5-7 casas de apostas
- [ ] Abrir contas e verificar limites
- [ ] Identificar APIs disponíveis por casa
- [ ] Desenvolver scraper para casas sem API
- [ ] Implementar sistema de coleta de odds
- [ ] Desenvolver algoritmo de matching de eventos
- [ ] Implementar deteção de arbitragem básica
- [ ] Desenvolver cálculo de stake distribution
- [ ] Implementar filtros de qualidade
- [ ] Testar manualmente por 2 semanas
- [ ] Automatizar execução
- [ ] Implementar sistema de gestão de risco
- [ ] Monitorizar limitações de contas
- [ ] Documentar aprendizados e best practices

---

## 14. LINKS CRUZADOS

- [[41_Future_Expansion/INDEX]] ← Secção mãe
- [[14_APIs/INDEX]] → Integrações com APIs de casas
- [[09_Execution_System/INDEX]] → Sistema de execução
- [[08_Risk_Management/INDEX]] → Gestão de risco
- [[10_Monitoring/INDEX]] → Monitorização do sistema