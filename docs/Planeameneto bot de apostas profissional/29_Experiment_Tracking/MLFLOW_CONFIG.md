# MLFLOW_CONFIG — Configuração do MLflow

**ID:** `EXP-001` | **Fase:** Todas | **Owner:** ML Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar a configuração do MLflow para tracking de experimentos.

---

## 2. CONFIGURAÇÃO

### 2.1 Backend Store
```yaml
# mlflow.yml
tracking:
  backend: postgresql
  uri: postgresql://user:password@localhost:5432/mlflow
```

### 2.2 Artifact Store
```yaml
artifacts:
  type: s3
  uri: s3://mlflow-artifacts/
```

### 2.3 Environment Variables
```bash
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin
```

---

## 3. BACKLOG

- [ ] Configurar autenticação MLflow
- [ ] Implementar retenção de experimentos
- [ ] Configurar notificações de experimentos

---

## 4. LINKS CRUZADOS

- [[29_Experiment_Tracking/INDEX]] ← Secção mãe
