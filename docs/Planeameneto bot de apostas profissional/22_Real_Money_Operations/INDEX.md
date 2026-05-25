# 22_Real_Money_Operations — INDEX

**ID:** `SEC-22` | **Fase:** #phase/4-6 | **Owner:** Operations Lead + Risk Manager | **Status:** #status/active

---

## 1. OBJETIVO

Gerir a execução real de apostas com dinheiro. Este é o momento de verdade: qualquer erro aqui tem consequências financeiras reais. A disciplina operacional deve ser máxima.

---

## 2. NOTAS FUNDAMENTAIS

- [[MICRO_BANCA_PROTOCOL]] — Regras para operar com 500-1000€
- [[TRACKING_APOSTAS]] — Como registar cada aposta meticulosamente
- [[RECONCILIACAO_DIARIA]] — Verificação de que execução = plano
- [[DIVERGENCIA_PNL]] — Análise de diferenças entre PnL real e esperado
- [[BANCA_GESTAO]] — Aumento gradual da banca, regras de escala

---

## 3. PROTOCOLO DE MICRO BANCA

### 3.1 Fase 4A: Depósito Inicial (Mês 4)

**Preparação:**
- Verificar que paper trading foi aprovado com todos os critérios
- Confirmar que conta Betfair Exchange está verificada
- Configurar autenticação 2FA
- Definir limites de depósito na conta bancária

**Depósito:**
- Valor: 500€ na Betfair Exchange (não Sportsbook)
- Fonte: Conta dedicada para apostas (nunca conta pessoal)
- Divisão: 50 unidades de 10€ cada
- Maximo por aposta: 2 unidades (20€)
- Reserva: 100€ (20%) nunca apostável

**Validação:**
- [ ] Depósito confirmado na Betfair
- [ ] Saldo visível na conta
- [ ] API Betfair configurada e testada
- [ ] Sistema de tracking pronto
- [ ] Operador treinado no protocolo

### 3.2 Fase 4B: Primeiras 50 Apostas

**Execução:**
- Seguir sinais EXATAMENTE como gerados
- Registar odd obtida vs odd sinalizada
- Registar tempo entre sinal e execução
- Nenhuma aposta fora do sistema (zero emoção)
- Execução manual inicialmente (validação do processo)

**Registro de cada aposta:**
```
ID da aposta | Jogo | Mercado | Seleção | Odd Sinal | Odd Obtida | Stake | Resultado | PnL | CLV | Latência | Timestamp
```

**Checklist antes de cada aposta:**
- [ ] Sinal aprovado pelo sistema
- [ ] Stake conforme Kelly fraction
- [ ] Exposição diária dentro de limites
- [ ] Liquidez suficiente disponível
- [ ] Mercado ainda aberto
- [ ] Sem conflito com outras apostas

### 3.3 Fase 4C: Análise Após 50 Apostas

**Métricas a analisar:**
- Comparar CLV real com CLV paper
- Calcular slippage real médio
- Verificar se o drawdown é suportável psicologicamente
- Avaliar se o operador está seguindo o protocolo
- Identificar problemas operacionais

**Decisão:**
```
SE CLV real >= CLV paper - 1% E ROI > 0% E Drawdown < 15%:
    → CONTINUAR com micro banca
    → Considerar aumento gradual após 100 apostas
SENÃO:
    → PARAR operação
    → Investigar causa
    → CORRIGIR antes de continuar
```

---

## 4. REGRAS ABSOLUTAS DE OPERAÇÃO

### 4.1 As 5 Regras de Ouro

1. **Nunca apostar sem sinal aprovado.** Nenhuma exceção.
   - Se não há sinal, não há aposta.
   - "Gut feeling" não é estratégia.
   - Emoção é o inimigo do lucro.

2. **Nunca alterar stake recomendada.** Kelly é lei.
   - O modelo calculou o stake ótimo matematicamente.
   - Aumentar stake = aumentar risco desproporcionalmente.
   - Diminuir stake = diminuir ROI esperado.

3. **Nunca perseguir perdas.** Tilt = demissão imediata do operador.
   - Perdas fazem parte do jogo.
   - Tentar "recuperar" leva a decisões irracionais.
   - Se tilt ocorrer, parar por 24h mínimo.

4. **Sempre reconciliar no fecho do dia.**
   - Cada aposta deve ser verificada.
   - PnL real deve bater com sistema.
   - Discrepâncias devem ser investigadas.

5. **Sempre manter reserve de 20% da banca não apostável.**
   - Reserve é para emergências, não para apostas.
   - Se reserve for usada, parar imediatamente.
   - Recuperar reserve antes de continuar.

### 4.2 Regras Operacionais

| Situação | Ação | Justificação |
|----------|------|--------------|
| Sistema offline | Não apostar | Sem validação de risco |
| API de odds falhando | Não apostar | Sem dados confiáveis |
| Liquidez < stake | Não apostar | Risco de não preenchimento |
| Exposição diária atingida | Não apostar | Gestão de risco |
| Operador doente/fadigado | Não apostar | Erros aumentam |
| Drawdown > 20% | Parar e revisar | Proteção de banca |
| 3 erros consecutivos | Parar e investigar | Possível problema sistêmico |

---

## 5. FLUXO OPERACIONAL DETALHADO

### 5.1 Execução Manual (Fase 4)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. RECEÇÃO DE SINAL                                              │
├─────────────────────────────────────────────────────────────────┤
│ • Sinal recebido via Telegram/Email/Dashboard                    │
│ • Timestamp de receção registado                                │
│ • Sinal validado (não expirado, mercado aberto)                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. VERIFICAÇÃO DE RISCO                                          │
├─────────────────────────────────────────────────────────────────┤
│ • Exposição diária calculada                                     │
│ • Stake validado (dentro de limites)                            │
│ • Liquidez verificada                                            │
│ • Circuit breakers verificados                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. EXECUÇÃO NA BETFAIR                                           │
├─────────────────────────────────────────────────────────────────┤
│ • Login na Betfair Exchange                                      │
│ • Navegar para mercado                                           │
│ • Verificar odds atual                                          │
│ • Colocar aposta com stake recomendado                          │
│ • Confirmar execução                                             │
│ • Capturar odd obtida e timestamp                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. REGISTRO DE APOSTA                                            │
├─────────────────────────────────────────────────────────────────┤
│ • Inserir aposta na base de dados                               │
│ • Registrar: odds_sinal, odds_obtida, stake, resultado          │
│ • Calcular slippage                                              │
│ • Atualizar exposição diária                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. MONITORIZAÇÃO DE RESULTADO                                    │
├─────────────────────────────────────────────────────────────────┤
│ • Acompanhar jogo em tempo real                                  │
│ • Verificar resultado após término                               │
│ • Atualizar status da aposta (WIN/LOSS/VOID)                     │
│ • Calcular PnL                                                   │
│ • Calcular CLV_expost                                            │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Execução Automática (Fase 7+)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. SINAL GERADO AUTOMATICAMENTE                                  │
├─────────────────────────────────────────────────────────────────┤
│ • Motor de value gera sinal                                      │
│ • Sinal validado automaticamente                                 │
│ • Enviado para módulo de execução                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. API BETFAIR PLACE ORDER                                       │
├─────────────────────────────────────────────────────────────────┤
│ • Limit order colocada via API                                   │
│ • Preço: odds_sinal - 0.01 (ligeiramente melhor)                │
│ • Tamanho: stake recomendado                                     │
│ • Timeout: 60 segundos                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. VERIFICAÇÃO DE EXECUÇÃO                                       │
├─────────────────────────────────────────────────────────────────┤
│ • Poll API para verificar status                                 │
│ • Se FILLED: registrar sucesso                                   │
│ • Se TIMEOUT: cancelar e alertar                                 │
│ • Se REJECTED: investigar motivo                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. REGISTRO AUTOMÁTICO                                           │
├─────────────────────────────────────────────────────────────────┤
│ • Aposta registrada na BD automaticamente                        │
│ • Odd obtida capturada                                           │
│ • Slippage calculado                                             │
│ • Exposição atualizada                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. GESTÃO DE BANCA

### 6.1 Estrutura da Banca

```
Banca Total: 500€
├── Reserva (não apostável): 100€ (20%)
└── Banca Ativa: 400€ (80%)
    ├── Apostas Ativas: até 120€ (30%)
    ├── Disponível: até 280€ (70%)
```

### 6.2 Gestão de Stake

| Banca Ativa | Unidade | Stake Min | Stake Max | Exposição Diária Max |
|-------------|---------|-----------|-----------|---------------------|
| 400€ | 10€ | 5€ (0.5u) | 20€ (2u) | 120€ (12u) |
| 800€ | 20€ | 10€ (0.5u) | 40€ (2u) | 240€ (12u) |
| 1600€ | 40€ | 20€ (0.5u) | 80€ (2u) | 480€ (12u) |

**Regra de Kelly:**
```
Stake = (Banca Ativa * Kelly Fraction * Edge) / Odds

Onde:
- Kelly Fraction: 0.25 (conservador)
- Edge: CLV esperado
- Odds: odds da aposta
```

### 6.3 Limites de Exposição

| Tipo de Limite | Valor | Justificação |
|----------------|-------|--------------|
| Por aposta | 2 unidades (20€) | Limitar risco individual |
| Por dia | 12 unidades (120€) | Diversificação temporal |
| Por mercado | 4 unidades (40€) | Diversificação de mercado |
| Por jogo | 2 unidades (20€) | Evitar sobre-exposição |
| Drawdown max | 20% da banca | Proteção de banca |

---

## 7. RECONCILIAÇÃO DIÁRIA

### 7.1 Processo de Reconciliação

**Horário:** Diariamente às 00:00 UTC (após todos os jogos)

**Passos:**
1. Exportar histórico de apostas da Betfair
2. Comparar com base de dados interna
3. Verificar discrepâncias (odds, stakes, resultados)
4. Calcular PnL real vs PnL esperado
5. Atualizar métricas diárias
6. Gerar relatório de reconciliação

### 7.2 Template de Relatório

```
═══════════════════════════════════════════════════════════════
RELATÓRIO DE RECONCILIAÇÃO DIÁRIA
Data: 2024-01-15
══════───────────────────────────────────────────────────────────

RESUMO
───────────────────────────────────────────────────────────────
Apostas no sistema: 12
Apostas na Betfair: 12
Discrepâncias: 0 ✓

PnL Sistema: +45.50€
PnL Betfair: +45.50€
Diferença: 0.00€ ✓

DETALES
───────────────────────────────────────────────────────────────
ID  | Jogo              | Odd Sinal | Odd Obtida | Stake | Resultado | PnL
----+-------------------+-----------+------------+-------+-----------+-----
001  | Lakers vs Celtics | 2.10      | 2.08       | 10€   | WIN       | +10.80€
002  | Warriors vs Heat  | 1.85      | 1.85       | 15€   | LOSS      | -15.00€
...

MÉTRICAS
───────────────────────────────────────────────────────────────
ROI do dia: +3.8%
CLV médio: +2.1%
Slippage médio: -0.5%
Exposição diária: 120€ / 120€ (100%)

STATUS: RECONCILIADO ✓
═══════════════════════════════════════════════════════════════
```

---

## 8. GESTÃO DE ERROS E INCIDENTES

### 8.1 Classificação de Erros

| Severidade | Exemplo | Ação Imediata |
|------------|---------|---------------|
| Crítica | Aposta duplicada | Parar operação, investigar |
| Alta | Stake incorreto | Cancelar se possível, documentar |
| Média | Slippage excessivo | Ajustar filtros, monitorizar |
| Baixa | Pequeno delay de registro | Documentar, corrigir |

### 8.2 Processo de Incident Response

```
1. DETECÇÃO
   • Erro identificado por operador ou sistema
   • Classificação de severidade

2. CONTENÇÃO
   • Se crítico: parar operação imediatamente
   • Se alto: pausar novas apostas
   • Se médio/baixo: continuar com monitorização

3. INVESTIGAÇÃO
   • Identificar causa raiz
   • Documentar timeline
   • Avaliar impacto financeiro

4. CORREÇÃO
   • Implementar correção imediata
   • Validar correção
   • Retomar operação se seguro

5. PREVENÇÃO
   • Adicionar checks para prevenir recorrência
   • Atualizar documentação
   • Treinar operador se necessário
```

---

## 9. PSICOLOGIA DO OPERADOR

### 9.1 Sinais de Tilt

- Impaciência com sinais
- Desejo de "recuperar" perdas
- Apostas fora do sistema
- Aumento de stake não autorizado
- Irritação com resultados negativos
- Negligência de protocolos

### 9.2 Gestão de Tilt

**Se tilt detectado:**
1. Parar imediatamente (nenhuma nova aposta)
2. Afastar-se do sistema por 24h mínimo
3. Revisar protocolos e regras
4. Retornar apenas quando mentalmente estável
5. Se recorrente: considerar substituição de operador

### 9.3 Mindset Correto

- Apostas são números, não emoções
- Perdas são custo de fazer negócio
- Disciplina > inteligência
- Processo > resultado de curto prazo
- Longo prazo: o sistema vence se seguido

---

## 10. PROCEDIMENTOS DIÁRIOS DETALHADOS

### 10.1 Rotina Matinal (Antes dos Jogos)

**Horário:** 1 hora antes do primeiro jogo do dia

```
CHECKLIST MATINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. VERIFICAÇÃO DE SISTEMA
   [ ] Sistema de sinais online
   [ ] APIs de odds acessíveis
   [ ] Base de dados operacional
   [ ] Notificações configuradas
   [ ] Espaço em disco suficiente

2. VERIFICAÇÃO DE CONTA
   [ ] Saldo Betfair visível
   [ ] Limite de depósito não atingido
   [ ] Sem transações não autorizadas
   [ ] 2FA funcionando

3. VERIFICAÇÃO DE BANCA
   [ ] Banca total: ____€
   [ ] Reserva: ____€ (20%)
   [ ] Banca ativa: ____€ (80%)
   [ ] Exposição atual: ____€
   [ ] Disponível para apostas: ____€

4. REVISÃO DE ONTEM
   [ ] Reconciliação concluída
   [ ] PnL do dia: ____€
   [ ] ROI do dia: ____%
   [ ] Anomalias documentadas
   [ ] Erros corrigidos

5. PREPARAÇÃO DO DIA
   [ ] Calendário de jogos revisado
   [ ] Horários dos jogos verificados
   [ ] Limites diários definidos
   [ ] Operador descansado e focado

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATUS: PRONTO PARA OPERAR [ ] SIM [ ] NÃO
```

### 10.2 Checklist Pré-Aposta (Para Cada Sinal)

```
CHECKLIST PRÉ-APOSTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID do sinal: ____________________
Jogo: ____________________
Mercado: ____________________
Seleção: ____________________
Odd sinalizada: ____________________
Stake recomendado: ____________________
Timestamp: ____________________

VALIDAÇÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Sinal aprovado pelo sistema
[ ] Sinal não expirado (< 5 minutos)
[ ] Mercado ainda aberto
[ ] Odds sinalizada ainda válida (±1%)

RISCO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Exposição diária atual: ____€
[ ] Exposição + stake < limite (120€)
[ ] Stake < máximo por aposta (20€)
[ ] Sem conflito com outras apostas
[ ] Circuit breakers não ativados

LIQUIDEZ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Liquidez disponível >= stake × 2
[ ] Odd atual >= odd sinal - 1%
[ ] Mercado com volume suficiente

DECISÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] APROVADO para execução
[ ] REJEITADO (motivo: ____________________)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 10.3 Checklist Pós-Aposta (Imediato)

```
CHECKLIST PÓS-APOSTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXECUÇÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Aposta colocada na Betfair
[ ] Confirmação recebida
[ ] ID da aposta Betfair: ____________________
[ ] Odd obtida: ____________________
[ ] Stake executado: ____________________
[ ] Timestamp execução: ____________________

REGISTRO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Aposta registrada no sistema
[ ] Odd sinalizada: ____________________
[ ] Odd obtida: ____________________
[ ] Slippage: ____________________%
[ ] Latência: ____________________ segundos
[ ] Exposição atualizada

VERIFICAÇÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Betfair saldo deduzido corretamente
[ ] Aposta visível no histórico Betfair
[ ] Sistema mostra aposta como ativa
[ ] Sem erros no registro

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 10.4 Rotina de Fecho de Dia

**Horário:** Após término de todos os jogos (geralmente 03:00-04:00 UTC)

```
CHECKLIST FECHO DE DIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ATUALIZAÇÃO DE RESULTADOS
   [ ] Todos os jogos finalizados
   [ ] Resultados obtidos (NBA.com/ESPN)
   [ ] Status de todas as apostas atualizado
   [ ] PnL calculado para cada aposta

2. RECONCILIAÇÃO
   [ ] Exportar histórico Betfair
   [ ] Comparar com sistema interno
   [ ] Verificar discrepâncias
   [ ] Corrigir se necessário

3. MÉTRICAS DO DIA
   [ ] Total de apostas: ____
   [ ] Apostas WIN: ____
   [ ] Apostas LOSS: ____
   [ ] PnL total: ____€
   [ ] ROI do dia: ____%
   [ ] CLV médio: ____%
   [ ] Slippage médio: ____%

4. BANCA
   [ ] Saldo Betfair: ____€
   [ ] Banca total: ____€
   [ ] Reserva intacta: ____€
   [ ] Exposição: 0€ (todas liquidadas)

5. DOCUMENTAÇÃO
   [ ] Relatório diário gerado
   [ ] Anomalias documentadas
   [ ] Lições aprendidas registradas
   [ ] Logs de erros revisados

6. PREPARAÇÃO AMANHÃ
   [ ] Calendário de jogos verificado
   [ ] Sistema pronto para amanhã
   [ ] Notificações configuradas

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATUS: DIA CONCLUÍDO [ ] SIM [ ] NÃO
```

---

## 11. PROCEDIMENTOS DE EMERGÊNCIA

### 11.1 Falha Crítica de Sistema

**Sintomas:**
- Sistema completamente offline
- API Betfair inacessível
- Base de dados corrompida
- Perda de dados

**Ação Imediata:**
1. **PARAR TODAS AS APOSTAS**
   - Nenhuma nova aposta manual ou automática
   - Notificar operador imediatamente

2. **AVALIAR SITUAÇÃO**
   - Determinar scope do problema
   - Identificar causa raiz se possível
   - Estimar tempo de recuperação

3. **PROTEGER BANCA**
   - Verificar saldo Betfair
   - Confirmar que nenhuma aposta pendente
   - Ativar 2FA extra se necessário

4. **INICIAR RECUPERAÇÃO**
   - Restaurar backup mais recente
   - Reparar infraestrutura
   - Validar sistema

5. **RECONCILIAR**
   - Comparar dados antes/depois
   - Identificar apostas perdidas
   - Registrar manualmente se necessário

6. **DOCUMENTAR**
   - Timeline do incidente
   - Causa raiz
   - Impacto financeiro
   - Medidas preventivas

### 11.2 Aposta Incorreta Executada

**Sintomas:**
- Stake errado
- Seleção errada
- Mercado errado
- Duplicação de aposta

**Ação Imediata:**
1. **IDENTIFICAR ERRO**
   - Qual aposta está incorreta?
   - Qual é o erro exato?
   - Quando ocorreu?

2. **AVALIAR POSSIBILIDADE DE CANCELAMENTO**
   - Mercado ainda aberto?
   - Betfair permite cancelamento?
   - Tempo desde execução?

3. **SE CANCELAMENTO POSSÍVEL:**
   - Cancelar imediatamente via Betfair
   - Confirmar cancelamento
   - Registrar no sistema

4. **SE CANCELAMENTO IMPOSSÍVEL:**
   - Aceitar resultado da aposta
   - Documentar erro detalhadamente
   - Investigar causa raiz
   - Implementar prevenção

5. **PREVENÇÃO FUTURA**
   - Adicionar validação extra
   - Revisar checklist pré-aposta
   - Treinar operador
   - Testar sistema

### 11.3 Drawdown Excessivo

**Sintomas:**
- Drawdown > 20% da banca
- Sequência de perdas prolongada
- ROI negativo por período estendido

**Ação Imediata:**
1. **PARAR OPERAÇÃO**
   - Nenhuma nova aposta
   - Notificar responsável

2. **AVALIAR SITUAÇÃO**
   - Calcular drawdown exato
   - Identificar período de perdas
   - Analisar causas possíveis

3. **ANÁLISE DE CAUSAS**
   - Modelo deteriorou?
   - Condições de mercado mudaram?
   - Erros operacionais?
   - Mera variância estatística?

4. **DECISÃO:**
   ```
   SE drawdown < 25% E causas identificadas E corrigíveis:
       → Corrigir problema
       → Continuar com stake reduzido (50%)
       → Monitorizar intensivamente

   SE drawdown > 25% OU causas não identificadas:
       → Parar operação por 7 dias
       → Revisar modelo completamente
       → Considerar rollback para paper trading
   ```

5. **DOCUMENTAÇÃO**
   - Análise completa de causas
   - Plano de correção
   - Timeline de recuperação

### 11.4 Suspeita de Fraude ou Comprometimento

**Sintomas:**
- Transações não autorizadas
- Acesso suspeito à conta
- Alterações não autorizadas no sistema
- Comportamento anormal da API

**Ação Imediata:**
1. **ISOLAR SISTEMA**
   - Parar todas as operações
   - Desconectar APIs
   - Mudar passwords imediatamente

2. **PROTEGER BANCA**
   - Transferir banca para conta segura
   - Notificar Betfair de atividade suspeita
   - Ativar bloqueio temporário

3. **INVESTIGAR**
   - Revisar logs de acesso
   - Verificar transações
   - Identificar origem do comprometimento

4. **NOTIFICAR**
   - Autoridades se necessário
   - Banco se comprometimento financeiro
   - Time de segurança

5. **RECUPERAR**
   - Limpar sistema
   - Restaurar de backup limpo
   - Implementar segurança adicional

6. **DOCUMENTAR**
   - Relatório completo de incidente
   - Lições aprendidas
   - Melhorias de segurança

---

## 12. INTEGRAÇÃO COM SISTEMAS DE TRACKING

### 12.1 Sistema de Tracking de Apostas

```python
class BetTrackingSystem:
    def __init__(self, db_config):
        self.db = Database(db_config)

    def register_bet(self, signal, execution):
        """Registra aposta executada"""
        bet = {
            'bet_id': str(uuid.uuid4()),
            'signal_id': signal.id,
            'game_id': signal.game_id,
            'market_type': signal.market_type,
            'selection': signal.selection,

            # Sinal
            'signal_odds': signal.odds,
            'signal_stake': signal.stake,
            'signal_timestamp': signal.timestamp,

            # Execução
            'execution_odds': execution.odds_obtained,
            'execution_stake': execution.stake,
            'execution_timestamp': execution.timestamp,
            'execution_status': execution.status,

            # Metadados
            'betfair_bet_id': execution.betfair_id,
            'mode': 'real',
            'created_at': datetime.now()
        }

        self.db.insert('bets', bet)
        return bet['bet_id']

    def update_result(self, bet_id, result):
        """Atualiza resultado da aposta"""
        update = {
            'result': result.outcome,  # 'WIN', 'LOSS', 'VOID'
            'pnl': result.pnl,
            'closing_odds': result.closing_odds,
            'clv_expost': result.clv,
            'result_timestamp': datetime.now()
        }

        self.db.update('bets', bet_id, update)

    def calculate_daily_metrics(self, date):
        """Calcula métricas do dia"""
        query = """
        SELECT
            COUNT(*) as n_bets,
            SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as n_wins,
            SUM(pnl) as total_pnl,
            AVG(clv_expost) as avg_clv,
            AVG((execution_odds / signal_odds) - 1) as avg_slippage
        FROM bets
        WHERE DATE(execution_timestamp) = %s
        AND mode = 'real'
        """
        return self.db.execute_one(query, (date,))
```

### 12.2 Reconciliação Automática

```python
class BetfairReconciler:
    def __init__(self, betfair_api, tracking_db):
        self.betfair = betfair_api
        self.db = tracking_db

    def reconcile_daily(self, date):
        """Reconcilia apostas do dia com Betfair"""
        # 1. Obter apostas da Betfair
        betfair_bets = self.betfair.get_settled_bets(date)

        # 2. Obter apostas do sistema
        system_bets = self.db.get_bets_by_date(date, mode='real')

        # 3. Comparar
        discrepancies = self.compare_bets(betfair_bets, system_bets)

        # 4. Reportar
        if discrepancies:
            self.send_alert(discrepancies)
        else:
            self.log_success()

        return discrepancies

    def compare_bets(self, betfair_bets, system_bets):
        """Compara apostas e identifica discrepâncias"""
        discrepancies = []

        # Criar mapa por ID
        betfair_map = {b['bet_id']: b for b in betfair_bets}
        system_map = {b['betfair_bet_id']: b for b in system_bets}

        # Verificar apostas em Betfair mas não no sistema
        for bet_id in betfair_map:
            if bet_id not in system_map:
                discrepancies.append({
                    'type': 'MISSING_IN_SYSTEM',
                    'bet_id': bet_id,
                    'betfair_bet': betfair_map[bet_id]
                })

        # Verificar apostas no sistema mas não na Betfair
        for betfair_id in system_map:
            if betfair_id not in betfair_map:
                discrepancies.append({
                    'type': 'MISSING_IN_BETFAIR',
                    'betfair_bet_id': betfair_id,
                    'system_bet': system_map[betfair_id]
                })

        # Verificar detalhes de apostas correspondentes
        for bet_id in betfair_map:
            if bet_id in system_map:
                bf = betfair_map[bet_id]
                sys = system_map[bet_id]

                if abs(bf['stake'] - sys['execution_stake']) > 0.01:
                    discrepancies.append({
                        'type': 'STAKE_MISMATCH',
                        'bet_id': bet_id,
                        'betfair_stake': bf['stake'],
                        'system_stake': sys['execution_stake']
                    })

                if abs(bf['odds'] - sys['execution_odds']) > 0.01:
                    discrepancies.append({
                        'type': 'ODDS_MISMATCH',
                        'bet_id': bet_id,
                        'betfair_odds': bf['odds'],
                        'system_odds': sys['execution_odds']
                    })

        return discrepancies
```

---

## 13. IMPLEMENTAÇÃO COMPLETA

### 13.1 Script Robusto de Operações Reais
```python
"""
Sistema completo de operações reais para value betting
Inclui tracking de apostas, reconciliação, e gestão de banca
"""

import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd
import numpy as np

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BetRecord:
    """Registro de aposta"""
    bet_id: str
    signal_id: str
    game_id: str
    market: str
    selection: str
    odd_signal: float
    odd_executed: float
    stake: float
    outcome: Optional[str] = None  # 'win', 'loss', 'void', None
    pnl: Optional[float] = None
    clv: Optional[float] = None
    slippage: Optional[float] = None
    latency_seconds: Optional[float] = None
    betfair_bet_id: Optional[str] = None
    executed_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None

@dataclass
class DailyMetrics:
    """Métricas diárias"""
    date: str
    n_bets: int
    n_wins: int
    n_losses: int
    total_pnl: float
    roi: float
    avg_clv: float
    avg_slippage: float
    max_drawdown: float
    bankroll: float

class BetTrackingSystem:
    """Sistema de tracking de apostas"""
    
    def __init__(self, db_config: Dict, betfair_api=None):
        self.db_config = db_config
        self.betfair_api = betfair_api
        self.bets = []
        
        logger.info("📊 BetTrackingSystem inicializado")
    
    def register_bet(self, signal: Dict, execution: Dict) -> str:
        """Registra aposta executada"""
        bet = BetRecord(
            bet_id=f"BET-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(self.bets)+1:03d}",
            signal_id=signal['signal_id'],
            game_id=signal['game_id'],
            market=signal['market'],
            selection=signal['selection'],
            odd_signal=signal['odd'],
            odd_executed=execution['odd_executed'],
            stake=execution['stake'],
            slippage=(execution['odd_executed'] / signal['odd'] - 1) if signal['odd'] > 0 else 0,
            latency_seconds=execution.get('latency_seconds'),
            betfair_bet_id=execution.get('betfair_bet_id'),
            executed_at=datetime.now()
        )
        
        self.bets.append(bet)
        
        logger.info(f"✅ Aposta registrada: {bet.bet_id} - {bet.market} - €{bet.stake:.2f}")
        
        return bet.bet_id
    
    def update_result(self, bet_id: str, outcome: str, pnl: float,
                     closing_odd: Optional[float] = None):
        """Atualiza resultado da aposta"""
        bet = next((b for b in self.bets if b.bet_id == bet_id), None)
        
        if bet:
            bet.outcome = outcome
            bet.pnl = pnl
            bet.settled_at = datetime.now()
            
            # Calcular CLV se closing odd disponível
            if closing_odd and bet.odd_executed > 0:
                bet.clv = (closing_odd / bet.odd_executed - 1)
            
            logger.info(f"📊 Resultado atualizado: {bet_id} - {outcome} - PnL: €{pnl:.2f}")
        else:
            logger.warning(f"❌ Aposta não encontrada: {bet_id}")
    
    def calculate_daily_metrics(self, date: str) -> DailyMetrics:
        """Calcula métricas do dia"""
        day_bets = [b for b in self.bets if b.executed_at and b.executed_at.strftime('%Y-%m-%d') == date]
        
        if not day_bets:
            return DailyMetrics(date=date, n_bets=0, n_wins=0, n_losses=0,
                              total_pnl=0.0, roi=0.0, avg_clv=0.0,
                              avg_slippage=0.0, max_drawdown=0.0, bankroll=0.0)
        
        n_bets = len(day_bets)
        n_wins = sum(1 for b in day_bets if b.outcome == 'win')
        n_losses = sum(1 for b in day_bets if b.outcome == 'loss')
        
        total_pnl = sum(b.pnl for b in day_bets if b.pnl is not None)
        total_stake = sum(b.stake for b in day_bets)
        roi = total_pnl / total_stake if total_stake > 0 else 0.0
        
        avg_clv = np.mean([b.clv for b in day_bets if b.clv is not None]) if any(b.clv is not None for b in day_bets) else 0.0
        avg_slippage = np.mean([b.slippage for b in day_bets if b.slippage is not None]) if any(b.slippage is not None for b in day_bets) else 0.0
        
        return DailyMetrics(
            date=date,
            n_bets=n_bets,
            n_wins=n_wins,
            n_losses=n_losses,
            total_pnl=total_pnl,
            roi=roi,
            avg_clv=avg_clv,
            avg_slippage=avg_slippage,
            max_drawdown=0.0,  # Calculado separadamente
            bankroll=0.0  # Calculado separadamente
        )
    
    def export_to_csv(self, filepath: str):
        """Exporta apostas para CSV"""
        if not self.bets:
            logger.warning("⚠️  Nenhuma aposta para exportar")
            return
        
        df = pd.DataFrame([asdict(b) for b in self.bets])
        df.to_csv(filepath, index=False)
        
        logger.info(f"💾 Apostas exportadas: {filepath}")
    
    def get_open_bets(self) -> List[BetRecord]:
        """Retorna apostas em aberto"""
        return [b for b in self.bets if b.outcome is None]
    
    def get_bet_history(self, days: int = 30) -> List[BetRecord]:
        """Retorna histórico de apostas"""
        cutoff = datetime.now() - timedelta(days=days)
        return [b for b in self.bets if b.executed_at and b.executed_at >= cutoff]

class BetfairReconciler:
    """Reconciliador com Betfair"""
    
    def __init__(self, betfair_api, tracking_system: BetTrackingSystem):
        self.betfair_api = betfair_api
        self.tracking = tracking_system
        
        logger.info("🔄 BetfairReconciler inicializado")
    
    def reconcile_daily(self, date: str) -> Dict:
        """Reconcilia apostas do dia com Betfair"""
        logger.info(f"🔄 Reconciliando apostas de {date}...")
        
        # 1. Obter apostas da Betfair
        try:
            betfair_bets = self.betfair_api.get_settled_bets(date) if self.betfair_api else []
        except Exception as e:
            logger.error(f"❌ Erro ao obter apostas da Betfair: {e}")
            betfair_bets = []
        
        # 2. Obter apostas do sistema
        system_bets = [b for b in self.tracking.bets
                      if b.executed_at and b.executed_at.strftime('%Y-%m-%d') == date]
        
        # 3. Comparar
        discrepancies = self._compare_bets(betfair_bets, system_bets)
        
        # 4. Reportar
        result = {
            'date': date,
            'betfair_count': len(betfair_bets),
            'system_count': len(system_bets),
            'discrepancies': discrepancies,
            'reconciled': len(discrepancies) == 0
        }
        
        if discrepancies:
            logger.warning(f"⚠️  {len(discrepancies)} discrepâncias encontradas")
            for d in discrepancies:
                logger.warning(f"   {d['type']}: {d}")
        else:
            logger.info("✅ Reconciliação: OK")
        
        return result
    
    def _compare_bets(self, betfair_bets: List[Dict], system_bets: List[BetRecord]) -> List[Dict]:
        """Compara apostas e identifica discrepâncias"""
        discrepancies = []
        
        # Criar mapa por ID
        betfair_map = {b.get('bet_id'): b for b in betfair_bets}
        system_map = {b.betfair_bet_id: b for b in system_bets if b.betfair_bet_id}
        
        # Verificar apostas em Betfair mas não no sistema
        for bet_id, bf in betfair_map.items():
            if bet_id not in system_map:
                discrepancies.append({
                    'type': 'MISSING_IN_SYSTEM',
                    'bet_id': bet_id,
                    'details': bf
                })
        
        # Verificar apostas no sistema mas não na Betfair
        for bet_id, sys in system_map.items():
            if bet_id not in betfair_map:
                discrepancies.append({
                    'type': 'MISSING_IN_BETFAIR',
                    'bet_id': bet_id,
                    'details': asdict(sys)
                })
        
        # Comparar stakes e odds
        for bet_id in set(betfair_map.keys()) & set(system_map.keys()):
            bf = betfair_map[bet_id]
            sys = system_map[bet_id]
            
            if abs(bf.get('stake', 0) - sys.stake) > 0.01:
                discrepancies.append({
                    'type': 'STAKE_MISMATCH',
                    'bet_id': bet_id,
                    'betfair_stake': bf.get('stake'),
                    'system_stake': sys.stake
                })
            
            if abs(bf.get('odds', 0) - sys.odd_executed) > 0.01:
                discrepancies.append({
                    'type': 'ODDS_MISMATCH',
                    'bet_id': bet_id,
                    'betfair_odds': bf.get('odds'),
                    'system_odds': sys.odd_executed
                })
        
        return discrepancies

class BankrollManager:
    """Gestor de banca"""
    
    def __init__(self, initial_bankroll: float = 1000.0, reserve_pct: float = 0.2):
        self.initial_bankroll = initial_bankroll
        self.reserve_pct = reserve_pct
        self.current_bankroll = initial_bankroll
        self.peak_bankroll = initial_bankroll
        self.reserve = initial_bankroll * reserve_pct
        self.active_bankroll = initial_bankroll * (1 - reserve_pct)
        
        logger.info("💰 BankrollManager inicializado")
    
    def update_after_bet(self, pnl: float):
        """Atualiza banca após aposta"""
        self.current_bankroll += pnl
        
        if self.current_bankroll > self.peak_bankroll:
            self.peak_bankroll = self.current_bankroll
        
        # Recalcular reserve e active
        self.reserve = self.current_bankroll * self.reserve_pct
        self.active_bankroll = self.current_bankroll * (1 - self.reserve_pct)
        
        logger.info(f"💰 Banca atualizada: €{self.current_bankroll:.2f} (Peak: €{self.peak_bankroll:.2f})")
    
    def get_drawdown(self) -> float:
        """Calcula drawdown atual"""
        if self.peak_bankroll <= 0:
            return 0.0
        return (self.peak_bankroll - self.current_bankroll) / self.peak_bankroll
    
    def can_bet(self, stake: float) -> bool:
        """Verifica se pode apostar"""
        if self.active_bankroll <= 0:
            return False
        
        if stake > self.active_bankroll * 0.02:  # Max 2% da banca ativa
            return False
        
        return True
    
    def get_status(self) -> Dict:
        """Retorna status da banca"""
        return {
            'initial_bankroll': self.initial_bankroll,
            'current_bankroll': self.current_bankroll,
            'peak_bankroll': self.peak_bankroll,
            'reserve': self.reserve,
            'active_bankroll': self.active_bankroll,
            'drawdown': self.get_drawdown(),
            'profit': self.current_bankroll - self.initial_bankroll
        }

class DailyReconciliationReport:
    """Gerador de relatório de reconciliação diária"""
    
    def __init__(self, tracking_system: BetTrackingSystem, bankroll_manager: BankrollManager):
        self.tracking = tracking_system
        self.bankroll = bankroll_manager
        
        logger.info("📄 DailyReconciliationReport inicializado")
    
    def generate(self, date: str) -> str:
        """Gera relatório de reconciliação"""
        metrics = self.tracking.calculate_daily_metrics(date)
        status = self.bankroll.get_status()
        
        report = f"""
        ═══════════════════════════════════════════════════════════════
        RELATÓRIO DE RECONCILIAÇÃO DIÁRIA
        Data: {date}
        ══════───────────────────────────────────────────────────────────
        
        RESUMO
        ───────────────────────────────────────────────────────────────
        Apostas no sistema: {metrics.n_bets}
        Apostas WIN: {metrics.n_wins}
        Apostas LOSS: {metrics.n_losses}
        
        PnL Sistema: €{metrics.total_pnl:.2f}
        ROI do dia: {metrics.roi:.2%}
        
        DETALHES
        ───────────────────────────────────────────────────────────────
        CLV médio: {metrics.avg_clv:.2%}
        Slippage médio: {metrics.avg_slippage:.2%}
        
        BANCA
        ───────────────────────────────────────────────────────────────
        Banca atual: €{status['current_bankroll']:.2f}
        Peak banca: €{status['peak_bankroll']:.2f}
        Drawdown: {status['drawdown']:.2%}
        Lucro total: €{status['profit']:.2f}
        
        STATUS: RECONCILIADO ✓
        ═══════════════════════════════════════════════════════════════
        """
        
        return report

# Uso
if __name__ == "__main__":
    # Criar componentes
    tracking = BetTrackingSystem(db_config={})
    bankroll = BankrollManager(initial_bankroll=500.0)
    reconciler = BetfairReconciler(betfair_api=None, tracking_system=tracking)
    report_generator = DailyReconciliationReport(tracking, bankroll)
    
    # Exemplo: registrar aposta
    signal = {
        'signal_id': 'SIG-001',
        'game_id': '0022300001',
        'market': 'moneyline',
        'selection': 'Celtics',
        'odd': 1.85
    }
    
    execution = {
        'odd_executed': 1.84,
        'stake': 10.0,
        'latency_seconds': 2.5,
        'betfair_bet_id': 'BF-123456'
    }
    
    bet_id = tracking.register_bet(signal, execution)
    
    # Exemplo: atualizar resultado
    tracking.update_result(bet_id, 'win', 8.40, closing_odd=1.75)
    bankroll.update_after_bet(8.40)
    
    # Gerar relatório
    today = datetime.now().strftime('%Y-%m-%d')
    report = report_generator.generate(today)
    print(report)
    
    # Reconciliar
    reconciliation = reconciler.reconcile_daily(today)
    print(f"Reconciliação: {reconciliation}")
```

---

## 14. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[08_Risk_Management/INDEX]] → Kelly, drawdown, circuit breakers
- [[09_Execution_System/INDEX]] → Como as apostas são executadas
- [[21_Paper_Trading/INDEX]] → Fase anterior que validou o sistema
- [[23_Scaling/INDEX]] → Escala de banca após micro banca
- [[44_Exchange_Execution/INDEX]] → Execução automática via API
- [[MICRO_BANCA_PROTOCOL]] → Protocolo detalhado de micro banca
