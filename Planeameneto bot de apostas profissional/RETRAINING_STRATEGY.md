# RETRAINING_STRATEGY — Quando e Como Retreinar

**ID:** `ML-003` | **Fase:** #phase/4-6 | **Owner:** MLOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir quando e como re-treinar o modelo para manter edge à medida que novos dados chegam e o mercado evolui.

---

## 2. TIPOS DE RETRAINING

### 2.1 Scheduled (Agendado)

Retreino em intervalos fixos, independente de performance.

| Frequência | Quando usar | Vantagens | Desvantagens |
|------------|-------------|-----------|--------------|
| Semanal | Dados estáveis | Simples | Pode re-treinar desnecessariamente |
| Mensal | Sazonalidade forte | Balanceado | Lento para responder a mudanças |
| Trimestral | Mercado muito estável | Menor custo | Risco de edge obsoleto |

### 2.2 Triggered (Baseado em Trigger)

Retreino quando condições específicas são atingidas.

```python
def check_retraining_triggers(metrics):
    """Verifica se re-treino é necessário."""
    triggers = {
        'clv_drop': metrics['clv_recent'] < metrics['clv_baseline'] - 0.01,
        'roi_negative': metrics['roi_recent'] < 0,
        'drift_detected': metrics['psi'] > 0.2,
        'regime_change': detect_regime_change(metrics['clv_history'])
    }
    
    return any(triggers.values())
```

---

## 3. ESTRATÉGIA HÍBRIDA (Recomendada)

Combina scheduled com triggered:

```python
retraining_strategy = {
    'schedule': 'weekly',      # Retreino mínimo semanal
    'trigger_conditions': [    # Retreino imediato se:
        'clv_drop > 1%',
        'roi < 0% for 50 bets',
        'drift detected'
    ],
    'max_frequency': 'daily'   # Nunca mais que diário
}
```

---

## 4. PIPELINE DE RETRAINING

```python
def retraining_pipeline():
    """Pipeline completo de re-treino."""
    # 1. Coletar dados recentes
    recent_data = collect_recent_data(days=90)
    
    # 2. Preparar features
    features = feature_engineering(recent_data)
    
    # 3. Split temporal (purged)
    X_train, X_val, X_test = temporal_split(features)
    
    # 4. Otimizar hiperparâmetros
    best_params = optuna_tuning(X_train, X_val)
    
    # 5. Treinar modelo
    model = train_model(X_train, best_params)
    
    # 6. Validar
    metrics = validate_model(model, X_test)
    
    # 7. Comparar com modelo atual
    if metrics['clv'] > current_model_metrics['clv']:
        promote_to_production(model)
    else:
        log("Novo modelo não supera atual - manter")
```

---

## 5. SHADOW DEPLOYMENT

Antes de promover, fazer shadow deployment:

```python
def shadow_deploy(new_model, duration_days=7):
    """Executa novo modelo em shadow (sem apostas reais)."""
    for _ in range(duration_days):
        # Gerar sinais do novo modelo
        new_signals = new_model.predict(features_today)
        
        # Registar em shadow table (não executar)
        log_shadow_signals(new_signals)
    
    # Após período, comparar performance
    shadow_metrics = evaluate_shadow_performance()
    
    return shadow_metrics
```

---

## 6. ROLLBACK

Se novo modelo falha em produção:

```python
def rollback_model():
    """Volta para versão anterior."""
    current_version = get_production_version()
    previous_version = current_version - 1
    
    promote_version(previous_version)
    log(f"Rollback de v{current_version} para v{previous_version}")
```

---

## 7. CRITÉRIOS DE PROMOÇÃO

Novo modelo só é promovido se:
- CLV > modelo atual + 0.5%
- Sharpe > modelo atual
- Sem overfitting (train-val diff < 0.05)
- Passa shadow deployment por ≥ 7 dias

---

## 8. LINKS CRUZADOS

- [[11_MLOps/INDEX]]
- [[30_Model_Registry/INDEX]] → Versioning
