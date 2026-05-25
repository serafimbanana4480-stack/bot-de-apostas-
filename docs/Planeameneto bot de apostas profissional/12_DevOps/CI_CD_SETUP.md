# CI_CD_SETUP — Configuração de CI/CD, GitHub Actions e Testes Automatizados

**ID:** `DEV-003` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Configurar um pipeline de Integração Contínua e Deploy Contínuo (CI/CD) que automatize testes, build, quality checks e deployment. O CI/CD garante que cada mudança é validada automaticamente antes de chegar a produção, reduzindo erros e acelerando o ciclo de desenvolvimento.

---

## 2. ARQUITETURA DO PIPELINE

### 2.1 Visão Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE                               │
└─────────────────────────────────────────────────────────────────┘

1. TRIGGER
   ├── Push para branch (feature/develop/staging/main)
   ├── Pull Request criado/atualizado
   ├── Manual (workflow_dispatch)
   └── Schedule (cron jobs)

2. CI (CONTINUOUS INTEGRATION)
   ├── Checkout código
   ├── Setup ambiente (Python 3.11)
   ├── Install dependencies
   ├── Linting (flake8, black, mypy)
   ├── Security scan (bandit, safety)
   ├── Unit tests (pytest)
   ├── Integration tests
   └── Build Docker image

3. CD (CONTINUOUS DEPLOYMENT)
   ├── Push Docker image para registry
   ├── Deploy para staging (se branch=develop)
   ├── Run smoke tests em staging
   ├── Deploy para produção (se branch=main)
   └── Health check + monitorização

4. NOTIFICAÇÃO
   ├── Slack (sucesso/falha)
   ├── Email (falhas críticas)
   └── GitHub status checks
```

### 2.2 Stages por Branch

| Branch | Stages | Deploy Target |
|--------|--------|---------------|
| `feature/*` | Lint, Test, Security | Nenhum |
| `develop` | Lint, Test, Security, Build | Staging |
| `staging` | Lint, Test, Security, Build | Staging (validação) |
| `main` | Lint, Test, Security, Build, Deploy | Production |

---

## 3. GITHUB ACTIONS WORKFLOWS

### 3.1 Workflow Principal (CI)

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches:
      - main
      - develop
      - staging
      - 'feature/**'
  pull_request:
    branches:
      - main
      - develop
      - staging

jobs:
  lint:
    name: Lint Code
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install black flake8 mypy isort
          pip install -r requirements.txt
      
      - name: Run Black
        run: black --check src/
      
      - name: Run isort
        run: isort --check-only src/
      
      - name: Run Flake8
        run: flake8 src/ --max-line-length=100 --extend-ignore=E203
      
      - name: Run MyPy
        run: mypy src/ --ignore-missing-imports

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install bandit safety
          pip install -r requirements.txt
      
      - name: Run Bandit
        run: bandit -r src/ -f json -o bandit-report.json || true
      
      - name: Run Safety
        run: safety check --json > safety-report.json || true
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json
            safety-report.json

  test:
    name: Run Tests
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ['3.10', '3.11']
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install pytest pytest-cov pytest-xdist
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=src --cov-report=xml --cov-report=html
      
      - name: Run integration tests
        run: |
          pytest tests/integration/ -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [lint, security, test]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-
            type=semver,pattern={{version}}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### 3.2 Workflow de Deploy para Staging

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging

on:
  push:
    branches:
      - develop
  workflow_dispatch:

jobs:
  deploy:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.valuebetting.com
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:staging
          cache-from: type=gha
      
      - name: Deploy to staging server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /app/valuebetting
            docker-compose -f docker-compose.staging.yml pull
            docker-compose -f docker-compose.staging.yml up -d
            docker system prune -f
      
      - name: Run smoke tests
        run: |
          sleep 30
          curl -f ${{ secrets.STAGING_URL }}/health || exit 1
          curl -f ${{ secrets.STAGING_URL }}/api/v1/predict -X POST \
            -H "Content-Type: application/json" \
            -d '{"features": {"odds": 2.5, "home_team_strength": 0.7}}' || exit 1
      
      - name: Notify Slack on success
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: success
          text: 'Deploy to staging completed successfully'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
      
      - name: Notify Slack on failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: failure
          text: 'Deploy to staging failed'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 3.3 Workflow de Deploy para Produção

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches:
      - main
  workflow_dispatch:
    inputs:
      confirm:
        description: 'Type CONFIRM to deploy to production'
        required: true
        default: ''

jobs:
  confirm:
    name: Confirm Deployment
    runs-on: ubuntu-latest
    steps:
      - name: Check confirmation
        run: |
          if [ "${{ github.event.inputs.confirm }}" != "CONFIRM" ]; then
            echo "Deployment not confirmed. Aborting."
            exit 1
          fi

  deploy:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: confirm
    environment:
      name: production
      url: https://api.valuebetting.com
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:latest
            ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
      
      - name: Blue-green deployment
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PRODUCTION_HOST }}
          username: ${{ secrets.PRODUCTION_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /app/valuebetting
            # Deploy to green environment
            export VERSION=${{ github.sha }}
            docker-compose -f docker-compose.blue-green.yml up -d app-green
            # Wait for health check
            sleep 60
            curl -f http://localhost:8001/health || exit 1
            # Switch traffic
            ./scripts/switch-to-green.sh
      
      - name: Run smoke tests
        run: |
          sleep 30
          curl -f ${{ secrets.PRODUCTION_URL }}/health || exit 1
          curl -f ${{ secrets.PRODUCTION_URL }}/api/v1/predict -X POST \
            -H "Content-Type: application/json" \
            -d '{"features": {"odds": 2.5, "home_team_strength": 0.7}}' || exit 1
      
      - name: Monitor for 10 minutes
        run: |
          for i in {1..20}; do
            curl -f ${{ secrets.PRODUCTION_URL }}/health || exit 1
            sleep 30
          done
      
      - name: Notify Slack on success
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: success
          text: 'Deploy to production completed successfully'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
      
      - name: Rollback on failure
        if: failure()
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PRODUCTION_HOST }}
          username: ${{ secrets.PRODUCTION_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /app/valuebetting
            ./scripts/rollback-to-blue.sh
```

### 3.4 Workflow de Testes Noturnos

```yaml
# .github/workflows/nightly-tests.yml
name: Nightly Tests

on:
  schedule:
    - cron: '0 2 * * *'  # 02:00 UTC todos os dias
  workflow_dispatch:

jobs:
  full-test-suite:
    name: Full Test Suite
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pytest pytest-xdist
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run all tests with coverage
        run: |
          pytest tests/ -v --cov=src --cov-report=xml --cov-report=html --dist=loadscope -n auto
      
      - name: Generate test report
        run: |
          pytest tests/ --html=test-report.html --self-contained-html
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
      
      - name: Upload test report
        uses: actions/upload-artifact@v3
        with:
          name: test-report
          path: test-report.html
      
      - name: Run performance tests
        run: |
          python scripts/performance_tests.py
      
      - name: Notify on failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: failure
          text: 'Nightly tests failed'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 4. CONFIGURAÇÃO DE TESTES

### 4.1 Estrutura de Testes

```
tests/
├── unit/
│   ├── test_data_loader.py
│   ├── test_feature_engineering.py
│   ├── test_model_trainer.py
│   └── test_metrics.py
├── integration/
│   ├── test_api.py
│   ├── test_database.py
│   └── test_mlflow_integration.py
├── e2e/
│   ├── test_betting_flow.py
│   └── test_model_retraining.py
└── conftest.py
```

### 4.2 Conftest.py (Fixtures Comuns)

```python
# tests/conftest.py
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock

@pytest.fixture
def sample_data():
    """Dados de exemplo para testes"""
    return pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=100),
        'home_team': ['Team_' + str(i % 10) for i in range(100)],
        'away_team': ['Team_' + str((i + 5) % 10) for i in range(100)],
        'odds': np.random.uniform(1.5, 3.5, 100),
        'home_team_strength': np.random.uniform(0, 1, 100),
        'away_team_strength': np.random.uniform(0, 1, 100),
        'target': np.random.randint(0, 2, 100)
    })

@pytest.fixture
def mock_model():
    """Mock de modelo para testes"""
    model = Mock()
    model.predict_proba.return_value = np.random.uniform(0, 1, (10, 2))
    return model

@pytest.fixture
def test_database():
    """Base de dados de teste"""
    # Setup database de teste
    # ...
    yield
    # Cleanup
    # ...
```

### 4.3 Exemplo de Teste Unitário

```python
# tests/unit/test_feature_engineering.py
import pytest
import pandas as pd
import numpy as np
from src.features.feature_engineering import create_team_strength, create_form

def test_create_team_strength(sample_data):
    """Testa criação de feature de força de equipa"""
    result = create_team_strength(sample_data)
    
    assert 'home_team_strength' in result.columns
    assert 'away_team_strength' in result.columns
    assert result['home_team_strength'].between(0, 1).all()
    assert len(result) == len(sample_data)

def test_create_form(sample_data):
    """Testa criação de feature de forma"""
    result = create_form(sample_data, window=5)
    
    assert 'home_form' in result.columns
    assert 'away_form' in result.columns
    assert result['home_form'].between(0, 1).all()
    
    # Verificar que primeiros 4 jogos são NaN (window=5)
    assert result['home_form'].iloc[:4].isna().sum() == 4

def test_feature_engineering_pipeline(sample_data):
    """Testa pipeline completo de feature engineering"""
    from src.features.feature_engineering import create_features
    
    result = create_features(sample_data)
    
    # Verificar que todas as features esperadas estão presentes
    expected_features = [
        'odds', 'home_team_strength', 'away_team_strength',
        'home_form', 'away_form', 'h2h_home_win_rate'
    ]
    
    for feature in expected_features:
        assert feature in result.columns
    
    # Verificar que não há NaNs (exceto onde esperado)
    assert result.isnull().sum().sum() < len(result) * 0.1
```

### 4.4 Exemplo de Teste de Integração

```python
# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_check():
    """Testa endpoint de health check"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_predict_endpoint():
    """Testa endpoint de predição"""
    response = client.post(
        "/api/v1/predict",
        json={
            "features": {
                "odds": 2.5,
                "home_team_strength": 0.7,
                "away_team_strength": 0.5
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert 0 <= data["prediction"] <= 1
    assert "model_version" in data

def test_predict_endpoint_invalid_input():
    """Testa endpoint com input inválido"""
    response = client.post(
        "/api/v1/predict",
        json={"features": {"odds": -1.0}}  # Odds inválido
    )
    
    assert response.status_code == 422
```

### 4.5 Configuração de Pytest

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --tb=short

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

---

## 5. QUALITY CHECKS

### 5.1 Linting com Flake8

```ini
# setup.cfg
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    venv,
    .venv,
    build,
    dist
per-file-ignores =
    __init__.py:F401
```

### 5.2 Formatação com Black

```ini
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | build
  | dist
)/
'''
```

### 5.3 Type Checking com MyPy

```ini
# mypy.ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
ignore_missing_imports = True

[mypy.plugins]
add_plugin = mypy.plugins.pytest
```

---

## 6. SECRETS E VARIÁVEIS DE AMBIENTE

### 6.1 Secrets no GitHub

Configurar secrets em Settings → Secrets and variables → Actions:

```
PRODUCTION_HOST
PRODUCTION_USER
SSH_KEY
STAGING_HOST
STAGING_USER
STAGING_URL
PRODUCTION_URL
DATABASE_URL
MLFLOW_TRACKING_URI
SLACK_WEBHOOK
GITHUB_TOKEN (automático)
```

### 6.2 Uso de Secrets

```yaml
- name: Deploy
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
  run: |
    python scripts/deploy.py
```

---

## 7. MONITORIZAÇÃO DO PIPELINE

### 7.1 Métricas

- **Pipeline success rate:** % de pipelines bem-sucedidos
- **Pipeline duration:** Tempo médio de execução
- **Test coverage:** Cobertura de código
- **Deployment frequency:** Frequência de deploys
- **Lead time:** Tempo desde commit até deploy

### 7.2 Dashboard

Criar dashboard no GitHub Actions ou ferramenta externa (ex: Grafana) para visualizar métricas do pipeline.

---

## 8. BACKLOG TÉCNICO

- [ ] Implementar cache de dependências para acelerar builds
- [ ] Adicionar testes de carga no pipeline
- [ ] Implementar testes de mutação
- [ ] Adicionar integração com SonarQube
- [ ] Implementar deploy automático para múltiplos ambientes
- [ ] Adicionar testes de segurança automatizados (SAST/DAST)

---

## 9. LINKS CRUZADOS

- [[12_DevOps/INDEX]] ← Secção mãe
- [[12_DevOps/GIT_WORKFLOW]] → Estratégia Git
- [[12_DevOps/DEPLOYMENT_STRATEGY]] → Estratégias de deploy
- [[11_MLOps/CI_CD_MODELOS]] → CI/CD específico de modelos