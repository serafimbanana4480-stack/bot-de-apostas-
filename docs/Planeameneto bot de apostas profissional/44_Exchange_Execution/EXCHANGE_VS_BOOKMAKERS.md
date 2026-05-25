# EXCHANGE_VS_BOOKMAKERS — Diferenças Fundamentais

**ID:** `EXE-003` | **Fase:** #phase/7 | **Owner:** Trading Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar as diferenças fundamentais entre apostar em bookmakers tradicionais e exchanges como Betfair. Compreender estas diferenças é crítico para desenvolver estratégias de value betting e trading adequadas.

**Princípio:** Exchanges são mercados de peer-to-peer, não casas de aposta. A dinâmica é completamente diferente.

---

## 2. ARQUITETURA DE MERCADO

### 2.1 Bookmaker Tradicional

**Modelo:** House vs Player

```
┌─────────────────────────────────────────────────────────────────┐
│ BOOKMAKER TRADICIONAL                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  JOGADOR A          BOOKMAKER          JOGADOR B                 │
│     │                  │                   │                     │
│     │  Aposta $100     │                   │                     │
│     │─────────────────>│                   │                     │
│     │                  │                   │                     │
│     │                  │  Aposta $100      │                     │
│     │                  │<─────────────────│                     │
│     │                  │                   │                     │
│     │                  │  Retém margem     │                     │
│     │                  │  (5-15%)          │                     │
│     │                  │                   │                     │
│     │                  │  Se A ganha:      │                     │
│     │  Paga $190       │─────────────────>│                     │
│     │<─────────────────│                   │                     │
│     │                  │                   │                     │
│     │                  │  Se B ganha:      │                     │
│     │                  │─────────────────>│  Paga $190          │
│     │                  │                   │<─────────────────│  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Características:**
- Bookmaker define as odds
- Bookmaker assume o risco
- Margem embutida nas odds (overround)
- Apostas fixas (não pode alterar após colocação)
- Limite de stake definido pelo bookmaker
- Contas podem ser limitadas/bloqueadas

### 2.2 Exchange (Betfair)

**Modelo:** Peer-to-Peer

```
┌─────────────────────────────────────────────────────────────────┐
│ EXCHANGE (BETFAIR)                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  JOGADOR A          EXCHANGE           JOGADOR B                 │
│     │                  │                   │                     │
│     │  BACK $100 @ 2.0 │                   │                     │
│     │─────────────────>│                   │                     │
│     │                  │                   │                     │
│     │                  │  MATCHING ENGINE  │                     │
│     │                  │                   │                     │
│     │                  │  LAY $100 @ 2.0   │                     │
│     │                  │<─────────────────│                     │
│     │                  │                   │                     │
│     │                  │  MATCH EXECUTED   │                     │
│     │                  │                   │                     │
│     │  ← $200          │                   │  → $0 (perdeu)      │
│     │  (ganhou)        │                   │                     │
│     │                  │  COBRA COMISSÃO   │                     │
│     │                  │  (5% sobre lucro)  │                     │
│     │                  │                   │                     │
│     │  ← $190          │                   │                     │
│     │  (líquido)       │                   │                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Características:**
- Usuários definem as odds (mercado)
- Exchange não assume risco (apenas facilita)
- Comissão sobre lucro (tipicamente 5%)
- Liquidez determinada por usuários
- Pode alterar/cancelar ordens antes de serem matched
- Stake limitado apenas pela liquidez disponível
- Sem limitações de conta (baseado em volume)

---

## 3. CONCEITOS FUNDAMENTAIS

### 3.1 Back vs Lay

**BACK (A favor):**
- Aposta que um resultado ocorrerá
- Equivalente a apostar em bookmaker tradicional
- Exemplo: "Aposto que o Lakers vai ganhar"

**LAY (Contra):**
- Aposta que um resultado NÃO ocorrerá
- Age como bookmaker
- Exemplo: "Aposto que o Lakers NÃO vai ganhar" (ou seja, vai perder ou empatar)

**Exemplo Prático:**

```
BACK Lakers @ 2.0 com $100:
- Se Lakers ganhar: lucro $100
- Se Lakers perder/perder: perda $100

LAY Lakers @ 2.0 com $100:
- Se Lakers ganhar: perda $100
- Se Lakers não ganhar: lucro $100
```

### 3.2 Odds Decimais

**Formato:** Decimal (1.01 - 1000+)

| Odd Decimal | Probabilidade Implícita | Lucro por $100 |
|-------------|------------------------|----------------|
| 1.01 | 99.0% | $1 |
| 1.50 | 66.7% | $50 |
| 2.00 | 50.0% | $100 |
| 3.00 | 33.3% | $200 |
| 5.00 | 20.0% | $400 |
| 10.00 | 10.0% | $900 |

**Cálculo de Probabilidade:**
```
Probabilidade Implícita = 1 / Odd Decimal

Exemplo:
Odd 2.00 → 1/2 = 50%
Odd 3.00 → 1/3 = 33.3%
```

### 3.3 Overround vs Commission

**Bookmaker (Overround):**

```
Jogo: Team A vs Team B

Odds Bookmaker:
- Team A: 1.90 (52.6%)
- Team B: 2.10 (47.6%)
Total: 100.2%

Margem: 0.2% (mas na prática é 5-15%)
```

**Exchange (Comissão):**

```
Jogo: Team A vs Team B

Odds Exchange (sem comissão):
- Team A: 2.00 (50.0%)
- Team B: 2.00 (50.0%)
Total: 100.0%

Comissão: 5% sobre lucro

Se apostar $100 em Team A @ 2.00:
- Lucro bruto: $100
- Comissão (5%): $5
- Lucro líquido: $95
```

**Comparação de Custo:**

| Cenário | Bookmaker (5% margin) | Exchange (5% comissão) | Diferença |
|---------|----------------------|------------------------|-----------|
| Apostar $100 @ 2.00 | Lucro $90 | Lucro $95 | +$5 |
| Apostar $100 @ 3.00 | Lucro $180 | Lucro $185 | +$5 |
| Apostar $100 @ 10.00 | Lucro $850 | Lucro $855 | +$5 |

**Observação:** Exchange geralmente oferece melhor valor, especialmente em odds altas.

---

## 4. LIQUIDEZ E MERCADO

### 4.1 Depth of Market

**Bookmaker:**
- Liquidez ilimitada (teoricamente)
- Stake limitado por bookmaker
- Odds fixas independentemente do volume

**Exchange:**
- Liquidez limitada pelos usuários
- Stake limitado pela liquidez disponível
- Odds variam com volume

**Exemplo de Livro de Ordens Betfair:**

```
BACK (Comprar)          ODD          LAY (Vender)

          $500 @ 1.98
          $1,000 @ 1.97
          $2,000 @ 1.96
          $5,000 @ 1.95
                        2.00
          $5,000 @ 2.05
          $2,000 @ 2.06
          $1,000 @ 2.07
          $500 @ 2.08
```

**Leitura:**
- Para BACK @ 2.00: liquidez disponível = $5,000
- Para LAY @ 2.00: liquidez disponível = $5,000
- Spread: 2.00 (back) - 2.00 (lay) = 0 (mercado eficiente)
- Se quiser apostar $10,000 @ 2.00: só $5,000 será matched imediatamente

### 4.2 Tipos de Liquidez

**Liquidez Imediata (Available to Back/Lay):**
- Ordens já no livro
- Execução instantânea
- Odd atual do mercado

**Liquidez Latente (Unmatched):**
- Ordens não matched
- Execução não garantida
- Odd pode ser melhor/ pior

**Exemplo:**

```
Situação: Quero apostar $10,000 em Team A @ 2.00

Liquidez disponível @ 2.00: $5,000

Opção 1 - Execução Parcial:
- $5,000 matched @ 2.00 (imediato)
- $5,000 unmatched (fica no livro)

Opção 2 - Pegar Pior Odd:
- $10,000 matched @ 2.05 (slippage de 2.5%)

Opção 3 - Esperar:
- Colocar $10,000 @ 2.00
- Esperar por mais liquidez
- Risco de não ser matched
```

---

## 5. GESTÃO DE ORDEM

### 5.1 Bookmaker

**Processo:**
1. Seleciona odd
2. Insere stake
3. Confirma
4. **Ordem é final** (não pode cancelar)
5. Aguarda resultado

**Limitações:**
- Não pode cancelar após confirmação
- Não pode alterar odd
- Não pode fazer partial fill
- Stake limitado pelo bookmaker

### 5.2 Exchange

**Processo:**
1. Seleciona odd (ou define odd própria)
2. Insere stake
3. Escolhe tipo de ordem (Limit, Market, etc.)
4. Confirma
5. **Ordem pode ser cancelada/modificada** até ser matched
6. Aguarda matching ou resultado

**Opções:**
- Cancelar ordem unmatched
- Modificar odd/stake
- Parcial fills aceitos
- Stake limitado apenas pela liquidez

**Estados de Ordem:**

```
PENDING → Submitted, aguardando matching
   ↓
PARTIALLY MATCHED → Parte matched, parte unmatched
   ↓
FULLY MATCHED → Ordem completada
   ↓
SETTLED → Resultado finalizado

ou

PENDING → CANCELLED → Ordem cancelada pelo usuário
   ↓
EXPIRED → Timeout atingido
```

---

## 6. RISCO E EXPOSIÇÃO

### 6.1 Bookmaker

**Risco:** Limitado ao stake

```
Aposta $100 em Team A @ 2.00:
- Risco máximo: $100
- Lucro potencial: $90 (após margem)
```

**Exposição:** Sempre conhecida antecipadamente

### 6.2 Exchange

**Risco BACK:** Limitado ao stake

```
BACK $100 em Team A @ 2.00:
- Risco máximo: $100
- Lucro potencial: $100 (antes de comissão)
```

**Risco LAY:** Variável dependendo da odd

```
LAY $100 em Team A @ 2.00:
- Risco máximo: $100 (se Team A ganhar)
- Lucro potencial: $100 (se Team A não ganhar)

LAY $100 em Team A @ 10.00:
- Risco máximo: $900 (se Team A ganhar)
- Lucro potencial: $100 (se Team A não ganhar)
```

**Cálculo de Exposição LAY:**

```
Exposição LAY = Stake × (Odd - 1)

Exemplo:
LAY $100 @ 2.00 → $100 × (2.00 - 1) = $100
LAY $100 @ 3.00 → $100 × (3.00 - 1) = $200
LAY $100 @ 10.00 → $100 × (10.00 - 1) = $900
```

---

## 7. HEDGING E TRADING

### 7.1 Bookmaker

**Hedging:** Limitado
- Não pode fazer lay
- Hedging requer outra bookmaker
- Geralmente não eficiente

**Trading:** Não possível
- Não pode sair de posição
- Ordem é final

### 7.2 Exchange

**Hedging:** Nativo
- Pode fazer back e lay no mesmo mercado
- Garantir lucro independentemente do resultado

**Exemplo de Hedging:**

```
Cenário: Apostou BACK $100 em Team A @ 3.00
Odd atual: Team A @ 2.00

Passo 1 - Calcular lay para green:
Lucro potencial original: $200
Nova odd: 2.00

Stake LAY = Lucro potencial / (Nova Odd - 1)
Stake LAY = $200 / (2.00 - 1) = $200

Passo 2 - Executar LAY:
LAY $200 em Team A @ 2.00

Resultado:
- Se Team A ganhar: BACK $200 - LAY $200 = $0
- Se Team A perder: LAY $200 - BACK $100 = $100

Lucro garantido: $100 (independentemente do resultado)
```

**Trading:** Possível
- Pode entrar e sair de posições
- Lucrar com movimentos de odds
- Scalping em mercados rápidos

---

## 8. CUSTOS E TAXAS

### 8.1 Bookmaker

**Custos:**
- Margem embutida nas odds (5-15%)
- Sem taxas adicionais
- Sem comissão sobre lucro

**Custo Total:** Margem da odd

### 8.2 Exchange

**Custos:**
- Comissão sobre lucro (tipicamente 5%)
- Premium charge (para apostadores de alto volume)
- Sem margem embutida

**Custo Total:** Comissão sobre lucro

**Comparação:**

| Cenário | Bookmaker (10% margin) | Exchange (5% comissão) | Diferença |
|---------|----------------------|------------------------|-----------|
| Apostar $100 @ 2.00 | Lucro $80 | Lucro $95 | +$15 |
| Apostar $100 @ 3.00 | Lucro $170 | Lucro $185 | +$15 |
| Apostar $100 @ 10.00 | Lucro $800 | Lucro $855 | +$55 |

**Observação:** Exchange é significativamente mais barato em odds altas.

---

## 9. LIMITAÇÕES E RESTRIÇÕES

### 9.1 Bookmaker

**Limitações:**
- Contas podem ser limitadas
- Contas podem ser bloqueadas
- Stake máximo por aposta
- Odds podem ser alteradas unilateralmente
- Não pode apostar contra resultados

**Mitigação:**
- Usar múltiplas bookmakers
- Rotacionar contas
- Evitar padrões suspeitos

### 9.2 Exchange

**Limitações:**
- Liquidez limitada em mercados pequenos
- Premium charge para high rollers
- Requer licenciamento
- Curva de aprendizado mais íngreme

**Mitigação:**
- Focar em mercados líquidos
- Gerenciar volume para evitar premium charge
- Treinar em sandbox antes de real money

---

## 10. QUANDO USAR CADA UM

### 10.1 Bookmaker

**Ideal para:**
- Apostadores casuais
- Mercados sem liquidez em exchange
- Apostas simples (back only)
- Stake baixo

**Não ideal para:**
- Value betting sistemático
- Trading de odds
- Apostas de alto volume
- Estratégias complexas

### 10.2 Exchange

**Ideal para:**
- Value betting sistemático
- Trading de odds
- Hedging de posições
- Apostas de alto volume
- Estratégias complexas

**Não ideal para:**
- Apostadores casuais
- Mercados sem liquidez
- Stake muito baixo (comissão pode ser proporcionalmente alta)

---

## 11. IMPLICAÇÕES PARA VALUE BETTING

### 11.1 Detecção de Value

**Bookmaker:**
- Value = (Probabilidade Real × Odd Bookmaker) - 1
- Margem já embutida na odd
- Comparação com odds de referência

**Exchange:**
- Value = (Probabilidade Real × Odd Exchange) - 1 - Comissão
- Sem margem embutida
- Odds mais próximas da probabilidade real

### 11.2 Execução

**Bookmaker:**
- Execução imediata (se stake aceito)
- Sem slippage
- Ordem final

**Exchange:**
- Execução não garantida (depende de liquidez)
- Slippage possível
- Ordem pode ser cancelada

### 11.3 Gestão de Bankroll

**Bookmaker:**
- Mais simples (stake fixo)
- Menor risco (exposição conhecida)
- Mais previsível

**Exchange:**
- Mais complexo (variável)
- Maior risco (exposição LAY)
- Menos previsível

---

## 12. CONCLUSÃO

**Principais Diferenças:**

| Aspecto | Bookmaker | Exchange |
|---------|-----------|----------|
| Modelo | House vs Player | Peer-to-Peer |
| Odds | Definidas por bookmaker | Definidas por mercado |
| Margem | 5-15% embutida | 5% comissão sobre lucro |
| Liquidez | Ilimitada (teórica) | Limitada por usuários |
| Ordem | Final | Pode cancelar/modificar |
| Hedging | Limitado | Nativo |
| Trading | Não possível | Possível |
| Limitações | Contas podem ser limitadas | Liquidez limitada |
| Custo | Margem da odd | Comissão sobre lucro |

**Recomendação:**
- Para value betting sistemático: **Exchange é superior**
- Para apostas casuais: **Bookmaker é mais simples**
- Para trading de odds: **Apenas exchange**
- Para hedging: **Apenas exchange**

---

## 13. LINKS CRUZADOS

- [[44_Exchange_Execution/INDEX]] ← Seção mãe
- [[EXCHANGE_TRADING]] → Estratégias de trading em exchanges
- [[LIQUIDITY_DEPTH]] → Liquidez e profundidade de mercado
- [[POSITION_MANAGEMENT]] → Gestão de posição
- [[EXCHANGE_COSTS]] → Custos detalhados de exchange
- [[45_Bookmaker_Analysis/INDEX]] → Análise de bookmakers