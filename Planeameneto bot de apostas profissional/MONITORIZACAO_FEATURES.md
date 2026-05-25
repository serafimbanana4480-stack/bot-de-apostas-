# MONITORIZACAO_FEATURES — Monitorização de Features

**ID:** `ML-016` | **Fase:** #phase/4-6 | **Owner:** MLOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Monitorizar drift de features para detetar degradação do modelo.

---

## 2. MÉTRICAS DE DRIFT

| Métrica | Threshold | Ação |
|---------|-----------|------|
| Drift de média | > 0.1 | Alerta |
| Drift de distribuição | KS > 0.05 | Alerta |
| Missing rate | > 5% | Alerta |
| Outlier rate | > 10% | Alerta |

---

## 3. CÁLCULO DE DRIFT

```python
def calculate_feature_drift(reference_features, current_features):
    """
    Calcula drift de features.
    
    Args:
        reference_features: Features de referência (treino)
        current_features: Features atuais
    
    Returns:
        Dict com métricas de drift
    """
    drift_metrics = {}
    
    for feature in reference_features.columns:
        ref = reference_features[feature]
        curr = current_features[feature]
        
        # Drift de média
        mean_drift = abs(ref.mean() - curr.mean()) / ref.std()
        
        # Drift de distribuição (KS test)
        from scipy.stats import ks_2samp
        ks_stat, _ = ks_2samp(ref, curr)
        
        drift_metrics[feature] = {
            'mean_drift': mean_drift,
            'ks_stat': ks_stat
        }
    
    return drift_metrics
```

---

## 4. MONITORIZAÇÃO

```python
def monitor_features():
    """Monitoriza drift de features diariamente."""
    # Obter features de referência
    reference = get_training_features()
    
    # Obter features atuais (últimos 7 dias)
    current = get_recent_features(days=7)
    
    # Calcular drift
    drift = calculate_feature_drift(reference, current)
    
    # Verificar thresholds
    for feature, metrics in drift.items():
        if metrics['mean_drift'] > 0.1:
            send_alert(f"⚠️ Drift de média alto em {feature}: {metrics['mean_drift']:.2f}")
        
        if metrics['ks_stat'] > 0.05:
            send_alert(f"⚠️ Drift de distribuição em {feature}: {metrics['ks_stat']:.2f}")
```

---

## 5. AÇÃO SE DRIFT DETETADO

```python
def handle_feature_drift():
    """Ação se drift de features detetado."""
    # 1. Retreinar modelo com dados recentes
    retrain_with_recent_data()
    
    # 2. Revalidar modelo
    validate_model()
    
    # 3. Shadow deployment
    shadow_deploy(new_model, days=7)
```

---

## 6. CRITÉRIOS

- **Monitorizar diariamente**
- **Alerta se drift > threshold**
- **Retreinar** se drift significativo

---

## 7. LINKS CRUZADOS

- [[11_MLOps/INDEX]]
- [[RETRAINING_AUTO]]
