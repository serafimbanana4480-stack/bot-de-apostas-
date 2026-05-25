# SOP_DEPLOY_MODELO — SOP de Deploy de Modelo

**ID:** `SOP-001` | **Fase:** #phase/4-6 | **Owner:** MLOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir procedimento padrão para deploy de novo modelo em produção.

---

## 2. PRÉ-REQUISITOS

- [ ] Modelo treinado e validado
- [ ] Backtest com CLV > 2%
- [ ] Shadow deployment concluído (7+ dias)
- [ ] Checklist de segurança preenchido

---

## 3. PROCEDIMENTO

```python
def deploy_model(new_model_version):
    """
    Executa deploy de novo modelo.
    
    Passos:
    1. Backup do modelo atual
    2. Shadow deployment (7 dias)
    3. Comparação de performance
    4. Promoção se OK
    5. Monitorização pós-deploy
    """
    # 1. Backup
    backup_current_model()
    
    # 2. Shadow deployment
    shadow_metrics = run_shadow_deployment(new_model_version, days=7)
    
    # 3. Comparação
    if compare_shadow_vs_production(shadow_metrics):
        # 4. Promover
        promote_model(new_model_version)
        logger.info(f"Modelo {new_model_version} promovido")
    else:
        logger.warning("Shadow não supera produção - manter atual")
```

---

## 4. CHECKLIST

- [ ] Backup do modelo atual
- [ ] Shadow deployment iniciado
- [ ] Shadow deployment concluído (7 dias)
- [ ] Performance shadow > produção
- [ ] Modelo promovido
- [ ] Monitorização pós-deploy iniciada

---

## 5. ROLLBACK

Se problemas detetados após deploy:

```python
def rollback_model():
    """Rollback para modelo anterior."""
    restore_backup()
    logger.info("Rollback executado")
```

---

## 6. CRITÉRIOS

- **Mínimo 7 dias** de shadow deployment
- **Shadow > produção + 0.5% CLV**
- **Rollback disponível** sempre

---

## 7. LINKS CRUZADOS

- [[11_MLOps/INDEX]]
- [[SHADOW_DEPLOYMENT]]
