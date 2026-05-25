# Testing Strategy

**ID:** `TST-001` | **Fase:** #phase/1 | **Owner:** Lead Developer | **Status:** #status/active

---

## 1. ESTRATÉGIA DE TESTES

### 1.1 Pirâmide de Testes

```
        /\
       /  \
      / E2E \  ← 10% (Integração completa)
     /--------\
    /          \
   /  Integration \ ← 30% (API, Database, External)
  /--------------\
 /                \
/    Unit Tests    \ ← 60% (Funções individuais)
/--------------------\
```

**Distribuição alvo:**
- **Unit tests:** 60-70%
- **Integration tests:** 20-30%
- **E2E tests:** 5-10%

---

## 2. UNIT TESTS

### 2.1 Estrutura de Diretórios

```
tests/
├── unit/
│   ├── test_ingestion/
│   │   ├── test_nba_ingester.py
│   │   ├── test_betfair_ingester.py
│   │   └── test_injury_ingester.py
│   ├── test_features/
│   │   ├── test_feature_engineer.py
│   │   └── test_feature_validators.py
│   ├── test_models/
│   │   ├── test_xgboost_model.py
│   │   ├── test_meta_model.py
│   │   └── test_calibration.py
│   ├── test_risk/
│   │   ├── test_kelly_calculator.py
│   │   └── test_circuit_breakers.py
│   └── test_utils/
│       ├── test_helpers.py
│       └── test_validators.py
├── integration/
│   ├── test_api/
│   │   ├── test_endpoints.py
│   │   └── test_auth.py
│   ├── test_database/
│   │   ├── test_migrations.py
│   │   └── test_queries.py
│   └── test_external/
│       ├── test_betfair_api.py
│       └── test_telegram_bot.py
└── e2e/
    ├── test_full_pipeline.py
    └── test_paper_trading.py
```

### 2.2 Exemplo de Unit Test

```python
# tests/unit/test_features/test_feature_engineer.py
import pytest
import numpy as np
import pandas as pd
from app.features.feature_engineer import FeatureEngineer

@pytest.fixture
def sample_game_data():
    """Fixture com dados de jogo de exemplo"""
    return {
        'game_id': '0022400001',
        'home_team_id': 1610612740,
        'away_team_id': 1610612752,
        'game_date': pd.Timestamp('2024-01-15'),
        'home_score': 110,
        'away_score': 105
    }

@pytest.fixture
def feature_engineer():
    """Fixture com FeatureEngineer"""
    return FeatureEngineer()

class TestFeatureEngineer:
    def test_calculate_recent_form(self, feature_engineer, sample_game_data):
        """Testar cálculo de forma recente"""
        # Setup
        recent_games = pd.DataFrame({
            'team_id': [sample_game_data['home_team_id']] * 5,
            'points': [100, 105, 110, 95, 108],
            'opponent_points': [98, 102, 108, 92, 105]
        })
        
        # Execute
        form_score = feature_engineer._calculate_recent_form(
            sample_game_data['home_team_id'],
            recent_games
        )
        
        # Assert
        assert isinstance(form_score, float)
        assert 0 <= form_score <= 1  # Normalizado entre 0 e 1
        assert form_score > 0.5  # Equipe com performance acima da média
    
    def test_calculate_four_factors(self, feature_engineer, sample_game_data):
        """Testar cálculo de Four Factors"""
        # Setup
        stats = {
            'efg_pct': 0.52,
            'tov_pct': 0.12,
            'orb_pct': 0.25,
            'ft_fga': 0.20
        }
        
        # Execute
        four_factors = feature_engineer._calculate_four_factors(stats)
        
        # Assert
        assert 'efg' in four_factors
        assert 'tov' in four_factors
        assert 'orb' in four_factors
        assert 'ft' in four_factors
        assert all(0 <= v <= 1 for v in four_factors.values())
    
    def test_validate_features(self, feature_engineer):
        """Testar validação de features"""
        # Setup
        features = {
            'home_recent_form': 0.75,
            'away_recent_form': 0.60,
            'home_four_factors_efg': 0.52,
            'odds': 2.10,
            'edge': 0.05
        }
        
        # Execute
        is_valid, errors = feature_engineer.validate_features(features)
        
        # Assert
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_features_missing_values(self, feature_engineer):
        """Testar validação com valores missing"""
        # Setup
        features = {
            'home_recent_form': None,  # Missing
            'away_recent_form': 0.60,
            'home_four_factors_efg': 0.52
        }
        
        # Execute
        is_valid, errors = feature_engineer.validate_features(features)
        
        # Assert
        assert is_valid is False
        assert len(errors) > 0
        assert 'home_recent_form' in str(errors)
    
    def test_validate_features_lookahead(self, feature_engineer):
        """Testar detecção de look-ahead leakage"""
        # Setup
        features = {
            'home_recent_form': 0.75,
            'final_score': 110  # Isto é look-ahead!
        }
        
        # Execute
        is_valid, errors = feature_engineer.validate_features(features)
        
        # Assert
        assert is_valid is False
        assert any('look-ahead' in str(e).lower() for e in errors)
```

### 2.3 Executar Unit Tests

```bash
# Executar todos os unit tests
pytest tests/unit/ -v

# Executar com coverage
pytest tests/unit/ --cov=app --cov-report=html --cov-report=term

# Executar teste específico
pytest tests/unit/test_features/test_feature_engineer.py::TestFeatureEngineer::test_calculate_recent_form -v

# Executar com filtro
pytest tests/unit/ -k "feature" -v
```

---

## 3. INTEGRATION TESTS

### 3.1 Teste de API

```python
# tests/integration/test_api/test_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Fixture com cliente de teste FastAPI"""
    return TestClient(app)

class TestAPIEndpoints:
    def test_health_check(self, client):
        """Testar endpoint de health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_generate_signals(self, client, mock_model):
        """Testar geração de sinais"""
        response = client.post("/api/v1/signals/generate", json={
            'game_id': '0022400001',
            'current_odds': 2.10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert 'approved' in data
        assert 'edge' in data
        assert 'stake_percent' in data
    
    def test_get_signals_history(self, client):
        """Testar obtenção de histórico de sinais"""
        response = client.get("/api/v1/signals/history?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert 'signals' in data
        assert len(data['signals']) <= 10
```

### 3.2 Teste de Database

```python
# tests/integration/test_database/test_queries.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Game, Signal

@pytest.fixture(scope="module")
def test_db():
    """Fixture com database de teste"""
    engine = create_engine("postgresql://test:test@localhost:5432/vb_test")
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal
    
    Base.metadata.drop_all(bind=engine)

class TestDatabaseQueries:
    def test_insert_and_retrieve_game(self, test_db):
        """Testar inserção e recuperação de jogo"""
        db = test_db()
        
        # Insert
        game = Game(
            game_id='0022400001',
            game_date='2024-01-15',
            home_team_id=1610612740,
            away_team_id=1610612752
        )
        db.add(game)
        db.commit()
        
        # Retrieve
        retrieved = db.query(Game).filter(Game.game_id == '0022400001').first()
        
        assert retrieved is not None
        assert retrieved.home_team_id == 1610612740
        
        db.close()
    
    def test_signal_with_game_relation(self, test_db):
        """Testar relação entre Signal e Game"""
        db = test_db()
        
        # Setup
        game = Game(
            game_id='0022400001',
            game_date='2024-01-15',
            home_team_id=1610612740,
            away_team_id=1610612752
        )
        db.add(game)
        db.commit()
        
        signal = Signal(
            game_id='0022400001',
            edge=0.05,
            stake_percent=0.02,
            status='approved'
        )
        db.add(signal)
        db.commit()
        
        # Test
        retrieved_signal = db.query(Signal).filter(Signal.game_id == '0022400001').first()
        assert retrieved_signal.game.game_id == '0022400001'
        
        db.close()
```

### 3.3 Executar Integration Tests

```bash
# Executar todos os integration tests
pytest tests/integration/ -v

# Executar com database de teste
pytest tests/integration/ --db-url=postgresql://test:test@localhost:5432/vb_test

# Executar em paralelo
pytest tests/integration/ -n auto
```

---

## 4. E2E TESTS

### 4.1 Teste de Pipeline Completo

```python
# tests/e2e/test_full_pipeline.py
import pytest
from datetime import datetime, timedelta
from app.ingestion.nba_ingester import NBAIngester
from app.features.feature_engineer import FeatureEngineer
from app.inference.value_engine import ValueEngine
from app.signals.signal_distributor import SignalDistributor
from app.database import SessionLocal

@pytest.mark.e2e
@pytest.mark.slow
def test_full_pipeline_e2e():
    """
    Teste end-to-end do pipeline completo
    Tempo estimado: 5-10 minutos
    """
    db = SessionLocal()
    
    try:
        # Step 1: Ingestão
        test_date = datetime.now().date() - timedelta(days=7)
        nba_ingester = NBAIngester(db)
        games = nba_ingester.ingest_games(test_date)
        assert len(games) > 0, "Nenhum jogo ingerido"
        
        # Step 2: Features
        engineer = FeatureEngineer(db)
        for game in games[:3]:  # Testar apenas 3 jogos
            features = engineer.generate_features(game['game_id'])
            assert features is not None
            engineer.persist_features(features)
        
        # Step 3: Inferência
        engine = ValueEngine()
        test_game = games[0]
        test_odds = 2.10
        signal = engine.evaluate_opportunity(test_game['game_id'], test_odds)
        assert 'approved' in signal
        
        # Step 4: Distribuição (se aprovado)
        if signal['approved']:
            distributor = SignalDistributor()
            # Mock Telegram em testes
            distributor.telegram_bot.send_signal = lambda x: None
            
            distributor.distribute_signal(signal)
            print(f"✓ Sinal distribuído: {signal['game_id']}")
        
        print("✓ Teste E2E completado com sucesso")
        
    finally:
        db.close()
```

### 4.2 Executar E2E Tests

```bash
# Executar E2E tests
pytest tests/e2e/ -v -m e2e

# Executar com timeout
pytest tests/e2e/ -v -m e2e --timeout=600

# Executar apenas testes marcados como slow
pytest tests/e2e/ -v -m slow
```

---

## 5. CONFIGURAÇÃO DO PYTEST

### 5.1 pytest.ini

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
    --tb=short
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    requires_db: Tests requiring database
    requires_api: Tests requiring external API
```

### 5.2 conftest.py

```python
# tests/conftest.py
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app
from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def test_db():
    """Setup database de teste para toda a sessão"""
    engine = create_engine(os.getenv("TEST_DATABASE_URL"))
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db):
    """Setup sessão de database para cada teste"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()

@pytest.fixture
def client():
    """Setup cliente de teste FastAPI"""
    return TestClient(app)

@pytest.fixture
def mock_betfair_api(mocker):
    """Mock da API Betfair para testes"""
    mock_response = {
        'market_id': '1.12345678',
        'odds': 2.10,
        'liquidity': 5000
    }
    
    mocker.patch('app.ingestion.betfair_ingester.BetfairIngester.get_odds', return_value=mock_response)
    return mock_response
```

---

## 6. COVERAGE TARGETS

### 6.1 Metas

| Tipo de Código | Coverage Alvo |
|----------------|---------------|
| Core logic (models, features) | > 90% |
| API endpoints | > 85% |
| Database queries | > 80% |
| Utilities | > 75% |
| Overall | > 80% |

### 6.2 Relatório de Coverage

```bash
# Gerar relatório HTML
pytest --cov=app --cov-report=html

# Abrir relatório
# Abre htmlcov/index.html no browser
```

---

## 7. CONTÍNUO INTEGRATION

### 7.1 Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml

  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest tests/unit/
        language: system
        pass_filenames: false
        always_run: true
```

### 7.2 Instalar Pre-commit

```bash
pip install pre-commit
pre-commit install
```

---

## 8. CHECKLIST DE TESTES

### Pré-Commit
- [ ] Todos os unit tests passam
- [ ] Coverage > 80%
- [ ] Code formatting (black, isort)
- [ ] Linting (flake8) sem erros

### PR
- [ ] Todos os tests passam
- [ ] Novos testes adicionados
- [ ] Coverage não diminuiu
- [ ] Integration tests passam

### Release
- [ ] Todos os tests passam
- [ ] E2E tests passam
- [ ] Performance tests passam
- [ ] Security scans passam

---

## 9. LINKS CRUZADOS

- [[00_Master_Index/INTEGRATION_GUIDE]] ← Integração
- [[00_Master_Index/GETTING_STARTED]] ← Setup
- [[05_Machine_Learning/XGBoost_BASELINE]] → Modelo
- [[06_Backtesting/INDEX]] → Backtesting
