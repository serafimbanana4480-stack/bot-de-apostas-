# Requisitos Mínimos - Setup Zero Euros

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  

---

## 🎯 OBJETIVO

Verificar se o teu PC e ambiente são adequados para implementação 100% gratuita do VBQ-UNIFIED.

---

## 💻 REQUISITOS DE HARDWARE

### **Mínimo Absoluto (Funciona mas lento)**
```
CPU: 4 cores (Intel i5/AMD Ryzen 5)
RAM: 8GB DDR4
Disco: 50GB SSD livre
Rede: 10 Mbps estável
Sistema: Windows 10/11, macOS, Linux
```

### **Recomendado (Experiência boa)**
```
CPU: 8+ cores (Intel i7/AMD Ryzen 7)
RAM: 16GB+ DDR4
Disco: 100GB+ SSD livre
Rede: 50+ Mbps estável
Sistema: Windows 11, macOS, Ubuntu 22.04+
```

### **Ideal (Performance máxima)**
```
CPU: 12+ cores com hyperthreading
RAM: 32GB+ DDR4
Disco: 200GB+ NVMe SSD
Rede: 100+ Mbps fibra
Sistema: Linux nativo ou WSL2
```

---

## 🛠️ REQUISITOS DE SOFTWARE

### **Essencial (Obrigatório)**
```bash
# Sistema Operacional
- Windows 10/11 ou macOS 10.15+ ou Linux (Ubuntu 20.04+)

# Python
- Python 3.11+ (recomendado 3.11.5)
- pip e gerenciador de pacotes

# Docker
- Docker Desktop (Windows/Mac) ou Docker Engine (Linux)
- Mínimo 4GB RAM para Docker

# Git
- Git 2.30+ para versionamento
```

### **Desenvolvimento (Recomendado)**
```bash
# IDE/Editor
- VS Code (recomendado) ou PyCharm Community
- Extensões: Python, Docker, Git

# Navegador
- Chrome/Edge/Firefox moderno
- Para debugging e acesso local

# Utilitários
- Terminal avançado (Windows Terminal/iterm2)
- Ferramentas de sistema
```

### **Opcional (Nice to have)**
```bash
# Banco de Dados GUI
- DBeaver ou pgAdmin para PostgreSQL
- Redis Desktop Manager

# Monitoramento
- htop (Linux) ou Task Manager (Windows)
- Grafana Desktop (opcional)

# Documentação
- Obsidian (já tens)
- Markdown editor
```

---

## 🌐 REQUISITOS DE REDE

### **Internet Mínima**
```
Velocidade下载: 10 Mbps
Velocidade上传: 5 Mbps
Latência: <100ms
Estabilidade: <5% downtime/dia
```

### **Internet Recomendada**
```
Velocidade下载: 50+ Mbps
Velocidade上传: 20+ Mbps
Latência: <50ms
Estabilidade: <1% downtime/dia
```

### **Acesso Necessário**
```bash
# APIs externas (gratuitas)
- nba.com (sem restrição)
- basketball-reference.com (scraping)
- the-odds-api.com (500 req/day)
- github.com (código e datasets)

# Portas locais (precisam estar livres)
- 5432 (PostgreSQL)
- 6379 (Redis)
- 8000 (FastAPI)
- 8501 (Streamlit)
- 5000 (MLflow)
```

---

## 📊 VERIFICAÇÃO AUTOMÁTICA

### **Script de Verificação Avançado (Python)**
```python
import platform
import psutil
import subprocess
import sys
import requests
import socket
from pathlib import Path

def check_requirements():
    """Verificação completa e detalhada dos requisitos"""
    
    print("="*70)
    print("🔍 VERIFICAÇÃO COMPLETA DE REQUISITOS - VBQ-UNIFIED ZERO EUROS")
    print("="*70)
    
    results = {
        'hardware': {},
        'software': {},
        'network': {},
        'overall': True
    }
    
    # ==================== HARDWARE ====================
    print("\n📦 HARDWARE")
    print("-" * 70)
    
    # Sistema Operacional
    os_info = platform.uname()
    os_system = os_info.system
    os_release = os_info.release
    print(f"💻 Sistema Operacional: {os_system} {os_release}")
    results['hardware']['os'] = os_system
    
    # CPU
    cpu_count = psutil.cpu_count(logical=False)
    cpu_count_logical = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    print(f"🔧 CPU Física: {cpu_count} cores")
    print(f"🔧 CPU Lógica: {cpu_count_logical} threads")
    print(f"🔧 CPU Frequência: {cpu_freq.current:.0f}MHz (max: {cpu_freq.max:.0f}MHz)")
    print(f"🔧 CPU Uso atual: {cpu_percent}%")
    
    results['hardware']['cpu_cores'] = cpu_count
    results['hardware']['cpu_freq'] = cpu_freq.current
    
    # RAM
    memory = psutil.virtual_memory()
    ram_gb = memory.total / (1024**3)
    ram_available_gb = memory.available / (1024**3)
    ram_percent = memory.percent
    
    print(f"🧠 RAM Total: {ram_gb:.1f}GB")
    print(f"🧠 RAM Disponível: {ram_available_gb:.1f}GB ({100-ram_percent:.1f}%)")
    print(f"🧠 RAM Uso: {ram_percent}%")
    
    results['hardware']['ram_gb'] = ram_gb
    results['hardware']['ram_available_gb'] = ram_available_gb
    
    # Disco
    disk = psutil.disk_usage('/')
    disk_total_gb = disk.total / (1024**3)
    disk_free_gb = disk.free / (1024**3)
    disk_used_percent = disk.percent
    
    print(f"💾 Disco Total: {disk_total_gb:.0f}GB")
    print(f"💾 Disco Livre: {disk_free_gb:.0f}GB ({100-disk_used_percent:.1f}%)")
    print(f"💾 Disco Uso: {disk_used_percent}%")
    
    results['hardware']['disk_free_gb'] = disk_free_gb
    
    # Classificação de hardware
    if cpu_count >= 12 and ram_gb >= 32 and disk_free_gb >= 200:
        hw_level = "IDEAL 🚀"
    elif cpu_count >= 8 and ram_gb >= 16 and disk_free_gb >= 100:
        hw_level = "RECOMENDADO ✅"
    elif cpu_count >= 4 and ram_gb >= 8 and disk_free_gb >= 50:
        hw_level = "MÍNIMO ⚠️"
    else:
        hw_level = "INSUFICIENTE ❌"
    
    print(f"\n📊 Classificação Hardware: {hw_level}")
    results['hardware']['level'] = hw_level
    
    # ==================== SOFTWARE ====================
    print("\n🛠️ SOFTWARE")
    print("-" * 70)
    
    # Python
    python_version = sys.version_info
    python_version_str = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
    print(f"🐍 Python: {python_version_str}")
    
    if python_version >= (3, 11):
        print(f"   ✅ Python 3.11+ OK")
        results['software']['python'] = True
    else:
        print(f"   ❌ Python 3.11+ necessário (atual: {python_version_str})")
        results['software']['python'] = False
        results['overall'] = False
    
    # pip
    try:
        pip_version = subprocess.run(['pip', '--version'], 
                                    capture_output=True, text=True)
        print(f"📦 pip: {pip_version.stdout.strip()}")
        results['software']['pip'] = True
    except:
        print("❌ pip: Não encontrado")
        results['software']['pip'] = False
        results['overall'] = False
    
    # Docker
    try:
        docker_version = subprocess.run(['docker', '--version'], 
                                      capture_output=True, text=True)
        print(f"🐳 Docker: {docker_version.stdout.strip()}")
        results['software']['docker'] = True
        
        # Testar Docker
        docker_test = subprocess.run(['docker', 'ps'], 
                                    capture_output=True, text=True)
        if docker_test.returncode == 0:
            print(f"   ✅ Docker funcionando")
        else:
            print(f"   ⚠️ Docker instalado mas não funcionando")
            results['software']['docker_running'] = False
            results['overall'] = False
    except:
        print("❌ Docker: Não encontrado")
        results['software']['docker'] = False
        results['overall'] = False
    
    # Git
    try:
        git_version = subprocess.run(['git', '--version'], 
                                   capture_output=True, text=True)
        print(f"📦 Git: {git_version.stdout.strip()}")
        results['software']['git'] = True
    except:
        print("❌ Git: Não encontrado")
        results['software']['git'] = False
        results['overall'] = False
    
    # VS Code (opcional)
    try:
        code_version = subprocess.run(['code', '--version'], 
                                    capture_output=True, text=True)
        print(f"💻 VS Code: Instalado")
        results['software']['vscode'] = True
    except:
        print("💻 VS Code: Não encontrado (opcional)")
        results['software']['vscode'] = False
    
    # ==================== REDE ====================
    print("\n🌐 REDE")
    print("-" * 70)
    
    # Testar portas locais
    ports_to_check = [5432, 6379, 8000, 8501, 5000]
    print("Verificando portas locais:")
    for port in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        if result == 0:
            print(f"   ❌ Porta {port}: Em uso")
            results['network'][f'port_{port}'] = False
        else:
            print(f"   ✅ Porta {port}: Livre")
            results['network'][f'port_{port}'] = True
        sock.close()
    
    # Testar conectividade externa
    print("\nTestando conectividade externa:")
    apis = {
        "NBA API": "https://stats.nba.com",
        "Basketball Reference": "https://basketball-reference.com",
        "The-Odds-API": "https://the-odds-api.com",
        "GitHub": "https://github.com"
    }
    
    for name, url in apis.items():
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {name}: OK")
                results['network'][name] = True
            else:
                print(f"   ⚠️ {name}: Status {response.status_code}")
                results['network'][name] = False
        except Exception as e:
            print(f"   ❌ {name}: Erro - {str(e)}")
            results['network'][name] = False
    
    # ==================== RESUMO ====================
    print("\n" + "="*70)
    print("📊 RESUMO DA VERIFICAÇÃO")
    print("="*70)
    
    issues = []
    
    # Hardware issues
    if cpu_count < 4:
        issues.append("CPU com menos de 4 cores (recomendado: 8+)")
    if ram_gb < 8:
        issues.append(f"RAM com menos de 8GB (atual: {ram_gb:.1f}GB)")
    if disk_free_gb < 50:
        issues.append(f"Disco com menos de 50GB livre (atual: {disk_free_gb:.0f}GB)")
    
    # Software issues
    if not results['software'].get('python', False):
        issues.append("Python 3.11+ não instalado")
    if not results['software'].get('docker', False):
        issues.append("Docker não instalado")
    if not results['software'].get('git', False):
        issues.append("Git não instalado")
    
    # Network issues
    blocked_ports = [k for k, v in results['network'].items() if 'port_' in k and not v]
    if blocked_ports:
        issues.append(f"Portas bloqueadas: {', '.join([p.replace('port_', '') for p in blocked_ports])}")
    
    failed_apis = [k for k, v in results['network'].items() if 'port_' not in k and not v]
    if failed_apis:
        issues.append(f"APIs inacessíveis: {', '.join(failed_apis)}")
    
    if issues:
        print("\n⚠️ ISSUES ENCONTRADOS:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\n❌ VERIFICAÇÃO FALHOU")
        print("\nRecomendações:")
        print("- Resolver issues acima antes de prosseguir")
        print("- Verificar secção 'Problemas Comuns' abaixo")
        print("- Considerar upgrade de hardware se necessário")
        return False
    else:
        print("\n✅ TODOS OS REQUISITOS MÍNIMOS CUMPRIDOS!")
        print(f"\n🎯 Hardware: {hw_level}")
        print("🚀 Pode prosseguir para instalação!")
        return True

if __name__ == "__main__":
    check_requirements()
```

---

## 📋 MATRIZ DE COMPATIBILIDADE POR SISTEMA

### **Windows 10/11**
```
Hardware:
├── Mínimo: Intel i5/AMD Ryzen 5, 8GB RAM, 50GB SSD
├── Recomendado: Intel i7/AMD Ryzen 7, 16GB RAM, 100GB SSD
└── Ideal: Intel i9/AMD Ryzen 9, 32GB RAM, 200GB NVMe

Software:
├── Python 3.11+ (via python.org ou Chocolatey)
├── Docker Desktop for Windows (requer WSL2)
├── Git (via Git for Windows ou Chocolatey)
├── VS Code (recomendado)
└── Windows Terminal (recomendado)

Limitações:
├── WSL2 overhead (~10-15% performance)
├── Docker Desktop consome ~2GB RAM
├── Path length limit (260 caracteres)
└── Firewall pode bloquear portas

Troubleshooting Comum:
├── Habilitar WSL2: `dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux2 /all /norestart`
├── Docker não inicia: Verificar virtualização no BIOS
├── Python PATH: Adicionar manualmente às variáveis de ambiente
└── Portas bloqueadas: Verificar Windows Firewall
```

### **macOS 10.15+ (Intel e Apple Silicon)**
```
Hardware:
├── Mínimo: Intel i5/M1, 8GB RAM, 50GB SSD
├── Recomendado: Intel i7/M2, 16GB RAM, 100GB SSD
└── Ideal: Intel i9/M3, 32GB RAM, 200GB NVMe

Software:
├── Python 3.11+ (via Homebrew ou python.org)
├── Docker Desktop for Mac
├── Git (via Xcode Command Line Tools ou Homebrew)
├── VS Code (recomendado)
└── iTerm2 (recomendado)

Limitações:
├── Apple Silicon: Algumas libs podem não ter wheel nativo
├── Docker Desktop consome ~2GB RAM
├── Filesystem case-insensitive (pode causar issues)
└── SIP (System Integrity Protection) pode restringir

Troubleshooting Comum:
├── Docker não inicia: Verificar permissões do sistema
├── Apple Silicon: Use `arch -arm64` para comandos nativos
├── Python installs: Use `pyenv` para múltiplas versões
└── Portas bloqueadas: Verificar firewall do macOS
```

### **Linux (Ubuntu 20.04+/Debian 11+)**
```
Hardware:
├── Mínimo: 4 cores, 8GB RAM, 50GB SSD
├── Recomendado: 8+ cores, 16GB RAM, 100GB SSD
└── Ideal: 12+ cores, 32GB RAM, 200GB NVMe

Software:
├── Python 3.11+ (via apt ou pyenv)
├── Docker Engine (via apt)
├── Git (via apt)
├── VS Code (recomendado)
└── tmux/terminator (recomendado)

Limitações:
├── Menor overhead que Windows/macOS
├── Requer conhecimento de terminal
├── Docker nativo (melhor performance)
└── Dependências de sistema podem variar

Troubleshooting Comum:
├── Docker sem permissão: `sudo usermod -aG docker $USER`
├── Python version: Use `deadsnakes PPA` para versões recentes
├── Portas bloqueadas: `sudo ufw allow 5432/tcp`
└── Memory limits: Ajustar `/etc/security/limits.conf`
```

### **Comparação de Sistemas**
```
┌─────────────────┬──────────┬──────────┬──────────┐
│ Característica  │ Windows  │ macOS    │ Linux    │
├─────────────────┼──────────┼──────────┼──────────┤
│ Performance     │ 85%      │ 90%      │ 100%     │
│ Facilidade      │ 95%      │ 90%      │ 70%      │
│ Compatibilidade │ 95%      │ 90%      │ 85%      │
│ Docker          │ 85%      │ 90%      │ 100%     │
│ Recursos        │ Alto     │ Médio    │ Baixo    │
│ Recomendado     │ ✅       │ ✅       │ ✅✅     │
└─────────────────┴──────────┴──────────┴──────────┘

**Recomendação:** Linux > macOS > Windows (para performance)
**Facilidade:** Windows > macOS > Linux (para iniciantes)
```

---

## 🔧 SETUP DE SOFTWARE

### **1. Instalar Python 3.11+**

#### **Windows**
```powershell
# Usar Chocolatey (recomendado)
choco install python

# Ou download manual
# https://www.python.org/downloads/
# Adicionar ao PATH durante instalação
```

#### **macOS**
```bash
# Usar Homebrew
brew install python@3.11

# Ou download manual
# https://www.python.org/downloads/macos/
```

#### **Linux (Ubuntu/Debian)**
```bash
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv
```

### **2. Instalar Docker Desktop**

#### **Windows**
```powershell
# Download via Chocolatey
choco install docker-desktop

# Ou download manual
# https://www.docker.com/products/docker-desktop/
# Requer Windows 10/11 Pro ou Home com WSL2
```

#### **macOS**
```bash
# Download manual
# https://www.docker.com/products/docker-desktop/
# Requer macOS 10.15+ com chip Intel ou Apple Silicon
```

#### **Linux**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
# Fazer logout e login novamente
```

### **3. Instalar Git**

#### **Windows**
```powershell
# Via Chocolatey
choco install git

# Ou download manual
# https://git-scm.com/download/win
```

#### **macOS**
```bash
# Via Homebrew
brew install git
```

#### **Linux**
```bash
# Ubuntu/Debian
sudo apt install git
```

---

## 🧪 TESTE DE REDE

### **Verificar Conectividade**
```python
import requests
import time

def test_connectivity():
    """Testa acesso às APIs necessárias"""
    
    apis = {
        "NBA API": "https://stats.nba.com",
        "Basketball Reference": "https://basketball-reference.com",
        "The-Odds-API": "https://the-odds-api.com",
        "GitHub": "https://github.com"
    }
    
    print("🌐 Testando conectividade...\n")
    
    for name, url in apis.items():
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: OK ({response.status_code})")
            else:
                print(f"⚠️  {name}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Erro - {str(e)}")
        time.sleep(1)  # Rate limiting
    
    print("\n" + "="*50)

if __name__ == "__main__":
    test_connectivity()
```

---

## 📋 CHECKLIST FINAL

### **Hardware:**
- [ ] CPU: 4+ cores
- [ ] RAM: 8GB+ 
- [ ] Disco: 50GB+ SSD livre
- [ ] Rede: 10+ Mbps estável

### **Software:**
- [ ] Python 3.11+ instalado
- [ ] Docker Desktop funcionando
- [ ] Git configurado
- [ ] VS Code (ou outro IDE)

### **Rede:**
- [ ] Internet estável
- [ ] Acesso APIs externas
- [ ] Portas locais livres
- [ ] Sem firewall bloqueando

### **Ambiente:**
- [ ] Tempo dedicado: 2 semanas
- [ ] Espaço físico adequado
- [ ] Backup externo dos dados
- [ ] Plano de energia (PC ligado 24/7)

---

## ⚠️ TROUBLESHOOTING AVANÇADO POR CATEGORIA

### **🔧 HARDWARE ISSUES**

#### **CPU Insuficiente**
```
Sintomas:
- Sistema lento, alto CPU usage
- Treino de modelo muito lento
- Docker containers travando

Soluções:
1. Fechar aplicações desnecessárias
2. Limitar número de containers Docker
3. Usar modelos mais leves (menos features)
4. Considerar upgrade de CPU

Diagnóstico:
- Windows: Task Manager > Performance
- macOS: Activity Monitor > CPU
- Linux: htop ou top
```

#### **RAM Insuficiente**
```
Sintomas:
- Sistema swapping constantemente
- Docker containers crashing (OOMKilled)
- Python MemoryError

Soluções:
1. Fechar browser e aplicações pesadas
2. Limitar Docker memory (Docker Desktop > Settings > Resources)
3. Usar batch processing em vez de carregar tudo em memória
4. Aumentar swap no sistema

Diagnóstico:
- Windows: Task Manager > Memory
- macOS: Activity Monitor > Memory
- Linux: free -h, vmstat
```

#### **Disco Cheio**
```
Sintomas:
- Erros ao escrever logs/dados
- Docker containers não iniciam
- Sistema lento

Soluções:
1. Limpar Docker images: docker system prune -a
2. Limpar cache Python: pip cache purge
3. Remover arquivos temporários
4. Mover dados para disco externo

Diagnóstico:
- Windows: Disk Management
- macOS: Disk Utility
- Linux: df -h, du -sh
```

---

### **🛠️ SOFTWARE ISSUES**

#### **Python Version Mismatch**
```
Sintomas:
- ImportError: module not found
- SyntaxError (features do Python 3.11+)
- pip install falha

Soluções:
1. Verificar versão: python --version
2. Instalar Python 3.11+ se necessário
3. Usar pyenv para múltiplas versões (Linux/macOS)
4. Atualizar pip: python -m pip install --upgrade pip

Windows:
- Desinstalar versões antigas
- Instalar via python.org (marcar "Add to PATH")

Linux:
sudo apt update
sudo apt install python3.11 python3.11-venv

macOS:
brew install python@3.11
```

#### **Docker Não Funciona**
```
Sintomas:
- "docker: command not found"
- "Cannot connect to Docker daemon"
- Containers não iniciam

Windows:
1. Habilitar WSL2:
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux2 /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
2. Reiniciar PC
3. Atualizar Docker Desktop
4. Verificar virtualização no BIOS

macOS:
1. Verificar permissões do sistema
2. Reinstalar Docker Desktop
3. Verificar se SIP está bloqueando

Linux:
1. Adicionar usuário ao grupo docker:
   sudo usermod -aG docker $USER
   newgrp docker
2. Iniciar Docker:
   sudo systemctl start docker
   sudo systemctl enable docker
3. Verificar logs:
   sudo journalctl -u docker
```

#### **Git Configuration Issues**
```
Sintomas:
- "fatal: not a git repository"
- "Permission denied"
- SSH keys não funcionam

Soluções:
1. Inicializar repo: git init
2. Configurar user:
   git config --global user.name "Seu Nome"
   git config --global user.email "seu@email.com"
3. SSH keys:
   ssh-keygen -t ed25519 -C "seu@email.com"
   Adicionar chave ao GitHub
4. Verificar permissões: chmod 600 ~/.ssh/id_ed25519
```

---

### **🌐 REDE ISSUES**

#### **Portas Bloqueadas**
```
Sintomas:
- "Address already in use"
- Containers não iniciam
- API não acessível

Diagnóstico:
Windows:
netstat -ano | findstr :5432
netstat -ano | findstr :6379
netstat -ano | findstr :8000

Linux/macOS:
lsof -i :5432
lsof -i :6379
lsof -i :8000

Soluções:
1. Matar processo usando a porta:
   Windows: taskkill /PID <PID> /F
   Linux/macOS: kill -9 <PID>
2. Mudar porta no docker-compose.yml
3. Configurar firewall para permitir
```

#### **Conectividade Externa Bloqueada**
```
Sintomas:
- Timeout ao acessar APIs
- "Connection refused"
- DNS falha

Diagnóstico:
ping stats.nba.com
ping basketball-reference.com
ping the-odds-api.com

Soluções:
1. Verificar firewall/antivírus
2. Testar com VPN (se geobloqueio)
3. Usar DNS alternativo (8.8.8.8, 1.1.1.1)
4. Verificar proxy corporativo
```

#### **Rate Limiting**
```
Sintomas:
- 429 Too Many Requests
- API bloqueada temporariamente
- Dados incompletos

Soluções:
1. Implementar exponential backoff
2. Usar cache local
3. Respeitar rate limits documentados
4. Usar múltiplas API keys (se disponível)
```

---

### **🐳 DOCKER ESPECÍFICO**

#### **Docker Containers Crashing**
```
Sintomas:
- Container para imediatamente
- Exit code 137 (OOMKilled)
- Exit code 1 (error)

Diagnóstico:
docker logs <container_name>
docker inspect <container_name>

Soluções:
1. Aumentar memória alocada (Docker Desktop > Settings)
2. Verificar logs do container
3. Verificar variáveis de ambiente
4. Verificar portas em conflito
```

#### **Docker Build Falha**
```
Sintomas:
- "failed to compute cache key"
- "no matching manifest"
- Build timeout

Soluções:
1. Limpar cache: docker builder prune
2. Usar --no-cache flag
3. Verificar Dockerfile syntax
4. Verificar internet durante build
```

#### **Docker Volume Issues**
```
Sintomas:
- Dados não persistem
- Permissões negadas
- Volume não montado

Soluções:
1. Verificar permissões do volume
2. Usar volumes nomeados em vez de bind mounts
3. Verificar docker-compose.yml volumes section
4. Reiniciar Docker
```

---

### **🐍 PYTHON ESPECÍFICO**

#### **Virtual Environment Issues**
```
Sintomas:
- "No module named X"
- Scripts usam Python global
- venv não ativa

Soluções:
1. Criar venv corretamente:
   python -m venv venv
2. Ativar:
   Windows: venv\Scripts\activate
   Linux/macOS: source venv/bin/activate
3. Verificar ativação: which python
4. Reinstalar dependências: pip install -r requirements.txt
```

#### **Package Installation Falha**
```
Sintomas:
- "Could not find a version"
- Build errors
- SSL errors

Soluções:
1. Atualizar pip: python -m pip install --upgrade pip
2. Usar wheel: pip install --use-wheel
3. Instalar build tools:
   Windows: Visual C++ Build Tools
   Linux: sudo apt install build-essential
4. Usar mirror alternativo:
   pip install -i https://pypi.org/simple/
```

---

### **🔍 DIAGNÓSTICO SISTEMÁTICO**

### **Script de Diagnóstico Completo**
```python
import platform
import psutil
import subprocess
import socket
import requests

def diagnose_system():
    """Diagnóstico sistemático de problemas"""
    
    print("="*70)
    print("🔍 DIAGNÓSTICO SISTEMÁTICO DO SISTEMA")
    print("="*70)
    
    issues = []
    
    # 1. Hardware
    print("\n📦 HARDWARE")
    cpu_count = psutil.cpu_count()
    ram_gb = psutil.virtual_memory().total / (1024**3)
    disk_gb = psutil.disk_usage('/').free / (1024**3)
    
    if cpu_count < 4:
        issues.append(f"CPU insuficiente: {cpu_count} cores (mínimo: 4)")
    if ram_gb < 8:
        issues.append(f"RAM insuficiente: {ram_gb:.1f}GB (mínimo: 8GB)")
    if disk_gb < 50:
        issues.append(f"Disco insuficiente: {disk_gb:.0f}GB livre (mínimo: 50GB)")
    
    # 2. Software
    print("\n🛠️ SOFTWARE")
    try:
        py_ver = sys.version_info
        if py_ver < (3, 11):
            issues.append(f"Python desatualizado: {py_ver.major}.{py_ver.minor} (mínimo: 3.11)")
    except:
        issues.append("Python não encontrado")
    
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
    except:
        issues.append("Docker não instalado ou não funciona")
    
    try:
        subprocess.run(['git', '--version'], check=True, capture_output=True)
    except:
        issues.append("Git não instalado")
    
    # 3. Rede
    print("\n🌐 REDE")
    ports = [5432, 6379, 8000, 8501, 5000]
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if sock.connect_ex(('localhost', port)) == 0:
            issues.append(f"Porta {port} já em uso")
        sock.close()
    
    # 4. APIs externas
    print("\n🔌 APIs EXTERNAS")
    apis = ["https://stats.nba.com", "https://basketball-reference.com"]
    for api in apis:
        try:
            requests.get(api, timeout=5)
        except:
            issues.append(f"API inacessível: {api}")
    
    # 5. Resumo
    print("\n" + "="*70)
    if issues:
        print("⚠️ PROBLEMAS ENCONTRADOS:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("✅ NENHUM PROBLEMA ENCONTRADO")
    print("="*70)
    
    return len(issues) == 0

if __name__ == "__main__":
    diagnose_system()
```

---

## 🚀 PRÓXIMOS PASSOS

Se todos os requisitos estiverem OK:

1. **Ir para:** [[00_SETUP_ZERO/INSTALACAO]]
2. **Seguir passo-a-passo completo**
3. **Testar com:** [[00_SETUP_ZERO/VALIDACAO]]
4. **Verificar custos:** [[00_SETUP_ZERO/CUSTOS]]

Se algum requisito falhar:

1. **Resolver issue** (ver secção problemas comuns)
2. **Considerar upgrade** de hardware se necessário
3. **Avançar com limitações** (performance reduzida)

---

**Status:** Verificação necessária  
**Tempo estimado:** 30-60 minutos  
**Resultado:** Confirmação se PC está apto  

---

#status/active #priority/critical #phase/setup-zero
