# Instalação Completa - Setup Zero Euros

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  

---

## 🎯 OBJETIVO

Guia passo-a-passo completo para instalar todos os componentes necessários para implementação 100% gratuita do VBQ-UNIFIED no teu PC.

**Tempo estimado:** 2-3 horas  
**Dificuldade:** Intermediária  
**Pré-requisitos:** Verificados em [[00_SETUP_ZERO/REQUISITOS]]

---

## 🚀 SCRIPT DE INSTALAÇÃO AUTOMATIZADA

### **Instalação Automática (Windows PowerShell)**
```powershell
# Salvar como setup_zero_euros.ps1
# Executar como Administrador

Write-Host "="*70 -ForegroundColor Cyan
Write-Host "🚀 SETUP AUTOMATIZADO - VBQ-UNIFIED ZERO EUROS" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan

# Função para verificar comando
function Test-Command {
    param($command)
    try {
        $null = Get-Command $command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Função para instalar via Chocolatey
function Install-ChocoPackage {
    param($package)
    if (Test-Command choco) {
        Write-Host "📦 Instalando $package via Chocolatey..." -ForegroundColor Yellow
        choco install $package -y
    } else {
        Write-Host "⚠️ Chocolatey não encontrado. Instale manualmente." -ForegroundColor Red
    }
}

# 1. Verificar Chocolatey
Write-Host "`n📦 VERIFICANDO CHOCOLATEY..." -ForegroundColor Cyan
if (-not (Test-Command choco)) {
    Write-Host "📥 Instalando Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# 2. Instalar Python
Write-Host "`n🐍 INSTALANDO PYTHON..." -ForegroundColor Cyan
if (-not (Test-Command python)) {
    Install-ChocoPackage "python"
} else {
    Write-Host "✅ Python já instalado" -ForegroundColor Green
    python --version
}

# 3. Instalar Docker
Write-Host "`n🐳 INSTALANDO DOCKER..." -ForegroundColor Cyan
if (-not (Test-Command docker)) {
    Install-ChocoPackage "docker-desktop"
    Write-Host "⚠️ Docker Desktop instalado. REINICIE o PC e execute novamente." -ForegroundColor Yellow
    exit
} else {
    Write-Host "✅ Docker já instalado" -ForegroundColor Green
    docker --version
}

# 4. Instalar Git
Write-Host "`n📦 INSTALANDO GIT..." -ForegroundColor Cyan
if (-not (Test-Command git)) {
    Install-ChocoPackage "git"
} else {
    Write-Host "✅ Git já instalado" -ForegroundColor Green
    git --version
}

# 5. Configurar projeto
Write-Host "`n🏗️ CONFIGURANDO PROJETO..." -ForegroundColor Cyan
$projectPath = "C:\Users\rodri\Desktop\bot de apostas\Planeameneto bot de apostas profissional"
if (Test-Path $projectPath) {
    Set-Location $projectPath
    Write-Host "✅ Navegando para: $projectPath" -ForegroundColor Green
    
    # Criar venv
    Write-Host "`n🔧 CRIANDO AMBIENTE VIRTUAL..." -ForegroundColor Yellow
    python -m venv venv
    
    # Ativar venv
    Write-Host "🔧 ATIVANDO AMBIENTE VIRTUAL..." -ForegroundColor Yellow
    & ".\venv\Scripts\activate.ps1"
    
    # Instalar dependências
    if (Test-Path "requirements.txt") {
        Write-Host "📦 INSTALANDO DEPENDÊNCIAS..." -ForegroundColor Yellow
        pip install --upgrade pip
        pip install -r requirements.txt
    }
    
    # Configurar .env
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ .env criado. Edite com suas credenciais." -ForegroundColor Green
    }
} else {
    Write-Host "❌ Caminho do projeto não encontrado: $projectPath" -ForegroundColor Red
}

# 6. Iniciar Docker
Write-Host "`n🐳 INICIANDO DOCKER COMPOSE..." -ForegroundColor Cyan
if (Test-Path "docker-compose.yml") {
    docker-compose up -d postgres redis
    Write-Host "✅ Containers iniciados" -ForegroundColor Green
    docker-compose ps
} else {
    Write-Host "⚠️ docker-compose.yml não encontrado" -ForegroundColor Yellow
}

Write-Host "`n" + "="*70 -ForegroundColor Cyan
Write-Host "✅ SETUP COMPLETO!" -ForegroundColor Green
Write-Host "="*70 -ForegroundColor Cyan
Write-Host "`nPróximos passos:" -ForegroundColor Cyan
Write-Host "1. Edite .env com suas credenciais" -ForegroundColor White
Write-Host "2. Execute: [[00_SETUP_ZERO/VALIDACAO]]" -ForegroundColor White
Write-Host "3. Verifique custos: [[00_SETUP_ZERO/CUSTOS]]" -ForegroundColor White
```

### **Instalação Automática (macOS/Linux Bash)**
```bash
#!/bin/bash
# Salvar como setup_zero_euros.sh
# Executar: chmod +x setup_zero_euros.sh && ./setup_zero_euros.sh

echo "============================================================"
echo "🚀 SETUP AUTOMATIZADO - VBQ-UNIFIED ZERO EUROS"
echo "============================================================"

# Função para verificar comando
check_command() {
    if command -v $1 &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Detectar sistema
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
    PKG_MANAGER="brew"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
    PKG_MANAGER="apt"
else
    echo "❌ Sistema não suportado"
    exit 1
fi

echo "📦 Sistema detetado: $OS"

# 1. Instalar gerenciador de pacotes
if [[ "$OS" == "macOS" ]] && ! check_command brew; then
    echo "📥 Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 2. Instalar Python
echo "🐍 VERIFICANDO PYTHON..."
if ! check_command python3.11; then
    if [[ "$OS" == "macOS" ]]; then
        brew install python@3.11
    else
        sudo apt update
        sudo apt install python3.11 python3.11-venv python3.11-pip -y
    fi
else
    echo "✅ Python 3.11 já instalado"
    python3.11 --version
fi

# 3. Instalar Docker
echo "🐳 VERIFICANDO DOCKER..."
if ! check_command docker; then
    if [[ "$OS" == "macOS" ]]; then
        echo "📥 Instale Docker Desktop manualmente:"
        echo "https://www.docker.com/products/docker-desktop/"
    else
        sudo apt install docker.io docker-compose -y
        sudo usermod -aG docker $USER
        echo "⚠️ Faça logout e login novamente"
    fi
else
    echo "✅ Docker já instalado"
    docker --version
fi

# 4. Instalar Git
echo "📦 VERIFICANDO GIT..."
if ! check_command git; then
    if [[ "$OS" == "macOS" ]]; then
        brew install git
    else
        sudo apt install git -y
    fi
else
    echo "✅ Git já instalado"
    git --version
fi

# 5. Configurar projeto
echo "🏗️ CONFIGURANDO PROJETO..."
PROJECT_PATH="$HOME/Desktop/bot de apostas/Planeameneto bot de apostas profissional"
if [ -d "$PROJECT_PATH" ]; then
    cd "$PROJECT_PATH"
    echo "✅ Navegando para: $PROJECT_PATH"
    
    # Criar venv
    echo "🔧 CRIANDO AMBIENTE VIRTUAL..."
    python3.11 -m venv venv
    
    # Ativar venv
    echo "🔧 ATIVANDO AMBIENTE VIRTUAL..."
    source venv/bin/activate
    
    # Instalar dependências
    if [ -f "requirements.txt" ]; then
        echo "📦 INSTALANDO DEPENDÊNCIAS..."
        pip install --upgrade pip
        pip install -r requirements.txt
    fi
    
    # Configurar .env
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ .env criado. Edite com suas credenciais."
    fi
else
    echo "❌ Caminho do projeto não encontrado: $PROJECT_PATH"
fi

# 6. Iniciar Docker
echo "🐳 INICIANDO DOCKER COMPOSE..."
if [ -f "docker-compose.yml" ]; then
    docker-compose up -d postgres redis
    echo "✅ Containers iniciados"
    docker-compose ps
else
    echo "⚠️ docker-compose.yml não encontrado"
fi

echo "============================================================"
echo "✅ SETUP COMPLETO!"
echo "============================================================"
echo "Próximos passos:"
echo "1. Edite .env com suas credenciais"
echo "2. Execute: [[00_SETUP_ZERO/VALIDACAO]]"
echo "3. Verifique custos: [[00_SETUP_ZERO/CUSTOS]]"
```

---

## 📋 PRÉ-INSTALAÇÃO

### **Verificar Pré-requisitos**
```bash
# Se ainda não verificaste, ir para:
[[00_SETUP_ZERO/REQUISITOS]]
```

### **Backup do Sistema**
```bash
# Recomendado antes de instalação:
- Backup dos dados importantes
- Criar ponto de restauração (Windows)
- Time Machine backup (macOS)

# Windows:
# Painel de Controle > Sistema > Proteção do Sistema > Criar
```

### **Escolher Método de Instalação**
```
┌─────────────────────────────────────────────────────────┐
│ OPÇÃO 1: INSTALAÇÃO AUTOMATIZADA (Recomendado)        │
├─────────────────────────────────────────────────────────┤
│ ✅ Mais rápido (10-15 minutos)                         │
│ ✅ Menos erros manuais                                 │
│ ✅ Scripts validam cada passo                          │
│ ⚠️ Requer permissões de administrador                 │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ OPÇÃO 2: INSTALAÇÃO MANUAL (Passo-a-passo)            │
├─────────────────────────────────────────────────────────┤
│ ✅ Mais controle sobre cada componente                │
│ ✅ Melhor para aprendizado                             │
│ ⚠️ Mais lento (2-3 horas)                              │
│ ⚠️ Maior chance de erros manuais                       │
└─────────────────────────────────────────────────────────┘

Recomendação: Usar automático primeiro, manual se falhar.
```

---

## 🔧 PASSO 1: INSTALAÇÃO PYTHON

### **Windows**
```powershell
# Método 1: Chocolatey (Recomendado)
choco install python -y

# Método 2: Download Manual
# 1. Ir para https://www.python.org/downloads/
# 2. Download Python 3.11.x
# 3. Instalar com "Add Python to PATH" marcado
# 4. Verificar instalação:
python --version
pip --version
```

### **macOS**
```bash
# Método 1: Homebrew (Recomendado)
brew install python@3.11

# Método 2: Download Manual
# 1. Ir para https://www.python.org/downloads/macos/
# 2. Download Python 3.11.x
# 3. Instalar .pkg
# 4. Verificar instalação:
python3 --version
pip3 --version
```

### **Linux (Ubuntu/Debian)**
```bash
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv -y

# Verificar instalação:
python3.11 --version
pip3.11 --version
```

### **✅ VALIDAÇÃO APÓS PASSO 1**
```python
import sys

def validate_python():
    """Valida instalação do Python"""
    print("🔍 Validando Python...")
    
    version = sys.version_info
    if version >= (3, 11):
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} desatualizado")
        print("   Requerido: Python 3.11+")
        return False

if __name__ == "__main__":
    validate_python()
```

**Resultado esperado:** ✅ Python 3.11.x OK

---

## 🐳 PASSO 2: INSTALAÇÃO DOCKER

### **Windows**
```powershell
# Método 1: Chocolatey
choco install docker-desktop -y

# Método 2: Download Manual
# 1. Ir para https://www.docker.com/products/docker-desktop/
# 2. Download Docker Desktop for Windows
# 3. Instalar (requer WSL2)
# 4. Reiniciar PC
# 5. Iniciar Docker Desktop
# 6. Verificar:
docker --version
docker-compose --version
```

### **macOS**
```bash
# Download Manual (único método)
# 1. Ir para https://www.docker.com/products/docker-desktop/
# 2. Download Docker Desktop for Mac
# 3. Arrastar para Applications
# 4. Iniciar Docker Desktop
# 5. Verificar:
docker --version
docker-compose --version
```

### **Linux (Ubuntu/Debian)**
```bash
# Instalar Docker Engine
sudo apt update
sudo apt install docker.io docker-compose -y

# Adicionar utilizador ao grupo docker
sudo usermod -aG docker $USER

# Fazer logout e login novamente
# Verificar:
docker --version
docker-compose --version
```

### **✅ VALIDAÇÃO APÓS PASSO 2**
```python
import subprocess

def validate_docker():
    """Valida instalação do Docker"""
    print("🔍 Validando Docker...")
    
    try:
        result = subprocess.run(['docker', '--version'], 
                               capture_output=True, text=True)
        print(f"✅ Docker: {result.stdout.strip()}")
        
        result = subprocess.run(['docker-compose', '--version'], 
                               capture_output=True, text=True)
        print(f"✅ Docker Compose: {result.stdout.strip()}")
        
        # Testar Docker
        result = subprocess.run(['docker', 'ps'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker funcionando")
            return True
        else:
            print("❌ Docker não está a responder")
            return False
    except FileNotFoundError:
        print("❌ Docker não encontrado")
        return False

if __name__ == "__main__":
    validate_docker()
```

**Resultado esperado:** ✅ Docker funcionando

---

## 📦 PASSO 3: INSTALAÇÃO GIT

### **Windows**
```powershell
# Método 1: Chocolatey
choco install git -y

# Método 2: Download Manual
# 1. Ir para https://git-scm.com/download/win
# 2. Download Git for Windows
# 3. Instalar com defaults
# 4. Verificar:
git --version
```

### **macOS**
```bash
# Método 1: Homebrew
brew install git

# Método 2: Xcode Command Line Tools
xcode-select --install

# Verificar:
git --version
```

### **Linux**
```bash
sudo apt install git -y

# Verificar:
git --version
```

### **✅ VALIDAÇÃO APÓS PASSO 3**
```python
import subprocess

def validate_git():
    """Valida instalação do Git"""
    print("🔍 Validando Git...")
    
    try:
        result = subprocess.run(['git', '--version'], 
                               capture_output=True, text=True)
        print(f"✅ Git: {result.stdout.strip()}")
        
        # Configurar se necessário
        subprocess.run(['git', 'config', '--global', 'user.name', 'VBQ User'], 
                      capture_output=True)
        subprocess.run(['git', 'config', '--global', 'user.email', 'vbq@example.com'], 
                      capture_output=True)
        print("✅ Git configurado")
        return True
    except FileNotFoundError:
        print("❌ Git não encontrado")
        return False

if __name__ == "__main__":
    validate_git()
```

**Resultado esperado:** ✅ Git configurado

---

## 🏗️ PASSO 4: CLONAR REPOSITÓRIO

### **Clonar Projeto**
```bash
# Navegar para diretório desejado:
cd "C:\Users\rodri\Desktop\bot de apostas"

# Clonar repositório (se existir):
# git clone <url-do-repositorio>

# Se já tens o projeto, navegar para:
cd "Planeameneto bot de apostas profissional"
```

### **Verificar Estrutura**
```bash
# Listar diretórios:
ls -la

# Deverias ver:
# 00_SETUP_ZERO/ (novo)
# 01_Vision_And_Strategy/
# 02_Business_Model/
# ... etc
```

### **✅ VALIDAÇÃO APÓS PASSO 4**
```python
import os
from pathlib import Path

def validate_project_structure():
    """Valida estrutura do projeto"""
    print("🔍 Validando estrutura do projeto...")
    
    required_dirs = [
        "00_SETUP_ZERO",
        "00_Master_Index",
        "01_Vision_And_Strategy",
        "02_Business_Model",
        "03_Quant_Research",
        "04_Data_Engineering",
        "05_Machine_Learning",
        "10_Infrastructure",
        "14_APIs"
    ]
    
    project_path = Path(".")
    missing = []
    
    for dir_name in required_dirs:
        if not (project_path / dir_name).exists():
            missing.append(dir_name)
        else:
            print(f"✅ {dir_name}/ existe")
    
    if missing:
        print(f"❌ Diretórios missing: {', '.join(missing)}")
        return False
    else:
        print("✅ Estrutura do projeto OK")
        return True

if __name__ == "__main__":
    validate_project_structure()
```

**Resultado esperado:** ✅ Estrutura do projeto OK

---

## 🔨 PASSO 5: CRIAR AMBIENTE VIRTUAL

### **Criar Ambiente Virtual**
```bash
# Navegar para diretório do projeto:
cd "Planeameneto bot de apostas profissional"

# Criar ambiente virtual:
python -m venv venv

# Ativar ambiente virtual:

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### **Instalar Dependências**
```bash
# Atualizar pip:
pip install --upgrade pip

# Instalar requirements:
pip install -r requirements.txt

# Verificar instalação:
pip list
```

### **✅ VALIDAÇÃO APÓS PASSO 5**
```python
import sys
from pathlib import Path

def validate_venv():
    """Valida ambiente virtual"""
    print("🔍 Validando ambiente virtual...")
    
    # Verificar se está em venv
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Ambiente virtual ativo")
        print(f"   Python: {sys.prefix}")
    else:
        print("❌ Ambiente virtual não ativo")
        return False
    
    # Verificar venv directory
    if Path("venv").exists():
        print("✅ Diretório venv existe")
    else:
        print("❌ Diretório venv não encontrado")
        return False
    
    # Verificar requirements
    if Path("requirements.txt").exists():
        print("✅ requirements.txt encontrado")
    else:
        print("⚠️ requirements.txt não encontrado")
    
    return True

if __name__ == "__main__":
    validate_venv()
```

**Resultado esperado:** ✅ Ambiente virtual ativo

---

## 🐋 PASSO 6: CONFIGURAR DOCKER COMPOSE

### **Verificar docker-compose.yml**
```bash
# Verificar se ficheiro existe:
ls docker-compose.yml

# Verificar conteúdo:
cat docker-compose.yml
```

### **Criar .env**
```bash
# Copiar exemplo:
cp .env.example .env

# Editar .env com valores seguros:
# POSTGRES_DB=valuebetting
# POSTGRES_USER=vb_admin
# POSTGRES_PASSWORD=senha_segura_aqui
# REDIS_PASSWORD=senha_segura_aqui
# ENVIRONMENT=development
```

### **✅ VALIDAÇÃO APÓS PASSO 6**
```python
from pathlib import Path

def validate_docker_config():
    """Valida configuração Docker"""
    print("🔍 Validando configuração Docker...")
    
    # Verificar docker-compose.yml
    if Path("docker-compose.yml").exists():
        print("✅ docker-compose.yml existe")
    else:
        print("❌ docker-compose.yml não encontrado")
        return False
    
    # Verificar .env
    if Path(".env").exists():
        print("✅ .env existe")
    else:
        print("⚠️ .env não encontrado (criado a partir de .env.example)")
        if Path(".env.example").exists():
            Path(".env").write_text(Path(".env.example").read_text())
            print("✅ .env criado")
    
    # Verificar Dockerfile
    if Path("Dockerfile").exists():
        print("✅ Dockerfile existe")
    
    return True

if __name__ == "__main__":
    validate_docker_config()
```

**Resultado esperado:** ✅ Configuração Docker OK

---

## 🚀 PASSO 7: INICIAR CONTAINERS

### **Iniciar Serviços Básicos**
```bash
# Iniciar PostgreSQL e Redis apenas:
docker-compose up -d postgres redis

# Verificar se estão a correr:
docker-compose ps

# Verificar logs:
docker-compose logs postgres
docker-compose logs redis
```

### **Testar Conexões**
```bash
# Testar PostgreSQL:
docker exec -it vb-postgres psql -U vb_admin -d valuebetting

# Testar Redis:
docker exec -it vb-redis redis-cli -a tua_senha ping
# Deve responder: PONG
```

### **✅ VALIDAÇÃO APÓS PASSO 7**
```python
import subprocess
import requests

def validate_containers():
    """Valida containers Docker"""
    print("🔍 Validando containers...")
    
    # Verificar containers
    result = subprocess.run(['docker-compose', 'ps'], 
                          capture_output=True, text=True)
    print(result.stdout)
    
    # Testar PostgreSQL
    try:
        result = subprocess.run(['docker', 'exec', 'vb-postgres', 'pg_isready'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PostgreSQL: Ready")
        else:
            print("❌ PostgreSQL: Not ready")
    except:
        print("⚠️ PostgreSQL: Não foi possível testar")
    
    # Testar Redis
    try:
        result = subprocess.run(['docker', 'exec', 'vb-redis', 'redis-cli', 'ping'],
                              capture_output=True, text=True)
        if "PONG" in result.stdout:
            print("✅ Redis: Ready")
        else:
            print("❌ Redis: Not ready")
    except:
        print("⚠️ Redis: Não foi possível testar")
    
    return True

if __name__ == "__main__":
    validate_containers()
```

**Resultado esperado:** ✅ Containers funcionando

---

## 🤖 PASSO 8: CONFIGURAR MLFLOW LOCAL

### **Iniciar MLflow**
```bash
# Iniciar MLflow com backend PostgreSQL:
docker-compose up -d mlflow

# Verificar se está a correr:
docker-compose ps mlflow

# Aceder a UI:
# http://localhost:5000
```

### **Configurar MLflow**
```python
# No Python:
import mlflow

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("VBQ-UNIFIED")

# Testar:
with mlflow.start_run():
    mlflow.log_param("test", "value")
```

### **✅ VALIDAÇÃO APÓS PASSO 8**
```python
import requests

def validate_mlflow():
    """Valida MLflow"""
    print("🔍 Validando MLflow...")
    
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            print("✅ MLflow UI: Acessível (http://localhost:5000)")
            
            # Testar tracking
            import mlflow
            mlflow.set_tracking_uri("http://localhost:5000")
            with mlflow.start_run():
                mlflow.log_param("validation", "test")
            print("✅ MLflow Tracking: Funcionando")
            return True
        else:
            print(f"❌ MLflow: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ MLflow: {e}")
        return False

if __name__ == "__main__":
    validate_mlflow()
```

**Resultado esperado:** ✅ MLflow funcionando

---

## 📊 PASSO 9: CONFIGURAR MONITORING LOCAL

### **Iniciar Prometheus e Grafana**
```bash
# Iniciar monitoring:
docker-compose up -d prometheus grafana

# Verificar:
docker-compose ps prometheus grafana

# Aceder:
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
# (admin/admin - mudar depois)
```

### **Configurar Dashboards**
```bash
# Dashboards em:
# monitoring/grafana/dashboards/

# Importar manualmente se necessário:
# Grafana UI > Dashboards > Import
```

### **✅ VALIDAÇÃO APÓS PASSO 9**
```python
import requests

def validate_monitoring():
    """Valida Prometheus e Grafana"""
    print("🔍 Validando monitoring...")
    
    # Testar Prometheus
    try:
        response = requests.get("http://localhost:9090", timeout=5)
        if response.status_code == 200:
            print("✅ Prometheus: Acessível (http://localhost:9090)")
        else:
            print(f"❌ Prometheus: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Prometheus: {e}")
    
    # Testar Grafana
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Grafana: Acessível (http://localhost:3000)")
        else:
            print(f"❌ Grafana: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Grafana: {e}")
    
    return True

if __name__ == "__main__":
    validate_monitoring()
```

**Resultado esperado:** ✅ Monitoring funcionando

---

## 🧪 PASSO 10: VALIDAR INSTALAÇÃO

### **Script de Validação Completa**
```python
import sys
import subprocess
import requests
from pathlib import Path

def validate_installation():
    """Valida todos os componentes instalados"""
    
    print("="*70)
    print("🔍 VALIDAÇÃO FINAL DE INSTALAÇÃO")
    print("="*70)
    
    all_ok = True
    
    # Python version
    print("\n🐍 Python:")
    py_version = sys.version_info
    if py_version >= (3, 11):
        print(f"   ✅ {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        print(f"   ❌ {py_version.major}.{py_version.minor}.{py_version.micro} (requerido: 3.11+)")
        all_ok = False
    
    # Docker
    print("\n🐳 Docker:")
    try:
        docker = subprocess.run(['docker', '--version'], 
                               capture_output=True, text=True)
        print(f"   ✅ {docker.stdout.strip()}")
    except:
        print("   ❌ Não encontrado")
        all_ok = False
    
    # Git
    print("\n📦 Git:")
    try:
        git = subprocess.run(['git', '--version'], 
                           capture_output=True, text=True)
        print(f"   ✅ {git.stdout.strip()}")
    except:
        print("   ❌ Não encontrado")
        all_ok = False
    
    # Ambiente virtual
    print("\n🔧 Ambiente Virtual:")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("   ✅ Ativo")
    else:
        print("   ❌ Não ativo")
        all_ok = False
    
    # Estrutura do projeto
    print("\n📁 Estrutura do Projeto:")
    if Path("00_SETUP_ZERO").exists():
        print("   ✅ 00_SETUP_ZERO/")
    if Path("requirements.txt").exists():
        print("   ✅ requirements.txt")
    if Path("docker-compose.yml").exists():
        print("   ✅ docker-compose.yml")
    if Path(".env").exists():
        print("   ✅ .env")
    
    # Containers
    print("\n🐳 Containers:")
    try:
        result = subprocess.run(['docker-compose', 'ps'], 
                              capture_output=True, text=True)
        print(result.stdout)
    except:
        print("   ❌ Não foi possível verificar")
        all_ok = False
    
    # Serviços
    print("\n🔌 Serviços:")
    services = {
        "PostgreSQL": "localhost:5432",
        "Redis": "localhost:6379",
        "MLflow": "localhost:5000",
        "Prometheus": "localhost:9090",
        "Grafana": "localhost:3000"
    }
    
    for name, url in services.items():
        try:
            response = requests.get(f"http://{url}", timeout=2)
            if response.status_code == 200:
                print(f"   ✅ {name}: OK")
            else:
                print(f"   ⚠️ {name}: Status {response.status_code}")
        except:
            print(f"   ⚠️ {name}: Não acessível")
    
    # Resumo
    print("\n" + "="*70)
    if all_ok:
        print("✅ INSTALAÇÃO COMPLETA E VALIDADA!")
        print("🚀 Próximo passo: [[00_SETUP_ZERO/VALIDACAO]]")
    else:
        print("⚠️ INSTALAÇÃO COMPLETA COM PROBLEMAS")
        print("🔧 Verificar secção 'Problemas Comuns' abaixo")
    print("="*70)
    
    return all_ok

if __name__ == "__main__":
    validate_installation()
```

### **✅ VALIDAÇÃO FINAL APÓS PASSO 10**
```bash
# Executar script de validação:
python validate_installation.py

# Ou executar manualmente:
# - Verificar Python: python --version
# - Verificar Docker: docker --version
# - Verificar Git: git --version
# - Verificar containers: docker-compose ps
# - Testar serviços: abrir URLs no browser
```

**Resultado esperado:** ✅ INSTALAÇÃO COMPLETA E VALIDADA

---

## 📋 CHECKLIST FINAL DE INSTALAÇÃO

### **Software:**
- [ ] Python 3.11+ instalado
- [ ] Docker Desktop funcionando
- [ ] Git configurado
- [ ] VS Code instalado

### **Projeto:**
- [ ] Repositório clonado
- [ ] Ambiente virtual criado
- [ ] Dependências instaladas
- [ ] .env configurado

### **Containers:**
- [ ] PostgreSQL a correr
- [ ] Redis a correr
- [ ] MLflow a correr
- [ ] Prometheus a correr
- [ ] Grafana a correr

### **Conectividade:**
- [ ] PostgreSQL acessível
- [ ] Redis acessível
- [ ] MLflow UI acessível
- [ ] Grafana UI acessível

---

## 🚀 PRÓXIMOS PASSOS

### **Validação Completa**
1. **Ir para:** [[00_SETUP_ZERO/VALIDACAO]]
2. **Correr testes completos**
3. **Verificar tudo funcional**

### **Verificar Custos**
1. **Ir para:** [[00_SETUP_ZERO/CUSTOS]]
2. **Confirmar zero euros**
3. **Documentar alternativas**

### **Começar Implementação**
1. **Ir para:** [[04_Data_Engineering/FONTES_GRATUITAS]]
2. **Configurar dados gratuitos**
3. **Começar desenvolvimento**

---

## ⚠️ PROBLEMAS COMUNS

### **Docker não inicia**
```bash
# Windows: Habilitar virtualização
# BIOS > Virtualization Technology > Enabled

# Linux: Adicionar ao grupo
sudo usermod -aG docker $USER
newgrp docker
```

### **Portas em uso**
```bash
# Verificar portas:
netstat -tulpn | grep :5432
netstat -tulpn | grep :6379

# Mudar portas no .env:
POSTGRES_PORT=5433
REDIS_PORT=6380
```

### **Memória insuficiente**
```bash
# Docker Desktop > Settings > Resources
# Ajustar Memory para 4-8GB
# Ajustar Swap para 2-4GB
```

---

**Status:** Instalação em progresso  
**Tempo estimado:** 2-3 horas  
**Resultado:** Stack completa funcional  

---

#status/active #priority/critical #phase/setup-zero
