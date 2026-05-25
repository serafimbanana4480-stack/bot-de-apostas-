# 11_MLOps — INDEX

**ID:** `SEC-11` | **Fase:** #phase/6-12 | **Owner:** MLOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Garantir que os modelos são treinados, validados, promovidos e monitorizados de forma reprodutível, automatizada e auditável. O MLOps não é um "nice to have" — é a diferença entre um modelo que funciona uma vez e um sistema que funciona continuamente.

---

## 2. NOTAS FUNDAMENTAIS

- [[CI_CD_MODELOS]] — Pipeline de integração contínua para modelos
- [[RETRAINING_AUTO]] — Triggered retraining vs scheduled retraining
- [[MONITORIZACAO_DRIFT]] — Data drift, feature drift, model decay
- [[SHADOW_DEPLOYMENT]] — Deploy de modelos em shadow antes de produção
- [[MODEL_REGISTRY_GESTAO]] — Versioning, staging, promoção, rollback
- [[REPRODUCIBILIDADE]] — Ambientes, seeds, requirements freeze
- [[FEATURE_DRIFT]] — Deteção de mudanças na distribuição das features
- [[PREDICTION_DRIFT]] — Monitorização das predições do modelo em produção

---

## 3. CICLO DE VIDA DO MODELO

```
1. EXPERIMENTAÇÃO
   ├── Cientista/Quant treina modelo em notebook/script
   ├── Regista experimento em [[29_Experiment_Tracking/INDEX]]
   └── Guarda artifacts (modelo, dados, config)

2. VALIDAÇÃO
   ├── Backtest rigoroso em hold-out set
   ├── Comparação com modelo em produção (shadow)
   └── Se supera em todas as métricas → promove a STAGING

3. STAGING
   ├── Deploy em ambiente de staging
   ├── Shadow mode por 7 dias (predições sem execução real)
   └── Se CLV shadow > modelo prod → promove a PROD

4. PRODUÇÃO
   ├── Modelo serve predições em tempo real
   ├── Monitorização contínua de drift e performance
   └── Se drift > threshold ou CLV < 0% → ROLLBACK

5. RETIREMENT
   ├── Modelo arquivado no registry
   ├── Dados de performance mantidos para audit
   └── Lições aprendidas documentadas
```

---

## 4. RETRAINING STRATEGY

| Tipo | Trigger | Frequência | Dados Usados |
|------|---------|------------|--------------|
| Scheduled | Cron semanal | Toda segunda-feira, 04:00 | Últimos 3 anos |
| Triggered | Drift > 0.20 PSI | Imediato (após deteção) | Últimos 6 meses + histórico |
| Triggered | CLV 7d < 0% | Após 48h de confirmação | Últimos 3 anos |
| Manual | Decisão estratégica | Sob demanda | Configurável |

**Regra:** Nunca retreinar com dados que incluem o período de deteção do drift (evitar overfitting ao noise).

---

## 5. STACK MLOPS

| Componente | Escolha | Justificação |
|------------|---------|--------------|
| Experiment Tracking | MLflow (local) | Simples, logging de métricas e artifacts |
| Model Registry | MLflow Registry | Staging → Production transitions |
| Orchestration | Prefect | Reusa orquestração existente de dados |
| Monitoring | Prometheus + custom | Métricas customizadas de drift |
| Ambiente | Docker | Reprodutibilidade garantida |

---

## 6. BACKLOG TÉCNICO

- [ ] Configurar MLflow tracking server
- [ ] Criar pipeline de retraining automatizado (Prefect)
- [ ] Implementar deteção de data drift (KS test, PSI)
- [ ] Criar sistema de shadow deployment
- [ ] Implementar rollback automático de modelos
- [ ] Criar dashboard de drift em Grafana
- [ ] Documentar reprodutibilidade (Dockerfile, requirements, seeds)

---

## 7. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[05_Machine_Learning/INDEX]] → Modelos a operacionalizar
- [[29_Experiment_Tracking/INDEX]] → Tracking de experimentos
- [[30_Model_Registry/INDEX]] → Gestão de versões
- [[48_Data_Drift/INDEX]] → Deteção de drift
