# DISCIPLINE_FRAMEWORK — Framework de Disciplina Operacional

**ID:** `BP-003` | **Fase:** #phase/4 | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. VISÃO GERAL

Disciplina não é uma característica pessoal — é um **sistema** que garante execução consistente de regras, independentemente do estado emocional. Este framework define checklists, protocolos e mecanismos de accountability para eliminar a necessidade de "força de vontade" nas operações.

**Princípio Central:** O sistema decide, o operador executa. Não há espaço para interpretação.

---

## 2. PILARES DA DISCIPLINA

### 2.1 Os 4 Pilares

| Pilar | Descrição | Implementação |
|-------|-----------|---------------|
| **Sistematização** | Transformar regras em processos automáticos | Checklists, automação, scripts |
| **Externalização** | Remover decisão do operador | Sistema calcula, operador aprova |
| **Accountability** | Tornar ações visíveis e auditáveis | Logs, revisões, buddy system |
| **Redundância** | Múltiplos sistemas de proteção | Circuit breakers, limites hard, revisões |

### 2.2 Filosofia

> "A disciplina não é sobre forçar-se a fazer a coisa certa quando não quer. É sobre criar um sistema onde a coisa certa é a única opção."

**Regra de Ouro:** Se uma decisão depende da força de vontade do operador, o sistema está falhado.

---

## 3. CHECKLISTS OPERACIONAIS

### 3.1 Checklist Diário (Antes de Operar)

**Tempo estimado:** 5 minutos

```markdown
## CHECKLIST PRÉ-OPERAÇÃO

### Estado Físico
- [ ] Dormi ≥7 horas nas últimas 24h?
- [ ] Comi nas últimas 4h?
- [ ] Não estou sob influência de álcool/drogas?
- [ ] Não estou com dor/doença significativa?

### Estado Mental
- [ ] Stress level ≤ 5/10?
- [ ] Não estou sob pressão financeira este mês?
- [ ] Confiança no sistema ≥ 8/10?
- [ ] Motivação é processo, não resultado?

### Ambiente
- [ ] Ambiente de trabalho organizado?
- [ ] Sem distrações (telefone, notificações)?
- [ ] Conexão estável testada?
- [ ] Backup de energia (UPS) disponível?

### Sistema
- [ ] Sistema atualizado?
- [ ] Todos os serviços running?
- [ ] Logs sem erros críticos?
- [ ] Circuit breakers desativados (se apropriado)?

### SE QUALQUER ITEM FOR NÃO → NÃO OPERAR HOJE
```

### 3.2 Checklist de Trade (Por Aposta)

**Tempo estimado:** 30 segundos

```markdown
## CHECKLIST DE TRADE

### Validação de Sinal
- [ ] Sinal completo recebido?
- [ ] Odds dentro do range esperado?
- [ ] Stake calculado pelo sistema (não manual)?
- [ ] Market liquidez suficiente?

### Validação de Risco
- [ ] Exposure dentro dos limites?
- [ ] Não excede max stake?
- [ ] Não viola circuit breakers?
- [ ] Bankroll suficiente?

### Validação de Estado
- [ ] Operador não em tilt (auto-avaliação)?
- [ ] Tempo desde última aposta ≥ 30s?
- [ ] Total de apostas hoje ≤ limite?
- [ ] Tempo de operação hoje ≤ 8h?

### Confirmação
- [ ] Rever todos os itens acima
- [ ] Confirmar execução

### SE QUALQUER ITEM FOR NÃO → NÃO EXECUTAR
```

### 3.3 Checklist Pós-Operação (Fim do Dia)

**Tempo estimado:** 10 minutos

```markdown
## CHECKLIST PÓS-OPERAÇÃO

### Encerramento
- [ ] Todas as posições fechadas?
- [ ] Sistema em modo de manutenção?
- [ ] Logs salvos e arquivados?

### Revisão
- [ ] Número de trades executados: ___
- [ ] P&L do dia: €___
- [ ] Incidentes de tilt: ___
- [ ] Erros técnicos: ___

### Diário
- [ ] Estado mental inicial documentado?
- [ ] Gatilhos de tilt identificados?
- [ ] Lições aprendidas registadas?
- [ ] Melhorias sugeridas?

### Planeamento
- [ ] Horário de operação amanhã definido?
- [ ] Stake máxima amanhã definida?
- [ ] Revisão de métricas agendada?

### Preparação
- [ ] Backup diário realizado?
- [ ] Sistema pronto para amanhã?
```

---

## 4. SISTEMA DE AUTOMAÇÃO DE DECISÕES

### 4.1 Princípio: Sistema Calcula, Operador Executa

**O que o sistema faz AUTOMATICAMENTE:**
- Calcular stake baseado em Kelly Criterion
- Validar odds e probabilidades
- Verificar limites de risco
- Verificar circuit breakers
- Calcular exposure
- Determinar se trade é válido

**O que o operador faz:**
- Verificar que sistema validou trade
- Clicar "confirmar" (one-click)
- Monitorizar execução

**O que o operador NUNCA faz:**
- Calcular stake manualmente
- Decidir se trade é "bom" subjetivamente
- Alterar limites em tempo real
- Ignorar alertas do sistema
- Justificar trades fora do sistema

### 4.2 Implementação Técnica

```python
class AutomatedDecisionSystem:
    """
    Sistema que toma todas as decisões de trading.
    O operador apenas aprova ou rejeita.
    """

    def evaluate_trade(self, market_data: dict) -> TradeDecision:
        """
        Avalia se um trade deve ser executado.
        Retorna decisão + justificação.
        """
        decision = TradeDecision(approved=False, reason="")

        # 1. Validar sinal completo
        if not self._signal_complete(market_data):
            decision.reason = "Sinal incompleto"
            return decision

        # 2. Calcular stake (Kelly)
        stake = self._calculate_kelly_stake(market_data)

        # 3. Validar odds
        if not self._validate_odds(market_data['odds']):
            decision.reason = "Odds fora do range"
            return decision

        # 4. Verificar limites de risco
        if not self._check_risk_limits(stake):
            decision.reason = "Excede limites de risco"
            return decision

        # 5. Verificar circuit breakers
        if self._circuit_breaker_active():
            decision.reason = "Circuit breaker ativo"
            return decision

        # 6. Verificar liquidez
        if not self._check_liquidity(market_data):
            decision.reason = "Liquidez insuficiente"
            return decision

        # Se passou todas as validações
        decision.approved = True
        decision.stake = stake
        decision.reason = "Todas as validações passadas"
        decision.confidence = self._calculate_confidence(market_data)

        return decision

    def present_to_operator(self, decision: TradeDecision):
        """
        Apresenta decisão ao operador de forma clara.
        """
        if decision.approved:
            print(f"""
            ✅ TRADE APROVADO
            Stake: €{decision.stake:.2f}
            Confiança: {decision.confidence:.1%}
            Razão: {decision.reason}

            [CONFIRMAR] ou [REJEITAR]
            """)
        else:
            print(f"""
            ❌ TRADE REJEITADO
            Razão: {decision.reason}

            Nenhuma ação necessária.
            """)
```

### 4.3 Interface de Operador

**Dashboard Simplificado:**
```
┌─────────────────────────────────────────┐
│  SISTEMA DE OPERAÇÕES - VALUE BETTING   │
├─────────────────────────────────────────┤
│                                         │
│  Próximo Trade:                         │
│  ┌─────────────────────────────────┐   │
│  │ Market: Arsenal vs Chelsea       │   │
│  │ Selection: Arsenal Win          │   │
│  │ Odds: 2.15                      │   │
│  │ Stake: €12.50 (Kelly)           │   │
│  │ Confiança: 87%                  │   │
│  │                                 │   │
│  │ [✅ CONFIRMAR]  [❌ REJEITAR]   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Métricas Hoje:                         │
│  Trades: 12 | P&L: +€45.30            │
│  Tilt Score: 15/100 (Verde)            │
│                                         │
│  Próxima pausa em: 45 min               │
└─────────────────────────────────────────┘
```

---

## 5. SISTEMA DE LIMITES

### 5.1 Limites Hard-Coded

**Limites que NUNCA podem ser alterados em tempo real:**

| Limite | Valor | Justificação |
|--------|-------|--------------|
| **Max stake por trade** | 2% bankroll | Proteção contra overconfidence |
| **Max trades por dia** | 50 | Prevenção de decision fatigue |
| **Max operação contínua** | 8 horas | Prevenção de fatigue |
| **Max perda diária** | 5% bankroll | Circuit breaker |
| **Max perda semanal** | 10% bankroll | Circuit breaker |
| **Min odds** | 1.5 | Evitar odds muito baixas |
| **Max odds** | 5.0 | Evitar odds muito altas |

### 5.2 Limites Ajustáveis (com processo)

**Limites que podem ser ajustados, mas com processo formal:**

| Limite | Valor Atual | Processo de Ajuste |
|--------|-------------|-------------------|
| **Target Kelly fraction** | 0.25 | Revisão trimestral, aprovação 2 pessoas |
| **Min liquidez** | €10,000 | Revisão mensal |
| **Max exposure por market** | €500 | Revisão mensal |
| **Pauses obrigatórias** | Após 3 perdas | Ajustável com justificação |

**Processo de Ajuste:**
1. Proposta escrita com justificação
2. Backtest com novos parâmetros
3. Aprovação de Risk Manager + Operations Lead
4. Implementação em horário fora de mercado
5. Monitorização aumentada por 1 semana

---

## 6. ACCOUNTABILITY SYSTEM

### 6.1 Logs Auditáveis

**Todas as ações são logadas:**
```json
{
  "timestamp": "2024-01-15T14:30:10Z",
  "operator_id": "op_123",
  "action": "trade_confirmed",
  "trade_id": "trade_456",
  "stake": 12.50,
  "auto_calculated": true,
  "manual_override": false,
  "tilt_score_at_moment": 15,
  "checklist_completed": true
}
```

**Logs são:**
- Imutáveis (append-only)
- Retidos por 7 anos (compliance)
- Revisados semanalmente
- Usados em investigações de incidentes

### 6.2 Revisões Obrigatórias

**Revisão Diária (5 min):**
- Revisar P&L do dia
- Documentar incidentes de tilt
- Verificar adesão a checklists

**Revisão Semanal (30 min):**
- Análise de métricas da semana
- Identificação de padrões
- Ajuste de estratégias se necessário
- Revisão de logs de anomalias

**Revisão Mensal (2 horas):**
- Análise completa de performance
- Backtest de estratégias
- Revisão de limites
- Planeamento do próximo mês

**Revisão Trimestral (1 dia):**
- Auditoria completa do sistema
- Revisão de todos os limites
- Análise de psicologia
- Planeamento estratégico

### 6.3 Buddy System

**Se aplicável (equipa >1 pessoa):**
- Cada operador tem um "buddy"
- Check-in diário (estado mental)
- Notificação se tilt detetado
- Revisão semanal conjunta
- Accountability mútua

---

## 7. PROTOCOLO DE VIOLAÇÃO

### 7.1 O que acontece se o operador violar regras?

**Violação Menor (ex: não completar checklist):**
1. Alerta automático no sistema
2. Notificação ao buddy/supervisor
3. Revisão obrigatória no final do dia
4. Documentação no diário

**Violação Moderada (ex: alterar stake manualmente):**
1. Sistema bloqueia ação se possível
2. Notificação imediata a supervisor
3. Pausa obrigatória de 1 dia
4. Revisão completa com supervisor
5. Plano de ação corretiva

**Violação Grave (ex: desativar circuit breaker):**
1. Sistema bloqueia ação (requer 2-factor approval)
2. Notificação imediata a toda a equipa
3. Suspensão temporária (3-7 dias)
3. Revisão completa com Risk Manager
4. Treinamento obrigatório
5. Probation period (30 dias)

**Violação Crítica (ex: fraude, sabotagem):**
1. Encerramento imediato de acessos
2. Investigação forense
3. Ações legais se aplicável
4. Terminação

### 7.2 Sistema de "Strike"

**3 strikes em 30 dias = Suspensão temporária**
**5 strikes em 90 dias = Revisão de continuidade**

Strike expira após 90 dias sem incidentes.

---

## 8. MELHORIA CONTÍNUA

### 8.1 Feedback Loop

1. **Operar** → Seguir checklists e protocolos
2. **Monitorizar** → Logs automáticos + revisões manuais
3. **Analisar** → Identificar padrões e problemas
4. **Ajustar** → Melhorar checklists e protocolos
5. **Repetir**

### 8.2 Métricas de Disciplina

| Métrica | Target | Alerta |
|---------|--------|--------|
| **Adesão a checklist pré-operação** | 100% | < 95% |
| **Adesão a checklist de trade** | 100% | < 98% |
| **Adesão a checklist pós-operação** | 100% | < 90% |
| **Trades executados sem validação** | 0 | > 0 |
| **Alterações manuais de stake** | 0 | > 0 |
| **Violações de limites** | 0 | > 0 |

---

## 9. BACKLOG

- [ ] Implementar sistema de checklists digitais
- [ ] Criar dashboard de métricas de disciplina
- [ ] Desenvolver sistema de buddy system
- [ ] Criar templates de revisão (diária/semanal/mensal)
- [ ] Implementar sistema de strikes
- [ ] Desenvolver treinamento de disciplina

---

## 10. LINKS CRUZADOS

- [[38_Betting_Psychology/INDEX]] ← Secão mãe
- [[38_Betting_Psychology/TILT_MANAGEMENT]] → Gestão de tilt
- [[38_Betting_Psychology/EMOTIONAL_REGULATION]] → Regulação emocional
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Limites de risco
- [[22_Real_Money_Operations/INDEX]] → Operações reais