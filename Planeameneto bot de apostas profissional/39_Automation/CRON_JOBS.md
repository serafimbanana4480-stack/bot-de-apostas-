# CRON_JOBS — Tarefas Periodicas

**ID:** `AUTO-001` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. CRONTAB PRINCIPAL

```bash
# Ingestao de dados (30min em dias de jogo, 1x/dia offseason)
*/30 10-23 * 10-4 * /opt/vb/scripts/ingest_nba.sh
0 8 * 5-9 * /opt/vb/scripts/ingest_nba.sh

# Motor de value (a cada 2h em dias de jogo)
0 10,12,14,16,18,20 * 10-4 * /opt/vb/scripts/run_value_engine.sh

# Retreino semanal (2a feira 04:00)
0 4 * * 1 /opt/vb/scripts/retrain_model.sh

# Backup diario
0 3 * * * /opt/backup/backup.sh

# Relatorio diario (08:00)
0 8 * * * /opt/vb/scripts/daily_report.sh

# Monitorizacao drift (domingo 02:00)
0 2 * * 0 /opt/vb/scripts/check_drift.sh
```

---

## 2. IMPLEMENTACAO COM PREFECT

```python
from prefect import flow, task
from prefect.schedules import CronSchedule

@task
def ingest_data():
    # ...
    pass

@task
def run_value_engine():
    # ...
    pass

@task
def send_signals():
    # ...
    pass

@flow(name="nba_daily_pipeline")
def daily_pipeline():
    ingest_data()
    run_value_engine()
    send_signals()

# Schedule: 10h, 12h, 14h, 16h, 18h, 20h em dias de jogo
from prefect.deployments import Deployment
deployment = Deployment.build_from_flow(
    flow=daily_pipeline,
    name="nba_daily",
    schedule=CronSchedule(cron="0 10,12,14,16,18,20 * 10-4 *")
)
```

---

## 3. BACKLOG

- [ ] Configurar Prefect server
- [ ] Migrar cron jobs para flows Prefect
- [ ] Documentar dependencias entre tarefas

---

## 4. LINKS CRUZADOS

- [[39_Automation/INDEX]] ← Secao mae
- [[11_MLOps/INDEX]] → Retraining automatizado
