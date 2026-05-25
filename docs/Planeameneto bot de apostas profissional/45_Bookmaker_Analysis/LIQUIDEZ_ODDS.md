# LIQUIDEZ_E_ODDS — Análise de Liquidez e Odds por Casa

**ID:** `BK-001` | **Fase:** #phase/3-6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Analisar as casas de apostas em termos de odds, liquidez, velocidade de ajuste e qualidade de execução. Identificar a melhor casa para cada fase do projeto e mercado específico, maximizando edge e minimizando slippage.

**Princípio:** Liquidez adequada + odds competitivas + execução rápida = lucro consistente.

---

## 2. CONCEITOS FUNDAMENTAIS

### 2.1 Liquidez

**Definição:** Volume disponível no mercado a uma determinada odd ou melhor.

**Importância:**
- Liquidez insuficiente = slippage alto = edge perdido
- Liquidez excessiva = custos de comissão maiores
- Liquidez ideal = suficiente para stake sem mover o mercado

**Métricas:**
- **Volume Disponível:** Quantidade de dinheiro a odd alvo
- **Profundidade:** Volume disponível em diferentes níveis de odd
- **Spread:** Diferença entre back e lay (exchanges)
- **Volatilidade:** Frequência e magnitude de mudanças de odds

### 2.2 Overround (Margem da Casa)

**Definição:** Margem embutida nas odds pela casa de apostas.

**Cálculo:**
```
Overround = (1/odd_A + 1/odd_B + ...) - 1

Exemplo Moneyline:
Team A: 2.00, Team B: 2.00
Overround = (1/2.00 + 1/2.00) - 1 = 0.5 + 0.5 - 1 = 0%
Mercado justo (sem margem)

Exemplo com margem:
Team A: 1.90, Team B: 1.90
Overround = (1/1.90 + 1/1.90) - 1 = 0.526 + 0.526 - 1 = 5.2%
Margem de 5.2% para a casa
```

**Impacto no Edge:**
```
Edge Real = Edge Calculado - Overround

Exemplo:
Edge Calculado = 5%
Overround = 3%
Edge Real = 5% - 3% = 2%
```

### 2.3 Slippage

**Definição:** Diferença entre a odd sinalizada pelo modelo e a odd obtida na execução.

**Causas:**
- Movimento de odds entre sinal e execução
- Liquidez insuficiente na odd alvo
- Execução lenta (latência alta)
- Tamanho de stake move o mercado

**Cálculo:**
```
Slippage % = (Odd Obtida - Odd Alvo) / Odd Alvo

Exemplo:
Odd Alvo: 2.10
Odd Obtida: 2.05
Slippage = (2.05 - 2.10) / 2.10 = -2.38%
```

### 2.4 Velocidade de Ajuste

**Definição:** Tempo que a casa demora a ajustar odds após novas informações (lesões, news, etc.).

**Classificação:**
- **Muito Rápida (< 30s):** Exchanges com trading ativo
- **Rápida (30-120s):** Sharp books (Pinnacle)
- **Média (2-5min):** Soft books com API
- **Lenta (> 5min):** Recreational books

**Implicações:**
- Ajuste rápido = menos oportunidades de arbitragem
- Ajuste lento = mais value mas mais risco de slippage

---

## 3. ANÁLISE POR CASA

### 3.1 Betfair Exchange

**Liquidez NBA:**
- Moneyline: €10,000-50,000 em jogos principais
- Spread: €5,000-20,000
- Totals: €5,000-15,000
- Player Props: €500-2,000

**Overround:**
- Praticamente 0% (peer-to-peer)
- Comissão: 5% sobre lucros (reduzível com volume)
- Overround efetivo: ~2-3% após comissão

**Velocidade de Ajuste:**
- Muito rápida (10-30 segundos)
- Trading ativo ajusta quase instantaneamente
- Ideal para CLV rápido

**Slippage Típico:**
- < 0.5% para stakes até €1,000
- 0.5-1% para stakes €1,000-5,000
- 1-2% para stakes €5,000-10,000

**API:**
- Excelente (REST + Streaming)
- Latência: 50-200ms
- Rate limits: Generosos

**Veredito:** Melhor opção geral para operação quant

### 3.2 Pinnacle

**Liquidez NBA:**
- Moneyline: €50,000-200,000
- Spread: €30,000-100,000
- Totals: €20,000-80,000

**Overround:**
- ~2% (muito baixo para bookmaker)
- Sem comissão adicional
- Overround efetivo: 2%

**Velocidade de Ajuste:**
- Rápida (30-90 segundos)
- Referência de mercado (abre e ajusta primeiro)
- Excelente para validação de CLV

**Slippage Típico:**
- < 0.3% para stakes até €5,000
- 0.3-0.8% para stakes €5,000-20,000
- 0.8-1.5% para stakes €20,000-50,000

**API:**
- Limitada (requer aprovação)
- Latência: 100-300ms
- Rate limits: Restritivos

**Veredito:** Melhor para referência de odds e shadow betting

### 3.3 Smarkets

**Liquidez NBA:**
- Moneyline: €1,000-5,000
- Spread: €500-2,000
- Totals: €500-1,500

**Overround:**
- Praticamente 0% (peer-to-peer)
- Comissão: 2% (fixa)
- Overround efetivo: ~1-2%

**Velocidade de Ajuste:**
- Média (1-3 minutos)
- Menos trading ativo que Betfair

**Slippage Típico:**
- < 1% para stakes até €500
- 1-2% para stakes €500-1,000
- 2-4% para stakes €1,000-2,000

**API:**
- Boa (REST)
- Latência: 150-300ms
- Rate limits: Moderados

**Veredito:** Boa alternativa para diversificação e comissão mais baixa

### 3.4 Matchbook

**Liquidez NBA:**
- Moneyline: €500-2,000
- Spread: €300-1,000
- Totals: €200-800

**Overround:**
- Praticamente 0% (peer-to-peer)
- Comissão: 1.5% (fixa)
- Overround efetivo: ~0.8-1.5%

**Velocidade de Ajuste:**
- Média-Lenta (2-5 minutos)
- Pouco trading ativo

**Slippage Típico:**
- < 1.5% para stakes até €300
- 1.5-3% para stakes €300-800
- 3-5% para stakes €800-1,500

**API:**
- Básica (REST)
- Latência: 200-400ms
- Rate limits: Baixos

**Veredito:** Apenas para niche específicos ou apostas muito pequenas

---

## 4. COMPARAÇÃO DE MÉTRICAS

### 4.1 Tabela Comparativa

| Casa | Liquidez NBA | Overround | Comissão | Slippage (€1k) | Ajuste | API Score |
|------|--------------|-----------|----------|----------------|--------|-----------|
| Betfair | Alta (★★★★★) | 0% | 5% | < 0.5% | Muito Rápido | 10/10 |
| Pinnacle | Muito Alta (★★★★★) | 2% | 0% | < 0.3% | Rápido | 6/10 |
| Smarkets | Média (★★★) | 0% | 2% | 1-2% | Médio | 8/10 |
| Matchbook | Baixa (★★) | 0% | 1.5% | 1.5-3% | Médio-Lento | 6/10 |

### 4.2 Ranking por Critério

**Para Maximizar Liquidez:**
1. Pinnacle (★★★★★)
2. Betfair (★★★★★)
3. Smarkets (★★★)
4. Matchbook (★★)

**Para Minimizar Custos (Overround + Comissão):**
1. Matchbook (1.5%)
2. Smarkets (2%)
3. Pinnacle (2%)
4. Betfair (5%)

**Para Minimizar Slippage:**
1. Pinnacle (< 0.3%)
2. Betfair (< 0.5%)
3. Smarkets (1-2%)
4. Matchbook (1.5-3%)

**Para Velocidade de Execução:**
1. Betfair (★★★★★)
2. Pinnacle (★★★★)
3. Smarkets (★★★)
4. Matchbook (★★)

---

## 5. ESTRATÉGIA POR FASE

### 5.1 Fase 4-6 (Micro-Small Banca: €100-1,000)

**Casa Recomendada:** Betfair Exchange

**Justificação:**
- Liquidez suficiente para stakes pequenos
- API excelente para automação
- Execução rápida minimiza slippage
- Overround baixo (apenas comissão)

**Estratégia:**
- 100% do volume em Betfair
- Focar em Moneyline e Spread (maior liquidez)
- Evitar Player Props (liquidez baixa)

### 5.2 Fase 7-9 (Medium Banca: €1,000-10,000)

**Distribuição Recomendada:**
- Betfair: 70%
- Smarkets: 20%
- Pinnacle (shadow): 10%

**Justificação:**
- Diversificar risco operacional
- Aproveitar comissão mais baixa do Smarkets
- Usar Pinnacle apenas para referência

**Estratégia:**
- Apostas principais: Betfair
- Apostas secundárias: Smarkets (quando liquidez suficiente)
- Validação de CLV: Pinnacle

### 5.3 Fase 10+ (Large Banca: €10,000+)

**Distribuição Recomendada:**
- Betfair: 50%
- Pinnacle: 20% (se disponível)
- Smarkets: 15%
- Matchbook: 5%
- Outros: 10%

**Justificação:**
- Distribuir volume para não mover mercado
- Maximizar liquidez total disponível
- Reduzir dependência de única casa

**Estratégia:**
- Apostas grandes (>€5,000): Dividir entre casas
- Apostas pequenas: Casa com melhor odd no momento
- Line shopping sistemático entre todas as casas

---

## 6. MÉTRICAS DE MONITORIZAÇÃO

### 6.1 KPIs por Casa

| KPI | Descrição | Target |
|-----|-----------|--------|
| Slippage Médio | Diferença média odd alvo vs obtida | < 1% |
| Taxa de Rejeição | % de apostas rejeitadas | < 5% |
| Tempo de Execução | Tempo do sinal à confirmação | < 5s |
| Liquidez Média | Volume disponível médio | > 5x stake |
| Overround Efetivo | Margem real pag | < 3% |

### 6.2 Alertas

**Gerar Alerta Se:**
- Slippage > 2% em 3 apostas consecutivas
- Liquidez < 2x stake em 5 tentativas
- Taxa de rejeição > 10% em 1 hora
- Tempo de execução > 10s em 3 tentativas
- Overround > 5% consistentemente

---

## 7. BACKLOG TÉCNICO

- [ ] Implementar monitorização de liquidez em tempo real
- [ ] Criar sistema de ranking dinâmico de casas por métrica
- [ ] Desenvolver algoritmo de line shopping automático
- [ ] Integrar APIs de múltiplas casas para comparação
- [ ] Criar histórico de slippage por casa e mercado
- [ ] Implementar alertas automáticos para liquidez baixa
- [ ] Documentar overround por mercado e época
- [ ] Criar dashboard comparativo de casas em tempo real

---

## 8. LINKS CRUZADOS

- [[45_Bookmaker_Analysis/INDEX]] ← Secção mãe
- [[BOOKMAKER_COMPARISON]] → Comparação detalhada de casas
- [[SHARP_MONEY_TRACKING]] → Rastreamento de movimentos de odds
- [[47_Shadow_Betting/INDEX]] → Simulação multi-casa
- [[LINE_SHOPPING]] → Estratégias de encontrar melhor linha
