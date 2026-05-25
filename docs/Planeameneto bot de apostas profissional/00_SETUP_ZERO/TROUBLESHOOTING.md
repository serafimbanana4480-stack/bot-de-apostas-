# Troubleshooting - Setup Zero Euros

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  

---

## 🎯 OBJETIVO

Guia de resolução de problemas comuns durante o setup e implementação do sistema VBQ-UNIFIED zero euros, com exemplos de logs e diagnóstico sistemático.

---

## 🔍 DIAGNÓSTICO RÁPIDO

### **Fluxograma de Diagnóstico**
```
┌─────────────────┐
│ PROBLEMA OCORREU│
└────────┬────────┘
         ↓
┌─────────────────┐
│ Qual categoria? │
└────────┬────────┘
    ↓    ↓    ↓    ↓
Hardware Docker Python Rede
    ↓    ↓    ↓    ↓
Ver logs Ver logs Ver logs Testar
sistema containers terminal conect.
    ↓    ↓    ↓    ↓
Aplicar solução específica
         ↓
┌─────────────────┐
│  PROBLEMA RESOLVIDO? │
└────────┬────────┘
    ↓         ↓
   SIM        NÃO
    ↓         ↓
Continuar   Reset
```

---

## 🔧 PROBLEMAS COMUNS POR CATEGORIA

### **Problemas de Hardware**

#### **Memória Insuficiente**
```bash
# Sintomas:
- Containers crash com OOM (Out of Memory)
- Sistema lento
- Docker não inicia

# Logs típicos:
docker-compose logs postgres:
  "OutOfMemoryError: Java heap space"
  "Killed"

# Soluções:
1. Aumentar RAM do sistema (ideal 16GB+)
2. Limitar memória Docker:
   Docker Desktop > Settings > Resources > Memory
   Ajustar para 4-8GB
3. Fechar aplicações desnecessárias
4. Aumentar swap do sistema:
   Windows: Ajustar no sistema
   Linux: sudo fallocate -l 4G /swapfile
```

#### **CPU Sobrecarregado**
```bash
# Sintomas:
- CPU 100% constantemente
- Sistema responsivo
- Containers lentos

# Logs típicos:
docker stats:
  CONTAINER   CPU %   MEM USAGE
  vb-mlflow   450%    2.5GB
  vb-api      200%    1.8GB

# Soluções:
1. Reduzir número de containers
2. Limitar CPU por container:
   docker-compose.yml:
   deploy:
     resources:
       limits:
         cpus: '2.0'
3. Priorizar processos essenciais
4. Desativar serviços não críticos
```

#### **Disco Cheio**
```bash
# Sintomas:
- Erro "No space left on device"
- Containers não iniciam
- Logs não escritos

# Logs típicos:
docker-compose logs:
  "ERROR: could not write to log file: No space left on device"
  "ERROR: failed to allocate directory"

# Soluções:
1. Limpar Docker:
   docker system prune -a
2. Limpar logs:
   docker-compose logs --tail=0
3. Aumentar espaço disco
4. Mover dados para disco externo
```

---

### **Problemas de Docker**

#### **Docker não Inicia**
```bash
# Windows:
# Sintomas:
- "Docker Desktop failed to start"
- "WSL 2 installation is incomplete"

# Logs típicos:
Event Viewer > Windows Logs > Application:
  "The Docker Desktop Service service failed to start"
  "Error: WSL 2 component is not installed"

# Soluções:
# 1. Habilitar WSL2:
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux2 /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 2. Reiniciar PC

# 3. Instalar WSL2:
wsl --install

# 4. Verificar:
wsl --list --verbose

# Linux:
# Sintomas:
- "Cannot connect to Docker daemon"
- "permission denied while trying to connect"

# Logs típicos:
journalctl -u docker:
  "failed to start Docker Application Container Engine"
  "permission denied: unix:///var/run/docker.sock"

# Soluções:
# 1. Adicionar usuário ao grupo docker:
sudo usermod -aG docker $USER

# 2. Fazer logout e login:
newgrp docker

# 3. Verificar:
docker ps
```

#### **Portas em Uso**
```bash
# Sintomas:
- "port is already allocated"
- Containers não iniciam

# Logs típicos:
docker-compose up:
  "ERROR: for postgres  Cannot start service postgres: driver failed programming external connectivity"
  "Error: bind: address already in use"

# Soluções:
1. Identificar processo na porta:
   Windows: netstat -ano | findstr :5432
   Linux: lsof -i :5432

2. Matar processo:
   Windows: taskkill /PID <PID> /F
   Linux: kill -9 <PID>

3. Mudar portas no .env:
   POSTGRES_PORT=5433
   REDIS_PORT=6380

4. Reiniciar containers:
   docker-compose down
   docker-compose up -d
```

#### **Containers não Conectam**
```bash
# Sintomas:
- "connection refused"
- "host not found in upstream"

# Logs típicos:
docker-compose logs:
  "redis: Connection refused"
  "api: Error connecting to database: could not connect to server"

# Soluções:
1. Verificar network:
   docker network ls
   docker network inspect vb-network

2. Recriar network:
   docker-compose down
   docker network prune
   docker-compose up -d

3. Verificar DNS:
   docker-compose.yml:
   extra_hosts:
     - "host.docker.internal:host-gateway"
```

---

### **Problemas de Python**

#### **Python não Encontrado**
```bash
# Windows:
# Sintomas:
- "'python' is not recognized"
- "Command not found"

# Logs típicos:
PowerShell:
  "python : The term 'python' is not recognized as the name of a cmdlet"

# Soluções:
# 1. Adicionar ao PATH manualmente:
# C:\Users\Nome\AppData\Local\Programs\Python\Python311\
# C:\Users\Nome\AppData\Local\Programs\Python\Python311\Scripts\

# 2. Reiniciar terminal

# 3. Verificar:
python --version
where python

# Linux/macOS:
# Sintomas:
- "bash: python: command not found"
- "python3: command not found"

# Logs típicos:
Terminal:
  "bash: python: command not found"

# Soluções:
# 1. Criar alias:
echo 'alias python=python3.11' >> ~/.bashrc
source ~/.bashrc

# 2. Verificar:
python --version
which python
```

#### **Pip não Funciona**
```bash
# Sintomas:
- "pip: command not found"
- Erros de instalação

# Logs típicos:
pip install package:
  "pip: command not found"
  "ModuleNotFoundError: No module named pip"

# Soluções:
1. Usar python -m pip:
   python -m pip install --upgrade pip

2. Reinstalar pip:
   python -m ensurepip --upgrade

3. Verificar PATH:
   echo $PATH  # Linux/macOS
   echo %PATH%  # Windows
```

#### **Dependências Falham**
```bash
# Sintomas:
- Erros de compilação
- Versões incompatíveis

# Logs típicos:
pip install numpy:
  "error: Microsoft Visual C++ 14.0 is required"
  "fatal error C1083: Cannot open include file: 'pyconfig.h'"

# Soluções:
1. Atualizar pip:
   pip install --upgrade pip

2. Usar versões específicas:
   pip install package==version

3. Instalar ferramentas de compilação:
   Windows: Visual C++ Build Tools
   Linux: sudo apt install build-essential
   macOS: xcode-select --install

4. Usar pré-compilados:
   pip install --only-binary :all: package
```

---

### **Problemas de Database**

#### **PostgreSQL não Conecta**
```bash
# Sintomas:
- "connection refused"
- "password authentication failed"

# Logs típicos:
docker-compose logs postgres:
  "FATAL: password authentication failed for user \"vb_admin\""
  "LOG: could not connect to server: Connection refused"

# Soluções:
1. Verificar se container está a correr:
   docker-compose ps postgres

2. Verificar logs:
   docker-compose logs postgres

3. Testar conexão direta:
   docker exec -it vb-postgres psql -U vb_admin -d valuebetting

4. Verificar .env:
   POSTGRES_PASSWORD=senha_correta

5. Reiniciar container:
   docker-compose restart postgres
```

#### **Redis não Conecta**
```bash
# Sintomas:
- "connection refused"
- "NOAUTH Authentication required"

# Logs típicos:
docker-compose logs redis:
  "Warning: AUTH password didn't match"
  "Connection refused"

# Soluções:
1. Verificar se container está a correr:
   docker-compose ps redis

2. Verificar logs:
   docker-compose logs redis

3. Testar conexão:
   docker exec -it vb-redis redis-cli -a tua_senha ping

4. Verificar .env:
   REDIS_PASSWORD=senha_correta

5. Reiniciar container:
   docker-compose restart redis
```

#### **Database Lock**
```bash
# Sintomas:
- Queries bloqueadas
- "database is locked"

# Logs típicos:
PostgreSQL logs:
  "LOG: process <PID> still waiting for AccessExclusiveLock"
  "ERROR: deadlock detected"

# Soluções:
1. Identificar locks:
   docker exec -it vb-postgres psql -U vb_admin -d valuebetting
   SELECT * FROM pg_stat_activity WHERE state = 'active';

2. Matar queries bloqueadas:
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';

3. Reiniciar database:
   docker-compose restart postgres
```

---

### **Problemas de Rede**

#### **Internet Instável**
```bash
# Sintomas:
- APIs externas não respondem
- Downloads falham
- Timeouts frequentes

# Logs típicos:
Application logs:
  "requests.exceptions.Timeout: Connection timeout"
  "requests.exceptions.ConnectionError: Connection refused"

# Soluções:
1. Testar conectividade:
   ping google.com
   ping nba.com

2. Verificar firewall:
   Windows: Windows Defender
   Linux: sudo ufw status

3. Usar VPN se necessário
4. Aumentar timeouts:
   requests.get(url, timeout=30)
```

#### **Rate Limits APIs**
```bash
# Sintomas:
- "429 Too Many Requests"
- APIs bloqueadas

# Logs típicos:
API logs:
  "HTTPError: 429 Client Error: Too Many Requests"
  "Rate limit exceeded. Try again in 60 seconds."

# Soluções:
1. Adicionar delays entre requests:
   import time
   time.sleep(1)  # 1 segundo delay

2. Usar cache:
   @lru_cache(maxsize=100)
   def get_data():
       pass

3. Implementar backoff:
   import time
   from requests.adapters import HTTPAdapter
   from urllib3.util.retry import Retry

4. Usar múltiplas APIs:
   Rotacionar entre diferentes fontes
```

#### **DNS Issues**
```bash
# Sintomas:
- "name resolution failed"
- Domínios não resolvem

# Logs típicos:
Application logs:
  "gaierror: [Errno -2] Name or service not known"
  "requests.exceptions.ConnectionError: Failed to establish connection"

# Soluções:
1. Limpar cache DNS:
   Windows: ipconfig /flushdns
   Linux: sudo systemd-resolve --flush-caches
   macOS: sudo dscacheutil -flushcache

2. Mudar DNS:
   Usar Google DNS (8.8.8.8, 8.8.4.4)
   Usar Cloudflare DNS (1.1.1.1, 1.0.0.1)

3. Verificar /etc/hosts (Linux/macOS)
```

---

### **Problemas de MLflow**

#### **MLflow não Inicia**
```bash
# Sintomas:
- Container crash imediatamente
- UI não acessível

# Logs típicos:
docker-compose logs mlflow:
  "ERROR: Could not connect to database"
  "psycopg2.OperationalError: could not connect to server"

# Soluções:
1. Verificar logs:
   docker-compose logs mlflow

2. Verificar conexão PostgreSQL:
   docker exec -it vb-mlflow bash
   ping postgres

3. Verificar backend store:
   .env:
   BACKEND_STORE_URI=postgresql://...

4. Reiniciar com debug:
   docker-compose up mlflow
```

#### **Experiments não Aparecem**
```bash
# Sintomas:
- UI vazia
- Experiments não registados

# Logs típicos:
Python logs:
  "MlflowException: Experiment 'VBQ-UNIFIED' does not exist"

# Soluções:
1. Verificar tracking URI:
   import mlflow
   mlflow.set_tracking_uri("http://localhost:5000")

2. Verificar experiment name:
   mlflow.set_experiment("VBQ-UNIFIED")

3. Verificar permissões:
   docker exec -it vb-mlflow bash
   ls -la /mlflow

4. Criar experiment manualmente:
   mlflow.create_experiment("VBQ-UNIFIED")
```

---

### **Problemas de Grafana/Prometheus**

#### **Grafana não Acessível**
```bash
# Sintomas:
- "connection refused"
- Login falha

# Logs típicos:
docker-compose logs grafana:
  "Failed to connect to database"
  "Cannot connect to PostgreSQL"

# Soluções:
1. Verificar se está a correr:
   docker-compose ps grafana

2. Verificar logs:
   docker-compose logs grafana

3. Reset password:
   docker exec -it vb-grafana grafana-cli admin reset-admin-password admin

4. Verificar port:
   http://localhost:3000
```

#### **Prometheus não Recolhe Métricas**
```bash
# Sintomas:
- Dashboards vazios
- Sem dados

# Logs típicos:
Prometheus logs:
  "context deadline exceeded"
  "no such host"

# Soluções:
1. Verificar configuração:
   cat monitoring/prometheus/prometheus.yml

2. Verificar targets:
   http://localhost:9090/targets

3. Verificar se apps exportam métricas:
   http://localhost:8000/metrics

4. Recarregar configuração:
   docker exec -it vb-prometheus kill -HUP 1
```

---

## 📊 DIAGNÓSTICO SISTEMÁTICO

### **Script de Diagnóstico**
```python
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd):
    """Executa comando e retorna output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

def diagnose_system():
    """Diagnóstico completo do sistema"""
    
    print("🔍 Diagnóstico Sistemático do Sistema\n")
    print("="*50)
    
    # Sistema
    print("🖥️  Sistema Operacional:")
    output, code = run_command("uname -a" if os.name != "nt" else "systeminfo")
    print(f"   {output}")
    
    # CPU
    print("\n🔧 CPU:")
    output, code = run_command("nproc" if os.name != "nt" else "wmic cpu get name")
    print(f"   {output}")
    
    # RAM
    print("\n🧠 RAM:")
    if os.name != "nt":
        output, code = run_command("free -h")
    else:
        output, code = run_command("wmic OS get TotalVisibleMemorySize")
    print(f"   {output}")
    
    # Disco
    print("\n💾 Disco:")
    if os.name != "nt":
        output, code = run_command("df -h")
    else:
        output, code = run_command("wmic logicaldisk get size,freespace,caption")
    print(f"   {output}")
    
    # Docker
    print("\n🐳 Docker:")
    output, code = run_command("docker --version")
    if code == 0:
        print(f"   ✅ {output}")
        output, code = run_command("docker ps")
        print(f"   Containers: {len(output.split('\\n'))-1}")
    else:
        print(f"   ❌ Docker não instalado")
    
    # Python
    print("\n🐍 Python:")
    output, code = run_command("python --version")
    if code == 0:
        print(f"   ✅ {output}")
    else:
        print(f"   ❌ Python não instalado")
    
    # Portas
    print("\n🔌 Portas em uso:")
    ports = [5432, 6379, 8000, 5000, 9090, 3000]
    for port in ports:
        if os.name != "nt":
            output, code = run_command(f"lsof -i :{port}")
        else:
            output, code = run_command(f"netstat -ano | findstr :{port}")
        
        if code == 0:
            print(f"   ❌ Porta {port} em uso")
        else:
            print(f"   ✅ Porta {port} livre")
    
    print("="*50)

if __name__ == "__main__":
    diagnose_system()
```

---

## 🚨 EMERGÊNCIAS

### **Reset Completo do Sistema**
```bash
# ⚠️ ÚLTIMO RECURSO - Perde dados!

# 1. Parar todos os containers:
docker-compose down

# 2. Remover volumes:
docker volume rm $(docker volume ls -q)

# 3. Limpar tudo:
docker system prune -a --volumes

# 4. Recomeçar do zero:
# Seguir [[00_SETUP_ZERO/INSTALACAO]]
```

### **Backup de Emergência**
```bash
# Backup rápido antes de reset:
docker exec vb-postgres pg_dump -U vb_admin valuebetting > backup.sql
docker cp vb-postgres:/var/lib/postgresql/data ./postgres_backup
docker cp vb-redis:/data ./redis_backup
```

---

## 📞 SUPORTE

### **Onde Procurar Ajuda**
1. **Documentação oficial:**
   - Docker: https://docs.docker.com
   - PostgreSQL: https://www.postgresql.org/docs
   - Python: https://docs.python.org

2. **Comunidades:**
   - Stack Overflow
   - Reddit r/docker, r/python
   - GitHub issues

3. **Logs do sistema:**
   - Docker: docker-compose logs
   - Aplicação: logs/ directory
   - Sistema: /var/log (Linux), Event Viewer (Windows)

---

## 📋 CHECKLIST DE RESOLUÇÃO

### **Antes de Pedir Ajuda:**
- [ ] Ler documentação relevante
- [ ] Verificar logs completos
- [ ] Correr diagnóstico sistemático
- [ ] Tentar soluções básicas
- [ ] Documentar passos tomados

### **Informações para Incluir:**
- Sistema operacional e versão
- Versões de software (Python, Docker, etc.)
- Mensagem de erro completa
- Passos para reproduzir
- Logs relevantes
- Soluções já tentadas

---

**Status:** Referência para problemas  
**Última atualização:** 2026-05-18  
**Cobertura:** Hardware, Docker, Python, Database, Rede  

---

#status/active #priority/critical #phase/setup-zero
