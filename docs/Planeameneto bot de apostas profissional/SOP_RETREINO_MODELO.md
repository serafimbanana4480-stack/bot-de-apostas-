# SOP_RETREINO_MODELO — SOP de Retraining de Modelo

**ID:** `SOP-003` | **Fase:** #phase/4-6 | **Owner:** MLOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir procedimento padrão para retraining do modelo.

---

## 2. TRIGGERS DE RETRAINING

| Trigger | Condição | Ação |
|---------|----------|------|
| Performance drop | CLV < 1% por 7 dias | Retraining |
| Drift de features | Drift > 0.1 | Retraining |
| Agendado | Mensal | Retraining |
| Manual | Solicitado | Retraining |

---

## 3. PROCEDIMENTO

```python
def retrain_model():
    """
    Executa retraining do modelo.
    
    Passos:
    1. Obter dados recentes
    2. Treinar novo modelo
    3. Validar com purged CV
    4. Comparar com modelo atual
    5. Shadow deployment
    """
    # 1. Obter dados
    data = get_recent_data(months=3)
    
    # 2. Treinar
    new_model = train_model(data)
    
    # 3. Validar
    metrics = purged_cross_validation(new_model, data)
    
    # 4. Comparar
    if metrics['clv'] > current_clv + 0.005:
        # 5. Shadow deployment
        shadow_deploy(new_model, days=7)
        return True
    else:
        logger.info("Novo modelo não supera atual")
        return False
```

---

## 4. CHECKLIST

- [ ] Dados recentes obtidos
- [ ] Modelo treinado
- [ ] Validação concluída
- [ ] Performance superior ao atual
- [ ] Shadow deployment iniciado
- [ ] Monitorização iniciada

---

## 5. CRITÉRIOS

- **CLV > atual + 0.5%** para promover
- **Shadow deployment 7+ dias**
- **Rollback disponível**

---

## 6. LINKS CRUZADOS

- [[11_MLOps/INDEX]]
- [[RETRAINING_AUTO]]
