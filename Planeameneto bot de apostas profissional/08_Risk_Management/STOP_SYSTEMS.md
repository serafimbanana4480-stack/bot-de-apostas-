# Stop Systems

**ID:** RM-008 | **Fase:** Fase 4+ | **Owner:** Risk Manager

---

## 1. OBJETIVO

Definir sistemas de parada automática e manual para proteger a banca em situações de risco elevado ou performance insatisfatória.

---

## 2. TIPOS DE STOP

### 2.1 Stop Loss (Banca)

**Definição:** Parar operações se drawdown exceder threshold

| Threshold | Ação | Condição de Retorno |
|-----------|------|---------------------|
| 15% | Warning | - |
| 20% | Parar novas apostas | ROI últimos 7 dias > 0% |
| 30% | Parar operação completa | ROI últimos 30 dias > 2% |

**Implementação:**
```python
def check_stop_loss(bankroll, initial_bankroll):
    """
    Verifica se stop loss foi atingido
    """
    drawdown = (initial_bankroll - bankroll) / initial_bankroll
    
    if drawdown >= 0.30:
        return 'FULL_STOP', 'Drawdown >= 30%'
    elif drawdown >= 0.20:
        return 'PARTIAL_STOP', 'Drawdown >= 20%'
    elif drawdown >= 0.15:
        return 'WARNING', 'Drawdown >= 15%'
    else:
        return 'NORMAL', 'Drawdown aceitável'
```

### 2.2 Stop Loss (Sequencial)

**Definição:** Parar se X apostas consecutivas perdidas

| Threshold | Ação | Condição de Retorno |
|-----------|------|---------------------|
| 5 losses | Warning | 1 win |
| 8 losses | Parar novas apostas | 2 wins em 3 apostas |
| 10 losses | Parar operação completa | 3 wins em 5 apostas |

**Implementação:**
```python
def check_sequential_stop_loss(recent_bets):
    """
    Verifica stop loss sequencial
    """
    losses = [bet for bet in recent_bets if bet['outcome'] == 'loss']
    consecutive_losses = count_consecutive(losses)
    
    if consecutive_losses >= 10:
        return 'FULL_STOP', f'{consecutive_losses} losses consecutivas'
    elif consecutive_losses >= 8:
        return 'PARTIAL_STOP', f'{consecutive_losses} losses consecutivas'
    elif consecutive_losses >= 5:
        return 'WARNING', f'{consecutive_losses} losses consecutivas'
    else:
        return 'NORMAL', 'Sem sequência de losses'
```

### 2.3 Stop CLV

**Definição:** Parar se CLV médio cair abaixo de threshold

| Threshold | Ação | Condição de Retorno |
|-----------|------|---------------------|
| CLV < 1% (3 dias) | Warning | CLV > 1.5% (7 dias) |
| CLV < 0% (5 dias) | Parar novas apostas | CLV > 1.5% (14 dias) |
| CLV < -1% (7 dias) | Parar operação completa | CLV > 2% (30 dias) |

**Implementação:**
```python
def check_clv_stop(recent_clv_values):
    """
    Verifica stop baseado em CLV
    """
    avg_clv_3d = np.mean(recent_clv_values[-3:])
    avg_clv_5d = np.mean(recent_clv_values[-5:])
    avg_clv_7d = np.mean(recent_clv_values[-7:])
    
    if avg_clv_7d < -0.01:
        return 'FULL_STOP', f'CLV 7d = {avg_clv_7d:.2%}'
    elif avg_clv_5d < 0.00:
        return 'PARTIAL_STOP', f'CLV 5d = {avg_clv_5d:.2%}'
    elif avg_clv_3d < 0.01:
        return 'WARNING', f'CLV 3d = {avg_clv_3d:.2%}'
    else:
        return 'NORMAL', 'CLV aceitável'
```

### 2.4 Stop Volume

**Definição:** Parar se volume de apostas exceder limite

| Threshold | Ação | Condição de Retorno |
|-----------|------|---------------------|
| > 15 apostas/dia | Warning | Próximo dia |
| > 20 apostas/dia | Parar novas apostas | Próximo dia |
| > 50 apostas/semana | Parar operação | Próxima semana |

**Implementação:**
```python
def check_volume_stop(daily_bets, weekly_bets):
    """
    Verifica stop baseado em volume
    """
    if len(weekly_bets) > 50:
        return 'FULL_STOP', f'{len(weekly_bets)} apostas na semana'
    elif len(daily_bets) > 20:
        return 'PARTIAL_STOP', f'{len(daily_bets)} apostas no dia'
    elif len(daily_bets) > 15:
        return 'WARNING', f'{len(daily_bets)} apostas no dia'
    else:
        return 'NORMAL', 'Volume aceitável'
```

### 2.5 Stop Manual

**Definição:** Parada manual por decisão do operador

**Motivos:**
- Eventos externos (lesões, notícias)
- Problemas técnicos
- Descanso/tilt
- Planejamento estratégico

**Implementação:**
```python
def manual_stop(reason, duration_hours=None):
    """
    Ativa stop manual
    """
    stop_record = {
        'type': 'MANUAL',
        'reason': reason,
        'started_at': datetime.now(),
        'duration_hours': duration_hours,
        'status': 'ACTIVE'
    }
    
    # Registrar em audit log
    audit_log.add(stop_record)
    
    # Notificar equipe
    send_alert(
        severity='HIGH',
        message=f"Manual stop ativado: {reason}",
        channel='telegram'
    )
    
    return stop_record
```

---

## 3. SISTEMA DE RETOMADA

### 3.1 Processo de Retomada

```
1. Stop ativado
2. Sistema avalia condição de retomada
3. Se condição satisfeita → notificar operador
4. Operador aprova retomada manual
5. Sistema retoma operações
6. Monitorizar intensivamente (primeiros 10 sinais)
```

### 3.2 Validação Pré-Retomada

```python
def validate_resume_conditions(stop_type, current_metrics):
    """
    Valida se condições de retomada estão satisfeitas
    """
    validations = {
        'STOP_LOSS_BANKROLL': current_metrics['roi_7d'] > 0,
        'STOP_LOSS_SEQUENTIAL': validate_sequential_win(current_metrics['recent_bets']),
        'STOP_CLV': current_metrics['clv_7d'] > 0.015,
        'STOP_VOLUME': True,  # Volume reset automaticamente
        'STOP_MANUAL': True  # Manual requer aprovação explícita
    }
    
    return validations.get(stop_type, False)
```

---

## 4. HIERARQUIA DE STOPS

### 4.1 Prioridade

1. **Stop Manual** (mais alto) - Override tudo
2. **Stop CLV** - Indica problema no modelo
3. **Stop Loss Bankroll** - Proteção de banca
4. **Stop Loss Sequencial** - Proteção contra tilt
5. **Stop Volume** - Proteção contra over-trading

### 4.2 Lógica de Decisão

```python
def evaluate_stops(all_stops):
    """
    Avalia todos os stops e retorna ação mais severa
    """
    stop_hierarchy = {
        'FULL_STOP': 3,
        'PARTIAL_STOP': 2,
        'WARNING': 1,
        'NORMAL': 0
    }
    
    most_severe = max(
        all_stops,
        key=lambda x: stop_hierarchy[x['action']]
    )
    
    return most_severe
```

---

## 5. DASHBOARD DE STOPS

### 5.1 Visualizações

**Status Atual:**
- Stop ativo (tipo, motivo, duração)
- Condições de retomada
- Tempo até retomada possível

**Histórico:**
- Stops últimos 30 dias
- Razões mais comuns
- Tempo médio de stop

**Alertas:**
- Próximo stop (threshold warning)
- Stop ativado recentemente
- Retomada possível

### 5.2 Ações

- Ativar stop manual
- Aprovar retomada
- Ajustar thresholds
- Ver detalhes de stop

---

## 6. MONITORAMENTO

### 6.1 Métricas

| Métrica | Target | Frequência |
|---------|--------|------------|
| Tempo médio de stop | < 24h | Mensal |
| Taxa de falsos positivos | < 10% | Trimestral |
| Tempo para retomada | < 48h | Mensal |
| Número de stops/mês | < 5 | Mensal |

### 6.2 Análise de Stops

**Relatório Mensal:**
- Número de stops por tipo
- Razões mais comuns
- Impacto em performance
- Sugestões de ajuste

---

## 7. CONFIGURAÇÃO

### 7.1 Thresholds Configuráveis

```yaml
stops:
  stop_loss_bankroll:
    warning: 0.15
    partial: 0.20
    full: 0.30
  
  stop_loss_sequential:
    warning: 5
    partial: 8
    full: 10
  
  stop_clv:
    warning_3d: 0.01
    partial_5d: 0.00
    full_7d: -0.01
  
  stop_volume:
    warning: 15
    partial: 20
    full_weekly: 50
```

### 7.2 Condições de Retomada

```yaml
resume_conditions:
  stop_loss_bankroll:
    partial: "roi_7d > 0"
    full: "roi_30d > 0.02"
  
  stop_loss_sequential:
    partial: "2 wins in 3 bets"
    full: "3 wins in 5 bets"
  
  stop_clv:
    partial: "clv_7d > 0.015"
    full: "clv_30d > 0.02"
```

---

## 8. BACKLOG TÉCNICO

- [ ] Implementar sistema de stops automático
- [ ] Criar dashboard de stops
- [ ] Configurar alertas de stop
- [ ] Implementar sistema de retomada
- [ ] Criar relatórios de análise de stops
- [ ] Adicionar configuração dinâmica de thresholds

---

## 9. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]] ← Índice principal
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Circuit breakers
- [[08_Risk_Management/DRAWDOWN_CONTROL]] → Controle de drawdown
- [[26_Runbooks/INDEX]] → Runbooks de resposta
