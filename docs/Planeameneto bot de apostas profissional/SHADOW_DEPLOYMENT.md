# SHADOW_DEPLOYMENT — Deploy em Shadow

**ID:** `MLOP-001` | **Fase:** #phase/4-6 | **Owner:** MLOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Executar novo modelo em paralelo com o modelo atual (sem apostas reais) para validar antes de promover.

---

## 2. PROCESSO

```python
def shadow_deploy(new_model, duration_days=7):
    """
    Executa novo modelo em shadow.
    
    Args:
        new_model: Novo modelo a testar
        duration_days: Duração em dias
    
    Returns:
        Métricas do shadow deployment
    """
    shadow_signals = []
    
    for day in range(duration_days):
        # 1. Gerar sinais do novo modelo
        daily_features = get_daily_features()
        new_signals = new_model.predict(daily_features)
        
        # 2. Registar em shadow table (não executar)
        for signal in new_signals:
            shadow_signals.append({
                'date': datetime.now(),
                'game_id': signal['game_id'],
                'prob': signal['prob'],
                'odd': signal['odd'],
                'edge': signal['edge'],
                'shadow_only': True
            })
    
    # 3. Calcular métricas shadow
    shadow_metrics = evaluate_shadow_performance(shadow_signals)
    
    return shadow_metrics
```

---

## 3. COMPARAÇÃO COM MODELO ATUAL

```python
def compare_shadow_vs_production(shadow_metrics, prod_metrics):
    """
    Compara performance shadow vs produção.
    
    Returns:
        Boolean se shadow supera produção
    """
    improvement_threshold = 0.005  # 0.5% melhoria mínima
    
    clv_improvement = shadow_metrics['clv'] - prod_metrics['clv']
    
    if clv_improvement > improvement_threshold:
        return True
    
    return False
```

---

## 4. PROMOÇÃO

```python
def promote_from_shadow(new_model, shadow_metrics):
    """
    Promove modelo se shadow OK.
    """
    if compare_shadow_vs_production(shadow_metrics, current_metrics):
        promote_to_production(new_model)
        logger.info("Modelo promovido após shadow deployment")
        return True
    else:
        logger.info("Shadow não supera produção - manter atual")
        return False
```

---

## 5. DURAÇÃO

- **Mínimo 7 dias** para shadow
- **Ideal 14 dias** para maior confiança
- **Mínimo 50 sinais** para avaliação

---

## 6. CRITÉRIOS

- **Shadow > produção + 0.5% CLV** para promover
- **Mínimo 7 dias** de shadow
- **Mínimo 50 sinais** gerados

---

## 7. LINKS CRUZADOS

- [[11_MLOps/INDEX]]
- [[RETRAINING_STRATEGY]]
