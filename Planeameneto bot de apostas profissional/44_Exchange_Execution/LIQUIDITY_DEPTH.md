# LIQUIDITY_DEPTH — Liquidez e Profundidade de Mercado

**ID:** `EXE-005` | **Fase:** #phase/7 | **Owner:** Trading Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar conceitos de liquidez e profundidade de mercado em exchanges como Betfair. Liquidez é o fator mais crítico para execução bem-sucedida - sem liquidez, não há execução.

**Princípio:** Liquidez determina o que é possível executar, a que preço, e com que slippage.

---

## 2. CONCEITOS FUNDAMENTAIS

### 2.1 O que é Liquidez?

**Definição:** Quantidade de dinheiro disponível para ser matched a um determinado preço.

**Analogia:** Pense no mercado de ações:
- Alta liquidez = Ação da Apple (milhões transacionados por dia)
- Baixa liquidez = Penny stock (poucas transações)

**Em Exchanges:**
- Liquidez = Volume disponível no livro de ordens
- Determina quanto pode apostar a um dado preço
- Afeta slippage e custo de execução

### 2.2 Livro de Ordens (Order Book)

**Estrutura:**

```
BACK (Comprar)          ODD          LAY (Vender)

          $500 @ 1.98
          $1,000 @ 1.97
          $2,000 @ 1.96
          $5,000 @ 1.95
                        2.00 ← Current Price
          $5,000 @ 2.05
          $2,000 @ 2.06
          $1,000 @ 2.07
          $500 @ 2.08
```

**Componentes:**
- **BACK:** Ordens de compra (a favor)
- **LAY:** Ordens de venda (contra)
- **Odd:** Preço do contrato
- **Volume:** Quantidade disponível

**Leitura:**
- Para BACK @ 2.00: melhor odd disponível é 2.05
- Para LAY @ 2.00: melhor odd disponível é 1.95
- Spread: 2.05 - 1.95 = 0.10 (5%)

### 2.3 Depth of Market

**Definição:** Volume disponível em diferentes níveis de preço.

**Exemplo de Depth:**

```
Odd BACK   Volume Acumulado
1.95       $5,000
1.96       $7,000 ($5,000 + $2,000)
1.97       $8,000 ($7,000 + $1,000)
1.98       $8,500 ($8,000 + $500)
```

**Implicações:**
- Apostar $3,000 @ 1.97: executado imediatamente
- Apostar $10,000 @ 1.97: $8,000 matched, $2,000 unmatched
- Apostar $10,000 @ 1.96: executado imediatamente (com slippage)

---

## 3. MÉTRICAS DE LIQUIDEZ

### 3.1 Available to Back/Lay

**Definição:** Volume disponível nos melhores preços.

**Exemplo:**

```
BACK @ 2.00: $10,000 disponível
LAY @ 2.00: $8,000 disponível

Significado:
- Pode apostar até $10,000 em BACK @ 2.00 (execução imediata)
- Pode apostar até $8,000 em LAY @ 2.00 (execução imediata)
```

**Uso Prático:**
- Verificar se stake cabe na liquidez
- Determinar tamanho máximo de aposta
- Avaliar facilidade de entrada/saída

### 3.2 Total Matched

**Definição:** Volume total já transacionado no mercado.

**Exemplo:**

```
Total Matched: $1,000,000

Significado:
- Mercado ativo
- Muitos participantes
- Liquidez provavelmente boa
```

**Uso Prático:**
- Identificar mercados ativos
- Comparar popularidade de eventos
- Filtrar mercados para trading

### 3.3 Spread

**Definição:** Diferença entre melhor BACK e melhor LAY.

**Cálculo:**

```
Spread = Odd LAY - Odd BACK

Exemplo:
Melhor BACK: 1.98
Melhor LAY: 2.02
Spread: 2.02 - 1.98 = 0.04 (2%)
```

**Interpretação:**

| Spread | Eficiência | Implicação |
|--------|------------|------------|
| < 0.01 | Alta | Mercado muito eficiente |
| 0.01-0.03 | Média-Alta | Mercado eficiente |
| 0.03-0.05 | Média | Mercado razoável |
| 0.05-0.10 | Média-Baixa | Mercado ineficiente |
| > 0.10 | Baixa | Mercado pouco eficiente |

**Uso Prático:**
- Avaliar eficiência de mercado
- Estimar custo de round-trip
- Identificar oportunidades de arbitragem

### 3.4 Volatilidade

**Definição:** Velocidade de mudança das odds.

**Exemplo:**

```
Tempo 0: Odd 2.00
Tempo 10s: Odd 2.05
Tempo 20s: Odd 1.95
Tempo 30s: Odd 2.10

Volatilidade: Alta (mudança de 0.15 em 30s)
```

**Impacto na Liquidez:**
- Alta volatilidade → Liquidez pode evaporar
- Baixa volatilidade → Liquidez mais estável

**Uso Prático:**
- Determinar timing de execução
- Avaliar risco de slippage
- Calibrar estratégias de trading

---

## 4. PADRÕES DE LIQUIDEZ

### 4.1 Por Tipo de Mercado

**Mercados Pré-Jogo:**

| Tipo | Liquidez Típica | Padrão |
|------|-----------------|--------|
| Premier League | $1M+ | Muito alta, estável |
| NBA | $500K-$1M | Alta, estável |
| Liga Portuguesa | $50K-$100K | Média, estável |
| Esportes menores | $1K-$10K | Baixa, volátil |

**Mercados In-Play:**

| Tipo | Liquidez Típica | Padrão |
|------|-----------------|--------|
| Futebol (gols) | $100K-$500K | Alta, volátil |
| Basketball (pontos) | $50K-$200K | Média-alta, muito volátil |
| Tênis (pontos) | $10K-$50K | Média, extremamente volátil |
| Esportes de nicho | $100-$1K | Baixa, imprevisível |

### 4.2 Por Tempo

**Pré-Jogo:**

```
7 dias antes: Liquidez baixa
3 dias antes: Liquidez começa a aumentar
1 dia antes: Liquidez significativa
1 hora antes: Liquidez pico
Minutos antes: Liquidez máxima
```

**In-Play:**

```
Início: Liquidez alta
Durante jogo: Liquidez varia com eventos
Próximo ao fim: Liquidez diminui
Últimos minutos: Liquidez evapora
```

### 4.3 Por Evento

**Eventos que Aumentam Liquidez:**
- Gols em futebol
- Lesões de jogadores chave
- Mudanças de lineup
- Notícias importantes

**Eventos que Diminuem Liquidez:**
- Intervalo
- Fim de período
- Suspensões
- Tempo expirado

---

## 5. IMPACTO NA EXECUÇÃO

### 5.1 Slippage

**Definição:** Diferença entre odd desejada e odd executada.

**Exemplo:**

```
Odd desejada: 2.00
Liquidez @ 2.00: $5,000
Stake: $10,000

Execução:
- $5,000 @ 2.00 (matched imediatamente)
- $5,000 @ 2.05 (slippage de 2.5%)

Odd média: 2.025
Slippage: 1.25%
```

**Cálculo de Slippage:**

```
Slippage % = (Odd Executada - Odd Desejada) / Odd Desejada × 100

Exemplo:
Odd Desejada: 2.00
Odd Executada: 2.05

Slippage = (2.05 - 2.00) / 2.00 × 100 = 2.5%
```

**Fatores que Afetam Slippage:**
- Tamanho do stake relativo à liquidez
- Volatilidade do mercado
- Velocidade de execução
- Tipo de ordem (limit vs market)

### 5.2 Partial Fills

**Definição:** Ordem parcialmente executada.

**Exemplo:**

```
Ordem: BACK $10,000 @ 2.00
Liquidez @ 2.00: $5,000

Resultado:
- $5,000 matched @ 2.00
- $5,000 unmatched (fica no livro)

Opções:
1. Esperar por mais liquidez
2. Aceitar pior odd
3. Cancelar parte unmatched
```

**Gestão de Partial Fills:**

```
Estratégia 1 - Esperar:
- Vantagem: Pode conseguir odd desejada
- Desvantagem: Risco de não ser matched

Estratégia 2 - Pegar Pior Odd:
- Vantagem: Execução garantida
- Desvantagem: Slippage

Estratégia 3 - Cancelar:
- Vantagem: Evita exposição parcial
- Desvantagem: Perde oportunidade
```

### 5.3 Unmatched Bets

**Definição:** Ordens não executadas que ficam no livro.

**Exemplo:**

```
Ordem: BACK $10,000 @ 1.90
Liquidez @ 1.90: $2,000

Resultado:
- $2,000 matched @ 1.90
- $8,000 unmatched (fica no livro @ 1.90)

Riscos:
- Pode nunca ser matched
- Odd pode mover desfavoravelmente
- Capital fica travado
```

**Gestão de Unmatched Bets:**

```
Estratégia 1 - Timeout:
- Cancelar após X segundos
- Libertar capital
- Tentar nova odd

Estratégia 2 - Ajuste Dinâmico:
- Ajustar odd se mercado mover
- Aumentar chance de matching
- Aceitar mais slippage

Estratégia 3 - Keep Alive:
- Manter ordem até ser matched
- Risco de capital travado
- Apenas se confiança alta
```

---

## 6. AVALIAÇÃO DE LIQUIDEZ

### 6.1 Checklist Pré-Execução

**Antes de Executar:**

```
□ Liquidez suficiente para stake?
  - Stake < 50% da liquidez disponível

□ Spread aceitável?
  - Spread < 0.05 para mercados líquidos
  - Spread < 0.10 para mercados menos líquidos

□ Volatilidade controlada?
  - Odd não mudou > 5% nos últimos 30s
  - Liquidez estável nos últimos 60s

□ Total matched adequado?
  - > $100K para mercados principais
  - > $10K para mercados secundários

□ Depth suficiente?
  - Pelo menos 3 níveis de profundidade
  - Volume acumulado > 2× stake
```

### 6.2 Cálculo de Stake Máximo

**Fórmula Conservadora:**

```
Stake Máximo = Liquidez Disponível × 0.30

Exemplo:
Liquidez @ 2.00: $10,000
Stake Máximo: $3,000

Justificativa:
- Deixa espaço para erro
- Permite ajustes dinâmicos
- Reduz slippage
```

**Fórmula Moderada:**

```
Stake Máximo = Liquidez Disponível × 0.50

Exemplo:
Liquidez @ 2.00: $10,000
Stake Máximo: $5,000

Justificativa:
- Balanceia risco e oportunidade
- Ainda permite ajustes
- Slippage moderado
```

**Fórmula Agressiva:**

```
Stake Máximo = Liquidez Disponível × 0.80

Exemplo:
Liquidez @ 2.00: $10,000
Stake Máximo: $8,000

Justificativa:
- Maximiza oportunidade
- Alto risco de slippage
- Apenas para oportunidades excepcionais
```

### 6.3 Thresholds por Mercado

**Mercados Líquidos (Premier League, NBA):**

| Métrica | Threshold |
|---------|-----------|
| Available to Back/Lay | > $50,000 |
| Total Matched | > $500,000 |
| Spread | < 0.03 |
| Stake Máximo | Até 50% da liquidez |

**Mercados Moderadamente Líquidos (Liga Portuguesa):**

| Métrica | Threshold |
|---------|-----------|
| Available to Back/Lay | > $10,000 |
| Total Matched | > $50,000 |
| Spread | < 0.05 |
| Stake Máximo | Até 30% da liquidez |

**Mercados Pouco Líquidos (Esportes menores):**

| Métrica | Threshold |
|---------|-----------|
| Available to Back/Law | > $2,000 |
| Total Matched | > $5,000 |
| Spread | < 0.10 |
| Stake Máximo | Até 20% da liquidez |

---

## 7. ESTRATÉGIAS DE EXECUÇÃO

### 7.1 Iceberg Orders

**Conceito:** Dividir ordem grande em múltiplas ordens menores.

**Exemplo:**

```
Ordem original: BACK $10,000 @ 2.00
Liquidez @ 2.00: $5,000

Estratégia Iceberg:
1. BACK $5,000 @ 2.00 (matched imediatamente)
2. BACK $2,500 @ 2.00 (fica no livro)
3. BACK $2,500 @ 2.00 (fica no livro)
4. Se mais liquidez aparecer, executar
```

**Vantagens:**
- Reduz slippage
- Menos impacto no mercado
- Mais chances de execução

**Desvantagens:**
- Mais complexo
- Pode não ser totalmente executado
- Requer monitoramento contínuo

### 7.2 TWAP (Time-Weighted Average Price)

**Conceito:** Executar ordem ao longo do tempo.

**Exemplo:**

```
Ordem: BACK $10,000 @ ~2.00
Período: 5 minutos

Estratégia TWAP:
1. Minuto 1: BACK $2,000 @ melhor odd disponível
2. Minuto 2: BACK $2,000 @ melhor odd disponível
3. Minuto 3: BACK $2,000 @ melhor odd disponível
4. Minuto 4: BACK $2,000 @ melhor odd disponível
5. Minuto 5: BACK $2,000 @ melhor odd disponível

Resultado: Odd média próxima de 2.00
```

**Vantagens:**
- Reduz impacto no mercado
- Odd média mais previsível
- Menos slippage

**Desvantagens:**
- Mais lento
- Odd pode mover desfavoravelmente
- Requer automação

### 7.3 VWAP (Volume-Weighted Average Price)

**Conceito:** Executar baseado no volume disponível.

**Exemplo:**

```
Ordem: BACK $10,000
Livro de ordens:
- $5,000 @ 2.00
- $3,000 @ 2.05
- $2,000 @ 2.10

Estratégia VWAP:
1. BACK $5,000 @ 2.00 (100% da liquidez)
2. BACK $3,000 @ 2.05 (100% da liquidez)
3. BACK $2,000 @ 2.10 (100% da liquidez)

Odd média: (5,000×2.00 + 3,000×2.05 + 2,000×2.10) / 10,000
Odd média: 2.035
```

**Vantagens:**
- Maximiza execução
- Odd média previsível
- Eficiente para ordens grandes

**Desvantagens:**
- Slippage garantido
- Pode não ser ideal para value betting

---

## 8. MONITORAMENTO DE LIQUIDEZ

### 8.1 Métricas em Tempo Real

**Dashboard de Liquidez:**

```
┌─────────────────────────────────────────────────────────────────┐
│ DASHBOARD DE LIQUIDEZ - Lakers vs Warriors                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Available to Back @ 2.00:    $15,234  ████████████████░░░░     │
│ Available to Lay @ 2.00:     $12,456  ███████████████░░░░░     │
│ Total Matched:               $856,234 ████████████████████     │
│ Spread:                      0.02     ████░░░░░░░░░░░░░░░░░   │
│ Volatilidade (1m):           1.2%     ████░░░░░░░░░░░░░░░░░   │
│                                                                  │
│ Depth:                                                         │
│ Level 1 (±0.01):  $27,690  ████████████████████░░             │
│ Level 2 (±0.02):  $45,123  ███████████████████████            │
│ Level 3 (±0.03):  $62,456  █████████████████████████           │
│                                                                  │
│ Recomendação: STAKE MÁXIMO $7,500 (50% da liquidez)            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Alertas de Liquidez

**Alertas Configuráveis:**

```
□ Liquidez cai abaixo de threshold
  - Ação: Parar novas ordens

□ Spread aumenta acima de threshold
  - Ação: Aumentar tolerância de slippage

□ Volatilidade acima de threshold
  - Ação: Reduzir stake máximo

□ Liquidez desaparece rapidamente
  - Ação: Cancelar ordens pendentes
```

---

## 9. MELHORES PRÁTICAS

### 9.1 Antes da Execução

**Checklist:**
- [ ] Verificar liquidez disponível
- [ ] Calcular stake máximo
- [ ] Verificar spread
- [ ] Avaliar volatilidade
- [ ] Definir estratégia de execução
- [ ] Configurar alertas

### 9.2 Durante Execução

**Monitoramento:**
- Acompanhar liquidez em tempo real
- Monitorar slippage
- Verificar status da ordem
- Preparar plano B

### 9.3 Após Execução

**Análise:**
- Registrar slippage real
- Comparar com esperado
- Ajustar thresholds
- Otimizar estratégias

---

## 10. ERROS COMUNS

### 10.1 Ignorar Liquidez

**Erro:** Apostar sem verificar liquidez
**Consequência:** Ordem não executada ou slippage alto
**Solução:** Sempre verificar liquidez antes de executar

### 10.2 Overestimar Liquidez

**Erro:** Assumir que liquidez vai aparecer
**Consequência:** Ordem unmatched por longo tempo
**Solução:** Basear-se na liquidez atual, não esperada

### 10.3 Ignorar Volatilidade

**Erro:** Não considerar volatilidade
**Consequência:** Slippage inesperado
**Solução:** Avaliar volatilidade antes de executar

### 10.4 Não Usar Depth

**Erro:** Olhar apenas para melhor odd
**Consequência:** Liquidez insuficiente para stake
**Solução:** Verificar depth completo do livro

---

## 11. CONCLUSÃO

**Princípios Fundamentais:**

1. **Liquidez é rei** - Sem liquidez, não há execução
2. **Slippage é inevitável** - Planeje para ele
3. **Depth importa** - Não olhe apenas para melhor odd
4. **Volatilidade afeta liquidez** - Considere o timing
5. **Menos é mais** - Stake conservador é melhor

**Regras de Ouro:**

| Regra | Detalhe |
|-------|---------|
| Liquidez | Stake < 50% da liquidez disponível |
| Spread | Executar apenas se spread < threshold |
| Volatilidade | Reduzir stake se volatilidade alta |
| Depth | Verificar pelo menos 3 níveis |
| Monitoramento | Acompanhar liquidez em tempo real |

**Próximos Passos:**
- Implementar dashboard de liquidez
- Configurar alertas automáticos
- Desenvolver estratégias de execução
- Otimizar com dados históricos

---

## 12. LINKS CRUZADOS

- [[44_Exchange_Execution/INDEX]] ← Seção mãe
- [[EXCHANGE_VS_BOOKMAKERS]] → Diferenças fundamentais
- [[EXCHANGE_TRADING]] → Estratégias de trading
- [[POSITION_MANAGEMENT]] → Gestão de posição
- [[BETFAIR_EXECUTION]] → Execução via API
- [[LATENCY_OPTIMIZATION]] → Latência e execução em tempo real