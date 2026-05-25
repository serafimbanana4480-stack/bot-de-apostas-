# Prefect Pipelines

**ID:** AUTO-003 | **Fase:** #phase/6-12 | **Owner:** DevOps + Operations Lead | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Configuração de pipelines Prefect para automação de tarefas repetitivas: ingestão de dados, treino de modelos, envio de relatórios, backups, e alertas. Prefect fornece orquestração, retry logic, e monitorização de pipelines.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Configurar pipelines Prefect para automação |
| **Stack** | Prefect 2.0+, PostgreSQL, Docker |
| **Custo** | 0€ (open source) |

---

## 2. ARQUITETURA DE PIPELINES

### 2.1 Estrutura de Pipelines

```
┌─────────────────────────────────────────────────────────────┐
│ PREFECT PIPELINES                                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ DAILY_PIPELINE (Diária, 04:00 UTC)                  │   │
│  │ ├── Ingestão de dados NBA                            │   │
│  │ ├── Validação de dados (Great Expectations)          │   │
│  │ ├── Criação de snapshots                             │   │
│  │ ├── Geração de sinais                                │   │
│  │ └── Envio de relatório diário                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ WEEKLY_PIPELINE (Semanal, Segunda 04:00 UTC)         │   │
│  │ ├── Retreino de modelo                              │   │
│  │ ├── Validação de modelo                             │   │
│  │ ├── Promocão para staging                           │   │
│  │ └── Relatório semanal                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ MAINTENANCE_PIPELINE (Trimestral)                   │   │
│  │ ├── Backup PostgreSQL                               │   │
│  │ ├── Limpeza de runs antigos                         │   │
│  │ ├── Rotação de secrets                              │   │
│  │ └── Relatório de manutenção                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. CONFIGURAÇÃO DO PREFECT

### 3.1 Instalação

```bash
pip install prefect prefect-dask prefect-postgres
```

### 3.2 Configuração do Servidor

```python
# vbq/prefect/config.py
from prefect import settings

settings PREFECT_API_URL = "http://localhost:4200/api"
settings PREFECT_SERVER_API_HOST = "0.0.0.0"
settings PREFECT_SERVER_API_PORT = 4200
```

### 3.3 Configuração do Database

```python
# vbq/prefect/database.py
from prefect.blocks.system import JSON

# Configurar block de database
db_block = JSON(
    name="database-config",
    value={
        "url": "postgresql://user:password@localhost:5432/valuebetting",
        "schema": "public"
    }
)
db_block.save()
```

---

## 4. PIPELINE DIÁRIO

### 4.1 Definição do Pipeline

```python
# vbq/prefect/pipelines/daily_pipeline.py
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(retries=3, retry_delay_seconds=60, cache_key_fn=task_input_hash)
def ingest_nba_data(date: str):
    """Ingere dados NBA para uma data específica"""
    from vbq.ingestion.nba_api import NBAIngestion
    ingestion = NBAIngestion()
    return ingestion.ingest_date(date)

@task(retries=2)
def validate_data(data):
    """Valida dados com Great Expectations"""
    from vbq.validation.great_expectations import validate
    return validate(data)

@task
def create_snapshots(data):
    """Cria snapshots bronze e silver"""
    from vbq.data.snapshots import create_snapshots
    return create_snapshots(data)

@task
def generate_signals(data):
    """Gera sinais de value betting"""
    from vbq.models.signal_generator import generate_signals
    return generate_signals(data)

@task
def send_daily_report(signals):
    """Envia relatório diário via Telegram"""
    from vbq.notifications.telegram import send_report
    return send_report(signals)

@flow(name="daily_pipeline")
def daily_pipeline(date: str):
    """Pipeline diário completo"""
    # Ingestão
    data = ingest_nba_data(date)
    
    # Validação
    validated = validate_data(data, wait_for=[data])
    
    # Snapshots
    snapshots = create_snapshots(validated, wait_for=[validated])
    
    # Sinais
    signals = generate_signals(snapshots, wait_for=[snapshots])
    
    # Relatório
    report = send_daily_report(signals, wait_for=[signals])
    
    return report
```

### 4.2 Agendamento

```python
# vbq/prefect/schedules/daily_schedule.py
from prefect import flow
from prefect.deployments import Deployment
from prefect.schedules import CronSchedule
from vbq.prefect.pipelines.daily_pipeline import daily_pipeline

deployment = Deployment.build_from_flow(
    flow=daily_pipeline,
    name="daily-deployment",
    schedule=CronSchedule(cron="0 4 * * *"),  # 04:00 UTC diário
    work_queue_name="default",
    tags=["daily", "ingestion", "signals"]
)

deployment.apply()
```

---

## 5. PIPELINE SEMANAL

### 5.1 Definição do Pipeline

```python
# vbq/prefect/pipelines/weekly_pipeline.py
from prefect import flow, task

@task(retries=3, retry_delay_seconds=300)
def retrain_model():
    """Retreina modelo com dados recentes"""
    from vbq.models.retrain import retrain
    return retrain()

@task
def validate_model(model):
    """Valida modelo com purged CV"""
    from vbq.models.validation import validate_model
    return validate_model(model)

@task
def promote_to_staging(model):
    """Promove modelo para staging"""
    from vbq.models.registry import promote_to_staging
    return promote_to_staging(model)

@task
def generate_weekly_report(model):
    """Gera relatório semanal"""
    from vbq.reports.weekly import generate_report
    return generate_report(model)

@flow(name="weekly_pipeline")
def weekly_pipeline():
    """Pipeline semanal de treino"""
    # Retreino
    model = retrain_model()
    
    # Validação
    validated = validate_model(model, wait_for=[model])
    
    # Promoção
    staging = promote_to_staging(validated, wait_for=[validated])
    
    # Relatório
    report = generate_weekly_report(staging, wait_for=[staging])
    
    return report
```

### 5.2 Agendamento

```python
from prefect.deployments import Deployment
from prefect.schedules import CronSchedule

deployment = Deployment.build_from_flow(
    flow=weekly_pipeline,
    name="weekly-deployment",
    schedule=CronSchedule(cron="0 4 * * 1"),  # Segunda 04:00 UTC
    work_queue_name="default",
    tags=["weekly", "retrain", "model"]
)

deployment.apply()
```

---

## 6. PIPELINE DE MANUTENÇÃO

### 6.1 Definição do Pipeline

```python
# vbq/prefect/pipelines/maintenance_pipeline.py
from prefect import flow, task

@task
def backup_postgresql():
    """Backup PostgreSQL"""
    from vbq.infrastructure.backup import backup_db
    return backup_db()

@task
def cleanup_old_runs():
    """Limpa runs antigos do MLflow"""
    from vbq.mlops.cleanup import cleanup_mlflow
    return cleanup_mlflow()

@task
def rotate_secrets():
    """Verifica rotação de secrets"""
    from vbq.security.secrets import check_rotation
    return check_rotation()

@task
def generate_maintenance_report(results):
    """Gera relatório de manutenção"""
    from vbq.reports.maintenance import generate_report
    return generate_report(results)

@flow(name="maintenance_pipeline")
def maintenance_pipeline():
    """Pipeline trimestral de manutenção"""
    # Backup
    backup = backup_postgresql()
    
    # Cleanup
    cleanup = cleanup_old_runs()
    
    # Secrets
    secrets = rotate_secrets()
    
    # Relatório
    report = generate_maintenance_report({
        'backup': backup,
        'cleanup': cleanup,
        'secrets': secrets
    })
    
    return report
```

---

## 7. MONITORIZAÇÃO

### 7.1 Dashboard Prefect

O Prefect fornece um dashboard web em `http://localhost:4200` com:
- Estado de todos os pipelines
- Histórico de runs
- Logs detalhados
- Métricas de performance

### 7.2 Alertas

```python
# vbq/prefect/alerts.py
from prefect import flow
from prefect.notifications import notify_send_email

@flow(name="pipeline_with_alerts")
def pipeline_with_alerts():
    try:
        # Executar pipeline
        result = daily_pipeline()
        
        # Notificar sucesso
        notify_send_email(
            email_to="ops@valuebetting.com",
            subject="Pipeline daily concluído com sucesso",
            body=f"Pipeline daily concluído em {result['timestamp']}"
        )
        
    except Exception as e:
        # Notificar falha
        notify_send_email(
            email_to="ops@valuebetting.com",
            subject="Pipeline daily falhou",
            body=f"Erro: {str(e)}"
        )
        raise
```

---

## 8. DEPLOYMENT

### 8.1 Docker Compose

```yaml
# docker-compose.prefect.yml
version: '3.8'

services:
  prefect-server:
    image: prefecthq/prefect:2-python3.11
    command: prefect server start
    ports:
      - "4200:4200"
    environment:
      - PREFECT_API_URL=http://localhost:4200/api
      - PREFECT_SERVER_API_HOST=0.0.0.0
      - PREFECT_SERVER_API_PORT=4200
    volumes:
      - prefect_data:/prefect/storage

  prefect-agent:
    image: prefecthq/prefect:2-python3.11
    command: prefect agent start -q default
    environment:
      - PREFECT_API_URL=http://prefect-server:4200/api
    depends_on:
      - prefect-server
    volumes:
      - ./vbq:/app/vbq

volumes:
  prefect_data:
```

### 8.2 Comandos de Deployment

```bash
# Iniciar servidor Prefect
docker-compose -f docker-compose.prefect.yml up -d

# Aplicar deployments
python vbq/prefect/schedules/daily_schedule.py
python vbq/prefect/schedules/weekly_schedule.py

# Verificar estado
prefect deployment ls
prefect flow-runs ls
```

---

## 9. LINKS CRUZADOS

- [[39_Automation/INDEX]] ← Secção mãe
- [[39_Automation/CRON_JOBS]] → Crontab completo (alternativa)
- [[11_MLOps/INDEX]] → MLOps e orquestração
- [[10_Infrastructure/INDEX]] → Infraestrutura

---

**Custo de implementação:** 0€ (open source)  
**Tempo estimado de implementação:** 2 semanas  
**Prioridade:** ALTA (fundamental para automação)
