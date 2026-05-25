# EXCHANGE_TRADING — Estratégias de Trading em Exchanges

**ID:** `EXE-004` | **Fase:** #phase/7-12 | **Owner:** Trading Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar estratégias de trading em exchanges como Betfair, incluindo back/lay, hedging, trading out, e técnicas avançadas. Trading em exchanges difere fundamentalmente de apostas simples - permite lucrar independentemente do resultado final.

**Princípio:** Trading é sobre gestão de risco e timing, não previsão de resultados.

---

## 2. CONCEITOS FUNDAMENTAIS

### 2.1 Back e Lay

**BACK (A favor):**
- Comprar um contrato
- Lucra se o resultado ocorrer
- Equivalente a aposta tradicional

**LAY (Contra):**
- Vender um contrato
- Lucra se o resultado NÃO ocorrer
- Age como bookmaker

**Exemplo Simples:**

```
BACK Lakers @ 2.00 com $100:
- Se Lakers ganhar: +$100
- Se Lakers perder: -$100

LAY Lakers @ 2.00 com $100:
- Se Lakers ganhar: -$100
- Se Lakers não ganhar: +$100
```

### 2.2 Livro de Ordens

**Estrutura:**

```
BACK (Comprar)          ODD          LAY (Vender)

          $500 @ 1.98
          $1,000 @ 1.97
          $2,000 @ 1.96
                        2.00
          $2,000 @ 2.04
          $1,000 @ 2.05
          $500 @ 2.06
```

**Leitura:**
- Para BACK @ 2.00: melhor odd disponível é 2.04
- Para LAY @ 2.00: melhor odd disponível é 1.96
- Spread: 2.04 - 1.96 = 0.08 (4%)

---

## 3. ESTRATÉGIAS BÁSICAS

### 3.1 Back-to-Lay (Pré-Jogo)

**Conceito:** Back um resultado antes do jogo, lay depois que a odd cai.

**Exemplo:**

```
Cenário: Lakers vs Warriors
Pré-jogo: Lakers @ 3.00 (subvalorizado)

Passo 1 - BACK:
BACK $100 em Lakers @ 3.00
- Se Lakers ganhar: +$200
- Se Lakers perder: -$100

Passo 2 - Aguardar movimento:
Odd Lakers cai para 2.00 (após lineup ou notícias)

Passo 3 - LAY:
LAY $150 em Lakers @ 2.00
- Se Lakers ganhar: -$150
- Se Lakers perder: +$150

Resultado Final:
- Se Lakers ganhar: $200 - $150 = +$50
- Se Lakers perder: -$100 + $150 = +$50

Lucro garantido: $50 (independentemente do resultado)
```

**Fórmula de Stake LAY para Green:**

```
Stake LAY = (Lucro BACK Potencial) / (Odd LAY - 1)

Exemplo:
Lucro BACK = $200
Odd LAY = 2.00

Stake LAY = $200 / (2.00 - 1) = $200 / 1 = $200
```

**Quando Usar:**
- Odd inicial subvalorizada
- Expectativa de movimento de odd
- Antes de eventos que afetam odds (lineups, lesões)

**Riscos:**
- Odd pode subir em vez de cair
- Liquidez pode ser insuficiente
- Timing crítico

### 3.2 Lay-to-Back (Pré-Jogo)

**Conceito:** Lay um resultado antes do jogo, back depois que a odd sobe.

**Exemplo:**

```
Cenário: Lakers vs Warriors
Pré-jogo: Lakers @ 1.50 (sobrevalorizado)

Passo 1 - LAY:
LAY $100 em Lakers @ 1.50
- Se Lakers ganhar: -$50
- Se Lakers não ganhar: +$100

Passo 2 - Aguardar movimento:
Odd Lakers sobe para 2.00

Passo 3 - BACK:
BACK $50 em Lakers @ 2.00
- Se Lakers ganhar: +$50
- Se Lakers perder: -$50

Resultado Final:
- Se Lakers ganhar: -$50 + $50 = $0
- Se Lakers não ganhar: $100 - $50 = +$50

Lucro garantido: $50 se Lakers não ganhar
```

**Fórmula de Stake BACK para Green:**

```
Stake BACK = (Lucro LAY Potencial) / Odd BACK

Exemplo:
Lucro LAY = $100
Odd BACK = 2.00

Stake BACK = $100 / 2.00 = $50
```

**Quando Usar:**
- Odd inicial sobrevalorizada
- Expectativa de movimento de odd
- Antes de eventos que afetam odds

**Riscos:**
- Odd pode cair em vez de subir
- Liquidez pode ser insuficiente
- Timing crítico

### 3.3 Trading In-Play (Ao Vivo)

**Conceito:** Lucrar com movimentos de odds durante o jogo.

**Exemplo - Basketball:**

```
Cenário: Lakers vs Warriors
Score: Lakers 50-40 Warriors (Q2)
Odd Lakers: 1.40

Análise: Warriors ainda podem reagir

Passo 1 - LAY:
LAY $100 em Lakers @ 1.40
- Se Lakers ganhar: -$40
- Se Lakers não ganhar: +$100

Passo 2 - Aguardar:
Warriors reagem, score: Lakers 70-75 Warriors (Q3)
Odd Lakers: 2.50

Passo 3 - BACK:
BACK $40 em Lakers @ 2.50
- Se Lakers ganhar: +$60
- Se Lakers perder: -$40

Resultado Final:
- Se Lakers ganhar: -$40 + $60 = +$20
- Se Lakers perder: $100 - $40 = +$60

Lucro garantido: $20-$60
```

**Quando Usar:**
- Mercados líquidos in-play
- Conhecimento profundo do esporte
- Capacidade de reagir rápido

**Riscos:**
- Latência crítica
- Odds podem mover rapidamente
- Liquidez pode desaparecer
- Requer streaming de dados em tempo real

---

## 4. ESTRATÉGIAS DE HEDGING

### 4.1 Green Up (Lucro Garantido)

**Conceito:** Garantir lucro independentemente do resultado.

**Exemplo:**

```
Posição atual: BACK $100 em Team A @ 3.00
Odd atual: Team A @ 2.00

Passo 1 - Calcular lucro potencial:
Lucro BACK = $100 × (3.00 - 1) = $200

Passo 2 - Calcular stake LAY:
Stake LAY = Lucro BACK / (Odd LAY - 1)
Stake LAY = $200 / (2.00 - 1) = $200

Passo 3 - Executar LAY:
LAY $200 em Team A @ 2.00

Resultado:
- Se Team A ganhar: $200 - $200 = $0
- Se Team A perder: $200 - $100 = $100

Lucro garantido: $100
```

**Fórmula Geral:**

```
Para Green Up após BACK:
Stake LAY = (Stake BACK × Odd BACK) / Odd LAY

Para Green Up após LAY:
Stake BACK = (Stake LAY × Odd LAY) / Odd BACK
```

### 4.2 Red Up (Perda Minimizada)

**Conceito:** Minimizar perda quando posição está desfavorável.

**Exemplo:**

```
Posição atual: BACK $100 em Team A @ 2.00
Odd atual: Team A @ 3.00 (piorou)

Passo 1 - Calcular perda potencial:
Perda BACK = $100
Lucro potencial = $100

Passo 2 - Calcular stake LAY para minimizar:
Stake LAY = Stake BACK × (Odd BACK / Odd LAY)
Stake LAY = $100 × (2.00 / 3.00) = $66.67

Passo 3 - Executar LAY:
LAY $66.67 em Team A @ 3.00

Resultado:
- Se Team A ganhar: $100 - $133.33 = -$33.33
- Se Team A perder: $66.67 - $100 = -$33.33

Perda garantida: $33.33 (em vez de $100)
```

**Fórmula Geral:**

```
Para Red Up após BACK:
Stake LAY = Stake BACK × (Odd BACK / Odd LAY)

Para Red Up após LAY:
Stake BACK = Stake LAY × (Odd LAY / Odd BACK)
```

### 4.3 Partial Hedge

**Conceito:** Hedging parcial para reduzir exposição mantendo upside.

**Exemplo:**

```
Posição atual: BACK $100 em Team A @ 3.00
Odd atual: Team A @ 2.00

Opção 1 - Full Hedge:
LAY $200 → Lucro garantido $100

Opção 2 - Partial Hedge (50%):
LAY $100 em Team A @ 2.00

Resultado:
- Se Team A ganhar: $200 - $100 = +$100
- Se Team A perder: $100 - $100 = $0

Trade-off: Upside mantido com downside limitado
```

**Quando Usar:**
- Confiança parcial na posição original
- Quer reduzir risco sem eliminar upside
- Gestão de bankroll conservadora

---

## 5. ESTRATÉGIAS AVANÇADAS

### 5.1 Scalping

**Conceito:** Lucrar com pequenos movimentos de odds em curto período.

**Exemplo:**

```
Cenário: Mercado de gols em jogo de futebol
Odd atual: Over 2.5 Gols @ 2.00

Passo 1 - BACK:
BACK $500 em Over 2.5 @ 2.00

Passo 2 - Aguardar pequeno movimento (10-30 segundos):
Odd cai para 1.99

Passo 3 - LAY:
LAY $505 em Over 2.5 @ 1.99

Resultado:
- Se Over 2.5: $500 - $500.95 = -$0.95
- Se Under 2.5: $505 - $500 = +$5

Lucro médio: $2 por operação
```

**Características:**
- Múltiplas operações por jogo
- Lucros pequenos, acumulativos
- Requer latência mínima
- Alta frequência de trades

**Riscos:**
- Requer execução extremamente rápida
- Comissões acumulativas
- Stress psicológico
- Requer automação

### 5.2 Dutching

**Conceito:** Distribuir stake entre múltiplos resultados para garantir lucro.

**Exemplo:**

```
Cenário: Corrida de cavalos com 3 cavalos competitivos
Odds: Cavalo A @ 3.00, Cavalo B @ 4.00, Cavalo C @ 5.00

Passo 1 - Calcular probabilidades implícitas:
A: 1/3.00 = 33.3%
B: 1/4.00 = 25.0%
C: 1/5.00 = 20.0%
Total: 78.3% (arb opportunity de 21.7%)

Passo 2 - Calcular stakes para lucro igual:
Stake A = $100
Stake B = $100 × (3.00/4.00) = $75
Stake C = $100 × (3.00/5.00) = $60
Total stake: $235

Passo 3 - Executar:
BACK $100 em A @ 3.00
BACK $75 em B @ 4.00
BACK $60 em C @ 5.00

Resultado:
- Se A ganhar: $200 - $235 = -$35
- Se B ganhar: $300 - $235 = +$65
- Se C ganhar: $300 - $235 = +$65

Lucro esperado: +$32 (média)
```

**Quando Usar:**
- Arbitragem entre resultados
- Cobrir múltiplos cenários
- Reduzir risco de seleção

**Riscos:**
- Requer liquidez em múltiplos resultados
- Comissões em múltiplas apostas
- Complexidade de gestão

### 5.3 Arbitragem

**Conceito:** Lucrar sem risco explorando diferenças de odds entre mercados.

**Exemplo:**

```
Cenário: Jogo de futebol
Betfair: Team A @ 2.10
Bookmaker X: Team B @ 2.10

Passo 1 - Verificar arb:
Probabilidade A = 1/2.10 = 47.6%
Probabilidade B = 1/2.10 = 47.6%
Total = 95.2% (arb de 4.8%)

Passo 2 - Calcular stakes:
Stake A (Betfair) = $100
Stake B (Bookmaker) = $100 × (2.10/2.10) = $100

Passo 3 - Executar:
BACK $100 em Team A @ 2.10 (Betfair)
BACK $100 em Team B @ 2.10 (Bookmaker)

Resultado:
- Se A ganhar: $110 - $100 = +$10
- Se B ganhar: $110 - $100 = +$10

Lucro garantido: $10 (sem risco)
```

**Quando Usar:**
- Diferenças de odds entre mercados
- Movimentos assimétricos de odds
- Ineficiências de mercado

**Riscos:**
- Oportunidades raras e fugazes
- Requer múltiplas contas
- Limitações de stake
- Comissões podem eliminar arb

---

## 6. GESTÃO DE RISCO

### 6.1 Exposure Management

**Conceito:** Controlar exposição total em cada mercado.

**Exemplo:**

```
Regra: Exposição máxima por mercado = 5% do bankroll
Bankroll: $10,000
Exposição máxima: $500

Posição atual:
- BACK Team A: $200
- LAY Team B: $150
Exposição total: $350

Pode adicionar: até $150 de exposição adicional
```

**Métricas:**

```
Exposição BACK = Stake
Exposição LAY = Stake × (Odd - 1)
Exposição Total = |Exposição BACK| + |Exposição LAY|
```

### 6.2 Position Sizing

**Conceito:** Ajustar stake baseado em confiança e odds.

**Fórmula Kelly:**

```
Stake = (Probabilidade × Odd - 1) / (Odd - 1)

Exemplo:
Probabilidade estimada: 60%
Odd: 2.00

Stake = (0.60 × 2.00 - 1) / (2.00 - 1)
Stake = (1.20 - 1) / 1 = 0.20 (20% do bankroll)

Kelly fracionado (25%): 5% do bankroll
```

**Regras Práticas:**

| Confiança | Odds | Stake recomendado |
|-----------|------|-------------------|
| Alta | < 1.50 | 1-2% |
| Alta | 1.50-3.00 | 2-3% |
| Alta | > 3.00 | 1-2% |
| Média | < 1.50 | 0.5-1% |
| Média | 1.50-3.00 | 1-2% |
| Média | > 3.00 | 0.5-1% |
| Baixa | Qualquer | 0-0.5% |

### 6.3 Stop Loss

**Conceito:** Limitar perda máxima por operação.

**Exemplo:**

```
Regra: Stop loss = 2% do stake por operação

Operação: BACK $100 em Team A @ 2.00
Odd atual: Team A @ 2.50 (piorou)

Perda potencial: $100
Stop loss: $2

Ação: Red up para limitar perda a $2
```

**Tipos de Stop Loss:**
- **Hard Stop:** Valor fixo de perda
- **Percentage Stop:** Porcentagem do stake
- **Time Stop:** Cancelar após X segundos
- **Odd Stop:** Cancelar se odd mover além de threshold

---

## 7. AUTOMAÇÃO

### 7.1 Bot de Trading

**Componentes:**

```
┌─────────────────────────────────────────────────────────────────┐
│ BOT DE TRADING AUTOMÁTICO                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Data Feed    │───→│ Strategy     │───→│ Order Engine │      │
│  │ (Betfair)    │    │ Engine       │    │ (Betfair)    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         ↓                    ↓                    ↓             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Market Data  │←───│ Risk Manager │←───│ Position     │      │
│  │ Processor    │    │              │    │ Tracker      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Monitoramento contínuo de odds
- Execução automática de estratégias
- Gestão de risco em tempo real
- Logging detalhado

### 7.2 Estratégias Automatizadas

**Back-to-Lay Automático:**

```
Condição:
- Odd BACK < Odd Threshold
- Expected drop > X%

Ação:
1. Executar BACK
2. Monitorar odd
3. Se odd cair Y%, executar LAY para green
4. Se sobe Z%, executar LAY para red
```

**Scalping Automático:**

```
Condição:
- Liquidez disponível > Threshold
- Volatilidade dentro de range

Ação:
1. Executar BACK
2. Aguardar X segundos
3. Se odd move Y%, executar LAY
4. Repetir
```

---

## 8. MELHORES PRÁTICAS

### 8.1 Pré-Trade

**Checklist:**
- [ ] Verificar liquidez disponível
- [ ] Calcular exposição total
- [ ] Confirmar odds estão corretas
- [ ] Verificar comissão aplicável
- [ ] Definir stop loss
- [ ] Definir take profit

### 8.2 Durante Trade

**Monitoramento:**
- Acompanhar movimentos de odds
- Verificar liquidez contínuamente
- Monitorar exposição
- Preparar plano de saída

### 8.3 Pós-Trade

**Análise:**
- Registrar resultado
- Analisar performance
- Identificar erros
- Ajustar estratégias

---

## 9. ERROS COMUNS

### 9.1 Erros de Execução

**Erro:** Não verificar liquidez
**Consequência:** Ordem parcialmente matched
**Solução:** Verificar depth of market antes de executar

**Erro:** Calcular stake incorretamente
**Consequência:** Exposição maior que esperado
**Solução:** Usar calculadora e verificar duas vezes

**Erro:** Esquecer comissão
**Consequência:** Lucro menor que esperado
**Solução:** Incluir comissão em todos os cálculos

### 9.2 Erros de Estratégia

**Erro:** Overtrading
**Consequência:** Comissões acumulativas
**Solução:** Limitar número de trades por dia

**Erro:** Não definir stop loss
**Consequência:** Perdas grandes
**Solução:** Sempre definir stop loss

**Erro:** Ignorar psicológico
**Consequência:** Decisões emocionais
**Solução:** Seguir regras estritamente

---

## 10. CONCLUSÃO

**Princípios Fundamentais:**

1. **Trading é sobre gestão de risco, não previsão**
2. **Timing é crítico - segundos importam**
3. **Liquidez é rei - sem liquidez, não há trade**
4. **Comissões acumulam - considere em cada trade**
5. **Psicologia importa - siga regras estritamente**

**Estratégias por Nível:**

| Nível | Estratégias | Foco |
|-------|-------------|------|
| Iniciante | Back-to-Lay, Lay-to-Back | Aprender mecânica |
| Intermediário | In-Play Trading, Hedging | Timing e gestão |
| Avançado | Scalping, Arbitragem | Automação e velocidade |

**Próximos Passos:**
- Praticar em sandbox
- Começar com stakes pequenos
- Automatizar gradualmente
- Escalar com sucesso

---

## 11. LINKS CRUZADOS

- [[44_Exchange_Execution/INDEX]] ← Seção mãe
- [[EXCHANGE_VS_BOOKMAKERS]] → Diferenças fundamentais
- [[LIQUIDITY_DEPTH]] → Liquidez e profundidade de mercado
- [[POSITION_MANAGEMENT]] → Gestão de posição detalhada
- [[EXCHANGE_COSTS]] → Custos de exchange
- [[BETFAIR_EXECUTION]] → Execução via API