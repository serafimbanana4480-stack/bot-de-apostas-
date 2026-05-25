# CI_CD_MODELOS — Pipeline de Deploy

**ID:** `DO-001` | **Fase:** #phase/6 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. PIPELINE

```
Git Push -> Tests -> Build Docker -> Deploy Staging -> Shadow Mode -> Deploy Prod
```

---

## 2. FASES

### Tests
```bash
pytest tests/
python -m scripts.validate_schema
python -m scripts.audit_leakage
```

### Build
```bash
docker build -t valuebetting:$VERSION .
docker tag valuebetting:$VERSION valuebetting:latest
```

### Deploy Staging
```bash
docker-compose -f docker-compose.staging.yml up -d
# Run shadow mode for 7 days
```

### Promocao para Prod
```bash
# So se CLV shadow > modelo actual
kubectl set image deployment/model model=valuebetting:$VERSION
```

---

## 3. ROLLBACK

```bash
# Reverter para versao anterior
kubectl set image deployment/model model=valuebetting:$PREVIOUS_VERSION
# Ou via Docker Compose
docker-compose -f docker-compose.prod.yml up -d --no-deps --build model
```

---

## 4. BACKLOG

- [ ] Configurar GitHub Actions / GitLab CI
- [ ] Criar Dockerfiles para todos os servicos
- [ ] Documentar processo de rollback

---

## 5. LINKS CRUZADOS

- [[12_DevOps/INDEX]] ← Secao mae
- [[11_MLOps/INDEX]] → MLOps e retraining
