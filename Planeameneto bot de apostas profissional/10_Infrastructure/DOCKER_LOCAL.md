# Docker Local - Setup Zero Euros

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  

---

## 🎯 OBJETIVO

Configuração detalhada de Docker local para stack mínima do VBQ-UNIFIED, com instruções de setup, gestão e troubleshooting.

---

## 🐋 DOCKERFILE OTIMIZADO

### **Dockerfile para API**
```dockerfile
# Multi-stage build para imagem otimizada
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependências de compilação
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage final
FROM python:3.11-slim

WORKDIR /app

# Copiar dependências do builder
COPY --from=builder /root/.local /root/.local

# Copiar código da aplicação
COPY app/ ./app/
COPY models/ ./models/

# Definir PATH
ENV PATH=/root/.local/bin:$PATH

# Expor porta
EXPOSE 8000

# Comando de início
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📋 DOCKER COMPLETO

### **docker-compose.yml Final**
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
      - ./init:/docker-entrypoint-initdb.d
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - vb-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: vb-redis
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks:
      - vb-network

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
      - PYTHONUNBUFFERED=1
    ports:
      - "${API_PORT:-8000}:8000"
    volumes:
      - ./app:/app/app
      - ./models:/app/models
      - ./logs:/app/logs
      - ./data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - vb-network

volumes:
  postgres_data:
  redis_data:

networks:
  vb-network:
    driver: bridge
```

---

## 🔧 CONFIGURAÇÃO .ENV

### **.env Example**
```bash
# Database
POSTGRES_DB=valuebetting
POSTGRES_USER=vb_admin
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_PORT=5432

# Redis
REDIS_PASSWORD=your_secure_password_here
REDIS_PORT=6379

# API
API_PORT=8000
ENVIRONMENT=development

# Secrets (opcional para futuro)
SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here
```

### **Criar .env**
```bash
# Copiar exemplo
cp .env.example .env

# Editar com valores seguros
# Usar passwords fortes e únicas
```

---

## 🚀 COMANDOS DE GESTÃO

### **Setup Inicial**
```bash
# Criar diretórios necessários
mkdir -p backups init logs data models

# Criar network
docker network create vb-network

# Build imagem
docker-compose build

# Iniciar serviços
docker-compose up -d

# Verificar status
docker-compose ps
```

### **Gestão Diária**
```bash
# Ver logs em tempo real
docker-compose logs -f api

# Ver logs específicos
docker-compose logs postgres
docker-compose logs redis

# Reiniciar serviço
docker-compose restart api

# Parar serviço
docker-compose stop api

# Iniciar serviço
docker-compose start api
```

### **Backup e Restore**
```bash
# Backup PostgreSQL
docker exec vb-postgres pg_dump -U vb_admin valuebetting > backups/postgres_backup_$(date +%Y%m%d).sql

# Backup Redis
docker exec vb-redis redis-cli -a ${REDIS_PASSWORD} BGSAVE
docker cp vb-redis:/data/dump.rdb backups/redis_backup_$(date +%Y%m%d).rdb

# Restore PostgreSQL
docker exec -i vb-postgres psql -U vb_admin valuebetting < backups/postgres_backup_20240518.sql

# Restore Redis
docker cp backups/redis_backup_20240518.rdb vb-redis:/data/dump.rdb
docker-compose restart redis
```

---

## 📊 MONITORAMENTO DE CONTAINERS

### **Script Completo de Gestão de Docker**
```python
"""
Script completo de gestão de containers Docker
Inclui monitoramento, backup, restore e automação
"""

import docker
import subprocess
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional
import psutil

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DockerManager:
    """Gestor completo de Docker"""
    
    def __init__(self, compose_file="docker-compose.yml"):
        self.client = docker.from_env()
        self.compose_file = compose_file
        self.backup_dir = Path("backups/docker")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def get_container_status(self, container_name: str) -> Dict:
        """Obter status detalhado de um container"""
        try:
            container = self.client.containers.get(container_name)
            stats = container.stats(stream=False)
            
            # Calcular CPU
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta * 100) if system_delta > 0 else 0
            
            # Calcular memória
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
            
            return {
                'name': container.name,
                'status': container.status,
                'state': container.attrs['State']['Status'],
                'cpu_percent': cpu_percent,
                'memory_usage_mb': memory_usage / (1024**2),
                'memory_limit_mb': memory_limit / (1024**2),
                'memory_percent': memory_percent,
                'restart_count': container.attrs['RestartCount'],
                'created': container.attrs['Created'],
                'image': container.attrs['Config']['Image']
            }
        except docker.errors.NotFound:
            return {'name': container_name, 'status': 'not_found', 'error': 'Container não existe'}
        except Exception as e:
            logger.error(f"Erro ao obter status de {container_name}: {e}")
            return {'name': container_name, 'status': 'error', 'error': str(e)}
    
    def get_all_containers_status(self) -> Dict:
        """Obter status de todos os containers do compose"""
        containers = ['vb-postgres', 'vb-redis', 'vb-api']
        status = {}
        
        for container_name in containers:
            status[container_name] = self.get_container_status(container_name)
        
        return status
    
    def print_status_report(self):
        """Imprime relatório de status dos containers"""
        status = self.get_all_containers_status()
        
        print("\n" + "="*70)
        print("📊 RELATÓRIO DE STATUS DOS CONTAINERS")
        print("="*70)
        
        for container_name, data in status.items():
            print(f"\n📦 {container_name.upper()}")
            print("-" * 70)
            
            if data.get('status') == 'not_found':
                print(f"❌ Container não encontrado")
                continue
            
            if data.get('status') == 'error':
                print(f"❌ Erro: {data.get('error')}")
                continue
            
            print(f"Status: {data['status'].upper()}")
            print(f"State: {data['state']}")
            print(f"CPU: {data['cpu_percent']:.2f}%")
            print(f"Memória: {data['memory_usage_mb']:.2f} MB / {data['memory_limit_mb']:.2f} MB ({data['memory_percent']:.2f}%)")
            print(f"Restarts: {data['restart_count']}")
            print(f"Image: {data['image']}")
        
        print("\n" + "="*70)
    
    def restart_container(self, container_name: str) -> bool:
        """Reinicia um container"""
        try:
            container = self.client.containers.get(container_name)
            container.restart()
            logger.info(f"✅ Container {container_name} reiniciado")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao reiniciar {container_name}: {e}")
            return False
    
    def stop_container(self, container_name: str) -> bool:
        """Para um container"""
        try:
            container = self.client.containers.get(container_name)
            container.stop()
            logger.info(f"✅ Container {container_name} parado")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao parar {container_name}: {e}")
            return False
    
    def start_container(self, container_name: str) -> bool:
        """Inicia um container"""
        try:
            container = self.client.containers.get(container_name)
            container.start()
            logger.info(f"✅ Container {container_name} iniciado")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar {container_name}: {e}")
            return False
    
    def backup_postgres(self) -> bool:
        """Backup do PostgreSQL"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"postgres_backup_{timestamp}.sql"
            
            # Executar backup
            result = subprocess.run(
                [
                    'docker', 'exec', 'vb-postgres',
                    'pg_dump', '-U', 'vb_admin', 'valuebetting'
                ],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                with open(backup_file, 'w') as f:
                    f.write(result.stdout)
                
                logger.info(f"✅ Backup PostgreSQL salvo: {backup_file}")
                return True
            else:
                logger.error(f"❌ Erro ao fazer backup PostgreSQL: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao fazer backup PostgreSQL: {e}")
            return False
    
    def backup_redis(self) -> bool:
        """Backup do Redis"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"redis_backup_{timestamp}.rdb"
            
            # Executar BGSAVE
            subprocess.run(
                ['docker', 'exec', 'vb-redis', 'redis-cli', '-a', 
                 '${REDIS_PASSWORD}', 'BGSAVE'],
                capture_output=True,
                timeout=30
            )
            
            # Aguardar 5 segundos para o BGSAVE completar
            time.sleep(5)
            
            # Copiar dump.rdb
            subprocess.run(
                ['docker', 'cp', 'vb-redis:/data/dump.rdb', str(backup_file)],
                timeout=60
            )
            
            logger.info(f"✅ Backup Redis salvo: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer backup Redis: {e}")
            return False
    
    def backup_all(self) -> Dict:
        """Backup de todos os serviços"""
        logger.info("🔄 Iniciando backup completo...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'postgres': self.backup_postgres(),
            'redis': self.backup_redis()
        }
        
        success_count = sum(1 for v in results.values() if v is True)
        logger.info(f"✅ Backup completo: {success_count}/2 serviços")
        
        return results
    
    def restore_postgres(self, backup_file: str) -> bool:
        """Restore do PostgreSQL"""
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"❌ Arquivo de backup não encontrado: {backup_file}")
                return False
            
            # Executar restore
            with open(backup_path, 'r') as f:
                result = subprocess.run(
                    ['docker', 'exec', '-i', 'vb-postgres',
                     'psql', '-U', 'vb_admin', 'valuebetting'],
                    stdin=f,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            
            if result.returncode == 0:
                logger.info(f"✅ Restore PostgreSQL concluído: {backup_file}")
                return True
            else:
                logger.error(f"❌ Erro ao fazer restore PostgreSQL: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao fazer restore PostgreSQL: {e}")
            return False
    
    def restore_redis(self, backup_file: str) -> bool:
        """Restore do Redis"""
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"❌ Arquivo de backup não encontrado: {backup_file}")
                return False
            
            # Parar Redis
            self.stop_container('vb-redis')
            
            # Copiar backup
            subprocess.run(
                ['docker', 'cp', str(backup_path), 'vb-redis:/data/dump.rdb'],
                timeout=60
            )
            
            # Iniciar Redis
            self.start_container('vb-redis')
            
            logger.info(f"✅ Restore Redis concluído: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer restore Redis: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """Lista todos os backups disponíveis"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*"):
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'size_mb': stat.st_size / (1024**2),
                'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': 'postgres' if 'postgres' in backup_file.name else 'redis'
            })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def cleanup_old_backups(self, keep_days: int = 7) -> int:
        """Remove backups antigos"""
        cutoff = datetime.now() - timedelta(days=keep_days)
        removed = 0
        
        for backup_file in self.backup_dir.glob("*"):
            if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff:
                backup_file.unlink()
                removed += 1
                logger.info(f"🗑️  Backup removido: {backup_file.name}")
        
        logger.info(f"✅ Cleanup concluído: {removed} backups removidos")
        return removed
    
    def get_docker_system_info(self) -> Dict:
        """Obter informações do sistema Docker"""
        try:
            # Espaço usado
            df_result = subprocess.run(
                ['docker', 'system', 'df'],
                capture_output=True,
                text=True
            )
            
            # Informações do sistema
            info_result = subprocess.run(
                ['docker', 'info', '--format', '{{json .}}'],
                capture_output=True,
                text=True
            )
            
            info = json.loads(info_result.stdout) if info_result.returncode == 0 else {}
            
            return {
                'system_df': df_result.stdout,
                'containers_running': info.get('Containers', 0),
                'containers_paused': info.get('ContainersPaused', 0),
                'containers_stopped': info.get('ContainersStopped', 0),
                'images': info.get('Images', 0),
                'server_version': info.get('ServerVersion', 'unknown')
            }
        except Exception as e:
            logger.error(f"Erro ao obter info do sistema Docker: {e}")
            return {}
    
    def cleanup_docker(self) -> bool:
        """Limpeza do sistema Docker"""
        try:
            logger.info("🔄 Executando limpeza do Docker...")
            
            # Remover containers parados
            subprocess.run(['docker', 'container', 'prune', '-f'], timeout=60)
            
            # Remover imagens não usadas
            subprocess.run(['docker', 'image', 'prune', '-a', '-f'], timeout=300)
            
            # Remover volumes não usados
            subprocess.run(['docker', 'volume', 'prune', '-f'], timeout=60)
            
            logger.info("✅ Limpeza do Docker concluída")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar Docker: {e}")
            return False
    
    def health_check_all(self) -> Dict:
        """Health check completo de todos os containers"""
        status = self.get_all_containers_status()
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall': 'healthy',
            'containers': {}
        }
        
        for container_name, data in status.items():
            container_health = {
                'status': data.get('status', 'unknown'),
                'state': data.get('state', 'unknown'),
                'healthy': data.get('status') == 'running' and data.get('state') == 'running'
            }
            
            health_status['containers'][container_name] = container_health
            
            if not container_health['healthy']:
                health_status['overall'] = 'unhealthy'
        
        return health_status

# Uso
if __name__ == "__main__":
    manager = DockerManager()
    
    # Imprimir status
    manager.print_status_report()
    
    # Health check
    health = manager.health_check_all()
    print(f"\n🏥 Health Check: {health['overall'].upper()}")
    
    # Backup
    backup_results = manager.backup_all()
    print(f"\n💾 Backup Results: {backup_results}")
    
    # Listar backups
    backups = manager.list_backups()
    print(f"\n📋 Backups disponíveis: {len(backups)}")
    for backup in backups[:5]:
        print(f"  - {backup['filename']} ({backup['size_mb']:.2f} MB)")
```

---

## 🔧 OTIMIZAÇÃO DE RECURSOS

### **Limitar Memória por Container**
```yaml
# Adicionar ao docker-compose.yml
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
  
  redis:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
  
  api:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

### **Limitar CPU por Container**
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
        reservations:
          cpus: '1.0'
```

---

## 🧪 TESTES DE CONECTIVIDADE

### **Script de Teste**
```python
import requests
import psycopg2
import redis

def test_all_connections():
    """Testa todas as conexões"""
    
    print("🧪 Testando conexões...\n")
    
    # Test API
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ API: Conectado")
        else:
            print(f"❌ API: Status {response.status_code}")
    except Exception as e:
        print(f"❌ API: {e}")
    
    # Test PostgreSQL
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='valuebetting',
            user='vb_admin',
            password='your_password'
        )
        print("✅ PostgreSQL: Conectado")
        conn.close()
    except Exception as e:
        print(f"❌ PostgreSQL: {e}")
    
    # Test Redis
    try:
        r = redis.Redis(host='localhost', port=6379, 
                       password='your_password', decode_responses=True)
        r.ping()
        print("✅ Redis: Conectado")
    except Exception as e:
        print(f"❌ Redis: {e}")

if __name__ == "__main__":
    test_all_connections()
```

---

## 🔄 ATUALIZAÇÃO DE CONTAINERS

### **Rebuild com Código Novo**
```bash
# Parar containers
docker-compose down

# Rebuild imagem
docker-compose build --no-cache api

# Iniciar novamente
docker-compose up -d

# Verificar logs
docker-compose logs -f api
```

### **Atualizar Imagens Base**
```bash
# Pull novas imagens
docker-compose pull

# Rebuild e restart
docker-compose up -d --build
```

---

## 📋 CLEANUP E MANUTENÇÃO

### **Limpeza Regular**
```bash
# Remover containers parados
docker container prune

# Remover imagens não usadas
docker image prune -a

# Remover volumes não usados
docker volume prune

# Limpeza completa
docker system prune -a --volumes
```

### **Análise de Espaço**
```bash
# Ver espaço usado por Docker
docker system df

# Ver tamanho de imagens
docker images

# Ver tamanho de volumes
docker volume ls
```

---

## 🚨 TROUBLESHOOTING

### **Container não Inicia**
```bash
# Ver logs
docker-compose logs api

# Ver detalhes do container
docker inspect vb-api

# Verificar recursos
docker stats vb-api
```

### **Problemas de Rede**
```bash
# Ver networks
docker network ls

# Ver network do container
docker network inspect vb-network

# Testar conectividade
docker exec vb-api ping postgres
```

### **Problemas de Volume**
```bash
# Ver volumes
docker volume ls

# Ver detalhes do volume
docker volume inspect vb-postgres_data

# Backup antes de remover
docker run --rm -v vb-postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data
```

---

## 📊 PERFORMANCE TUNING

### **Otimizações PostgreSQL**
```yaml
# Adicionar ao docker-compose.yml
postgres:
  command:
    - postgres
    - -c
    - shared_buffers=256MB
    - -c
    - max_connections=100
    - -c
    - work_mem=4MB
    - -c
    - maintenance_work_mem=64MB
```

### **Otimizações Redis**
```yaml
redis:
  command:
    - redis-server
    - --requirepass
    - ${REDIS_PASSWORD}
    - --maxmemory
    - 256mb
    - --maxmemory-policy
    - allkeys-lru
```

---

## 📋 CHECKLIST DE DEPLOYMENT

### **Pré-Deployment**
- [ ] Docker Desktop instalado
- [ ] docker-compose.yml atualizado
- [ ] .env configurado
- [ ] Diretórios criados
- [ ] Network criada

### **Deployment**
- [ ] Build imagem com sucesso
- [ ] Containers iniciam
- [ ] Health checks passam
- [ ] Conectividade OK
- [ ] Logs sem erros

### **Pós-Deployment**
- [ ] Backup inicial criado
- [ ] Monitoring configurado
- [ ] Scripts de teste OK
- [ ] Documentação atualizada
- [ ] Equipe notificada

---

## 🚀 AUTOMAÇÃO

### **Script de Setup Automático**
```bash
#!/bin/bash

echo "🚀 Setup Automático VBQ-UNIFIED"

# Criar diretórios
mkdir -p backups init logs data models

# Criar network
docker network create vb-network

# Build e iniciar
docker-compose build
docker-compose up -d

# Aguardar health checks
echo "⏳ Aguardando containers ficarem saudáveis..."
sleep 30

# Testar conexões
python test_connections.py

echo "✅ Setup completo!"
```

---

**Status:** Docker local configurado  
**Custo:** 0€  
**Containers:** 3 essenciais  
**Performance:** Otimizado para PC local  

---

#status/active #priority/critical #phase/infra-local
