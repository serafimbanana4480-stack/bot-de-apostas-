# 39_Automation — INDEX

**ID:** `SEC-39` | **Fase:** #phase/6-12 | **Owner:** DevOps + Operations Lead | **Status:** #status/active

---

## 1. OBJETIVO

Automatizar tarefas repetitivas: ingestão de dados, treino de modelos, envio de relatórios, backups, e alertas. Automação reduz erros humanos e liberta tempo para análise de qualidade.

---

## 2. TAREFAS AUTOMATIZADAS

| Tarefa | Frequência | Ferramenta | Estado |
|--------|------------|------------|--------|
| Ingestão NBA | Diária (04:00) | Prefect/Cron | Pendente |
| Validação de dados | Diária (pós-ingestão) | Prefect + Great Expectations | Pendente |
| Geração de sinais | Cada 5 min (pré-jogo) | FastAPI + Celery | Pendente |
| Backup PostgreSQL | Diária (02:00) | Cron + pg_dump | Pendente |
| Retreino modelo | Semanal (Segunda 04:00) | Prefect | Pendente |
| Relatório diário | Diária (após último jogo) | Prefect + Telegram | Pendente |
| Rotação de secrets | Trimestral | Script + cron | Pendente |

---

## 3. CRONTAB COMPLETO (VPS)

```bash
# /etc/cron.d/valuebetting
# ┌── minuto (0-59)
# │   ┌── hora (0-23, UTC)
# │   │   ┌── dia do mês (1-31)
# │   │   │  ┌── mês (1-12)
# │   │   │  │  ┌── dia da semana (0-7, 0=Dom)
# │   │   │  │  │

# ---- DADOS ----
*/2  *  *  *  * vbq python -m workers.odds_ingestion --mode=high_frequency  # Dias de jogo, <1h antes
*/10 *  *  *  * vbq python -m workers.odds_ingestion --mode=medium           # Dias de jogo, 1-4h antes
0    *  *  *  * vbq python -m workers.odds_ingestion --mode=low_frequency    # Sem jogo / early

# ---- SNAPSHOTS ----
0    3  *  *  * vbq python -m scripts.create_daily_snapshot --layer=bronze
0    4  *  *  * vbq python -m scripts.create_daily_snapshot --layer=silver

# ---- BACKUPS ----
0    2  *  *  * vbq pg_dump $DATABASE_URL | gzip > /backups/$(date +%Y%m%d).sql.gz
0    2  *  *  0 vbq find /backups/ -mtime +90 -delete  # Limpar backups > 90 dias

# ---- MODELOS ----
0    4  *  *  1 vbq python -m scripts.retrain_model --mode=weekly             # Segunda 04:00 UTC

# ---- RELATÓRIOS ----
0    8  *  *  * vbq python -m workers.daily_report                            # Relatório diário 08:00 UTC

# ---- MANUTENÇÃO ----
0    1  1  *  * vbq python -m scripts.rotate_secrets --check                  # Verificar rotação trimestral
0    5  *  *  * vbq python -m scripts.cleanup_old_runs                        # Limpar MLflow runs antigos
```

---

## 4. AUTOMAÇÃO COM PREFECT (FASE 6+)

Para pipelines mais complexos com dependências e retry logic:

```python
from prefect import flow, task
from prefect.schedules import CronSchedule

@task(retries=3, retry_delay_seconds=60)
def ingest_odds():
    """Ingere odds da Betfair com retry automático."""
    pass

@task(retries=2)
def validate_data():
    """Valida dados com Great Expectations."""
    pass

@task
def generate_signals():
    """Gera sinais de value betting."""
    pass

@flow(
    name="daily_pipeline",
    schedule=CronSchedule(cron="0 4 * * *")
)
def daily_pipeline_flow():
    """Pipeline diário completo."""
    odds = ingest_odds()
    validated = validate_data(upstream_tasks=[odds])
    signals = generate_signals(upstream_tasks=[validated])
    return signals
```

---

## 5. MONITORIZAÇÃO DAS AUTOMAÇÕES

| Automação | Alerta se Falhar | SLA de Retry |
|-----------|-----------------|--------------|
| Ingestão de odds | Telegram imediato | 3 retries × 60s |
| Backup PostgreSQL | Telegram + Email | 1 retry manual |
| Retreino semanal | Telegram | Adiar 24h |
| Relatório diário | Telegram | 1 retry |
| Snapshot Bronze | Telegram | 3 retries |

```python
def alert_on_failure(job_name: str, error: Exception) -> None:
    """Enviar alerta Telegram quando automação falha."""
    message = f"⚠️ AUTOMAÇÃO FALHOU\n{job_name}\nErro: {error}\nHora: {datetime.now(UTC)}"
    telegram_bot.send_message(chat_id=OPERATOR_CHAT_ID, text=message)
```

---

## 6. BACKLOG

- [ ] Implementar crontab base para ingestão + backup (Fase 1)
- [ ] Implementar script de relatório diário (Fase 4)
- [ ] Migrar para Prefect quando pipeline tiver 5+ steps (Fase 6)
- [ ] Implementar health check de todas as automações no dashboard
- [ ] Documentar procedimento de restart manual para cada automação

---

## 7. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[11_MLOps/INDEX]] → Automação de re-treino e shadow deploy
- [[39_Automation/CRON_JOBS]] → Configuração detalhada de cron jobs
- [[33_Alerting/INDEX]] → Alertas de falha de automações
- [[04_Data_Engineering/OBSERVABILIDADE_PIPELINE]] → Monitorização dos pipelines
