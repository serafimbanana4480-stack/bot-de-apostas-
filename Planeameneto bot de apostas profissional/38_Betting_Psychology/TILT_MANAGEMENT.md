# TILT_MANAGEMENT — Detecção e Gestão de Tilt

**ID:** `BP-002` | **Fase:** #phase/4 | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. VISÃO GERAL

**Tilt** é o estado emocional negativo que afeta o julgamento racional, levando a decisões impulsivas e destrutivas. É a variável mais perigosa em qualquer sistema quantitativo, pois pode destruir meses ou anos de trabalho em poucas horas. Este documento define sistemas de deteção, prevenção e recuperação de tilt.

---

## 2. DEFINIÇÃO DE TILT

### 2.1 O Que é Tilt?

Tilt é um estado de **desregulação emocional** caracterizado por:
- Irritabilidade e frustração
- Pensamento rígido ("tenho que recuperar")
- Aversão a perdas exacerbada
- Impulsividade aumentada
- Negação da realidade

### 2.2 Causas Comuns

| Causa | Exemplo | Probabilidade de Tilt |
|-------|---------|----------------------|
| **Sequência de perdas** | 5 trades consecutivos -EV | Alta (70-80%) |
| **Má sorte percebida** | 3 trades +EV que perdem por variação | Média (40-50%) |
| **Erros técnicos** | Bug no sistema causa perda | Alta (60-70%) |
| **Fatores externos** | Problemas pessoais, stress | Variável |
| **Overtrading** | Operar >8h seguidas | Média (50-60%) |
| **Pressão financeira** | "Preciso ganhar X este mês" | Alta (70-80%) |

---

## 3. SISTEMA DE DETEÇÃO DE TILT

### 3.1 Indicadores Comportamentais

**Sinais de Tilt Leve:**
- [ ] Aumentar stake "só desta vez"
- [ ] Justificar apostas fora do sistema
- [ ] Verificar P&L a cada 5 minutos
- [ ] Irritabilidade leve (suspiros, comentários)
- [ ] Pressa em executar apostas

**Sinais de Tilt Moderado:**
- [ ] Ignorar sinais de risco do sistema
- [ ] Apostar em mercados não aprovados
- [ ] Blaming o sistema ("o algoritmo está errado")
- [ ] Aumentar agressividade de stakes
- [ ] Negar necessidade de pausa

**Sinais de Tilt Severo:**
- [ ] Martingale ou chasing losses
- [ ] Desligar ou ignorar circuit breakers
- [ ] Agressão verbal ou física
- [ ] Decisões completamente irracionais
- [ ] Negação total ("não estou em tilt")

### 3.2 Indicadores Quantitativos (Automáticos)

O sistema monitoriza automaticamente:

```python
class TiltDetector:
    def __init__(self):
        self.thresholds = {
            'consecutive_losses': 5,      # 5 perdas seguidas = alerta
            'loss_streak_increase': 1.5,  # Stake aumenta 50% após perda
            'bet_frequency_spike': 2.0,   # 2x mais apostas que normal
            'time_between_bets': 30,      # Menos de 30s entre apostas
            'deviation_from_kelly': 0.5,  # Stake >50% acima de Kelly
            'manual_override_attempts': 1 # Qualquer tentativa de override
        }

    def check_tilt_indicators(self, user_id: str, recent_bets: list):
        """
        Analisa apostas recentes para detetar padrões de tilt
        Retorna score de tilt (0-100) e indicadores ativos
        """
        indicators = []

        # 1. Sequência de perdas
        consecutive_losses = self._count_consecutive_losses(recent_bets)
        if consecutive_losses >= self.thresholds['consecutive_losses']:
            indicators.append(f"consecutive_losses_{consecutive_losses}")

        # 2. Aumento de stake após perda
        for i in range(1, len(recent_bets)):
            if recent_bets[i-1]['profit'] < 0:
                stake_increase = recent_bets[i]['stake'] / recent_bets[i-1]['stake']
                if stake_increase >= self.thresholds['loss_streak_increase']:
                    indicators.append("stake_increase_after_loss")

        # 3. Frequência de apostas
        if len(recent_bets) >= 2:
            time_diff = (recent_bets[0]['timestamp'] - recent_bets[-1]['timestamp']).total_seconds()
            avg_time = time_diff / len(recent_bets)
            if avg_time < self.thresholds['time_between_bets']:
                indicators.append("high_bet_frequency")

        # 4. Desvio de Kelly
        for bet in recent_bets:
            kelly_stake = calculate_kelly(bet['odds'], bet['probability'])
            actual_stake = bet['stake']
            if actual_stake > kelly_stake * (1 + self.thresholds['deviation_from_kelly']):
                indicators.append("deviation_from_kelly")

        # Calcular score de tilt
        tilt_score = min(100, len(indicators) * 20)

        return tilt_score, indicators
```

### 3.3 Níveis de Alerta

| Nível | Score | Ação Automática | Ação Manual |
|-------|-------|-----------------|-------------|
| **Verde** | 0-20 | Nenhuma | Continuar normal |
| **Amarelo** | 21-40 | Alerta no dashboard | Auto-avaliação |
| **Laranja** | 41-60 | Sugerir pausa | Pausa obrigatória 15min |
| **Vermelho** | 61-80 | Circuit breaker | Pausa obrigatória 1h |
| **Crítico** | 81-100 | Parar sistema | Pausa 24h + revisão |

---

## 4. PREVENÇÃO DE TILT

### 4.1 Prevenção Estrutural (Sistema)

**Regras Hard-Coded:**
```python
# O sistema NÃO permite:
- Aumentar stake beyond Kelly (sem aprovação)
- Apostar após N perdas consecutivas
- Apostar sem sinal completo
- Override de circuit breakers (sem aprovação 2-factor)
- Alterar limites de risco em tempo real
```

**Circuit Breakers Automáticos:**
```python
# Após 3 perdas consecutivas
if consecutive_losses >= 3:
    send_alert("3 consecutive losses detected. Consider taking a break.")
    log_warning("Potential tilt detected")

# Após 5 perdas consecutivas
if consecutive_losses >= 5:
    pause_trading(reason="circuit_breaker_consecutive_losses")
    send_alert("TRADING PAUSED: 5 consecutive losses. Mandatory 30-min break.")
    notify_team("operator_potential_tilt")

# Após 8h de operação contínua
if operation_time >= 8 * 3600:
    pause_trading(reason="decision_fatigue")
    send_alert("TRADING PAUSED: 8h operation limit. Mandatory 1-h break.")
```

### 4.2 Prevenção Pessoal (Operador)

**Checklist Diário Antes de Operar:**
- [ ] Dormi pelo menos 7h?
- [ ] Estou sob stress significativo?
- [ ] Tenho pressões financeiras este mês?
- [ ] Estou sob influência de álcool/drogas?
- [ ] Estou emocionalmente estável?

**Se qualquer resposta for NÃO:** Não operar hoje.

**Regras Pessoais:**
1. Nunca operar após >8h
2. Nunca operar sob influência
3. Nunca operar com pressão financeira
4. Pausa obrigatória após 3 perdas seguidas (15min)
5. Pausa obrigatória após 5 perdas seguidas (30min)
6. Nunca verificar P&L a cada 5min (máximo 1x/hora)

---

## 5. PROTOCOLO DE RECUPERAÇÃO

### 5.1 Quando Tilt é Detetado

**Passo 1: Reconhecimento (0-5 min)**
- Admitir: "Estou em tilt"
- Não justificar, não negar
- Parar imediatamente

**Passo 2: Pausa Física (5-30 min)**
- Afastar-se do ecrã
- Fazer exercício físico (caminhada, stretching)
- Respiração profunda (4-7-8 technique)

**Passo 3: Pausa Mental (30-60 min)**
- Meditação guiada (10-15 min)
- Ler algo não relacionado a apostas
- Conversar com alguém (não sobre apostas)

**Passo 4: Reavaliação (60+ min)**
- Revisar o que causou tilt
- Identificar gatilhos específicos
- Documentar no diário de operações

**Passo 5: Retorno Gradual (após 24h se tilt severo)**
- Retornar com stake reduzida (50%)
- Operar apenas 2-3h no primeiro dia
- Monitorização aumentada

### 5.2 Script de Recuperação

```
QUANDO DETETAR TILT:

1. DIZER EM VOZ ALTA: "Estou em tilt. Vou parar."
2. FECHAR APLICAÇÃO IMEDIATAMENTE
3. AFASTAR-SE DO COMPUTADOR
4. FAZER 10 RESPIRAÇÕES PROFUNDAS (4-7-8)
5. CAMINHAR 10 MINUTOS
6. BEBER ÁGUA
7. NÃO RETORNAR ANTES DE 1 HORA
8. SE TILT SEVERO: NÃO OPERAR HOJE

DOCUMENTAR:
- Data/hora
- Gatilho identificado
- Sintomas
- Ação tomada
```

### 5.3 Exercícios de Grounding

**5-4-3-2-1 Technique:**
- Nomear 5 coisas que vê
- Nomear 4 coisas que pode tocar
- Nomear 3 coisas que ouve
- Nomear 2 coisas que cheira
- Nomear 1 coisa que gosta em si mesmo

**Respiração 4-7-8:**
- Inspirar por 4 segundos
- Segurar por 7 segundos
- Expirar por 8 segundos
- Repetir 4 vezes

**Progressive Muscle Relaxation:**
- Tensionar cada grupo muscular por 5 segundos
- Relaxar por 10 segundos
- Progressar dos pés à cabeça

---

## 6. ACCOUNTABILITY

### 6.1 Sistema de Accountability

**Diário de Operações:**
```markdown
## Data: 2024-01-15

### Estado Mental Inicial
- Energia: 7/10
- Stress: 3/10
- Foco: 8/10
- Confiança no sistema: 9/10

### Gatilhos Identificados
- [ ] Sequência de perdas
- [ ] Erro técnico
- [ ] Pressão financeira
- [ ] Fatores externos

### Incidentes de Tilt
- **14:30** - Tilt moderado detetado após 3 perdas
  - Gatilho: Perda em trade +EV por variação
  - Ação: Pausa 30min, respiração, caminhada
  - Retorno: 15:05, stake normal

### Lições Aprendidas
- Variação estatística é normal, não é "má sorte"
- Pausa preventiva é melhor que recuperar de tilt
```

**Revisão Semanal:**
- Revisar diário de operações
- Identificar padrões de tilt
- Ajustar estratégias de prevenção
- Compartilhar com equipa (se aplicável)

### 6.2 Accountability Externa

**Buddy System:**
- Designar "accountability partner"
- Check-in diário (estado mental)
- Notificar se tilt detetado
- Revisão semanal conjunta

**Professional Help:**
- Se tilt ocorre >3x/semana consistentemente
- Se tilt severo (perdas significativas)
- Se tilt afeta vida pessoal
- Considerar terapia CBT (Cognitive Behavioral Therapy)

---

## 7. ESTATÍSTICAS E MÉTRICAS

### 7.1 Métricas a Monitorizar

| Métrica | Target | Alerta |
|---------|--------|--------|
| **Tilt incidents/mês** | < 2 | > 4 |
| **Perdas em tilt/mês** | €0 | > €100 |
| **Tempo de recuperação** | < 1h | > 4h |
| **Pauses preventivas/mês** | > 5 | < 2 |
| **Adesão ao checklist** | 100% | < 90% |

### 7.2 Análise de Padrões

Mensalmente, analisar:
- Quando o tilt ocorre mais (hora/dia/semana)
- Quais são os gatilhos mais comuns
- Quais técnicas de recuperação funcionam melhor
- Se circuit breakers estão a funcionar

---

## 8. BACKLOG

- [ ] Implementar detector de tilt automático em produção
- [ ] Criar dashboard de métricas de tilt
- [ ] Desenvolver app de breathing exercises
- [ ] Criar templates de diário de operações
- [ ] Implementar buddy system
- [ ] Pesquisar terapeutas CBT especializados em trading

---

## 9. LINKS CRUZADOS

- [[38_Betting_Psychology/INDEX]] ← Secão mãe
- [[38_Betting_Psychology/DISCIPLINA_FRAMEWORK]] → Framework de disciplina
- [[38_Betting_Psychology/EMOTIONAL_REGULATION]] → Regulação emocional
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Circuit breakers automáticos