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

### **Script de Verificação (Python)**
```python
import platform
import psutil
import subprocess
import sys

def check_requirements():
    """Verifica automaticamente os requisitos"""
    
    print("🔍 Verificando requisitos do sistema...\n")
    
    # Sistema Operacional
    os_info = platform.uname()
    print(f"💻 Sistema: {os_info.system} {os_info.release}")
    
    # CPU
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    print(f"🔧 CPU: {cpu_count} cores @ {cpu_freq.current:.0f}MHz")
    
    # RAM
    memory = psutil.virtual_memory()
    ram_gb = memory.total / (1024**3)
    print(f"🧠 RAM: {ram_gb:.1f}GB total ({memory.available/(1024**3):.1f}GB livre)")
    
    # Disco
    disk = psutil.disk_usage('/')
    disk_gb = disk.free / (1024**3)
    print(f"💾 Disco: {disk_gb:.1f}GB livre")
    
    # Python
    python_version = sys.version_info
    print(f"🐍 Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Docker
    try:
        docker_version = subprocess.run(['docker', '--version'], 
                                      capture_output=True, text=True)
        print(f"🐳 Docker: {docker_version.stdout.strip()}")
    except:
        print("❌ Docker: Não encontrado")
    
    # Git
    try:
        git_version = subprocess.run(['git', '--version'], 
                                   capture_output=True, text=True)
        print(f"📦 Git: {git_version.stdout.strip()}")
    except:
        print("❌ Git: Não encontrado")
    
    print("\n" + "="*50)
    
    # Avaliação
    issues = []
    
    if cpu_count < 4:
        issues.append("CPU com menos de 4 cores")
    
    if ram_gb < 8:
        issues.append("RAM com menos de 8GB")
    
    if disk_gb < 50:
        issues.append("Disco com menos de 50GB livre")
    
    if python_version < (3, 11):
        issues.append("Python 3.11+ necessário")
    
    if issues:
        print("⚠️  Issues encontrados:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ Todos os requisitos mínimos cumpridos!")
        return True

if __name__ == "__main__":
    check_requirements()
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

## ⚠️ PROBLEMAS COMUNS E SOLUÇÕES

### **Docker não inicia**
```bash
# Windows: Habilitar WSL2
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux2 /all /norestart

# Linux: Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

### **Python PATH issues**
```bash
# Windows: Adicionar ao PATH manualmente
# C:\Users\Nome\AppData\Local\Programs\Python\Python311\
# C:\Users\Nome\AppData\Local\Programs\Python\Python311\Scripts\

# Verificar instalação
python --version
pip --version
```

### **Portas bloqueadas**
```bash
# Verificar portas em uso
netstat -tulpn | grep :5432
netstat -tulpn | grep :6379
netstat -tulpn | grep :8000

# Windows: Verificar no Task Manager
# Linux: Verificar com ss ou lsof
```

### **Memória insuficiente**
```bash
# Docker: Limitar memória
# Docker Desktop > Settings > Resources > Memory
# Ajustar para 4-8GB

# Fechar aplicações desnecessárias
# Monitorar com htop ou Task Manager
```

---

## 🚀 PRÓXIMOS PASSOS

Se todos os requisitos estiverem OK:

1. **Ir para:** [[00_SETUP_ZERO/INSTALACAO]]
2. **Seguir passo-a-passo completo**
3. **Testar com:** [[00_SETUP_ZERO/VALIDACAO]]

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
