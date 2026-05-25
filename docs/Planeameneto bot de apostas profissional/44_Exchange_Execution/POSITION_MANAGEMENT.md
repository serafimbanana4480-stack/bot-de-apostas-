# POSITION_MANAGEMENT — Gestão de Posição em Exchanges

**ID:** `EXE-006` | **Fase:** #phase/7-12 | **Owner:** Trading Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar estratégias e práticas para gestão de posição em exchanges como Betfair, incluindo unmatched bets, partial fills, e técnicas de gestão de risco. Gestão de posição é a diferença entre lucro consistente e ruína.

**Princípio:** Cada posição deve ser monitorada, gerida, e fechada estrategicamente.

---

## 2. ESTADOS DE ORDEM

### 2.1 Ciclo de Vida de uma Ordem

```
┌─────────────────────────────────────────────────────────────────┐
│ CICLO DE VIDA DE UMA ORDEM BETFAIR                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SUBMITTED                                                       │
│     │                                                            │
│     ├──→ PENDING (aguardando matching)                           │
│     │        │                                                   │
│     │        ├──→ PARTIALLY MATCHED                              │
│     │        │        │                                          │
│     │        │        ├──→ FULLY MATCHED                         │
│     │        │        │        │                                 │
│     │        │        │        └──→ SETTLED (resultado final)    │
│     │        │        │                                          │
│     │        │        └──→ CANCELLED (usuário cancela)           │
│     │        │                                                   │
│     │        └──→ CANCELLED (usuário cancela)                    │
│     │                                                            │
│     └──→ EXECUTION_COMPLETE (imediatamente matched)              │
│              │                                                   │
│              └──→ SETTLED (resultado final)                      │
│                                                                  │
│  Estados de Erro:                                                 │
│  - REJECTED (ordem rejeitada)                                    │
│  - EXPIRED (timeout)                                             │
│  - LAPSED (mercado fechado)                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Descrição dos Estados

**SUBMITTED:**
- Ordem enviada para Betfair
- Aguardando confirmação
- Pode mudar para PENDING ou EXECUTION_COMPLETE

**PENDING:**
- Ordem confirmada, aguardando matching
- Ainda no livro de ordens
- Pode ser cancelada pelo usuário

**PARTIALLY MATCHED:**
- Parte da ordem foi executada
- Parte permanece no livro
- Pode continuar sendo matched ou ser cancelada

**FULLY MATCHED:**
- Ordem completamente executada
- Sai do livro de ordens
- Aguarda resultado do evento

**SETTLED:**
- Resultado do evento finalizado
- Lucro/perda calculado
- Posição fechada

**CANCELLED:**
- Ordem cancelada pelo usuário ou sistema
- Parte pode ter sido matched
- Restante do stake é devolvido

**REJECTED:**
- Ordem rejeitada pela Betfair
- Motivo: saldo insuficiente, mercado fechado, etc.
- Nenhuma execução ocorreu

**EXPIRED:**
- Ordem expirou por timeout
- Configurável pelo usuário
- Parte pode ter sido matched

**LAPSED:**
- Mercado foi fechado ou suspenso
- Ordem não pode ser executada
- Parte pode ter sido matched

---

## 3. UNMATCHED BETS

### 3.1 O que são Unmatched Bets?

**Definição:** Parte de uma ordem que não foi executada e permanece no livro de ordens.

**Exemplo:**

```
Ordem: BACK $10,000 @ 2.00
Liquidez @ 2.00: $5,000

Resultado:
- $5,000 matched @ 2.00 (executado)
- $5,000 unmatched (permanece no livro @ 2.00)
```

**Implicações:**
- Capital fica travado
- Risco de nunca ser matched
- Pode afetar outras operações

### 3.2 Causas Comuns

**Liquidez Insuficiente:**
```
Causa: Stake maior que liquidez disponível
Exemplo: Apostar $10,000 quando apenas $5,000 disponível
Solução: Verificar liquidez antes de executar
```

**Odd Desfavorável:**
```
Causa: Odd definida muito agressiva
Exemplo: BACK @ 1.90 quando mercado está em 2.00
Solução: Usar odd mais próxima do mercado
```

**Volatilidade Alta:**
```
Causa: Mercado move rapidamente
Exemplo: Odd era 2.00 quando submetido, agora é 2.10
Solução: Executar mais rápido ou usar ordens de mercado
```

**Tempo Errado:**
```
Causa: Executar em momento de baixa liquidez
Exemplo: Pré-jogo muito cedo ou in-play em momento calmo
Solução: Executar em momentos de alta liquidez
```

### 3.3 Estratégias de Gestão

**Estratégia 1 - Timeout Automático:**

```
Configuração:
- Timeout: 60 segundos
- Ação: Cancelar automaticamente

Vantagens:
- Capital não fica travado
- Permite reexecutar com nova odd
- Automático, sem intervenção

Desvantagens:
- Pode cancelar antes de matching
- Perde oportunidades
```

**Estratégia 2 - Ajuste Dinâmico:**

```
Configuração:
- Monitorar movimento de odd
- Ajustar odd se mercado mover
- Threshold: 1-2% de mudança

Vantagens:
- Aumenta chance de matching
- Adapta ao mercado
- Mantém posição

Desvantagens:
- Slippage
- Pode resultar em odd pior
```

**Estratégia 3 - Keep Alive:**

```
Configuração:
- Manter ordem até ser matched
- Sem timeout
- Apenas para oportunidades excepcionais

Vantagens:
- Maximiza chance de execução
- Mantém odd desejada

Desvantagens:
- Capital fica travado
- Risco de nunca ser matched
- Impede outras operações
```

**Estratégia 4 - Partial Acceptance:**

```
Configuração:
- Aceitar execução parcial
- Reexecutar remainder com nova odd
- Repetir até fully matched ou timeout

Vantagens:
- Maximiza execução
- Adapta ao mercado
- Flexível

Desvantagens:
- Complexo
- Múltiplas ordens
- Mais comissões
```

---

## 4. PARTIAL FILLS

### 4.1 O que são Partial Fills?

**Definição:** Ordem parcialmente executada, com parte matched e parte unmatched.

**Exemplo:**

```
Ordem: BACK $10,000 @ 2.00
Liquidez @ 2.00: $6,000

Resultado:
- $6,000 matched @ 2.00 (executado)
- $4,000 unmatched (permanece no livro @ 2.00)
```

**Implicações:**
- Exposição parcial
- Gestão mais complexa
- Decisões adicionais necessárias

### 4.2 Gestão de Partial Fills

**Opção 1 - Aceitar e Esperar:**

```
Ação: Manter $4,000 unmatched no livro

Vantagens:
- Pode conseguir odd desejada
- Simples

Desvantagens:
- Capital parcialmente travado
- Risco de não ser matched
```

**Opção 2 - Cancelar Remainder:**

```
Ação: Cancelar $4,000 unmatched

Vantagens:
- Libera capital
- Exposição controlada
- Pode reexecutar

Desvantagens:
- Perde parte da posição
- Menor stake executado
```

**Opção 3 - Pegar Pior Odd:**

```
Ação: LAY/BACK remainder a pior odd

Exemplo:
- $4,000 unmatched @ 2.00
- Aceitar @ 2.05 (slippage de 2.5%)

Vantagens:
- Execução completa
- Posição completa

Desvantagens:
- Slippage
- Odd pior
```

**Opção 4 - Reexecutar:**

```
Ação: Cancelar e reexecutar com nova odd

Exemplo:
- Cancelar $4,000 unmatched @ 2.00
- Reexecutar @ 2.02 (ajustado ao mercado)

Vantagens:
- Execução completa
- Odd ajustada ao mercado

Desvantagens:
- Mais complexo
- Pode não ser matched
```

### 4.3 Cálculo de Exposição em Partial Fills

**Exemplo:**

```
Ordem original: BACK $10,000 @ 2.00
Partial fill: $6,000 matched @ 2.00

Exposição atual:
- Matched: $6,00 @ 2.00
  - Se ganhar: +$6,000
  - Se perder: -$6,000
- Unmatched: $4,00 @ 2.00
  - Se matched: +$4,000 se ganhar, -$4,000 se perder
  - Se cancelado: $0

Exposição máxima (se remainder matched): $10,000
Exposição atual: $6,000
```

---

## 5. CANCELAMENTO E MODIFICAÇÃO

### 5.1 Cancelamento de Ordens

**Quando Cancelar:**

```
□ Odd move desfavoravelmente
  - Exemplo: BACK @ 2.00, mercado vai para 2.10
  - Ação: Cancelar e reexecutar ou abandonar

□ Liquidez evapora
  - Exemplo: Liquidez cai abaixo de threshold
  - Ação: Cancelar para liberar capital

□ Timeout atingido
  - Exemplo: 60 segundos sem matching
  - Ação: Cancelar automaticamente

□ Mudança de estratégia
  - Exemplo: Novas informações disponíveis
  - Ação: Cancelar e reavaliar
```

**Como Cancelar:**

```python
def cancel_order(order_id, client):
    """
    Cancela ordem na Betfair
    """
    cancel_instruction = betfairlightweight.resources.betting.CancelInstruction(
        bet_id=order_id
    )

    response = client.betting.cancel_orders([cancel_instruction])

    return response
```

### 5.2 Modificação de Ordens

**Quando Modificar:**

```
□ Mercado move favoravelmente
  - Exemplo: BACK @ 2.00, mercado vai para 1.95
  - Ação: Ajustar odd para 1.95 (melhor preço)

□ Liquidez aumenta
  - Exemplo: Mais liquidez disponível
  - Ação: Aumentar stake

□ Timeout aproximando
  - Exemplo: 50 segundos passados
  - Ação: Ajustar odd para aumentar chance de matching
```

**Como Modificar:**

```python
def modify_order(order_id, new_price, new_size, client):
    """
    Modifica ordem na Betfair (cancela e recria)
    """
    # Betfair não suporta modificação direta
    # Deve cancelar e recriar

    # 1. Cancelar ordem original
    cancel_order(order_id, client)

    # 2. Criar nova ordem com novos parâmetros
    place_limit_order(
        market_id=market_id,
        selection_id=selection_id,
        price=new_price,
        size=new_size,
        client=client
    )
```

---

## 6. MONITORAMENTO DE POSIÇÃO

### 6.1 Dashboard de Posição

```
┌─────────────────────────────────────────────────────────────────┐
│ DASHBOARD DE POSIÇÃO                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Posições Ativas: 5                                               │
│ Exposição Total: $12,500                                        │
│ Lucro/Perda Aberto: +$450                                       │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ POSIÇÃO 1: Lakers vs Warriors - BACK Lakers @ 2.00         │  │
│ ├────────────────────────────────────────────────────────────┤  │
│ │ Stake: $5,000  | Matched: $5,000  | Unmatched: $0        │  │
│ │ Odd: 2.00       | Odd Atual: 1.95  | Mudança: -2.5%       │  │
│ │ Exposição: $5,000 | P/L Potencial: +$5,000 / -$5,000      │  │
│ │ Status: FULLY MATCHED | Tempo: 2m34s                      │  │
│ │ Ações: [Hedge] [Green Up] [Red Up]                        │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ POSIÇÃO 2: Celtics vs Heat - BACK Celtics @ 3.00          │  │
│ ├────────────────────────────────────────────────────────────┤  │
│ │ Stake: $3,000  | Matched: $1,500  | Unmatched: $1,500    │  │
│ │ Odd: 3.00       | Odd Atual: 3.10  | Mudança: +3.3%       │  │
│ │ Exposição: $1,500 | P/L Potencial: +$3,000 / -$1,500      │  │
│ │ Status: PARTIALLY MATCHED | Tempo: 0m45s                 │  │
│ │ Ações: [Cancel Remainder] [Adjust Odd] [Wait]            │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ POSIÇÃO 3: Bulls vs Bucks - LAY Bulls @ 1.80              │  │
│ ├────────────────────────────────────────────────────────────┤  │
│ │ Stake: $2,000  | Matched: $0      | Unmatched: $2,000    │  │
│ │ Odd: 1.80       | Odd Atual: 1.85  | Mudança: +2.8%       │  │
│ │ Exposição: $0    | P/L Potencial: -$1,600 / +$2,000       │  │
│ │ Status: PENDING | Tempo: 0m12s                          │  │
│ │ Ações: [Cancel] [Adjust Odd] [Wait]                      │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│ Alertas:                                                         │
│ ⚠️ Posição 2: 50% unmatched por 45s                             │
│ ⚠️ Posição 3: Odd move desfavorável (2.8%)                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Métricas de Monitoramento

**Métricas por Posição:**

```
□ Stake Total
  - Valor da ordem original

□ Matched Amount
  - Valor já executado

□ Unmatched Amount
  - Valor pendente

□ Match Percentage
  - Matched / Stake Total × 100

□ Odd Entry
  - Odd da ordem original

□ Odd Current
  - Odd atual do mercado

□ Odd Change
  - (Odd Current - Odd Entry) / Odd Entry × 100

□ Exposure
  - Exposição atual (matched)

□ P/L Potential
  - Lucro/perda potencial

□ Time in Market
  - Tempo desde submissão

□ Status
  - Estado atual da ordem
```

**Métricas Agregadas:**

```
□ Total Positions
  - Número de posições ativas

□ Total Exposure
  - Soma de exposições

□ Total Unmatched
  - Soma de valores unmatched

□ Total P/L Potential
  - Soma de P/L potenciais

□ Average Time in Market
  - Tempo médio das posições
```

---

## 7. GESTÃO DE RISCO

### 7.1 Limites de Exposição

**Exposição por Mercado:**

```
Regra: Exposição máxima por mercado = 5% do bankroll
Bankroll: $10,000
Exposição máxima: $500

Exemplo:
Posição 1: BACK $300 em Team A
Posição 2: LAY $200 em Team B
Exposição total: $500

Pode adicionar: $0 (limite atingido)
```

**Exposição por Evento:**

```
Regra: Exposição máxima por evento = 10% do bankroll
Bankroll: $10,000
Exposição máxima: $1,000

Exemplo:
Jogo: Lakers vs Warriors
Posição 1: BACK $500 em Lakers
Posição 2: BACK $300 em Warriors
Exposição total: $800

Pode adicionar: até $200
```

**Exposição Total:**

```
Regra: Exposição total máxima = 20% do bankroll
Bankroll: $10,000
Exposição máxima: $2,000

Exemplo:
Todos os mercados: $1,800 em posições

Pode adicionar: até $200
```

### 7.2 Stop Loss

**Stop Loss por Posição:**

```
Regra: Stop loss = 2% do stake

Exemplo:
Stake: $1,000
Stop loss: $20

Se odd move desfavoravelmente de forma que perda potencial > $20:
- Executar hedge para limitar perda
- Ou cancelar posição
```

**Stop Loss por Dia:**

```
Regra: Stop loss diário = 5% do bankroll
Bankroll: $10,000
Stop loss: $500

Se perdas do dia > $500:
- Parar trading
- Reavaliar estratégias
- Retornar no dia seguinte
```

### 7.3 Position Sizing

**Fórmula de Kelly:**

```
Stake = (Probabilidade × Odd - 1) / (Odd - 1)

Exemplo:
Probabilidade estimada: 60%
Odd: 2.00

Stake = (0.60 × 2.00 - 1) / (2.00 - 1)
Stake = (1.20 - 1) / 1 = 0.20 (20% do bankroll)

Kelly fracionado (25%): 5% do bankroll
```

**Position Sizing Conservador:**

```
Regra: 1-2% do bankroll por posição

Bankroll: $10,000
Stake por posição: $100-$200

Vantagens:
- Baixo risco
- Sobrevive a losing streaks
- Crescimento consistente
```

---

## 8. AUTOMAÇÃO

### 8.1 Sistema Automático de Gestão

**Componentes:**

```
┌─────────────────────────────────────────────────────────────────┐
│ SISTEMA AUTOMÁTICO DE GESTÃO DE POSIÇÃO                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Order Monitor│───→│ Position     │───→│ Risk Manager │      │
│  │ (Betfair)    │    │ Tracker      │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         ↓                    ↓                    ↓             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Status       │←───│ Exposure     │←───│ Stop Loss    │      │
│  │ Checker      │    │ Calculator   │    │ Executor     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         ↓                    ↓                    ↓             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Auto Cancel  │    │ Auto Hedge   │    │ Alert System│      │
│  │ Executor     │    │ Executor     │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Monitoramento contínuo de posições
- Cálculo automático de exposição
- Execução automática de stop loss
- Cancelamento automático de timeouts
- Alertas em tempo real

### 8.2 Regras Automáticas

**Regra 1 - Timeout Auto-Cancel:**

```
Condição: Ordem unmatched por > 60 segundos
Ação: Cancelar automaticamente

Implementação:
if order.time_unmatched > 60:
    cancel_order(order.id)
```

**Regra 2 - Exposure Limit:**

```
Condição: Exposição > limite
Ação: Bloquear novas ordens

Implementação:
if total_exposure > exposure_limit:
    block_new_orders()
```

**Regra 3 - Stop Loss Auto-Execute:**

```
Condição: Perda potencial > stop loss
Ação: Executar hedge ou cancelar

Implementação:
if potential_loss > stop_loss:
    execute_hedge(position)
```

**Regra 4 - Odd Move Alert:**

```
Condição: Odd move > threshold
Ação: Enviar alerta

Implementação:
if abs(odd_change) > threshold:
    send_alert(f"Odd moved {odd_change}% for {position}")
```

---

## 9. MELHORES PRÁTICAS

### 9.1 Pré-Trade

**Checklist:**
- [ ] Verificar liquidez disponível
- [ ] Calcular exposição
- [ ] Confirmar que não excede limites
- [ ] Definir stop loss
- [ ] Configurar timeout
- [ ] Preparar plano de saída

### 9.2 Durante Trade

**Monitoramento:**
- Acompanhar status da ordem
- Monitorar movimento de odd
- Verificar exposição contínua
- Preparar para hedging se necessário

### 9.3 Pós-Trade

**Análise:**
- Registrar resultado
- Analisar execução
- Identificar erros
- Ajustar parâmetros

---

## 10. ERROS COMUNS

### 10.1 Ignorar Unmatched Bets

**Erro:** Não monitorar unmatched bets
**Consequência:** Capital fica travado
**Solução:** Monitorar unmatched bets continuamente

### 10.2 Overexposure

**Erro:** Exceder limites de exposição
**Consequência:** Risco excessivo
**Solução:** Implementar limites automáticos

### 10.3 Não Definir Stop Loss

**Erro:** Não definir stop loss
**Consequência:** Perdas grandes
**Solução:** Sempre definir stop loss

### 10.4 Ignorar Partial Fills

**Erro:** Não gerenciar partial fills
**Consequência:** Exposição parcial não controlada
**Solução:** Ter estratégia clara para partial fills

---

## 11. CONCLUSÃO

**Princípios Fundamentais:**

1. **Monitore tudo** - Cada posição deve ser monitorada
2. **Tenha limites** - Exposição, stop loss, timeout
3. **Automatize** - Reduz erro humano
4. **Seja proativo** - Não espere problemas acontecerem
5. **Aprenda com erros** - Analise e ajuste

**Regras de Ouro:**

| Regra | Detalhe |
|-------|---------|
| Exposição | Máximo 5% por mercado |
| Stop Loss | 2% do stake por posição |
| Timeout | 60 segundos para unmatched |
| Monitoramento | Contínuo e em tempo real |
| Automação | Automatize sempre que possível |

**Próximos Passos:**
- Implementar dashboard de posição
- Configurar alertas automáticos
- Desenvolver sistema de gestão automática
- Testar extensivamente antes de real money

---

## 12. LINKS CRUZADOS

- [[44_Exchange_Execution/INDEX]] ← Seção mãe
- [[EXCHANGE_VS_BOOKMAKERS]] → Diferenças fundamentais
- [[EXCHANGE_TRADING]] → Estratégias de trading
- [[LIQUIDITY_DEPTH]] → Liquidez e profundidade
- [[EXCHANGE_COSTS]] → Custos de exchange
- [[BETFAIR_EXECUTION]] → Execução via API