# ARBITRAGEM_BOOKMAKERS — Arbitragem Entre Bookmakers

**ID:** `BK-003` | **Fase:** #phase/3-6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar estratégias e técnicas de arbitragem entre bookmakers (surebets), identificando oportunidades, riscos e implementação prática para lucro garantido sem risco de mercado.

**Princípio:** Arbitragem é lucro sem risco, mas requer execução perfeita e gestão cuidadosa de riscos operacionais.

---

## 2. CONCEITOS FUNDAMENTAIS

### 2.1 O Que é Arbitragem (Surebet)

**Definição:** Apostar em todos os resultados possíveis de um evento em diferentes casas de apostas, garantindo lucro independentemente do resultado.

**Condição Matemática:**
```
Σ (1 / odd_i) < 1

Onde:
- odd_i = odd de cada resultado possível
- Σ = soma de todos os resultados
```

**Exemplo Simples (Moneyline):**
```
Lakers vs Celtics

Betfair: Lakers 2.10, Celtics 1.80
Pinnacle: Lakers 1.95, Celtics 1.95

Arbitragem:
Back Lakers 2.10 (Betfair)
Back Celtics 1.95 (Pinnacle)

Verificação:
1/2.10 + 1/1.95 = 0.476 + 0.513 = 0.989 < 1 ✓

Lucro garantido: (1 - 0.989) * 100% = 1.1%
```

### 2.2 Tipos de Arbitragem

**Por Mercado:**

| Tipo | Descrição | Complexidade |
|------|-----------|--------------|
| **Moneyline** | 2 resultados (vencedor) | Baixa |
| **3-Way** | 3 resultados (1X2) | Média |
| **Spread** | Cobrir spread em casas diferentes | Média |
| **Totals** | Over/Under em casas diferentes | Média |
| **Cross-Market** | Moneyline vs Spread vs Totals | Alta |
| **Multi-Leg** | Combinação de múltiplos mercados | Muito Alta |

**Por Casa:**

| Tipo | Descrição | Lucro Típico |
|------|-----------|--------------|
| **Sharp vs Soft** | Sharp book vs Soft book | 2-5% |
| **Soft vs Soft** | Duas soft books | 3-8% |
| **Exchange vs Book** | Exchange vs Bookmaker | 1-3% |
| **Exchange vs Exchange** | Duas exchanges | 0.5-2% |

### 2.3 Cálculo de Stakes

**Fórmula para Maximizar Lucro:**
```
Stake_i = (Investimento Total / odd_i) / Σ (1 / odd_j)

Onde:
- Stake_i = stake para resultado i
- odd_i = odd para resultado i
- Σ (1 / odd_j) = soma dos inversos de todas as odds
```

**Exemplo Prático:**
```
Investimento Total: €100
Lakers: 2.10 (Betfair)
Celtics: 1.95 (Pinnacle)

Σ (1 / odd) = 1/2.10 + 1/1.95 = 0.989

Stake Lakers = (100 / 2.10) / 0.989 = 47.62 / 0.989 = €48.15
Stake Celtics = (100 / 1.95) / 0.989 = 51.28 / 0.989 = €51.85

Verificação:
Se Lakers ganha: 48.15 * 2.10 = €101.12
Se Celtics ganha: 51.85 * 1.95 = €101.11
Lucro: €1.11 (1.1%)
```

---

## 3. DETECÇÃO DE ARBITRAGEM

### 3.1 Fontes de Oportunidades

**Onde Encontrar Arbitragem:**

1. **Line Movement Diferencial**
   - Sharp book ajusta rápido
   - Soft book ajusta lento
   - Janela de 1-5 minutos

2. **Diferença de Opinião**
   - Diferentes modelos de precificação
   - Mais comum em mercados menos populares
   - Pode durar minutos a horas

3. **Erros de Precificação**
   - Erros humanos ou técnicos
   - Geralmente corrigidos rapidamente
   - Risco de void (aposta anulada)

4. **Promoções e Bónus**
   - Odds boost temporárias
   - Free bets
   - Requer leitura cuidadosa de T&C

### 3.2 Algoritmo de Detecção

**Lógica Básica:**
```
Para cada evento:
    Para cada mercado do evento:
        Obter odds de todas as casas
        Calcular Σ (1 / odd) para todas as combinações
        Se Σ < 1:
            Calcular lucro potencial
            Se lucro > threshold:
                Alertar oportunidade
```

**Implementação:**
```python
def detect_arbitrage(event_odds, min_profit=0.01):
    """
    Detecta arbitragem num evento
    event_odds: dict {bookmaker: {outcome: odd}}
    min_profit: lucro mínimo desejado (1% = 0.01)
    """
    arbitrage_opportunities = []

    # Para cada mercado (Moneyline, Spread, etc.)
    for market in event_odds['markets']:
        # Obter todas as combinações de casas
        combinations = get_combinations(event_odds, market)

        for combo in combinations:
            # Calcular soma dos inversos
            inverse_sum = sum(1 / odd for odd in combo['odds'].values())

            # Verificar se há arbitragem
            if inverse_sum < 1:
                profit = (1 - inverse_sum) * 100

                if profit >= min_profit * 100:
                    arbitrage_opportunities.append({
                        'market': market,
                        'books': combo['books'],
                        'odds': combo['odds'],
                        'profit': profit,
                        'inverse_sum': inverse_sum
                    })

    return arbitrage_opportunities
```

### 3.3 Thresholds de Lucro

**Lucro Mínimo Recomendado:**

| Nível | Lucro Mínimo | Justificação |
|-------|--------------|--------------|
| **Conservador** | 2% | Compensa slippage e erros |
| **Moderado** | 1.5% | Equilíbrio risco/retorno |
| **Agressivo** | 1% | Mais oportunidades, mais risco |

**Fatores que Reduzem Lucro Real:**
- Slippage (0.5-2%)
- Comissões de exchange (0-5%)
- Erros de execução
- Odds que mudam durante execução
- Limites baixos em soft books

---

## 4. RISCOS DA ARBITRAGEM

### 4.1 Riscos Operacionais

**1. Slippage**
- Odds mudam entre deteção e execução
- Pode transformar lucro em prejuízo
- **Mitigação:** Execução rápida, stakes pequenos

**2. Liquidez Insuficiente**
- Volume disponível menor que stake necessário
- **Mitigação:** Verificar liquidez antes de apostar

**3. Limites de Stake**
- Soft books têm limites baixos
- **Mitigação:** Respeitar limites, usar múltiplas contas

**4. Erros de Execução**
- Apostar no resultado errado
- **Mitigação:** Verificação dupla, automatização

### 4.2 Riscos de Mercado

**1. Void de Aposta**
- Casa anula aposta por "erro de odd"
- Perda garantida no outro lado
- **Mitigação:** Evitar arbitragem com odds muito discrepantes

**2. Mudança de Regras**
- Regras diferentes entre casas
- Ex: empate em basquete (OT)
- **Mitigação:** Verificar regras antes de apostar

**3. Suspensão de Evento**
- Jogo cancelado ou adiado
- Apostas geralmente reembolsadas
- **Mitigação:** Monitorizar news

### 4.3 Riscos de Conta

**1. Limitação Rápida**
- Soft books detectam arbitragem
- Limitam contas em dias/semanas
- **Mitigação:** Rotação de contas, camuflagem

**2. Encerramento de Conta**
- Conta fechada por arbitragem
- **Mitigação:** Múltiplas identidades, diversificação

**3. Banimento**
- Banido de todas as casas do grupo
- **Mitigação:** Evitar grupos relacionados

### 4.4 Riscos Financeiros

**1. Lock-up de Capital**
- Capital preso em apostas pendentes
- **Mitigação:** Gestão de bankroll, liquidez

**2. Custos de Transação**
- Depósitos/levantamentos têm custos
- **Mitigação:** Escolher métodos baratos

**3. Volatilidade de Bankroll**
- Pequenos lucros, muitos trades
- **Mitigação:** Bankroll adequado

---

## 5. ESTRATÉGIAS DE EXECUÇÃO

### 5.1 Sequência de Execução

**Ordem Recomendada:**
```
1. Detectar oportunidade
2. Verificar liquidez em todas as casas
3. Calcular stakes exatos
4. Apostar na casa com menor liquidez primeiro
5. Apostar nas outras casas imediatamente
6. Verificar que todas as apostas foram aceites
7. Confirmar arbitragem completa
```

**Por que Menor Liquidez Primeiro?**
- Menor risco de slippage
- Se falhar, ainda pode apostar nas outras
- Priorizar o lado mais difícil

### 5.2 Gestão de Erros

**Se Uma Aposta Falha:**
1. **Parar imediatamente** - Não apostar no outro lado
2. **Avaliar situação** - Por que falhou?
3. **Opções:**
   - Tentar novamente (se liquidez ainda disponível)
   - Aceitar posição direcional (se edge positivo)
   - Hedge parcialmente (se possível)
   - Aceitar perda

**Nunca:**
- Apostar no outro lado sem confirmação
- Churn em tentativa de recuperar
- Ignorar o erro

### 5.3 Automação

**Vantagens:**
- Execução mais rápida (segundos vs minutos)
- Menor slippage
- Mais oportunidades
- Menor erro humano

**Desvantagens:**
- Requer desenvolvimento complexo
- Risco de bugs
- Deteção por soft books
- Custos de infraestrutura

**Implementação:**
```python
class ArbitrageBot:
    def __init__(self, config):
        self.betfair_api = BetfairAPI(config['betfair'])
        self.pinnacle_api = PinnacleAPI(config['pinnacle'])
        self.db = Database(config['database'])
        self.min_profit = config['min_profit']
        self.max_stake = config['max_stake']

    def scan_and_execute(self):
        """Scaneia e executa arbitragens"""
        opportunities = self.scan_opportunities()

        for opp in opportunities:
            if opp['profit'] >= self.min_profit:
                success = self.execute_arbitrage(opp)
                if success:
                    self.log_arbitrage(opp)

    def execute_arbitrage(self, opportunity):
        """Executa arbitragem com gestão de erros"""
        # Calcular stakes
        stakes = self.calculate_stakes(opportunity, self.max_stake)

        # Executar em ordem de liquidez
        sorted_books = sorted_by_liquidity(opportunity['books'])

        placed_bets = []
        for book in sorted_books:
            try:
                bet = self.place_bet(book, stakes[book])
                placed_bets.append(bet)
            except Exception as e:
                # Se falha, cancelar apostas anteriores se possível
                self.cancel_bets(placed_bets)
                return False

        return True
```

---

## 6. OTIMIZAÇÃO DE LUCRO

### 6.1 Maximização de Volume

**Estratégias:**
1. **Múltiplas Contas** - Uma conta por soft book
2. **Múltiplas Identidades** - Legalmente, se permitido
3. **Rotação** - Alternar entre contas
4. **Diversificação** - Não focar em única soft book

**Meta:** Executar 50-100 arbitragens por dia

### 6.2 Minimização de Custos

**Custos a Considerar:**
- Comissões de exchange (0-5%)
- Custos de depósito/levantamento (0-5%)
- Slippage (0.5-2%)
- Custos de infraestrutura (servidores, APIs)

**Otimização:**
- Usar exchanges com comissão mais baixa
- Escolher métodos de pagamento gratuitos
- Otimizar execução para reduzir slippage
- Usar infraestrutura eficiente

### 6.3 Seleção de Oportunidades

**Critérios de Seleção:**
```
Prioridade Alta:
- Lucro > 3%
- Liquidez > 2x stake necessário
- Casas com API disponível
- Sem histórico de void

Prioridade Média:
- Lucro 1.5-3%
- Liquidez 1.5-2x stake
- Uma soft book, uma sharp/exchange

Prioridade Baixa:
- Lucro 1-1.5%
- Liquidez 1-1.5x stake
- Duas soft books (risco de limitação)
```

---

## 7. ESTRATÉGIA POR FASE

### 7.1 Fase 4-6 (Micro-Small Banca: €100-1,000)

**Estratégia:**
- Focar em arbitragens de alto lucro (>3%)
- Apostas pequenas (€10-50)
- Manual ou semi-automatizado
- 5-10 arbitragens por dia

**Justificação:**
- Maximizar ROI com banca pequena
- Aprender processo sem grande risco
- Construir banca rapidamente

### 7.2 Fase 7-9 (Medium Banca: €1,000-10,000)

**Estratégia:**
- Arbitragens de lucro médio (1.5-3%)
- Apostas médias (€50-200)
- Semi-automatizado
- 20-50 arbitragens por dia

**Justificação:**
- Mais oportunidades disponíveis
- Começar automação parcial
- Diversificar entre casas

### 7.3 Fase 10+ (Large Banca: €10,000+)

**Estratégia:**
- Arbitragens de lucro menor (1-1.5%)
- Apostas grandes (€200-1,000)
- Completamente automatizado
- 50-100+ arbitragens por dia

**Justificação:**
- Volume > lucro por aposta
- Automação completa necessária
- Escalar operação

**Nota:** Em fases avançadas, reduzir arbitragem e aumentar value betting

---

## 8. MÉTRICAS DE MONITORIZAÇÃO

### 8.1 KPIs

| KPI | Descrição | Target |
|-----|-----------|--------|
| **Lucro por Arbitragem** | Lucro médio por operação | > 1.5% |
| **Taxa de Sucesso** | % de arbitragens completas com sucesso | > 95% |
| **Slippage Médio** | Diferença entre lucro esperado e real | < 0.5% |
| **Volume Diário** | Número de arbitragens por dia | 20-100 |
| **ROI Mensal** | Retorno sobre investimento mensal | > 10% |
| **Vida Média de Conta** | Tempo até limitação em soft books | > 2 meses |

### 8.2 Alertas

**Gerar Alerta Se:**
- Taxa de sucesso < 90% em 24h
- Slippage médio > 1% em 24h
- Conta limitada em soft book
- Lucro por arbitragem < 1% consistente
- Número de oportunidades < 5 por dia

---

## 9. CONSIDERAÇÕES LEGAIS E ÉTICAS

### 9.1 Legalidade

**Geralmente Legal:**
- Arbitragem entre casas diferentes
- Uso de informação pública
- Não é manipulação de mercado

**Potencialmente Ilegal:**
- Uso de informações privilegiadas (insider trading)
- Manipulação de odds
- Fraude ou identidade falsa

**Recomendação:**
- Consultar advogado local
- Seguir T&C de cada casa
- Documentar todas as atividades

### 9.2 Ética

**É Ético?**
- Sim: É exploração de ineficiências de mercado
- Sim: As casas aceitam este risco
- Não: Se usar métodos fraudulentos

**Perspectiva:**
- Arbitragem é comum em todos os mercados financeiros
- Soft books têm sistemas para detetar e prevenir
- É parte do ecossistema de apostas

---

## 10. BACKLOG TÉCNICO

- [ ] Implementar scanner de arbitragem em tempo real
- [ ] Desenvolver bot de execução automática
- [ ] Criar sistema de gestão de múltiplas contas
- [ ] Implementar monitorização de slippage
- [ ] Desenvolver sistema de alertas de oportunidades
- [ ] Criar dashboard de métricas de arbitragem
- [ ] Implementar gestão de erros de execução
- [ ] Desenvolver estratégias de rotação de contas

---

## 11. LINKS CRUZADOS

- [[45_Bookmaker_Analysis/INDEX]] ← Secção mãe
- [[SOFT_BOOKS_ANALYSIS]] → Análise soft vs sharp books
- [[LINE_SHOPPING]] → Estratégias de line shopping
- [[GESTAO_MULTIPLAS_CONTAS]] → Gestão de contas múltiplas
- [[RISCOS_LIMITACAO]] → Riscos de limitação/banimento
- [[DIVERSIFICACAO_CONTAS]] → Estratégias de diversificação