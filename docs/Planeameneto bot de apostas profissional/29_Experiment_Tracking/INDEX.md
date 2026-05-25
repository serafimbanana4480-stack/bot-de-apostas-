# 29_Experiment Tracking — INDEX

**ID:** `SEC-29` | **Fase:** #phase/2-15 | **Owner:** MLOps Engineer + Quant | **Status:** #status/active

---

## 1. OBJETIVO

Registar todos os experimentos de machine learning de forma estruturada, auditável e reprodutível. Cada experimento deve ter: hipótese clara, parâmetros, resultados, e decisão.

---

## 2. EXPERIMENTOS REGISTADOS

| ID | Hipótese | Autor | Data | Status | Modelo Resultante |
|----|----------|-------|------|--------|-------------------|
| | | | | | |

---

## 3. STACK

- **MLflow** (tracking local) para métricas e artifacts
- **Optuna** para hiperparameter optimization (integrado com MLflow)
- **Git tags** para código associado a cada experimento

---

## 4. BACKLOG TÉCNICO

- [ ] Configurar MLflow tracking server
- [ ] Criar wrapper de experimento padronizado
- [ ] Integrar Optuna com MLflow callbacks
- [ ] Documentar convenção de naming de runs

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[05_Machine_Learning/INDEX]] → Modelos experimentados
- [[30_Model_Registry/INDEX]] → Promoção de modelos bem-sucedidos
