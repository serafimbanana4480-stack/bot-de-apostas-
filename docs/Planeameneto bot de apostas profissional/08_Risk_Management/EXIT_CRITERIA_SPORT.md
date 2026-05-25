# EXIT CRITERIA BY SPORT — Regras de Desligamento

**ID:** `SEC-08` | **Status:** #status/pending | **Versão:** `2.0.0-EXIT`

---

## 1. OBJETIVO

Definir critérios de desligamento (kill switch) por desporto para evitar perdas excessivas.

---

## 2. PRINCÍPIO FUNDAMENTAL

**É melhor parar cedo e viver para apostar outro dia do que continuar e perder tudo.**

Os critérios de exit são triggers automáticos que pausam apostas num desporto específico quando o modelo ou o mercado deixam de ser favoráveis.

---

## 3. CRITÉRIOS DE EXIT POR DESPORTO

### 3.1 NBA

**Trigger 1: Drawdown Excessivo**
- Condição: Drawdown NBA > 15% da banca alocada à NBA
- Ação: Pausar apostas NBA imediatamente
- Reativação: Requer revisão manual e aprovação após análise

**Trigger 2: CLV Negativo Prolongado**
- Condição: CLV médio < 0% em 50 apostas consecutivas
- Ação: Pausar apostas NBA
- Reativação: Se CLV voltar a > 1% em 20 apostas após revisão

**Trigger 3: Loss Streak**
- Condição: 15 perdas consecutivas
- Ação: Pausar apostas NBA
- Reativação: Após 3 vitórias consecutivas em shadow mode

**Trigger 4: Modelo Degradado**
- Condição: Performance no set de validação cai < 2% CLV
- Ação: Pausar apostas NBA
- Reativação: Após retreino e validação com CLV > 2%

### 3.2 Football

**Trigger 1: Drawdown Excessivo**
- Condição: Drawdown Football > 18% da banca alocada à Football
- Ação: Pausar apostas Football imediatamente
- Reativação: Requer revisão manual

**Trigger 2: CLV Negativo Prolongado**
- Condição: CLV médio < 0% em 40 apostas consecutivas
- Ação: Pausar apostas Football
- Reativação: Se CLV voltar a > 1% em 15 apostas após revisão

**Trigger 3: Loss Streak**
- Condição: 12 perdas consecutivas
- Ação: Pausar apostas Football
- Reativação: Após 2 vitórias consecutivas em shadow mode

**Trigger 4: Liquidez Insuficiente**
- Condição: Volume médio por aposta < 100€ em 10 apostas consecutivas
- Ação: Pausar apostas Football
- Reativação: Quando volume recuperar

### 3.3 MMA/UFC

**Trigger 1: Drawdown Excessivo**
- Condição: Drawdown MMA > 20% da banca alocada à MMA
- Ação: Pausar apostas MMA imediatamente
- Reativação: Requer revisão manual

**Trigger 2: CLV Negativo Prolongado**
- Condição: CLV médio < 0% em 30 apostas consecutivas
- Ação: Pausar apostas MMA
- Reativação: Se CLV voltar a > 1% em 10 apostas após revisão

**Trigger 3: Loss Streak**
- Condição: 10 perdas consecutivas
- Ação: Pausar apostas MMA
- Reativação: Após 2 vitórias consecutivas em shadow mode

**Trigger 4: Incerteza Excessiva**
- Condição: effective_sample_size médio < 3 em 10 apostas consecutivas
- Ação: Pausar apostas MMA
- Reativação: Quando sample size aumentar

---

## 4. PROCEDIMENTO DE DESLIGAMENTO

### 4.1 Passo 1: Detecção

```python
class ExitCriteriaMonitor:
    """
    Monitoriza critérios de exit por desporto.
    """
    def __init__(self):
        self.exit_criteria = {
            'NBA': {
                'max_drawdown': 0.15,
                'max_loss_streak': 15,
                'min_clv_consecutive': 50,
                'min_validation_clv': 0.02
            },
            'Football': {
                'max_drawdown': 0.18,
                'max_loss_streak': 12,
                'min_clv_consecutive': 40,
                'min_volume': 100
            },
            'MMA': {
                'max_drawdown': 0.20,
                'max_loss_streak': 10,
                'min_clv_consecutive': 30,
                'min_sample_size': 3
            }
        }
    
    def check_exit_criteria(self, sport):
        """
        Verifica se algum critério de exit foi atingido.
        """
        criteria = self.exit_criteria[sport]
        triggered = []
        
        # Verificar drawdown
        drawdown = calculate_sport_drawdown(sport)
        if drawdown > criteria['max_drawdown']:
            triggered.append({
                'type': 'drawdown',
                'value': drawdown,
                'threshold': criteria['max_drawdown']
            })
        
        # Verificar loss streak
        loss_streak = get_loss_streak(sport)
        if loss_streak >= criteria['max_loss_streak']:
            triggered.append({
                'type': 'loss_streak',
                'value': loss_streak,
                'threshold': criteria['max_loss_streak']
            })
        
        # Verificar CLV
        if sport in ['NBA', 'Football', 'MMA']:
            clv_streak = get_negative_clv_streak(sport)
            if clv_streak >= criteria['min_clv_consecutive']:
                triggered.append({
                    'type': 'clv_negative',
                    'value': clv_streak,
                    'threshold': criteria['min_clv_consecutive']
                })
        
        # Verificar específicos por desporto
        if sport == 'NBA':
            validation_clv = get_validation_clv('NBA')
            if validation_clv < criteria['min_validation_clv']:
                triggered.append({
                    'type': 'validation_degraded',
                    'value': validation_clv,
                    'threshold': criteria['min_validation_clv']
                })
        
        elif sport == 'Football':
            avg_volume = get_avg_volume_last_10('Football')
            if avg_volume < criteria['min_volume']:
                triggered.append({
                    'type': 'low_volume',
                    'value': avg_volume,
                    'threshold': criteria['min_volume']
                })
        
        elif sport == 'MMA':
            avg_sample_size = get_avg_sample_size_last_10('MMA')
            if avg_sample_size < criteria['min_sample_size']:
                triggered.append({
                    'type': 'high_uncertainty',
                    'value': avg_sample_size,
                    'threshold': criteria['min_sample_size']
                })
        
        return triggered
```

### 4.2 Passo 2: Pausa Automática

```python
def trigger_sport_pause(sport, reason):
    """
    Pausa apostas num desporto.
    """
    # 1. Ativar flag de pausa
    set_sport_pause_flag(sport, True)
    
    # 2. Cancelar ordens pendentes
    cancel_pending_orders(sport)
    
    # 3. Registar evento
    log_exit_event(sport, reason)
    
    # 4. Enviar alerta
    send_alert(f"SPORT PAUSED: {sport} - {reason}")
    
    # 5. Notificar subscritores (se aplicável)
    if sport in active_tipster_sports:
        notify_subscribers(f"{sport} pausado temporariamente devido a: {reason}")
```

### 4.3 Passo 3: Análise de Root Cause

```python
def analyze_exit_root_cause(sport, trigger):
    """
    Analisa causa raiz do trigger de exit.
    """
    analysis = {
        'sport': sport,
        'trigger': trigger,
        'timestamp': datetime.now(),
        'metrics_at_exit': get_sport_metrics(sport),
        'recent_performance': get_recent_performance(sport, days=30),
        'model_health': check_model_health(sport),
        'market_conditions': check_market_conditions(sport)
    }
    
    # Salvar análise
    save_exit_analysis(analysis)
    
    return analysis
```

### 4.4 Passo 4: Procedimento de Reativação

```python
def reactivate_sport(sport):
    """
    Procedimento para reativar um desporto pausado.
    """
    # 1. Verificar se critérios de reativação são satisfeitos
    if not check_reactivation_criteria(sport):
        return False, "Critérios de reativação não satisfeitos"
    
    # 2. Requerer aprovação manual
    if not manual_approval_required(sport):
        return False, "Aprovação manual necessária"
    
    # 3. Executar shadow mode (se aplicável)
    if shadow_mode_required(sport):
        run_shadow_mode(sport, duration_days=7)
    
    # 4. Validar performance em shadow mode
    if not validate_shadow_mode_performance(sport):
        return False, "Performance em shadow mode insuficiente"
    
    # 5. Reativar
    set_sport_pause_flag(sport, False)
    
    # 6. Registar evento
    log_reactivation_event(sport)
    
    # 7. Notificar
    send_alert(f"SPORT REACTIVATED: {sport}")
    
    return True, "Reativado com sucesso"
```

---

## 5. MONITORIZAÇÃO DE ESTADO DE DESPORTO

### 5.1 Dashboard de Estado

```python
def get_sport_status(sport):
    """
    Retorna estado atual de um desporto.
    """
    return {
        'active': not is_sport_paused(sport),
        'current_drawdown': calculate_sport_drawdown(sport),
        'loss_streak': get_loss_streak(sport),
        'clv_trend': get_clv_trend(sport),
        'validation_clv': get_validation_clv(sport) if sport == 'NBA' else None,
        'volume_avg': get_avg_volume_last_10(sport) if sport == 'Football' else None,
        'sample_size_avg': get_avg_sample_size_last_10(sport) if sport == 'MMA' else None,
        'last_exit_event': get_last_exit_event(sport),
        'exit_reason': get_last_exit_reason(sport)
    }
```

---

## 6. CRITÉRIOS DE REATIVAÇÃO

### 6.1 NBA

- Drawdown deve ser < 10% (do pico)
- CLV médio > 1% em 20 apostas
- Pelo menos 3 vitórias consecutivas em shadow mode
- Modelo validado com CLV > 2%

### 6.2 Football

- Drawdown deve ser < 12% (do pico)
- CLV médio > 1% em 15 apostas
- Pelo menos 2 vitórias consecutivas em shadow mode
- Volume médio > 150€

### 6.3 MMA/UFC

- Drawdown deve ser < 15% (do pico)
- CLV médio > 1% em 10 apostas
- Pelo menos 2 vitórias consecutivas em shadow mode
- Effective sample size médio > 5

---

## 7. COMUNICAÇÃO COM STAKEHOLDERS

### 7.1 Durante Pausa

**Para Subscritores do Tipster:**
```
NOTIFICAÇÃO: [DESPORTO] Pausado Temporariamente

Olá [Nome],

Informamos que [DESPORTO] foi pausado temporariamente devido a:
[RAZÃO]

Isto é uma medida de proteção para garantir a consistência dos sinais.
Esperamos retomar em breve após revisão.

Equipa VBQ
```

**Para Investidores (se aplicável):**
```
RELATÓRIO: Circuit Breaker Ativado

Desporto: [DESPORTO]
Trigger: [TRIGGER]
Valor: [VALOR]
Threshold: [THRESHOLD]

Análise de root cause em progresso.
Atualização em 24 horas.
```

---

## 8. HISTÓRICO DE EXITS

### 8.1 Registo de Eventos

```python
class ExitHistoryTracker:
    """
    Registra histórico de eventos de exit.
    """
    def __init__(self):
        self.exit_history = []
    
    def log_exit(self, sport, trigger, metrics):
        """
        Registra evento de exit.
        """
        event = {
            'timestamp': datetime.now(),
            'sport': sport,
            'trigger_type': trigger['type'],
            'trigger_value': trigger['value'],
            'trigger_threshold': trigger['threshold'],
            'metrics_at_exit': metrics
        }
        
        self.exit_history.append(event)
        save_exit_history(self.exit_history)
    
    def get_exit_frequency(self, sport, days=90):
        """
        Retorna frequência de exits nos últimos X dias.
        """
        recent_exits = [
            e for e in self.exit_history
            if e['sport'] == sport and
            (datetime.now() - e['timestamp']).days <= days
        ]
        
        return len(recent_exits)
```

---

## 9. CRITÉRIOS DE SUCESSO

| Critério | Threshold |
|----------|-----------|
| Tempo de resposta a exit | < 5 minutos |
| Taxa de falsos positivos | < 10% |
| Tempo médio de reativação | < 7 dias |
| Drawdown após exit | < 2% adicional |
