# MICRO_BANCA_PROTOCOL — Operacao com Dinheiro Real

**ID:** `RMO-001` | **Fase:** #phase/4 | **Owner:** Operations Lead + Risk Manager | **Status:** #status/pending

---

## 1. DEPOSITO INICIAL

### 1.1 Valores e Estrutura

- **Valor:** 500-1000 EUR (recomendado: 500€ para início)
- **Casa:** Betfair Exchange (não Sportsbook)
- **Divisão:** 50 unidades de 10 EUR cada
- **Máximo por aposta:** 2 unidades (20 EUR)
- **Reserva não apostável:** 20% (100€)

### 1.2 Preparação da Conta

**Antes do depósito:**
- [ ] Conta Betfair Exchange verificada (KYC completo)
- [ ] Autenticação 2FA ativada
- [ ] Conta bancária dedicada para apostas
- [ ] Limite de depósito configurado no banco
- [ ] Paper trading aprovado com todos os critérios

**Após o depósito:**
- [ ] Confirmar saldo na Betfair
- [ ] Configurar API Betfair (se aplicável)
- [ ] Testar acesso à API
- [ ] Configurar notificações de conta
- [ ] Definir limites de auto-exclusão (segurança)

---

## 2. PROTOCOLO OPERACIONAL PASSO-A-PASSO

### 2.1 Fase 4A: Setup Inicial (Dia 1)

**Manhã:**
1. Verificar saldo na Betfair (deve ser 500€)
2. Confirmar que sistema de tracking está operacional
3. Verificar que APIs externas estão acessíveis
4. Testar fluxo de receção de sinais
5. Preparar spreadsheet/template de registro

**Durante o dia:**
1. Aguardar primeiros sinais do sistema
2. Para cada sinal, seguir protocolo de execução (ver abaixo)
3. Registrar meticulosamente cada aposta
4. Monitorizar exposição diária

**Fim do dia:**
1. Reconciliar todas as apostas
2. Calcular PnL do dia
3. Verificar que não há discrepâncias
4. Documentar qualquer anomalia

### 2.2 Protocolo de Execução de Aposta

```
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 1: RECEÇÃO DE SINAL                                         │
├─────────────────────────────────────────────────────────────────┤
│ • Sinal recebido via Telegram/Email/Dashboard                    │
│ • Verificar timestamp (não expirado)                             │
│ • Verificar que mercado ainda está aberto                        │
│ • Registrar timestamp de receção                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 2: VALIDAÇÃO DO SINAL                                       │
├─────────────────────────────────────────────────────────────────┤
│ • Verificar ID do sinal (único)                                  │
│ • Confirmar mercado (NBA Moneyline, Spread, etc.)                │
│ • Confirmar seleção (time, jogador)                              │
│ • Confirmar odds sinalizada                                      │
│ • Confirmar stake recomendado                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 3: VERIFICAÇÃO DE RISCO                                    │
├─────────────────────────────────────────────────────────────────┤
│ • Calcular exposição diária atual                                │
│ • Verificar: exposição + stake < limite diário (120€)           │
│ • Verificar: stake < máximo por aposta (20€)                     │
│ • Verificar: sem conflito com outras apostas                     │
│ • Verificar: circuit breakers não ativados                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 4: VERIFICAÇÃO DE LIQUIDEZ                                 │
├─────────────────────────────────────────────────────────────────┤
│ • Abrir Betfair Exchange                                         │
│ • Navegar para mercado                                           │
│ • Verificar odds atual                                           │
│ • Verificar liquidez disponível                                  │
│ • Confirmar: liquidez >= stake * 2                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 5: EXECUÇÃO DA APOSTA                                      │
├─────────────────────────────────────────────────────────────────┤
│ • Colocar aposta com stake EXATAMENTE como recomendado           │
│ • Aceitar odds se >= odds_sinal - 1% (slippage aceitável)        │
│ • Se odds < odds_sinal - 1%: não apostar                         │
│ • Confirmar execução                                              │
│ • Capturar odd obtida e timestamp                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 6: REGISTRO DA APOSTA                                      │
├─────────────────────────────────────────────────────────────────┤
│ • Inserir no sistema de tracking:                                │
│   - ID do sinal                                                  │
│   - Jogo, mercado, seleção                                       │
│   - Odds sinalizada, odds obtida                                 │
│   - Stake                                                         │
│   - Timestamp de execução                                        │
│ • Calcular slippage: (odds_obtida / odds_sinal) - 1             │
│ • Atualizar exposição diária                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PASSO 7: CONFIRMAÇÃO                                              │
├─────────────────────────────────────────────────────────────────┤
│ • Verificar que aposta aparece na Betfair                        │
│ • Verificar que stake está correto                               │
│ • Verificar que odds está correta                                │
│ • Se houver discrepância: cancelar e investigar                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Fase 4B: Primeiras 50 Apostas

**Objetivo:** Validar que o sistema funciona com dinheiro real

**Regras:**
- Seguir sinais EXATAMENTE como gerados
- Registar odd obtida vs odd sinalizada
- Registar tempo entre sinal e execução
- Zero apostas fora do sistema
- Execução 100% manual (validação do processo)

**Checklist diário:**
- [ ] Número de apostas executadas
- [ ] Número de sinais recebidos
- [ ] Fill rate (apostas / sinais)
- [ ] Slippage médio
- [ ] Exposição diária
- [ ] PnL do dia
- [ ] Erros ou anomalias

**Métricas a monitorizar:**
| Métrica | Target | Ação se abaixo |
|---------|--------|----------------|
| Fill rate | > 80% | Revisar filtros de liquidez |
| Slippage médio | < 2% | Revisar timing |
| Tempo de execução | < 5 min | Revisar processo |
| CLV real | > CLV paper - 1% | Investigar |

### 2.4 Fase 4C: Análise Após 50 Apostas

**Reunião de revisão (após 50 apostas ou 30 dias):**

1. **Comparar métricas:**
   - CLV real vs CLV paper
   - ROI real vs ROI paper
   - Slippage real vs slippage paper
   - Fill rate real vs fill rate paper

2. **Avaliar operação:**
   - Operador seguiu protocolo?
   - Houve erros operacionais?
   - Sistema foi confiável?
   - Psicologia do operador está OK?

3. **Decisão:**
   ```
   SE CLV real >= CLV paper - 1% E ROI > 0% E Drawdown < 15%:
       → CONTINUAR com micro banca
       → Planejar aumento após 100 apostas
   SENÃO SE ROI > 0% mas CLV < CLV paper - 1%:
       → INVESTIGAR causa de slippage
       → CORRIGIR antes de continuar
   SENÃO SE ROI < 0%:
       → PARAR operação
       → REVISAR modelo
       → RETORNAR ao paper trading
   ```

---

## 3. REGRAS ABSOLUTAS

### 3.1 As 5 Regras de Ouro

1. **Nunca apostar sem sinal aprovado.**
   - Se não há sinal, não há aposta.
   - "Gut feeling" não é estratégia.
   - Emoção é o inimigo do lucro.

2. **Nunca alterar stake recomendado.**
   - O modelo calculou o stake ótimo matematicamente.
   - Aumentar stake = aumentar risco desproporcionalmente.
   - Diminuir stake = diminuir ROI esperado.

3. **Nunca perseguir perdas.** (Tilt = demissão)
   - Perdas fazem parte do jogo.
   - Tentar "recuperar" leva a decisões irracionais.
   - Se tilt ocorrer, parar por 24h mínimo.

4. **Sempre reconciliar no fecho do dia.**
   - Cada aposta deve ser verificada.
   - PnL real deve bater com sistema.
   - Discrepâncias devem ser investigadas.

5. **Sempre manter reserva de 20% da banca.**
   - Reserve é para emergências, não para apostas.
   - Se reserve for usada, parar imediatamente.
   - Recuperar reserve antes de continuar.

### 3.2 Regras de Execução

| Situação | Ação | Justificação |
|----------|------|--------------|
| Sem sinal | Não apostar | Sem validação de edge |
| Sinal expirado | Não apostar | Odds podem ter mudado |
| Liquidez insuficiente | Não apostar | Risco de não preenchimento |
| Exposição diária atingida | Não apostar | Gestão de risco |
| Stake > 2 unidades | Não apostar | Limite de risco |
| Odds < sinal - 1% | Não apostar | Slippage excessivo |
| Operador fatigado | Não apostar | Erros aumentam |

### 3.3 Regras de Gestão de Banca

| Situação | Ação | Justificação |
|----------|------|--------------|
| Banca < 400€ | Parar | Reserve violada |
| Drawdown > 20% | Parar e revisar | Proteção de banca |
| 3 perdas consecutivas | Continuar (se dentro de limites) | Variabilidade normal |
| 5 perdas consecutivas | Pausar e investigar | Possível problema |
| ROI < 0% após 50 apostas | Parar e revisar modelo | Modelo pode estar quebrado |

---

## 4. TEMPLATE DE REGISTRO DE APOSTAS

### 4.1 Estrutura do Template

```csv
Data,ID_Sinal,Jogo,Mercado,Seleção,Odds_Sinal,Odds_Obtida,Stake,Resultado,PnL,CLV,Slippage,Latência,Notas
2024-01-15,SIG-001,Lakers vs Celtics,Moneyline,Lakers,2.10,2.08,10,WIN,+10.80,+6.7%,-0.95%,45s,
2024-01-15,SIG-002,Warriors vs Heat,Spread,Warriors -5.5,1.90,1.90,15,LOSS,-15.00,+0.0%,0.00%,30s,
...
```

### 4.2 Cálculos Automáticos

**Slippage:**
```
Slippage % = ((Odds_Obtida / Odds_Sinal) - 1) * 100
```

**CLV_expost:**
```
CLV % = ((Odds_Obtida / Odds_Fecho) - 1) * 100
```

**PnL:**
```
Se WIN: PnL = Stake * Odds_Obtida - Stake
Se LOSS: PnL = -Stake
Se VOID: PnL = 0
```

---

## 5. RECONCILIAÇÃO DIÁRIA

### 5.1 Processo

**Horário:** 00:00 UTC (após todos os jogos)

**Passos:**
1. Exportar histórico da Betfair (últimas 24h)
2. Comparar com template de registro
3. Verificar:
   - Número de apostas bate?
   - Stakes estão corretos?
   - Odds estão corretas?
   - Resultados estão corretos?
4. Calcular PnL real vs PnL esperado
5. Documentar discrepâncias
6. Atualizar métricas diárias

### 5.2 Template de Relatório Diário

```
═══════════════════════════════════════════════════════════════
RECONCILIAÇÃO DIÁRIA - Micro Banca
Data: 2024-01-15
Operador: [Nome]
═══════════════════════════════════════════════════════════════

RESUMO
───────────────────────────────────────────────────────────────
Apostas no template: 8
Apostas na Betfair: 8
Discrepâncias: 0 ✓

BANCA
───────────────────────────────────────────────────────────────
Saldo inicial: 500.00€
Saldo final: 535.50€
PnL do dia: +35.50€
ROI do dia: +7.1%

MÉTRICAS
───────────────────────────────────────────────────────────────
Fill rate: 100% (8/8 sinais)
Slippage médio: -0.4%
CLV médio: +2.3%
Exposição diária: 85€ / 120€ (71%)

APOSTAS
───────────────────────────────────────────────────────────────
ID  | Jogo              | Odds S | Odds O | Stake | Resultado | PnL
----+-------------------+--------+--------+-------+-----------+-----
001  | Lakers vs Celtics | 2.10   | 2.08   | 10€   | WIN       | +10.80€
002  | Warriors vs Heat  | 1.90   | 1.90   | 15€   | LOSS      | -15.00€
003  | Bulls vs Knicks   | 2.25   | 2.23   | 10€   | WIN       | +12.30€
...

STATUS: RECONCILIADO ✓
Operador: [Assinatura]
═══════════════════════════════════════════════════════════════
```

---

## 6. GESTÃO DE INCIDENTES

### 6.1 Classificação

| Severidade | Exemplo | Ação |
|------------|---------|------|
| Crítica | Aposta duplicada, stake errado | Parar, investigar, corrigir |
| Alta | Slippage > 5%, API falhou | Pausar, investigar |
| Média | Pequeno erro de registro | Documentar, corrigir |
| Baixa | Delay de notificação | Monitorizar |

### 6.2 Processo de Incident Response

```
1. DETECÇÃO
   • Erro identificado
   • Classificar severidade

2. CONTENÇÃO
   • Se crítico: PARAR operação
   • Se alto: PAUSAR novas apostas
   • Se médio/baixo: continuar com monitorização

3. INVESTIGAÇÃO
   • Identificar causa raiz
   • Documentar timeline
   • Avaliar impacto financeiro

4. CORREÇÃO
   • Implementar correção
   • Validar correção
   • Retomar operação

5. PREVENÇÃO
   • Adicionar checks
   • Atualizar protocolo
   • Treinar operador
```

---

## 7. CRITÉRIOS DE AUMENTO DE BANCA

### 7.1 Quando Aumentar

Condições TODAS devem ser satisfeitas:
- [ ] Pelo menos 100 apostas executadas
- [ ] ROI real > 3% nos últimos 30 dias
- [ ] CLV real > CLV paper - 1%
- [ ] Drawdown máximo < 15%
- [ ] Operador seguiu protocolo 100%
- [ ] Sistema estável (sem downtime)

### 7.2 Quanto Aumentar

| Banca Atual | Aumento | Nova Banca | Novo Stake Unitário |
|-------------|---------|------------|---------------------|
| 400€ | +200€ | 600€ | 12€ |
| 600€ | +400€ | 1000€ | 20€ |
| 1000€ | +1000€ | 2000€ | 40€ |

**Regra:** Nunca aumentar mais que 50% de uma vez

### 7.3 Após Aumento

- [ ] Recalcular stakes (nova unidade)
- [ ] Atualizar limites de exposição
- [ ] Monitorizar intensivamente por 30 dias
- [ ] Se drawdown > 10%: reduzir de volta

---

## 8. BACKLOG DE IMPLEMENTAÇÃO

- [x] Criar template de registo de apostas
- [ ] Implementar sistema de reconciliação diária automatizado
- [ ] Definir critérios formais de aumento de banca
- [ ] Criar dashboard de monitorização em tempo real
- [ ] Implementar alertas automáticos por Telegram
- [ ] Criar sistema de backup de dados
- [ ] Documentar casos de uso edge

---

## 9. CENÁRIOS DE EXEMPLO

### 9.1 Cenário 1: Execução Bem-Sucedida

**Sinal recebido:**
- Jogo: Lakers vs Celtics
- Mercado: Moneyline
- Seleção: Lakers
- Odds sinalizada: 2.10
- Stake recomendado: 10€
- Timestamp: 19:30:00 UTC

**Execução passo-a-passo:**

```
19:30:00 - Sinal recebido via Telegram
19:30:05 - Validado: mercado aberto, sinal não expirado
19:30:10 - Verificação de risco: exposição atual 50€ + 10€ = 60€ < 120€ ✓
19:30:15 - Verificação de liquidez: Betfair mostra 2.08 com €5000 disponível ✓
19:30:20 - Execução: aposta colocada a 2.08
19:30:21 - Confirmação Betfair recebida, ID: 12345678
19:30:25 - Registro no sistema: odds_obtida=2.08, slippage=-0.95%
19:30:30 - Exposição atualizada: 70€
22:00:00 - Jogo termina: Lakers ganha
22:15:00 - Odd de fecho capturada: 1.95
22:15:05 - PnL calculado: 10€ × 2.08 - 10€ = +10.80€
22:15:10 - CLV calculado: (2.08 / 1.95) - 1 = +6.67%
```

**Resultado:** ✓ SUCESSO
- Slippage aceitável (-0.95% < 1%)
- CLV positivo (+6.67%)
- PnL positivo (+10.80€)

### 9.2 Cenário 2: Liquidez Insuficiente

**Sinal recebido:**
- Jogo: Warriors vs Heat
- Mercado: Spread
- Seleção: Warriors -5.5
- Odds sinalizada: 1.90
- Stake recomendado: 20€
- Timestamp: 20:00:00 UTC

**Execução passo-a-passo:**

```
20:00:00 - Sinal recebido via Telegram
20:00:05 - Validado: mercado aberto, sinal não expirado
20:00:10 - Verificação de risco: exposição atual 40€ + 20€ = 60€ < 120€ ✓
20:00:15 - Verificação de liquidez: Betfair mostra 1.90 com apenas €25 disponível
20:00:16 - Liquidez (€25) < stake × 2 (€40) ✗
20:00:17 - DECISÃO: NÃO APOSTAR
20:00:18 - Registro no sistema: status=CANCELLED_LIQUIDITY
20:00:19 - Notificação enviada: "Sinal SIG-002 cancelado - liquidez insuficiente"
```

**Resultado:** ✓ CORRETOAMENTE CANCELADO
- Evitou risco de não preenchimento
- Protegeu banca
- Registrado para análise posterior

### 9.3 Cenário 3: Slippage Excessivo

**Sinal recebido:**
- Jogo: Bulls vs Knicks
- Mercado: Totals
- Seleção: Over 220.5
- Odds sinalizada: 2.00
- Stake recomendado: 15€
- Timestamp: 21:00:00 UTC

**Execução passo-a-passo:**

```
21:00:00 - Sinal recebido via Telegram
21:00:05 - Validado: mercado aberto, sinal não expirado
21:00:10 - Verificação de risco: exposição atual 30€ + 15€ = 45€ < 120€ ✓
21:00:15 - Verificação de liquidez: Betfair mostra 1.92 com €10000 disponível
21:00:16 - Odd atual (1.92) < odd sinal - 1% (1.98) ✗
21:00:17 - Slippage seria: (1.92 / 2.00) - 1 = -4% (excessivo)
21:00:18 - DECISÃO: NÃO APOSTAR
21:00:19 - Registro no sistema: status=CANCELLED_SLIPPAGE
21:00:20 - Notificação enviada: "Sinal SIG-003 cancelado - slippage excessivo (-4%)"
```

**Resultado:** ✓ CORRETOAMENTE CANCELADO
- Evitou perda de edge
- Seguiu regra de slippage máximo
- Protegeu ROI esperado

### 9.4 Cenário 4: Exposição Diária Atingida

**Situação:**
- Exposição atual: 115€
- Limite diário: 120€
- Novo sinal com stake: 10€

**Execução passo-a-passo:**

```
19:45:00 - Sinal recebido via Telegram
19:45:05 - Validado: mercado aberto, sinal não expirado
19:45:10 - Verificação de risco: exposição atual 115€ + 10€ = 125€ > 120€ ✗
19:45:11 - DECISÃO: NÃO APOSTAR
19:45:12 - Registro no sistema: status=CANCELLED_EXPOSURE
19:45:13 - Notificação enviada: "Sinal SIG-004 cancelado - exposição diária atingida"
```

**Resultado:** ✓ CORRETOAMENTE CANCELADO
- Respeitou limite de exposição
- Gestão de risco mantida
- Protegeu banca

---

## 10. PROCEDIMENTOS AVANÇADOS

### 10.1 Gestão de Multi-Sinais Simultâneos

**Situação:** Múltiplos sinais recebidos em curto período

**Protocolo:**
1. **Priorizar por CLV esperado:**
   - Executar primeiro sinal com maior CLV esperado
   - Se CLV similar, executar por ordem de receção

2. **Verificar exposição acumulada:**
   ```
   Exposição total = Soma de stakes de todos os sinais simultâneos
   Se exposição total > limite diário:
       → Executar apenas sinais com CLV > 3%
       → Cancelar sinais com CLV < 3%
   ```

3. **Verificar liquidez de cada mercado:**
   - Se múltiplos sinais no mesmo jogo, executar apenas o melhor
   - Evitar sobre-exposição a um único evento

4. **Registrar prioridade:**
   - Documentar quais sinais foram executados
   - Documentar quais foram cancelados e porquê
   - Analisar impacto de não executar sinais cancelados

### 10.2 Gestão de Atrasos de Execução

**Situação:** Sinal recebido mas operador indisponível

**Protocolo:**
1. **Se atraso < 2 minutos:**
   - Executar se mercado ainda aberto
   - Verificar que odds ainda válidas (±1%)
   - Registrar latência no sistema

2. **Se atraso 2-5 minutos:**
   - Verificar liquidez disponível
   - Se liquidez ainda boa (≥ stake × 3), executar
   - Se liquidez reduzida, cancelar
   - Registrar atraso e decisão

3. **Se atraso > 5 minutos:**
   - Cancelar automaticamente
   - Não executar
   - Investigar causa do atraso
   - Implementar prevenção

4. **Prevenção de atrasos:**
   - Configurar múltiplos canais de notificação
   - Ter operador backup
   - Implementar alertas de não-resposta

### 10.3 Gestão de Erros de Betfair

**Erro: "Account Suspended"**

```
AÇÃO IMEDIATA:
1. PARAR todas as operações
2. Verificar email da Betfair
3. Contactar suporte Betfair
4. Documentar motivo da suspensão

POSSÍVEIS CAUSAS:
- Violação de termos de serviço
- Atividade suspeita
- Problema de KYC
- Erro do sistema Betfair

RESOLUÇÃO:
- Se erro do sistema: aguardar resolução
- Se violação: corrigir comportamento
- Se KYC: submeter documentação adicional
- Se permanente: mudar para outra casa
```

**Erro: "Insufficient Funds"**

```
AÇÃO IMEDIATA:
1. Verificar saldo Betfair
2. Verificar reserva intacta
3. Se reserva intacta: transferir para banca ativa
4. Se reserva violada: PARAR operação

PREVENÇÃO:
- Manter monitorização de saldo
- Alertas automáticos se saldo < limite
- Reabastecer proativamente
```

**Erro: "Market Closed"**

```
AÇÃO IMEDIATA:
1. Cancelar aposta
2. Registrar status=CANCELLED_MARKET_CLOSED
3. Investigar porquê mercado fechou antes do esperado
4. Ajustar filtros de tempo

PREVENÇÃO:
- Verificar horário de fecho do mercado
- Adicionar buffer de segurança (5 min)
- Cancelar sinais perto do fecho
```

### 10.4 Gestão de Resultados Void/Cancelados

**Situação:** Jogo cancelado ou resultado void

**Protocolo:**
1. **Identificar status:**
   - Verificar se jogo foi cancelado
   - Verificar se resultado foi declarado void
   - Confirmar com fonte oficial (NBA.com)

2. **Atualizar aposta:**
   - Marcar resultado como VOID
   - PnL = 0 (stake devolvido)
   - CLV não aplicável

3. **Reconciliação:**
   - Verificar que Betfair devolveu stake
   - Confirmar saldo atualizado
   - Documentar no sistema

4. **Análise:**
   - Se recorrente: investigar mercado
   - Se esporádico: aceitar como variabilidade
   - Ajustar filtros se necessário

---

## 11. INTEGRAÇÃO COM SISTEMAS AUTOMATIZADOS

### 11.1 Sistema de Alertas Automáticos

```python
class MicroBancaAlertSystem:
    def __init__(self, telegram_bot, thresholds):
        self.telegram = telegram_bot
        self.thresholds = thresholds

    def check_exposure(self, current_exposure):
        """Verifica exposição e envia alerta se próximo do limite"""
        if current_exposure > self.thresholds['exposure_warning']:
            message = f"""
⚠️ ALERTA DE EXPOSIÇÃO

Exposição atual: {current_exposure}€
Limite diário: {self.thresholds['exposure_max']}€
Percentual: {current_exposure / self.thresholds['exposure_max'] * 100:.1f}%

Ação: Considerar parar novas apostas
            """
            self.telegram.send_message(message)

    def check_balance(self, current_balance):
        """Verifica saldo e envia alerta se baixo"""
        if current_balance < self.thresholds['balance_warning']:
            message = f"""
⚠️ ALERTA DE SALDO

Saldo atual: {current_balance}€
Limite mínimo: {self.thresholds['balance_min']}€

Ação: Recarregar conta ou parar operação
            """
            self.telegram.send_message(message)

    def check_drawdown(self, current_drawdown):
        """Verifica drawdown e envia alerta crítico se alto"""
        if current_drawdown > self.thresholds['drawdown_critical']:
            message = f"""
🚨 ALERTA CRÍTICO - DRAWDOWN

Drawdown atual: {current_drawdown:.2%}
Limite crítico: {self.thresholds['drawdown_critical']:.2%}

AÇÃO: PARAR OPERAÇÃO IMEDIATAMENTE
            """
            self.telegram.send_message(message)
```

### 11.2 Dashboard em Tempo Real

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/microbanca/realtime')
def get_microbanca_realtime():
    """Endpoint para dashboard em tempo real"""
    # Métricas atuais
    metrics = {
        'balance': get_current_balance(),
        'exposure': get_current_exposure(),
        'reserve': get_reserve(),
        'available': get_available_balance(),
        'n_bets_today': get_bets_today(),
        'pnl_today': get_pnl_today(),
        'roi_today': get_roi_today(),
        'drawdown_current': get_current_drawdown(),
    }

    # Últimas apostas
    recent_bets = get_recent_bets(limit=10)

    # Status
    status = {
        'system_online': check_system_online(),
        'betfair_connected': check_betfair_connection(),
        'within_limits': check_within_limits(),
        'alerts_active': get_active_alerts()
    }

    return jsonify({
        'metrics': metrics,
        'recent_bets': recent_bets,
        'status': status,
        'timestamp': datetime.now().isoformat()
    })
```

### 11.3 Sistema de Backup Automático

```python
class MicroBancaBackup:
    def __init__(self, db_config, backup_config):
        self.db = Database(db_config)
        self.backup_config = backup_config

    def daily_backup(self):
        """Backup diário dos dados de apostas"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Exportar dados
        data = self.db.export_bets(mode='real', date=today)

        # Salvar em arquivo
        filename = f"microbanca_backup_{timestamp}.csv"
        filepath = os.path.join(self.backup_config['dir'], filename)

        with open(filepath, 'w') as f:
            f.write(data)

        # Enviar para nuvem (opcional)
        if self.backup_config['cloud_enabled']:
            self.upload_to_cloud(filepath)

        # Manter últimos 30 dias apenas
        self.cleanup_old_backups(days=30)

        return filepath

    def cleanup_old_backups(self, days):
        """Remove backups antigos"""
        cutoff = datetime.now() - timedelta(days=days)
        for filename in os.listdir(self.backup_config['dir']):
            if filename.startswith('microbanca_backup_'):
                filepath = os.path.join(self.backup_config['dir'], filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff:
                    os.remove(filepath)
```

---

## 12. CHECKLIST DE VALIDAÇÃO FINAL

### 12.1 Antes de Iniciar Micro Banca

```
VALIDAÇÃO FINAL - MICRO BANCA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PAPER TRADING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Paper trading completado (mínimo 30 dias)
[ ] Mínimo 100 sinais gerados
[ ] CLV paper >= CLV backtest - 1%
[ ] ROI paper > 2%
[ ] Uptime sistema > 95%
[ ] Sem erros críticos nos últimos 30 dias
[ ] Relatório final aprovado

CONTA BETFAIR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Conta verificada (KYC completo)
[ ] 2FA ativado e testado
[ ] Depósito de 500€ confirmado
[ ] API Betfair configurada (se aplicável)
[ ] Notificações de conta configuradas
[ ] Limites de auto-exclusão definidos

SISTEMA DE TRACKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Template de registro criado
[ ] Base de dados configurada
[ ] Sistema de reconciliação testado
[ ] Alertas automáticos configurados
[ ] Dashboard operacional

OPERADOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Operador treinado no protocolo
[ ] Operador treinado no checklist
[ ] Operador consciente das regras de ouro
[ ] Operador preparado psicologicamente
[ ] Operador backup identificado

DOCUMENTAÇÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Protocolo de micro banca lido e entendido
[ ] Regras absolutas lidas e aceitas
[ ] Procedimentos de emergência conhecidos
[ ] Canais de comunicação estabelecidos

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
APROVAÇÃO FINAL
[ ] TODOS os itens acima validados
[ ] Assinatura do responsável: ____________________
[ ] Data: ____________________

STATUS: APROVADO PARA INICIAR MICRO BANCA [ ] SIM [ ] NÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 13. LINKS CRUZADOS

- [[22_Real_Money_Operations/INDEX]] ← Seção mãe
- [[08_Risk_Management/INDEX]] → Kelly e circuit breakers
- [[21_Paper_Trading/INDEX]] → Fase anterior (validação)
- [[23_Scaling/INDEX]] → Escala de banca
- [[44_Exchange_Execution/INDEX]] → Execução automática via API
