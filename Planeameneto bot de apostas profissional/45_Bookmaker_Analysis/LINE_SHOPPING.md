# LINE_SHOPPING — Estratégias de Line Shopping

**ID:** `BK-004` | **Fase:** #phase/3-6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar estratégias sistemáticas de line shopping - encontrar a melhor odd disponível entre múltiplas casas de apostas para maximizar edge e ROI em cada aposta.

**Princípio:** A diferença entre a melhor e a pior odd pode ser 5-10%; line shopping sistemático adiciona 2-3% de ROI adicional.

---

## 2. CONCEITOS FUNDAMENTAIS

### 2.1 O Que é Line Shopping

**Definição:** Processo de comparar odds entre múltiplas casas de apostas para encontrar a melhor odd disponível para uma determinada seleção.

**Analogia Financeira:**
- Igual a comparar preços em diferentes supermercados
- Se o produto A custa €10 no supermercado X e €12 no Y
- Comprar no X = economia de 20%
- Line shopping = comprar odd onde é "mais barata"

**Exemplo Prático:**
```
Lakers vs Celtics

Betfair: Lakers 2.10, Celtics 1.80
Pinnacle: Lakers 2.05, Celtics 1.85
Smarkets: Lakers 2.15, Celtics 1.78

Para apostar Lakers:
- Melhor odd: 2.15 (Smarkets)
- Pior odd: 2.05 (Pinnacle)
- Diferença: (2.15 - 2.05) / 2.05 = 4.9%

Impacto em €100:
- Odd 2.15: Retorno €215
- Odd 2.05: Retorno €205
- Diferença: €10 (4.9%)
```

### 2.2 Valor do Line Shopping

**Cálculo de Impacto:**
```
Edge Adicional = (Melhor Odd / Pior Odd) - 1

Se melhor odd = 2.15, pior odd = 2.05:
Edge Adicional = (2.15 / 2.05) - 1 = 4.9%

Se ROI base = 5%, com line shopping:
ROI com line shopping = 5% + 4.9% = 9.9%
```

**Impacto no Longo Prazo:**
```
1000 apostas de €100:
Sem line shopping (ROI 5%): €5,000 lucro
Com line shopping (ROI 9.9%): €9,900 lucro
Diferença: €4,900 (+98%)
```

### 2.3 Line Shopping vs Arbitragem

| Característica | Line Shopping | Arbitragem |
|----------------|---------------|------------|
| **Objetivo** | Maximizar odd em uma seleção | Lucro garantido em todos os resultados |
| **Risco** | Tem risco de mercado | Sem risco de mercado |
| **Complexidade** | Baixa-Média | Alta |
| **Frequência** | Todas as apostas | Oportunidades específicas |
| **Lucro por aposta** | 2-5% adicional | 1-5% garantido |
| **Escalabilidade** | Alta | Média |

**Relação:**
- Line shopping é complementar à arbitragem
- Pode fazer line shopping em value betting
- Pode fazer line shopping em arbitragem (encontrar melhor combinação)

---

## 3. ESTRATÉGIAS DE LINE SHOPPING

### 3.1 Estratégia Básica: Comparação Manual

**Processo:**
1. Identificar aposta desejada
2. Verificar odds em 3-5 casas
3. Selecionar casa com melhor odd
4. Apostar

**Vantagens:**
- Simples de implementar
- Sem custos de infraestrutura
- Bom para aprendizagem

**Desvantagens:**
- Demorado (5-10 minutos por aposta)
- Limitado a poucas casas
- Odds podem mudar durante processo
- Impossível escalar

**Quando Usar:**
- Fases iniciais (banca pequena)
- Poucas apostas por dia
- Aprendizagem do processo

### 3.2 Estratégia Intermediária: Scanner Semi-Automático

**Processo:**
1. Scanner verifica odds automaticamente
2. Sistema alerta quando encontra melhor odd
3. Usuário verifica e aprova
4. Sistema executa aposta

**Vantagens:**
- Mais rápido que manual
- Pode verificar mais casas
- Menor slippage
- Ainda tem controle manual

**Desvantagens:**
- Requer desenvolvimento
- Ainda dependente de aprovação manual
- Latência entre alerta e execução

**Quando Usar:**
- Fases intermédias (banca média)
- 10-30 apostas por dia
- Transição para automação

### 3.3 Estratégia Avançada: Scanner Automático

**Processo:**
1. Scanner verifica odds continuamente
2. Sistema identifica melhor odd automaticamente
3. Sistema executa aposta sem aprovação
4. Sistema monitoriza e reporta

**Vantagens:**
- Execução mais rápida (segundos)
- Pode verificar muitas casas
- Minimiza slippage
- Escalável para 100+ apostas/dia

**Desvantagens:**
- Desenvolvimento complexo
- Risco de bugs
- Requer infraestrutura robusta
- Menos controle humano

**Quando Usar:**
- Fases avançadas (banca grande)
- 50-100+ apostas por dia
- Operação em escala

### 3.4 Estratégia de Timing

**Quando Fazer Line Shopping:**

| Momento | Vantagem | Desvantagem |
|---------|----------|-------------|
| **Abertura de linha** | Melhores odds, menos movimento | Mais risco de erro |
| **1-2h antes do jogo** | Equilíbrio entre odd e liquidez | Menos oportunidades |
| **Últimos 30min** | Liquidez máxima | Odds podem estar ajustadas |

**Recomendação:**
- Focar em line shopping 1-2h antes do jogo
- Evitar últimos minutos (slippage alto)
- Considerar机会 de opening line se modelo forte

---

## 4. IMPLEMENTAÇÃO TÉCNICA

### 4.1 Arquitetura de Sistema

**Componentes:**

```
┌─────────────────┐
│  Data Feed      │ ← APIs de múltiplas casas
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Odds Aggregator│ ← Normaliza e agrega odds
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Line Shopper   │ ← Compara e seleciona melhor odd
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Execution Engine│ ← Executa aposta na melhor casa
└─────────────────┘
```

### 4.2 Agregador de Odds

**Função:** Coletar e normalizar odds de múltiplas fontes

**Implementação:**
```python
class OddsAggregator:
    def __init__(self, apis):
        self.apis = apis  # Dict de APIs por casa

    def get_odds(self, event_id, market):
        """
        Coleta odds de todas as casas para um evento/mercado
        """
        odds = {}

        for bookmaker, api in self.apis.items():
            try:
                book_odds = api.get_odds(event_id, market)
                odds[bookmaker] = book_odds
            except Exception as e:
                logger.error(f"Error fetching odds from {bookmaker}: {e}")

        return odds

    def normalize_odds(self, odds):
        """
        Normaliza odds para formato consistente
        """
        normalized = {}

        for bookmaker, book_odds in odds.items():
            normalized[bookmaker] = {
                'outcome_1': book_odds['team_a'],
                'outcome_2': book_odds['team_b'],
                'timestamp': book_odds['timestamp'],
                'liquidity': book_odds.get('liquidity', 0)
            }

        return normalized
```

### 4.3 Algoritmo de Line Shopping

**Função:** Identificar a melhor odd para cada seleção

**Implementação:**
```python
class LineShopper:
    def __init__(self, min_liquidity=100):
        self.min_liquidity = min_liquidity

    def find_best_odds(self, normalized_odds):
        """
        Encontra a melhor odd para cada seleção
        """
        best_odds = {}

        # Para cada resultado possível
        for outcome in ['outcome_1', 'outcome_2']:
            candidates = []

            # Coletar odds de todas as casas
            for bookmaker, odds in normalized_odds.items():
                odd = odds[outcome]
                liquidity = odds['liquidity']

                # Filtrar por liquidez mínima
                if liquidity >= self.min_liquidity:
                    candidates.append({
                        'bookmaker': bookmaker,
                        'odd': odd,
                        'liquidity': liquidity,
                        'timestamp': odds['timestamp']
                    })

            # Selecionar melhor odd
            if candidates:
                best = max(candidates, key=lambda x: x['odd'])
                best_odds[outcome] = best

        return best_odds

    def calculate_improvement(self, best_odds, reference_odds):
        """
        Calcula melhoria vs odd de referência
        """
        improvements = {}

        for outcome, best in best_odds.items():
            reference = reference_odds[outcome]
            improvement = (best['odd'] / reference - 1) * 100
            improvements[outcome] = improvement

        return improvements
```

### 4.4 Motor de Execução

**Função:** Executar aposta na casa com melhor odd

**Implementação:**
```python
class ExecutionEngine:
    def __init__(self, apis):
        self.apis = apis

    def execute_bet(self, selection, stake, best_odd):
        """
        Executa aposta na casa com melhor odd
        """
        bookmaker = best_odd['bookmaker']
        odd = best_odd['odd']
        api = self.apis[bookmaker]

        try:
            # Verificar liquidez
            if best_odd['liquidity'] < stake:
                logger.warning(f"Insufficient liquidity at {bookmaker}")
                return False

            # Colocar aposta
            bet = api.place_bet(selection, odd, stake)

            if bet['status'] == 'accepted':
                logger.info(f"Bet placed at {bookmaker}: {selection} @ {odd}")
                return True
            else:
                logger.error(f"Bet rejected at {bookmaker}: {bet['reason']}")
                return False

        except Exception as e:
            logger.error(f"Error executing bet at {bookmaker}: {e}")
            return False
```

---

## 5. OTIMIZAÇÃO DE LINE SHOPPING

### 5.1 Seleção de Casas

**Critérios para Incluir Casa:**

| Critério | Peso | Justificação |
|----------|------|--------------|
| **Liquidez** | Alta | Necessária para executar apostas |
| **API Disponível** | Alta | Essencial para automação |
| **Overround Baixo** | Média | Melhora ROI |
| **Velocidade de Ajuste** | Média | Menos slippage |
| **Limites Altos** | Média | Permite escalar |
| **Geografia** | Baixa | Se disponível no país |

**Casa Recomendadas:**
1. Betfair Exchange (★★★★★)
2. Pinnacle (★★★★★)
3. Smarkets (★★★★)
4. Matchbook (★★★)

### 5.2 Freqüência de Verificação

**Por Mercado:**

| Mercado | Freqüência Recomendada | Justificação |
|---------|------------------------|--------------|
| **Moneyline** | A cada 30s | Alta liquidez, movimento rápido |
| **Spread** | A cada 30s | Similar ao Moneyline |
| **Totals** | A cada 1min | Menos liquidez |
| **Player Props** | A cada 2min | Liquidez baixa |

**Por Tempo até Jogo:**

| Tempo até Jogo | Freqüência |
|----------------|-------------|
| > 24h | A cada 5min |
| 24-6h | A cada 2min |
| 6-1h | A cada 30s |
| < 1h | A cada 10s |

### 5.3 Gestão de Latência

**Fontes de Latência:**
1. API response time (50-500ms)
2. Network latency (10-100ms)
3. Processing time (10-50ms)
4. Execution time (100-500ms)

**Total Típico:** 170-1,150ms (0.17-1.15s)

**Otimização:**
- Usar servidores próximos às APIs
- Cache de odds frequentemente acessadas
- Processamento assíncrono
- Conexões persistentes

---

## 6. LINE SHOPPING POR TIPO DE APOSTA

### 6.1 Para Value Betting

**Estratégia:**
1. Modelo identifica value em seleção
2. Line shopper verifica todas as casas
3. Seleciona casa com melhor odd
4. Executa aposta

**Benefício:**
- Edge adicional de 2-5%
- ROI aumenta proporcionalmente
- Sem risco adicional

**Exemplo:**
```
Modelo: Lakers tem 52% probabilidade → Fair odd = 1.92
Pinnacle: Lakers 2.05 → Edge = (2.05 * 0.52) - 1 = 6.6%
Betfair: Lakers 2.15 → Edge = (2.15 * 0.52) - 1 = 11.8%

Line shopping: Apostar em Betfair
Edge adicional: 11.8% - 6.6% = 5.2%
```

### 6.2 Para Arbitragem

**Estratégia:**
1. Scanner detecta arbitragem potencial
2. Line shopper verifica todas as combinações
3. Seleciona combinação com maior lucro
4. Executa arbitragem

**Benefício:**
- Lucro adicional de 0.5-2%
- Mais oportunidades viáveis
- Melhor utilização de capital

**Exemplo:**
```
Combinação A:
Betfair: Lakers 2.10
Pinnacle: Celtics 1.95
Lucro: 1.1%

Combinação B (com line shopping):
Smarkets: Lakers 2.15
Pinnacle: Celtics 1.95
Lucro: 2.3%

Melhoria: 2.3% - 1.1% = 1.2%
```

### 6.3 Para CLV

**Estratégia:**
1. Modelo identifica aposta
2. Line shopper verifica odds vs closing
3. Seleciona casa com melhor CLV potencial
4. Executa aposta

**Benefício:**
- CLV adicional de 1-3%
- Validação mais forte de edge
- Melhor métrica de performance

---

## 7. MÉTRICAS DE MONITORIZAÇÃO

### 7.1 KPIs

| KPI | Descrição | Target |
|-----|-----------|--------|
| **Melhoria Média de Odd** | Diferença média vs odd de referência | > 2% |
| **Taxa de Melhoria** | % de apostas com odd melhor que referência | > 80% |
| **Slippage de Line Shopping** | Diferença entre odd identificada e obtida | < 0.5% |
| **Tempo de Execução** | Tempo da deteção à execução | < 2s |
| **Casas Utilizadas** | Número de casas no pool | 3-5 |
| **ROI Adicional** | ROI adicional atribuível ao line shopping | > 2% |

### 7.2 Alertas

**Gerar Alerta Se:**
- Melhoria média < 1% por 24h
- Taxa de melhoria < 70% por 24h
- Slippage > 1% em 5 apostas consecutivas
- Tempo de execução > 5s em 3 tentativas
- Casa do pool indisponível > 1h

---

## 8. ESTRATÉGIA POR FASE

### 8.1 Fase 4-6 (Micro-Small Banca: €100-1,000)

**Estratégia:**
- Line shopping manual
- Verificar 3 casas (Betfair, Pinnacle, Smarkets)
- 5-10 apostas por dia
- Focar em melhorias > 3%

**Justificação:**
- Simples de implementar
- Aprender processo
- Maximizar ROI com banca pequena

### 8.2 Fase 7-9 (Medium Banca: €1,000-10,000)

**Estratégia:**
- Line shopping semi-automático
- Verificar 4-5 casas
- 20-50 apostas por dia
- Focar em melhorias > 1.5%

**Justificação:**
- Mais eficiente
- Mais oportunidades
- Começar automação

### 8.3 Fase 10+ (Large Banca: €10,000+)

**Estratégia:**
- Line shopping completamente automático
- Verificar 5+ casas
- 50-100+ apostas por dia
- Aceitar melhorias > 1%

**Justificação:**
- Escala necessária
- Eficiência máxima
- ROI adicional significativo em volume alto

---

## 9. RISCOS E MITIGAÇÃO

### 9.1 Riscos

**1. Odds Mudam Durante Execução**
- **Risco:** Slippage reduz melhoria
- **Mitigação:** Execução rápida, stakes pequenos

**2. Liquidez Insuficiente**
- **Risco:** Não consegue executar na melhor odd
- **Mitigação:** Verificar liquidez antes, ter casas alternativas

**3. API Falha**
- **Risco:** Perda de dados de uma casa
- **Mitigação:** Múltiplas APIs, sistema de fallback

**4. Overround Oculto**
- **Risco:** Melhor odd tem overround alto
- **Mitigação:** Calcular overround real, não apenas odd

### 9.2 Melhores Práticas

1. **Sempre verificar liquidez** antes de executar
2. **Ter casas alternativas** se primeira falhar
3. **Monitorizar slippage** continuamente
4. **Calcular overround real** não apenas odd nominal
5. **Testar sistema** regularmente
6. **Ter plano de contingência** para falhas

---

## 10. BACKLOG TÉCNICO

- [ ] Implementar agregador de odds multi-casa
- [ ] Desenvolver algoritmo de line shopping automático
- [ ] Criar motor de execução integrado
- [ ] Implementar sistema de fallback para APIs
- [ ] Desenvolver dashboard de métricas em tempo real
- [ ] Criar sistema de alertas de oportunidades
- [ ] Implementar otimização de latência
- [ ] Desenvolver testes de stress do sistema

---

## 11. LINKS CRUZADOS

- [[45_Bookmaker_Analysis/INDEX]] ← Secção mãe
- [[LIQUIDEZ_ODDS]] → Análise de liquidez e odds
- [[SOFT_BOOKS_ANALYSIS]] → Análise soft vs sharp books
- [[ARBITRAGEM_BOOKMAKERS]] → Estratégias de arbitragem
- [[BOOKMAKER_COMPARISON]] → Comparação detalhada de casas