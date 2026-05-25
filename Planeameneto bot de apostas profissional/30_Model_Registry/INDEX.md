# 30_Model Registry — INDEX

**ID:** `SEC-30` | **Fase:** #phase/2-15 | **Owner:** MLOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Gerir o ciclo de vida de cada modelo: desde o experimento até à produção, passando por staging. Garantir que só modelos validados servem predições em produção, e que o rollback é sempre possível.

---

## 2. ESTADOS DO MODELO

```
EXPERIMENT → STAGING → PRODUCTION → ARCHIVED
                ↓         ↓
              ROLLBACK  ROLLBACK
```

| Estado | Quem promove | Critério |
|--------|--------------|----------|
| EXPERIMENT | Quant Engineer | Treino completo com purged CV |
| STAGING | MLOps Engineer | Todas as métricas de sucesso passam |
| PRODUCTION | Chief Architect + MLOps | 7 dias de shadow mode com CLV > modelo anterior |
| ARCHIVED | Automático (90 dias) | Modelo substituído em produção |

---

## 3. MODELOS REGISTADOS

| ID | Nome | Versão | Estado | Data Deploy | CLV em Prod | Notas |
|----|------|--------|--------|-------------|-------------|-------|
| | | | | | | |

---

## 4. BACKLOG TÉCNICO

- [ ] Configurar MLflow Model Registry
- [ ] Criar pipeline de staging → production
- [ ] Implementar rollback automático
- [ ] Documentar convenção de versioning

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[05_Machine_Learning/INDEX]] → Modelos a registar
- [[29_Experiment_Tracking/INDEX]] → Experimentos de origem
