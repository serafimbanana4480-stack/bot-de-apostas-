# RETRAINING_AUTO — Retraining Automático

**ID:** `ML-013` | **Fase:** #phase/4-6 | **Owner:** MLOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Automatizar o processo de re-treino do modelo baseado em triggers de performance.

---

## 2. TRIGGERS AUTOMÁTICOS

```python
def check_retraining_triggers():
    """
    Verifica se triggers de re-treino foram ativados.
    
    Returns:
        Boolean se re-treino é necessário
    """
    metrics = get_recent_metrics()
    
    triggers = {
        'clv_drop': metrics['clv_recent'] < metrics['clv_baseline'] - 0.01,
        'roi_negative': metrics['roi_recent'] < 0,
        'drift_detected': calculate_psi() > 0.2,
        'scheduled': is_scheduled_retraining_day()
    }
    
    return any(triggers.values()), triggers
```

---

## 3. PIPELINE AUTOMATIZADO

```python
def automatic_retraining_pipeline():
    """Pipeline completo de re-treino automático."""
    # 1. Verificar triggers
    should_retrain, triggers = check_retraining_triggers()
    
    if not should_retrain:
        return False
    
    logger.info(f"Retraining triggered by: {triggers}")
    
    # 2. Coletar dados recentes
    recent_data = collect_recent_data(days=90)
    
    # 3. Preparar features
    features = feature_engineering(recent_data)
    
    # 4. Split temporal
    X_train, X_val, X_test = temporal_split(features)
    
    # 5. Otimizar hiperparâmetros
    best_params = optuna_tuning(X_train, X_val, n_trials=20)
    
    # 6. Treinar modelo
    model = train_model(X_train, best_params)
    
    # 7. Validar
    metrics = validate_model(model, X_test)
    
    # 8. Comparar com modelo atual
    if metrics['clv'] > current_model_metrics['clv'] + 0.005:
        # 9. Shadow deployment
        shadow_deploy(model, duration_days=7)
        
        # 10. Promover se shadow OK
        if shadow_metrics_ok():
            promote_to_production(model)
            logger.info("Modelo promovido com sucesso")
            return True
    
    logger.info("Novo modelo não superou atual - manter")
    return False
```

---

## 4. SCHEDULED RETRAINING

```python
def is_scheduled_retraining_day():
    """Verifica se é dia de re-treino agendado."""
    today = datetime.now()
    
    # Retreino semanal às segundas
    if today.weekday() == 0:
        return True
    
    return False
```

---

## 5. MONITORIZAÇÃO DE RETRAINING

```python
def monitor_retraining_status():
    """Monitoriza status de re-treino."""
    status = {
        'last_retraining_date': get_last_retraining_date(),
        'last_retraining_result': get_last_retraining_result(),
        'current_model_version': get_production_version(),
        'pending_triggers': check_retraining_triggers()[1]
    }
    
    return status
```

---

## 6. ALERTAS

```python
def send_retraining_alert(result):
    """Envia alerta sobre resultado do re-treino."""
    if result:
        send_telegram_message("✅ Novo modelo promovido com sucesso")
    else:
        send_telegram_message("⚠️ Retraining falhou - modelo mantido")
```

---

## 7. CRITÉRIOS

- **Retreino semanal** (segundas)
- **Retreino imediato** se CLV cai > 1%
- **Shadow deployment** obrigatório (7 dias)
- **Promoção apenas** se melhoria > 0.5%

---

## 8. LINKS CRUZADOS

- [[11_MLOps/INDEX]]
- [[RETRAINING_STRATEGY]]
