# ROLLBACK_MODELO — Rollback de Modelo

**ID:** `MR-002` | **Fase:** Todas | **Owner:** ML Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar o procedimento de rollback para versões anteriores do modelo.

---

## 2. PROCEDIMENTO

### 2.1 Identificar Versão
```sql
-- Ver versões disponíveis
SELECT 
  model_name,
  version,
  run_id,
  creation_timestamp
FROM model_versions
WHERE model_name = 'nba_value_model'
ORDER BY version DESC;
```

### 2.2 Rollback
```python
import mlflow

# Carregar versão anterior
model = mlflow.pyfunc.load_model(
    model_uri="models:/nba_value_model/5"
)

# Deploy versão anterior
deploy_model(model, version=5)
```

### 2.3 Verificação
- [ ] Modelo carrega corretamente
- [ ] Predições funcionam
- [ ] Métricas estáveis
- [ ] Sem erros nos logs

---

## 3. BACKLOG

- [ ] Implementar rollback automático
- [ ] Adicionar shadow deployment antes de rollback
- [ ] Documentar critérios de rollback

---

## 4. LINKS CRUZADOS

- [[30_Model_Registry/INDEX]] ← Secção mãe
