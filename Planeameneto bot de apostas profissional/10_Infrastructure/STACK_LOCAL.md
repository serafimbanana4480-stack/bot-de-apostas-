# Stack Local Mínimo - Setup Zero Euros

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  

---

## 🎯 OBJETIVO

Documentação da stack mínima local para implementação 100% gratuita do VBQ-UNIFIED no PC, reduzindo de 9 containers originais para 3 essenciais.

---

## 📊 COMPARAÇÃO: ORIGINAL VS LOCAL

### **Stack Original (9 Containers)**
```yaml
services:
  postgres:         # Database
  redis:            # Cache
  api:              # FastAPI
  prefect-ui:       # Orquestração UI
  prefect-api:      # Orquestração API
  grafana:          # Monitoring UI
  mlflow:           # Experiment tracking
  prometheus:       # Metrics
  node-exporter:    # System metrics
```

### **Stack Local Mínimo (3 Containers)**
```yaml
services:
  postgres:         # Database (essencial)
  redis:            # Cache (essencial)
  api:              # FastAPI + modelos (essencial)
```

### **Redução: 67% menos containers**

---

## 🏗️ ARQUITETURA LOCAL MÍNIMA

### **Diagrama de Arquitetura Detalhado**
```
┌─────────────────────────────────────────────────────────────────┐
│                     PC Local (VBQ-UNIFIED)                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    User Interface Layer                   │  │
│  │                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │ Telegram Bot │  │  Streamlit   │  │  FastAPI UI  │  │  │
│  │  │   (notifica) │  │  (dashboard) │  │   (docs)     │  │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │  │
│  └─────────┼──────────────────┼──────────────────┼─────────┘  │
│            │                  │                  │            │
│            └──────────────────┼──────────────────┘            │
│                               ▼                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Application Layer                       │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │              FastAPI Backend                       │  │  │
│  │  │  ┌──────────────┐  ┌──────────────┐              │  │  │
│  │  │  │  API Routes  │  │  ML Models   │              │  │  │
│  │  │  │  /bets       │  │  XGBoost     │              │  │  │
│  │  │  │  /predictions│  │  LightGBM    │              │  │  │
│  │  │  │  /data       │  │  Neural Net  │              │  │  │
│  │  │  └──────┬───────┘  └──────┬───────┘              │  │  │
│  │  └─────────┼──────────────────┼───────────────────────┘  │  │
│  └────────────┼──────────────────┼───────────────────────────┘  │
│               │                  │                              │
│               └────────┬─────────┘                              │
│                        ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Data Layer                              │  │
│  │                                                          │  │
│  │  ┌──────────────┐         ┌──────────────┐              │  │
│  │  │  PostgreSQL  │◄────────┤   Redis      │              │  │
│  │  │              │         │              │              │  │
│  │  │  • bets      │         │  • cache     │              │  │
│  │  │  • users     │         │  • sessions  │              │  │
│  │  │  • models    │         │  • queue     │              │  │
│  │  │  • logs      │         │  • rate lim  │              │  │
│  │  └──────────────┘         └──────────────┘              │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │              File System                           │  │  │
│  │  │  • models/    (ML models)                         │  │  │
│  │  │  • data/      (CSV, JSON)                         │  │  │
│  │  │  • logs/      (Application logs)                 │  │  │
│  │  │  • backups/   (DB backups)                        │  │  │
│  │  │  • experiments/ (ML experiments)                  │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              External Data Sources                       │  │
│  │                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │  NBA API     │  │ The-Odds-API │  │ Basketball-  │  │  │
│  │  │  (gratuita)   │  │  (gratuita)   │  │ Reference    │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

Data Flow:
───────────
User → Telegram Bot/Streamlit → FastAPI → ML Models → PostgreSQL/Redis
                                                    ↑
NBA API/The-Odds-API → Scraping → Data Processing ──┘
```

### **Fluxo de Dados**
```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Telegram   │────►│  FastAPI    │────►│ PostgreSQL  │
│  Bot/Streamlit│    │  Backend    │     │  Database   │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                          │                   │
                          ▼                   │
                    ┌─────────────┐            │
                    │  ML Models  │            │
                    │  (XGBoost)  │            │
                    └──────┬──────┘            │
                           │                   │
                           └───────────────────┘
                                    │
                                    ▼
                          ┌─────────────┐
                          │   Redis     │
                          │   Cache     │
                          └─────────────┘

External Data:
────────────────
┌─────────────┐     ┌─────────────┐
│  NBA API    │────►│  Scraping   │
└─────────────┘     └──────┬──────┘
                          │
                          ▼
                    ┌─────────────┐
                    │  Data       │
                    │  Processing │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ PostgreSQL  │
                    └─────────────┘
```

---

## 🐋 DOCKER COMPOSE MÍNIMO

### **docker-compose.yml Simplificado**
```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: vb-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-valuebetting}
      POSTGRES_USER: ${POSTGRES_USER:-vb_admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: vb-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # FastAPI Backend
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: vb-api
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=${POSTGRES_DB:-valuebetting}
      - POSTGRES_USER=${POSTGRES_USER:-vb_admin}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - ENVIRONMENT=${ENVIRONMENT:-development}
    ports:
      - "${API_PORT:-8000}:8000"
    volumes:
      - ./app:/app/app
      - ./models:/app/models
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
  redis_data:
```

---

## 🔧 COMPONENTES REMOVIDOS E ALTERNATIVAS

### **Prefect UI/API → Scripts Python**
```python
# REMOVIDO: Prefect para orquestração
# ALTERNATIVA: Scripts Python com schedule

import schedule
import time

def run_data_pipeline():
    """Executa pipeline de dados"""
    print("🚀 Executando pipeline de dados...")
    # Código do pipeline aqui

def run_model_training():
    """Executa treino de modelo"""
    print("🤖 Treinando modelo...")
    # Código de treino aqui

# Schedule
schedule.every().day.at("00:00").do(run_data_pipeline)
schedule.every().week.at("00:00").do(run_model_training)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### **Grafana/Prometheus → Logging Simples**
```python
# REMOVIDO: Grafana + Prometheus para monitoring
# ALTERNATIVA: Logging estruturado + health checks

import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Health check simples
def health_check():
    """Health check básico"""
    status = {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'services': {
            'database': check_database(),
            'redis': check_redis(),
            'models': check_models()
        }
    }
    return status

logger.info("Health check: %s", health_check())
```

### **MLflow → Local File System**
```python
# REMOVIDO: MLflow para experiment tracking
# ALTERNATIVA: File system local + JSON

import json
from datetime import datetime
import os

class SimpleExperimentTracker:
    """Tracker simples de experimentos"""
    
    def __init__(self, base_dir='experiments'):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
    
    def log_experiment(self, name, params, metrics, model_path):
        """Regista experimento"""
        experiment = {
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'params': params,
            'metrics': metrics,
            'model_path': model_path
        }
        
        # Guardar em JSON
        filename = f"{self.base_dir}/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(experiment, f, indent=2)
        
        print(f"✅ Experimento guardado: {filename}")
    
    def load_experiments(self):
        """Carrega todos os experimentos"""
        experiments = []
        
        for filename in os.listdir(self.base_dir):
            if filename.endswith('.json'):
                with open(f"{self.base_dir}/{filename}", 'r') as f:
                    experiments.append(json.load(f))
        
        return experiments

# Uso
tracker = SimpleExperimentTracker()
tracker.log_experiment(
    name='xgboost_baseline',
    params={'n_estimators': 100, 'max_depth': 6},
    metrics={'accuracy': 0.65, 'f1': 0.62},
    model_path='models/xgboost_baseline.pkl'
)
```

### **Node Exporter → psutil**
```python
# REMOVIDO: Node Exporter para metrics do sistema
# ALTERNATIVA: psutil para monitoramento local

import psutil

def get_system_metrics():
    """Obter métricas do sistema"""
    metrics = {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'network_io': psutil.net_io_counters()
    }
    return metrics

# Log metrics
metrics = get_system_metrics()
print(f"CPU: {metrics['cpu_percent']}%")
print(f"Memory: {metrics['memory_percent']}%")
print(f"Disk: {metrics['disk_usage']}%")
```

---

## 📊 REQUISITOS DE RECURSOS

### **Memória por Container**
```yaml
# PostgreSQL: 2-4GB RAM
# Redis: 512MB-1GB RAM
# API: 2-4GB RAM
# Total: 4.5-9GB RAM
```

### **CPU por Container**
```yaml
# PostgreSQL: 1-2 vCPU
# Redis: 0.5 vCPU
# API: 2-4 vCPU
# Total: 3.5-6.5 vCPU
```

### **Disco**
```yaml
# PostgreSQL data: 10-50GB
# Redis data: 1-5GB
# Models: 1-5GB
# Logs: 1-2GB
# Total: 13-62GB
```

---

## 🚀 COMANDOS DE GESTÃO

### **Iniciar Stack**
```bash
# Iniciar todos os serviços
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f
```

### **Parar Stack**
```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes
docker-compose down -v
```

### **Reiniciar Serviço Específico**
```bash
# Reiniciar apenas API
docker-compose restart api

# Reiniciar PostgreSQL
docker-compose restart postgres
```

---

## 📋 CHECKLIST DE VALIDAÇÃO

### **PostgreSQL**
- [ ] Container a correr
- [ ] Porta 5432 acessível
- [ ] Database criada
- [ ] Conexão funcional
- [ ] Backup configurado

### **Redis**
- [ ] Container a correr
- [ ] Porta 6379 acessível
- [ ] Password configurada
- [ ] Ping funcional
- [ ] Persistência ativa

### **API**
- [ ] Container a correr
- [ ] Porta 8000 acessível
- [ ] Health check OK
- [ ] Conexões a DB/Redis
- [ ] Logs funcionando

---

## 🔄 MIGRAÇÃO DE STACK ORIGINAL PARA LOCAL

### **Passo 1: Backup Dados Existentes**
```bash
# Backup PostgreSQL
docker exec vb-postgres pg_dump -U vb_admin valuebetting > backup.sql

# Backup Redis
docker exec vb-redis redis-cli -a password SAVE
docker cp vb-redis:/data/dump.rdb ./redis_backup.rdb
```

### **Passo 2: Parar Stack Original**
```bash
docker-compose down
```

### **Passo 3: Atualizar docker-compose.yml**
```bash
# Substituir docker-compose.yml pelo versão mínima
# Verificar variáveis de ambiente
```

### **Passo 4: Iniciar Stack Mínima**
```bash
docker-compose up -d
```

### **Passo 5: Restaurar Dados**
```bash
# Restaurar PostgreSQL
docker exec -i vb-postgres psql -U vb_admin valuebetting < backup.sql

# Restaurar Redis
docker cp redis_backup.rdb vb-redis:/data/dump.rdb
docker exec vb-redis redis-cli -a password --rdb dump.rdb
```

---

## 🎯 MONITORAMENTO BÁSICO

### **Script Completo de Métricas com Visualização**
```python
"""
Script completo de monitoramento da stack local
Monitora PostgreSQL, Redis, API e sistema
Gera relatórios e alertas
"""

import requests
import psycopg2
import redis
import psutil
import subprocess
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StackMetricsCollector:
    """Coletor de métricas da stack local"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.metrics_history = []
        self.alerts = []
        
        # Thresholds para alertas
        self.thresholds = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
            'response_time': 5.0
        }
    
    def check_api_health(self) -> Dict:
        """Verifica saúde da API"""
        try:
            start_time = time.time()
            response = requests.get(
                f"http://{self.config['api_host']}:{self.config['api_port']}/health",
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': response_time,
                    'status_code': response.status_code
                }
            else:
                return {
                    'status': 'unhealthy',
                    'response_time': response_time,
                    'status_code': response.status_code
                }
        except Exception as e:
            logger.error(f"Erro ao verificar API: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_postgresql_health(self) -> Dict:
        """Verifica saúde do PostgreSQL"""
        try:
            conn = psycopg2.connect(
                host=self.config['postgres_host'],
                port=self.config['postgres_port'],
                database=self.config['postgres_db'],
                user=self.config['postgres_user'],
                password=self.config['postgres_password'],
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return {
                'status': 'healthy',
                'version': version[0],
                'connection_time': time.time()
            }
        except Exception as e:
            logger.error(f"Erro ao verificar PostgreSQL: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_redis_health(self) -> Dict:
        """Verifica saúde do Redis"""
        try:
            r = redis.Redis(
                host=self.config['redis_host'],
                port=self.config['redis_port'],
                password=self.config['redis_password'],
                decode_responses=True,
                socket_timeout=5
            )
            
            info = r.info()
            ping = r.ping()
            
            return {
                'status': 'healthy',
                'ping': ping,
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', 'N/A')
            }
        except Exception as e:
            logger.error(f"Erro ao verificar Redis: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def get_system_metrics(self) -> Dict:
        """Obtém métricas do sistema"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'memory_total_gb': memory.total / (1024**3),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / (1024**3),
            'disk_total_gb': disk.total / (1024**3),
            'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
        }
    
    def check_docker_containers(self) -> Dict:
        """Verifica status dos containers Docker"""
        try:
            result = subprocess.run(
                ['docker', 'compose', 'ps'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    'status': 'healthy',
                    'output': result.stdout
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': result.stderr
                }
        except Exception as e:
            logger.error(f"Erro ao verificar containers: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def collect_all_metrics(self) -> Dict:
        """Coleta todas as métricas"""
        timestamp = datetime.now()
        
        metrics = {
            'timestamp': timestamp.isoformat(),
            'api': self.check_api_health(),
            'postgresql': self.check_postgresql_health(),
            'redis': self.check_redis_health(),
            'system': self.get_system_metrics(),
            'docker': self.check_docker_containers()
        }
        
        # Verificar alertas
        self._check_alerts(metrics)
        
        # Adicionar ao histórico
        self.metrics_history.append(metrics)
        
        # Manter apenas últimos 1000 registros
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return metrics
    
    def _check_alerts(self, metrics: Dict):
        """Verifica se há alertas baseados nos thresholds"""
        system = metrics.get('system', {})
        
        # CPU
        if system.get('cpu_percent', 0) > self.thresholds['cpu_percent']:
            self.alerts.append({
                'timestamp': metrics['timestamp'],
                'type': 'cpu_high',
                'value': system['cpu_percent'],
                'threshold': self.thresholds['cpu_percent']
            })
        
        # Memory
        if system.get('memory_percent', 0) > self.thresholds['memory_percent']:
            self.alerts.append({
                'timestamp': metrics['timestamp'],
                'type': 'memory_high',
                'value': system['memory_percent'],
                'threshold': self.thresholds['memory_percent']
            })
        
        # Disk
        if system.get('disk_percent', 0) > self.thresholds['disk_percent']:
            self.alerts.append({
                'timestamp': metrics['timestamp'],
                'type': 'disk_high',
                'value': system['disk_percent'],
                'threshold': self.thresholds['disk_percent']
            })
        
        # API response time
        api = metrics.get('api', {})
        if api.get('response_time', 0) > self.thresholds['response_time']:
            self.alerts.append({
                'timestamp': metrics['timestamp'],
                'type': 'api_slow',
                'value': api['response_time'],
                'threshold': self.thresholds['response_time']
            })
    
    def generate_report(self) -> Dict:
        """Gera relatório de métricas"""
        if not self.metrics_history:
            return {'error': 'Sem dados de métricas'}
        
        latest = self.metrics_history[-1]
        
        # Calcular estatísticas
        cpu_values = [m['system']['cpu_percent'] for m in self.metrics_history]
        memory_values = [m['system']['memory_percent'] for m in self.metrics_history]
        
        report = {
            'timestamp': latest['timestamp'],
            'overall_status': self._calculate_overall_status(latest),
            'components': {
                'api': latest['api']['status'],
                'postgresql': latest['postgresql']['status'],
                'redis': latest['redis']['status'],
                'docker': latest['docker']['status']
            },
            'system': {
                'cpu': {
                    'current': latest['system']['cpu_percent'],
                    'avg': sum(cpu_values) / len(cpu_values),
                    'max': max(cpu_values)
                },
                'memory': {
                    'current': latest['system']['memory_percent'],
                    'avg': sum(memory_values) / len(memory_values),
                    'max': max(memory_values),
                    'available_gb': latest['system']['memory_available_gb']
                },
                'disk': {
                    'current': latest['system']['disk_percent'],
                    'free_gb': latest['system']['disk_free_gb']
                }
            },
            'alerts': {
                'total': len(self.alerts),
                'recent': [a for a in self.alerts if datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(hours=1)]
            },
            'metrics_collected': len(self.metrics_history)
        }
        
        return report
    
    def _calculate_overall_status(self, metrics: Dict) -> str:
        """Calcula status geral da stack"""
        components = [
            metrics['api']['status'],
            metrics['postgresql']['status'],
            metrics['redis']['status'],
            metrics['docker']['status']
        ]
        
        if all(c == 'healthy' for c in components):
            return 'healthy'
        elif any(c == 'healthy' for c in components):
            return 'degraded'
        else:
            return 'unhealthy'
    
    def save_metrics_to_csv(self, filename: str):
        """Salva métricas em CSV"""
        if not self.metrics_history:
            logger.warning("Sem métricas para salvar")
            return
        
        # Flatten metrics
        flattened = []
        for m in self.metrics_history:
            row = {
                'timestamp': m['timestamp'],
                'api_status': m['api']['status'],
                'api_response_time': m['api'].get('response_time', 0),
                'postgres_status': m['postgresql']['status'],
                'redis_status': m['redis']['status'],
                'docker_status': m['docker']['status'],
                'cpu_percent': m['system']['cpu_percent'],
                'memory_percent': m['system']['memory_percent'],
                'disk_percent': m['system']['disk_percent']
            }
            flattened.append(row)
        
        df = pd.DataFrame(flattened)
        output_dir = Path("data/metrics")
        output_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_dir / filename, index=False)
        logger.info(f"💾 Métricas salvas em: {output_dir / filename}")
    
    def visualize_metrics(self, save_path: str = None):
        """Gera visualização das métricas"""
        if not self.metrics_history:
            logger.warning("Sem métricas para visualizar")
            return
        
        # Preparar dados
        timestamps = [datetime.fromisoformat(m['timestamp']) for m in self.metrics_history]
        cpu_values = [m['system']['cpu_percent'] for m in self.metrics_history]
        memory_values = [m['system']['memory_percent'] for m in self.metrics_history]
        api_response_times = [m['api'].get('response_time', 0) for m in self.metrics_history]
        
        # Criar figura com 3 subplots
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # CPU
        axes[0].plot(timestamps, cpu_values, 'b-', linewidth=2)
        axes[0].axhline(y=self.thresholds['cpu_percent'], color='r', linestyle='--', label='Threshold')
        axes[0].set_title('CPU Usage %', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('%')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Memory
        axes[1].plot(timestamps, memory_values, 'g-', linewidth=2)
        axes[1].axhline(y=self.thresholds['memory_percent'], color='r', linestyle='--', label='Threshold')
        axes[1].set_title('Memory Usage %', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('%')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        # API Response Time
        axes[2].plot(timestamps, api_response_times, 'purple', linewidth=2)
        axes[2].axhline(y=self.thresholds['response_time'], color='r', linestyle='--', label='Threshold')
        axes[2].set_title('API Response Time (s)', fontsize=12, fontweight='bold')
        axes[2].set_ylabel('Seconds')
        axes[2].set_xlabel('Time')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            output_dir = Path("data/metrics")
            output_dir.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_dir / save_path, dpi=300, bbox_inches='tight')
            logger.info(f"💾 Gráfico salvo em: {output_dir / save_path}")
        else:
            plt.show()
        
        plt.close()

# Uso
if __name__ == "__main__":
    config = {
        'api_host': 'localhost',
        'api_port': 8000,
        'postgres_host': 'localhost',
        'postgres_port': 5432,
        'postgres_db': 'valuebetting',
        'postgres_user': 'vb_admin',
        'postgres_password': 'your_password',
        'redis_host': 'localhost',
        'redis_port': 6379,
        'redis_password': 'your_password'
    }
    
    collector = StackMetricsCollector(config)
    
    # Coletar métricas
    metrics = collector.collect_all_metrics()
    
    # Gerar relatório
    report = collector.generate_report()
    
    print("\n📊 Relatório de Métricas:")
    print("="*60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Status Geral: {report['overall_status'].upper()}")
    print(f"\nComponentes:")
    for component, status in report['components'].items():
        print(f"  {component}: {status}")
    print(f"\nSistema:")
    print(f"  CPU: {report['system']['cpu']['current']:.1f}% (avg: {report['system']['cpu']['avg']:.1f}%)")
    print(f"  Memory: {report['system']['memory']['current']:.1f}% (avg: {report['system']['memory']['avg']:.1f}%)")
    print(f"  Disk: {report['system']['disk']['current']:.1f}%")
    print(f"\nAlertas:")
    print(f"  Total: {report['alerts']['total']}")
    print(f"  Recent (1h): {len(report['alerts']['recent'])}")
    print("="*60)
    
    # Salvar métricas
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    collector.save_metrics_to_csv(f"metrics_{timestamp_str}.csv")
    
    # Visualizar
    collector.visualize_metrics(f"metrics_{timestamp_str}.png")
```

---

## 📈 ESCALABILIDADE

### **Quando Escalar?**
```
< 10 utilizadores: Stack local (3 containers)
10-50 utilizadores: Adicionar MLflow local
50-100 utilizadores: Considerar VPS
> 100 utilizadores: VPS + managed services
```

### **Caminho de Escalabilidade**
```yaml
# Fase 1: Local (atual)
postgres, redis, api

# Fase 2: Local + MLflow
postgres, redis, api, mlflow

# Fase 3: VPS básico
postgres, redis, api, mlflow, grafana, prometheus

# Fase 4: VPS completo
postgres, redis, api, mlflow, grafana, prometheus, prefect
```

---

## ⚠️ LIMITAÇÕES

### **Stack Local**
- **Escalabilidade:** Máximo 10 utilizadores simultâneos
- **Uptime:** PC precisa estar ligado 24/7
- **Backup:** Manual, não automático
- **Monitoring:** Básico, sem dashboards avançados

### **Quando Migrar para VPS**
- Sistema estável 3+ meses
- Mais de 10 utilizadores
- Receita justifica custo
- Necessário uptime garantido

---

## 🚀 PRÓXIMOS PASSOS

### **Implementação Imediata:**
1. **Atualizar docker-compose.yml** para versão mínima
2. **Testar stack local**
3. **Migrar dados se existentes**
4. **Validar funcionamento**

### **Documentação Adicional:**
- [[10_Infrastructure/DOCKER_LOCAL]] - Docker compose detalhado
- [[10_Infrastructure/MONITORING_LOCAL]] - Monitoring básico

---

**Status:** Stack local mínimo definido  
**Redução:** 67% menos containers (9 → 3)  
**Custo:** 0€  
**Escalabilidade:** Até 10 utilizadores  

---

#status/active #priority/critical #phase/infra-local
