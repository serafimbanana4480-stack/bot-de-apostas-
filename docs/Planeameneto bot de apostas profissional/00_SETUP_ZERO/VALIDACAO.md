# Validação do Setup - Setup Zero Euros

**Versão:** 1.0.0-ZERO-EUROS  
**Data:** 2026-05-18  
**Status:** #status/active #priority/critical  

---

## 🎯 OBJETIVO

Validar completamente o setup do sistema VBQ-UNIFIED para garantir que todos os componentes estão funcionais antes de começar o desenvolvimento.

---

## 📋 CHECKLIST DE VALIDAÇÃO

### **Hardware e Sistema**
- [ ] CPU com 4+ cores
- [ ] RAM com 8GB+ disponível
- [ ] Disco com 50GB+ livre
- [ ] Internet estável (>10Mbps)
- [ ] Sistema operacional compatível

### **Software Instalado**
- [ ] Python 3.11+ funcionando
- [ ] Docker Desktop operacional
- [ ] Git configurado
- [ ] VS Code instalado
- [ ] Navegador moderno

### **Projeto Configurado**
- [ ] Repositório clonado
- [ ] Ambiente virtual criado
- [ ] Dependências instaladas
- [ ] .env configurado
- [ ] docker-compose.yml presente

### **Containers Funcionais**
- [ ] PostgreSQL a correr
- [ ] Redis a correr
- [ ] MLflow a correr
- [ ] Prometheus a correr
- [ ] Grafana a correr

---

## 🧪 TESTES AUTOMATIZADOS

### **Script de Validação Completa e Expandida**
```python
import sys
import subprocess
import psycopg2
import redis
import requests
import time
import psutil
import platform
from pathlib import Path
from datetime import datetime
import json

class SetupValidator:
    """Validação completa e expandida do setup VBQ-UNIFIED"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.start_time = datetime.now()
        self.system_info = {}
    
    def log_result(self, test, status, message="", details=""):
        """Regista resultado de teste"""
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        self.results.append({
            "test": test,
            "status": status,
            "message": message,
            "details": details,
            "icon": icon
        })
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        else:
            self.warnings += 1
    
    def get_system_info(self):
        """Recolhe informação do sistema"""
        self.system_info = {
            "os": f"{platform.system()} {platform.release()}",
            "cpu_cores": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            "ram_total": psutil.virtual_memory().total / (1024**3),
            "ram_available": psutil.virtual_memory().available / (1024**3),
            "disk_free": psutil.disk_usage('/').free / (1024**3),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
    
    def test_hardware(self):
        """Testa requisitos de hardware"""
        cpu_cores = psutil.cpu_count()
        ram_gb = psutil.virtual_memory().total / (1024**3)
        disk_gb = psutil.disk_usage('/').free / (1024**3)
        
        if cpu_cores >= 4:
            self.log_result("CPU Cores", "PASS", f"{cpu_cores} cores")
        else:
            self.log_result("CPU Cores", "FAIL", f"{cpu_cores} cores (mínimo: 4)")
        
        if ram_gb >= 8:
            self.log_result("RAM", "PASS", f"{ram_gb:.1f}GB")
        else:
            self.log_result("RAM", "FAIL", f"{ram_gb:.1f}GB (mínimo: 8GB)")
        
        if disk_gb >= 50:
            self.log_result("Disk Space", "PASS", f"{disk_gb:.0f}GB livre")
        else:
            self.log_result("Disk Space", "FAIL", f"{disk_gb:.0f}GB livre (mínimo: 50GB)")
    
    def test_python_version(self):
        """Testa versão Python"""
        version = sys.version_info
        if version >= (3, 11):
            self.log_result("Python Version", "PASS", 
                           f"{version.major}.{version.minor}.{version.micro}")
        else:
            self.log_result("Python Version", "FAIL",
                           f"Need 3.11+, have {version.major}.{version.minor}")
    
    def test_docker(self):
        """Testa Docker"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log_result("Docker", "PASS", result.stdout.strip())
                # Testar se Docker está a responder
                result = subprocess.run(['docker', 'ps'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_result("Docker Running", "PASS", "Docker daemon responding")
                else:
                    self.log_result("Docker Running", "FAIL", "Docker daemon not responding")
            else:
                self.log_result("Docker", "FAIL", "Docker not responding")
        except:
            self.log_result("Docker", "FAIL", "Docker not installed")
    
    def test_git(self):
        """Testa Git"""
        try:
            result = subprocess.run(['git', '--version'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log_result("Git", "PASS", result.stdout.strip())
            else:
                self.log_result("Git", "FAIL", "Git not responding")
        except:
            self.log_result("Git", "FAIL", "Git not installed")
    
    def test_postgresql(self):
        """Testa PostgreSQL"""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="valuebetting",
                user="vb_admin",
                password="your_password"  # Mudar para tua senha
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            self.log_result("PostgreSQL", "PASS", f"Connected: {version[:50]}...")
            cursor.close()
            conn.close()
        except Exception as e:
            self.log_result("PostgreSQL", "FAIL", str(e))
    
    def test_redis(self):
        """Testa Redis"""
        try:
            r = redis.Redis(host='localhost', port=6379,
                           password="your_password",  # Mudar para tua senha
                           decode_responses=True)
            r.ping()
            info = r.info()
            self.log_result("Redis", "PASS", f"Connected, version: {info.get('redis_version', 'unknown')}")
        except Exception as e:
            self.log_result("Redis", "FAIL", str(e))
    
    def test_mlflow(self):
        """Testa MLflow"""
        try:
            response = requests.get("http://localhost:5000", timeout=5)
            if response.status_code == 200:
                # Testar tracking
                import mlflow
                mlflow.set_tracking_uri("http://localhost:5000")
                with mlflow.start_run():
                    mlflow.log_param("validation", "test")
                self.log_result("MLflow", "PASS", "UI responding, tracking working")
            else:
                self.log_result("MLflow", "FAIL", f"Status {response.status_code}")
        except Exception as e:
            self.log_result("MLflow", "FAIL", str(e))
    
    def test_prometheus(self):
        """Testa Prometheus"""
        try:
            response = requests.get("http://localhost:9090", timeout=5)
            if response.status_code == 200:
                self.log_result("Prometheus", "PASS", "UI responding")
            else:
                self.log_result("Prometheus", "FAIL", f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Prometheus", "FAIL", str(e))
    
    def test_grafana(self):
        """Testa Grafana"""
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                self.log_result("Grafana", "PASS", "UI responding")
            else:
                self.log_result("Grafana", "FAIL", f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Grafana", "FAIL", str(e))
    
    def test_project_structure(self):
        """Testa estrutura do projeto"""
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
        
        required_files = [
            "requirements.txt",
            "docker-compose.yml",
            ".env"
        ]
        
        base_path = Path(".")
        missing_dirs = []
        missing_files = []
        
        for dir_name in required_dirs:
            if not (base_path / dir_name).exists():
                missing_dirs.append(dir_name)
        
        for file_name in required_files:
            if not (base_path / file_name).exists():
                missing_files.append(file_name)
        
        if not missing_dirs and not missing_files:
            self.log_result("Project Structure", "PASS", "All directories and files present")
        else:
            issues = []
            if missing_dirs:
                issues.append(f"Missing dirs: {', '.join(missing_dirs)}")
            if missing_files:
                issues.append(f"Missing files: {', '.join(missing_files)}")
            self.log_result("Project Structure", "FAIL", "; ".join(issues))
    
    def test_dependencies(self):
        """Testa dependências Python"""
        try:
            import numpy
            import pandas
            import sklearn
            import xgboost
            import fastapi
            import sqlalchemy
            import redis
            import mlflow
            
            versions = {
                "numpy": numpy.__version__,
                "pandas": pandas.__version__,
                "sklearn": sklearn.__version__,
                "xgboost": xgboost.__version__,
                "fastapi": fastapi.__version__,
                "sqlalchemy": sqlalchemy.__version__,
                "redis": redis.__version__,
                "mlflow": mlflow.__version__
            }
            self.log_result("Dependencies", "PASS", 
                          ", ".join([f"{k} {v}" for k, v in versions.items()]))
        except ImportError as e:
            self.log_result("Dependencies", "FAIL", str(e))
    
    def test_network_connectivity(self):
        """Testa conectividade de rede"""
        apis = {
            "NBA API": "https://stats.nba.com",
            "Basketball Reference": "https://basketball-reference.com",
            "The-Odds-API": "https://the-odds-api.com",
            "GitHub": "https://github.com"
        }
        
        failed = []
        for name, url in apis.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.log_result(f"Network: {name}", "PASS", "Accessible")
                else:
                    self.log_result(f"Network: {name}", "WARN", f"Status {response.status_code}")
                    failed.append(name)
            except Exception as e:
                self.log_result(f"Network: {name}", "FAIL", str(e))
                failed.append(name)
            time.sleep(0.5)
    
    def test_performance(self):
        """Testa performance básica"""
        # Testar tempo de resposta de serviços
        services = {
            "MLflow": "http://localhost:5000",
            "Prometheus": "http://localhost:9090",
            "Grafana": "http://localhost:3000"
        }
        
        for name, url in services.items():
            try:
                start = time.time()
                response = requests.get(url, timeout=5)
                elapsed = (time.time() - start) * 1000
                
                if elapsed < 500:
                    self.log_result(f"Performance: {name}", "PASS", f"{elapsed:.0f}ms")
                else:
                    self.log_result(f"Performance: {name}", "WARN", f"{elapsed:.0f}ms (slow)")
            except:
                self.log_result(f"Performance: {name}", "FAIL", "Not accessible")
    
    def generate_html_report(self):
        """Gera relatório HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Relatório de Validação - Setup Zero Euros</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .summary-card {{ flex: 1; padding: 20px; border-radius: 8px; text-align: center; }}
        .pass {{ background: #4CAF50; color: white; }}
        .fail {{ background: #f44336; color: white; }}
        .warn {{ background: #ff9800; color: white; }}
        .summary-card h2 {{ margin: 0; font-size: 36px; }}
        .summary-card p {{ margin: 5px 0 0 0; }}
        .section {{ margin: 30px 0; }}
        .section h2 {{ color: #333; border-left: 4px solid #4CAF50; padding-left: 10px; }}
        .system-info {{ background: #f9f9f9; padding: 15px; border-radius: 5px; }}
        .system-info p {{ margin: 5px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #4CAF50; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .status-pass {{ color: #4CAF50; font-weight: bold; }}
        .status-fail {{ color: #f44336; font-weight: bold; }}
        .status-warn {{ color: #ff9800; font-weight: bold; }}
        .timestamp {{ color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Relatório de Validação - Setup Zero Euros</h1>
        <p class="timestamp">Gerado em: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="summary-card pass">
                <h2>{self.passed}</h2>
                <p>Passados</p>
            </div>
            <div class="summary-card fail">
                <h2>{self.failed}</h2>
                <p>Falhados</p>
            </div>
            <div class="summary-card warn">
                <h2>{self.warnings}</h2>
                <p>Avisos</p>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Informação do Sistema</h2>
            <div class="system-info">
                <p><strong>OS:</strong> {self.system_info.get('os', 'N/A')}</p>
                <p><strong>CPU:</strong> {self.system_info.get('cpu_cores', 0)} cores @ {self.system_info.get('cpu_freq', 0):.0f}MHz</p>
                <p><strong>RAM:</strong> {self.system_info.get('ram_total', 0):.1f}GB total, {self.system_info.get('ram_available', 0):.1f}GB disponível</p>
                <p><strong>Disco:</strong> {self.system_info.get('disk_free', 0):.0f}GB livre</p>
                <p><strong>Python:</strong> {self.system_info.get('python_version', 'N/A')}</p>
            </div>
        </div>
        
        <div class="section">
            <h2>🧪 Resultados dos Testes</h2>
            <table>
                <thead>
                    <tr>
                        <th>Teste</th>
                        <th>Status</th>
                        <th>Mensagem</th>
                        <th>Detalhes</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for result in self.results:
            status_class = f"status-{result['status'].lower()}"
            html += f"""
                    <tr>
                        <td>{result['test']}</td>
                        <td class="{status_class}">{result['status']}</td>
                        <td>{result['message']}</td>
                        <td>{result['details'] or '-'}</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>✅ Status Final</h2>
"""
        if self.failed == 0:
            html += '<p style="color: #4CAF50; font-size: 18px;">✅ Setup validado com sucesso! Pronto para desenvolvimento.</p>'
        else:
            html += f'<p style="color: #f44336; font-size: 18px;">❌ Setup com {self.failed} problema(s). Ver secção de troubleshooting.</p>'
        
        html += """
        </div>
    </div>
</body>
</html>
"""
        
        # Salvar relatório
        report_path = Path("validation_report.html")
        report_path.write_text(html)
        print(f"\n📄 Relatório HTML gerado: {report_path.absolute()}")
        return report_path
    
    def run_all_tests(self, generate_html=True):
        """Executa todos os testes"""
        print("🔍 Iniciando validação completa e expandida do setup...\n")
        print("="*70)
        
        self.get_system_info()
        
        # Hardware
        print("\n📦 HARDWARE")
        self.test_hardware()
        
        # Software
        print("\n🛠️ SOFTWARE")
        self.test_python_version()
        self.test_docker()
        self.test_git()
        
        # Projeto
        print("\n🏗️ PROJETO")
        self.test_project_structure()
        self.test_dependencies()
        
        # Containers
        print("\n🐳 CONTAINERS")
        self.test_postgresql()
        self.test_redis()
        self.test_mlflow()
        self.test_prometheus()
        self.test_grafana()
        
        # Rede
        print("\n🌐 REDE")
        self.test_network_connectivity()
        
        # Performance
        print("\n⚡ PERFORMANCE")
        self.test_performance()
        
        print("="*70)
        print(f"\n📊 Resultados: {self.passed} PASS, {self.failed} FAIL, {self.warnings} WARN")
        
        # Mostrar resultados
        for result in self.results:
            print(f"{result['icon']} {result['test']}: {result['message']}")
        
        print("="*70)
        
        # Gerar relatório HTML
        if generate_html:
            self.generate_html_report()
        
        # Status final
        if self.failed == 0:
            print("✅ Setup validado com sucesso!")
            return True
        else:
            print(f"⚠️  {self.failed} test(s) falharam. Verificar problemas.")
            return False

if __name__ == "__main__":
    validator = SetupValidator()
    success = validator.run_all_tests(generate_html=True)
    sys.exit(0 if success else 1)
```

---

## 🔧 TESTES MANUAIS

### **Teste PostgreSQL**
```bash
# Conectar ao PostgreSQL:
docker exec -it vb-postgres psql -U vb_admin -d valuebetting

# Correr query de teste:
SELECT version();

# Criar tabela de teste:
CREATE TABLE test_table (id SERIAL PRIMARY KEY, name VARCHAR(100));

# Inserir dados:
INSERT INTO test_table (name) VALUES ('test');

# Verificar dados:
SELECT * FROM test_table;

# Limpeza:
DROP TABLE test_table;
```

### **Teste Redis**
```bash
# Conectar ao Redis:
docker exec -it vb-redis redis-cli -a your_password

# Testar comandos:
PING
SET test_key "test_value"
GET test_key
DEL test_key
EXIT
```

### **Teste MLflow**
```python
# Script de teste MLflow:
import mlflow

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("VBQ-UNIFIED-TEST")

with mlflow.start_run():
    mlflow.log_param("test_param", "test_value")
    mlflow.log_metric("test_metric", 1.0)
    mlflow.log_artifact("test_file.txt")

print("✅ MLflow test passed")
```

### **Teste Grafana**
```bash
# Aceder a Grafana:
# http://localhost:3000
# Login: admin/admin
# Verificar:
# 1. Dashboard está acessível
# 2. Datasource Prometheus configurado
# 3. Pelo menos um dashboard importado
```

---

## 🌐 TESTE DE CONECTIVIDADE

### **Teste APIs Externas**
```python
import requests
import time

def test_external_apis():
    """Testa acesso a APIs externas"""
    
    apis = {
        "NBA API": "https://stats.nba.com",
        "Basketball Reference": "https://basketball-reference.com",
        "The-Odds-API": "https://the-odds-api.com",
        "GitHub": "https://github.com"
    }
    
    print("🌐 Testando conectividade externa...\n")
    
    for name, url in apis.items():
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: OK")
            else:
                print(f"⚠️  {name}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
        time.sleep(1)

if __name__ == "__main__":
    test_external_apis()
```

---

## 📊 TESTE DE PERFORMANCE

### **Teste Carga Básica**
```python
import time
import requests

def test_api_performance():
    """Testa performance da API"""
    
    print("🚀 Testando performance da API...\n")
    
    # Testar endpoint de health
    start = time.time()
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        elapsed = time.time() - start
        
        if response.status_code == 200 and elapsed < 0.5:
            print(f"✅ Health check: {elapsed*1000:.0f}ms")
        else:
            print(f"⚠️  Health check: {elapsed*1000:.0f}ms (slow)")
    except Exception as e:
        print(f"❌ Health check: {str(e)}")
    
    # Testar múltiplas requests
    print("\nTestando 10 requests consecutivas...")
    times = []
    
    for i in range(10):
        start = time.time()
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            elapsed = time.time() - start
            times.append(elapsed)
        except:
            times.append(1.0)  # Timeout
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    
    print(f"Média: {avg_time*1000:.0f}ms")
    print(f"Máximo: {max_time*1000:.0f}ms")
    
    if avg_time < 0.3:
        print("✅ Performance aceitável")
    else:
        print("⚠️  Performance precisa melhorar")

if __name__ == "__main__":
    test_api_performance()
```

---

## 🧪 TESTE DE INTEGRAÇÃO

### **Teste Pipeline Dados**
```python
import requests
import pandas as pd

def test_data_pipeline():
    """Testa pipeline de dados básico"""
    
    print("📊 Testando pipeline de dados...\n")
    
    # Testar ingestão de dados NBA
    try:
        from nba_api.stats.endpoints import leaguegamefinder
        import pandas as pd
        
        gamefinder = leaguegamefinder.LeagueGameFinder()
        games = gamefinder.get_data_frames()[0]
        
        if len(games) > 0:
            print(f"✅ NBA API: {len(games)} jogos obtidos")
        else:
            print("⚠️  NBA API: Sem dados obtidos")
    except Exception as e:
        print(f"❌ NBA API: {str(e)}")
    
    # Testar scraping Basketball-Reference
    try:
        import basketball_reference_web_scraper as br
        
        # Testar scraping de uma equipa
        teams = br.teams()
        if len(teams) > 0:
            print(f"✅ Basketball-Reference: {len(teams)} equipas")
        else:
            print("⚠️  Basketball-Reference: Sem dados")
    except Exception as e:
        print(f"❌ Basketball-Reference: {str(e)}")

if __name__ == "__main__":
    test_data_pipeline()
```

---

## 📋 RELATÓRIO FINAL

### **Template de Relatório**
```markdown
# Relatório de Validação - Setup Zero Euros

**Data:** [DATA]
**Validador:** [NOME]

## Resumo
- Total testes: [X]
- Passados: [Y]
- Falhados: [Z]
- Taxa sucesso: [Y/X]%

## Detalhes
### Hardware
- [X] CPU: [INFO]
- [X] RAM: [INFO]
- [X] Disco: [INFO]
- [X] Rede: [INFO]

### Software
- [X] Python: [INFO]
- [X] Docker: [INFO]
- [X] Git: [INFO]

### Containers
- [X] PostgreSQL: [INFO]
- [X] Redis: [INFO]
- [X] MLflow: [INFO]
- [X] Prometheus: [INFO]
- [X] Grafana: [INFO]

### Conectividade
- [X] APIs externas: [INFO]
- [X] Internet: [INFO]

## Problemas Encontrados
1. [PROBLEMA 1]
2. [PROBLEMA 2]

## Recomendações
1. [RECOMENDAÇÃO 1]
2. [RECOMENDAÇÃO 2]

## Status Final
[✅/❌] Setup pronto para desenvolvimento
```

---

## 🚀 PRÓXIMOS PASSOS

### **Se Validação Passou:**
1. **Ir para:** [[04_Data_Engineering/FONTES_GRATUITAS]]
2. **Configurar dados gratuitos**
3. **Começar desenvolvimento**

### **Se Validação Falhou:**
1. **Ir para:** [[00_SETUP_ZERO/TROUBLESHOOTING]]
2. **Resolver problemas**
3. **Re-validar setup**

---

**Status:** Validação necessária  
**Tempo estimado:** 1-2 horas  
**Resultado:** Confirmação setup funcional  

---

#status/active #priority/critical #phase/setup-zero
