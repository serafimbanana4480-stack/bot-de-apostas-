# Guia de Integração End-to-End

**ID:** `INT-001` | **Fase:** #phase/1 | **Owner:** Lead Data Engineer | **Status:** #status/active

---

## 1. ARQUITETURA DE INTEGRAÇÃO

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA INGESTION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  NBA API → Raw Data → PostgreSQL (Bronze)                       │
│  Betfair API → Odds → PostgreSQL (Bronze)                       │
│  ESPN RSS → Injuries → PostgreSQL (Bronze)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATA TRANSFORMATION LAYER                    │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL (Bronze) → Clean → PostgreSQL (Silver)             │
│  Feature Engineering → Features → PostgreSQL (Gold)            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MODEL INFERENCE LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  Features + Odds → XGBoost Model → Probabilities                │
│  Probabilities + Edge → Meta-Model → Filtered Signals           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SIGNAL DISTRIBUTION LAYER                     │
├─────────────────────────────────────────────────────────────────┤
│  Filtered Signals → Redis Queue → Telegram Bot                  │
│  Filtered Signals → PostgreSQL (Bets Table)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MONITORING LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  Metrics → Prometheus → Grafana Dashboards                       │
│  Alerts → Telegram/Email                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. FLUXO DE DADOS COMPLETO

### 2.1 Ingestão Diária (Automática)

```python
# scripts/daily_ingestion.py
from app.ingestion.nba_ingester import NBAIngester
from app.ingestion.betfair_ingester import BetfairIngester
from app.ingestion.injury_ingester import InjuryIngester
from app.database import SessionLocal

def run_daily_ingestion():
    """
    Executado automaticamente em batch a cada 2 horas em dias de jogo NBA
    Horários: 08:00, 10:00, 12:00, 14:00, 16:00 UTC
    """
    db = SessionLocal()
    
    try:
        # 1. Ingerir jogos e resultados NBA
        nba_ingester = NBAIngester(db)
        games = nba_ingester.ingest_games()
        print(f"Ingeridos {len(games)} jogos NBA")
        
        # 2. Ingerir odds Betfair
        betfair_ingester = BetfairIngester(db)
        odds = betfair_ingester.ingest_odds()
        print(f"Ingeridas {len(odds)} odds Betfair")
        
        # 3. Ingerir lesões
        injury_ingester = InjuryIngester(db)
        injuries = injury_ingester.ingest_injuries()
        print(f"Ingeridas {len(injuries)} atualizações de lesões")
        
        # 4. Validar qualidade dos dados
        from app.validation.data_validator import DataValidator
        validator = DataValidator(db)
        validation_result = validator.validate_daily_ingestion()
        
        if not validation_result['passed']:
            print(f"WARNING: Validação falhou: {validation_result['errors']}")
            # Enviar alerta
        
        db.commit()
        print("Ingestão diária completada com sucesso")
        
    except Exception as e:
        db.rollback()
        print(f"ERRO na ingestão: {e}")
        # Enviar alerta crítico
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_daily_ingestion()
```

### 2.2 Pipeline de Features (Batch)

```python
# scripts/generate_features.py
from app.features.feature_engineer import FeatureEngineer
from app.database import SessionLocal

def generate_features_for_date(target_date):
    """
    Gera features para todos os jogos de uma data específica
    """
    db = SessionLocal()
    
    try:
        engineer = FeatureEngineer(db)
        
        # 1. Obter jogos da data
        games = engineer.get_games_for_date(target_date)
        print(f"Processando {len(games)} jogos para {target_date}")
        
        # 2. Gerar features para cada jogo
        for game in games:
            features = engineer.generate_features(game['game_id'])
            
            # 3. Validar features
            if engineer.validate_features(features):
                # 4. Persistir no Feature Store
                engineer.persist_features(features)
            else:
                print(f"WARNING: Features inválidas para jogo {game['game_id']}")
        
        db.commit()
        print(f"Features geradas para {len(games)} jogos")
        
    except Exception as e:
        db.rollback()
        print(f"ERRO na geração de features: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    target_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    generate_features_for_date(target_date)
```

### 2.3 Motor de Decisão (Inferência)

```python
# app/inference/value_engine.py
from app.models.xgboost_model import XGBoostModel
from app.models.meta_model import MetaModel
from app.risk.kelly_calculator import KellyCalculator
from app.database import SessionLocal

class ValueEngine:
    def __init__(self):
        self.primary_model = XGBoostModel.load("models/xgboost_baseline_v1.pkl")
        self.meta_model = MetaModel.load("models/meta_model_v1.pkl")
        self.kelly_calc = KellyCalculator()
    
    def evaluate_opportunity(self, game_id, current_odds):
        """
        Avalia uma oportunidade de aposta
        """
        db = SessionLocal()
        
        try:
            # 1. Obter features do jogo
            features = self._get_features(game_id, db)
            
            # 2. Inferência do modelo primário
            prob_raw = self.primary_model.predict_proba(features)
            
            # 3. Calibração isotónica
            prob_calibrated = self._calibrate_probability(prob_raw, features)
            
            # 4. Calcular edge
            edge = (prob_calibrated * current_odds) - 1
            
            # 5. Se edge > threshold, chamar meta-modelo
            if edge > 0.04:  # 4% threshold
                meta_features = self._create_meta_features(
                    prob_calibrated, edge, features
                )
                meta_prob = self.meta_model.predict_proba(meta_features)
                
                # 6. Decisão final
                if meta_prob > 0.6:  # 60% confiança meta-modelo
                    stake = self.kelly_calc.calculate_stake(
                        prob_calibrated, current_odds
                    )
                    
                    return {
                        'approved': True,
                        'game_id': game_id,
                        'probability': prob_calibrated,
                        'edge': edge,
                        'stake_percent': stake,
                        'odds': current_odds
                    }
            
            return {'approved': False, 'reason': 'Edge insufficient or meta-model rejected'}
            
        finally:
            db.close()
    
    def _get_features(self, game_id, db):
        """Obtém features do Feature Store"""
        # Implementação
        pass
    
    def _calibrate_probability(self, prob_raw, features):
        """Aplica calibração isotónica por regime"""
        # Implementação
        pass
    
    def _create_meta_features(self, prob, edge, features):
        """Cria features para meta-modelo"""
        # Implementação
        pass
```

### 2.4 Distribuição de Sinais

```python
# app/signals/signal_distributor.py
import redis
import json
from app.database import SessionLocal
from app.telegram.bot import TelegramBot

class SignalDistributor:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
        self.telegram_bot = TelegramBot()
    
    def distribute_signal(self, signal):
        """
        Distribui sinal aprovado para múltiplos canais
        """
        db = SessionLocal()
        
        try:
            # 1. Persistir no PostgreSQL
            self._persist_signal(signal, db)
            
            # 2. Publicar no Redis (para consumidores)
            self.redis_client.lpush('signals:pending', json.dumps(signal))
            
            # 3. Enviar via Telegram
            message = self._format_telegram_message(signal)
            self.telegram_bot.send_signal(message)
            
            # 4. Log para monitorização
            self._log_signal_distributed(signal)
            
            db.commit()
            print(f"Sinal distribuído: {signal['game_id']}")
            
        except Exception as e:
            db.rollback()
            print(f"ERRO na distribuição: {e}")
            raise
        finally:
            db.close()
    
    def _persist_signal(self, signal, db):
        """Persiste sinal na base de dados"""
        # Implementação SQL
        pass
    
    def _format_telegram_message(self, signal):
        """Formata mensagem para Telegram"""
        return f"""
🏀 NBA Signal - {signal['game_id']}
📊 Edge: {signal['edge']:.2%}
💰 Stake: {signal['stake_percent']:.2%} of bankroll
🎯 Odd: {signal['odds']:.2f}
"""
    
    def _log_signal_distributed(self, signal):
        """Log para Prometheus"""
        # Implementação metrics
        pass
```

---

## 3. ORQUESTRAÇÃO COM PREFECT

### 3.1 Definição de Flow

```python
# app/orchestration/prefect_flows.py
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import datetime, timedelta
import hashlib

@task(cache_key_fn=task_input_hash)
def ingest_nba_data(date: datetime):
    """Task de ingestão de dados NBA"""
    from app.ingestion.nba_ingester import NBAIngester
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        ingester = NBAIngester(db)
        games = ingester.ingest_games(date)
        return len(games)
    finally:
        db.close()

@task(cache_key_fn=task_input_hash)
def generate_features(date: datetime):
    """Task de geração de features"""
    from app.features.feature_engineer import FeatureEngineer
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        engineer = FeatureEngineer(db)
        games = engineer.get_games_for_date(date)
        for game in games:
            features = engineer.generate_features(game['game_id'])
            engineer.persist_features(features)
        return len(games)
    finally:
        db.close()

@task
def evaluate_and_distribute_signals(date: datetime):
    """Task de avaliação e distribuição de sinais"""
    from app.inference.value_engine import ValueEngine
    from app.signals.signal_distributor import SignalDistributor
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        engine = ValueEngine()
        distributor = SignalDistributor()
        
        games = db.query(Game).filter(Game.game_date == date).all()
        signals_approved = 0
        
        for game in games:
            odds = get_current_betfair_odds(game.game_id)
            signal = engine.evaluate_opportunity(game.game_id, odds)
            
            if signal['approved']:
                distributor.distribute_signal(signal)
                signals_approved += 1
        
        return signals_approved
    finally:
        db.close()

@flow(name="Daily Value Betting Pipeline")
def daily_pipeline(date: datetime = None):
    """Flow principal diário"""
    if date is None:
        date = datetime.now().date()
    
    # Executar tasks em sequência
    games_count = ingest_nba_data(date)
    features_count = generate_features(date)
    signals_count = evaluate_and_distribute_signals(date)
    
    return {
        'games': games_count,
        'features': features_count,
        'signals': signals_count
    }

# Schedule para executar às 08:00 em dias de jogo
from prefect.schedules import Schedule
from prefect.orion.schemas.schedules import IntervalSchedule

schedule = Schedule(
    clock=clock,
    interval=timedelta(days=1),
    anchor_date=datetime(2024, 1, 1, 8, 0),  # 08:00
)
```

### 3.2 Deploy do Flow

```bash
# Registrar flow no Prefect
python -m app.orchestration.prefect_flows

# Agendar execução
prefect deployment build daily_pipeline:main \
  --name "daily-production" \
  --interval 86400 \
  --params 'date: null'

# Iniciar agente
prefect agent start --pool "production-pool"
```

---

## 4. INTEGRAÇÃO DE MONITORIZAÇÃO

### 4.1 Exportar Métricas para Prometheus

```python
# app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Métricas de negócio
signals_generated = Counter('vb_signals_generated_total', 'Total signals generated', ['status'])
bets_placed = Counter('vb_bets_placed_total', 'Total bets placed')
pnl_total = Gauge('vb_pnl_total_eur', 'Total PnL in EUR')
clv_average = Gauge('vb_clv_average_percent', 'Average CLV percentage')

# Métricas técnicas
ingestion_duration = Histogram('vb_ingestion_duration_seconds', 'Ingestion duration')
inference_duration = Histogram('vb_inference_duration_seconds', 'Inference duration')
api_requests = Counter('vb_api_requests_total', 'Total API requests', ['method', 'endpoint'])

# Métricas de sistema
db_connections = Gauge('vb_db_connections_active', 'Active database connections')
redis_operations = Counter('vb_redis_operations_total', 'Redis operations', ['operation'])

class MetricsMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            start_time = time.time()
            
            # Incrementar contador de requests
            method = scope['method']
            path = scope['path']
            api_requests.labels(method=method, endpoint=path).inc()
            
            # Process request
            await self.app(scope, receive, send)
            
            # Registrar duração
            duration = time.time() - start_time
            # TODO: Adicionar histogram de duração
        else:
            await self.app(scope, receive, send)
```

### 4.2 Integração no FastAPI

```python
# app/main.py
from fastapi import FastAPI
from app.monitoring.metrics import MetricsMiddleware

app = FastAPI(title="Value Betting System")

# Adicionar middleware de métricas
app.add_middleware(MetricsMiddleware)

@app.get("/metrics")
async def metrics():
    """Endpoint para Prometheus scraper"""
    from prometheus_client import generate_latest
    from prometheus_client.core import REGISTRY
    
    return Response(
        generate_latest(REGISTRY),
        media_type="text/plain"
    )
```

---

## 5. TESTE DE INTEGRAÇÃO END-TO-END

### 5.1 Script de Teste

```python
# tests/test_integration_e2e.py
import pytest
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.ingestion.nba_ingester import NBAIngester
from app.features.feature_engineer import FeatureEngineer
from app.inference.value_engine import ValueEngine
from app.signals.signal_distributor import SignalDistributor

@pytest.mark.integration
def test_full_pipeline_e2e():
    """
    Teste completo do pipeline de ingestão a distribuição de sinais
    """
    db = SessionLocal()
    
    try:
        # Setup: Data de teste
        test_date = datetime.now().date() - timedelta(days=1)
        
        # Step 1: Ingestão
        nba_ingester = NBAIngester(db)
        games = nba_ingester.ingest_games(test_date)
        assert len(games) > 0, "Nenhum jogo ingerido"
        
        # Step 2: Features
        engineer = FeatureEngineer(db)
        for game in games[:3]:  # Testar apenas 3 jogos
            features = engineer.generate_features(game['game_id'])
            assert features is not None, f"Features nulas para jogo {game['game_id']}"
            engineer.persist_features(features)
        
        # Step 3: Inferência
        engine = ValueEngine()
        test_game = games[0]
        test_odds = 2.10  # Odd simulada
        
        signal = engine.evaluate_opportunity(test_game['game_id'], test_odds)
        assert 'approved' in signal, "Sinal não tem campo 'approved'"
        
        # Step 4: Distribuição (apenas se aprovado)
        if signal['approved']:
            distributor = SignalDistributor()
            # Não enviar Telegram real em testes
            distributor.telegram_bot.send_signal = lambda x: None
            
            distributor.distribute_signal(signal)
            print(f"Sinal distribuído: {signal}")
        
        print("Teste E2E completado com sucesso")
        
    finally:
        db.close()
```

### 5.2 Executar Teste

```bash
# Executar teste de integração
pytest tests/test_integration_e2e.py -v

# Com coverage
pytest tests/test_integration_e2e.py --cov=app --cov-report=html
```

---

## 6. CHECKLIST DE INTEGRAÇÃO

### Pré-Produção
- [ ] Todas as componentes conectadas e testadas
- [ ] Pipeline Prefect registrado e agendado
- [ ] Métricas Prometheus exportadas
- [ ] Dashboards Grafana configurados
- [ ] Alertas Telegram funcionais
- [ ] Backup automático configurado
- [ ] Logs estruturados implementados
- [ ] Testes E2E passando

### Produção
- [ ] VPS provisionado e configurado
- [ ] Docker Compose ou Kubernetes deploy
- [ ] CI/CD pipeline configurado
- [ ] Domínio e SSL configurados
- [ ] Monitorização 24/7 ativa
- [ ] Runbooks de incidentes preparados
- [ ] Equela de on-call definida

---

## 7. TROUBLESHOOTING

### 7.1 Pipeline Falha na Ingestão

```bash
# Ver logs do Prefect
prefect flow-run ls --name "daily-production"

# Ver logs específicos
prefect flow-run inspect <flow-run-id>

# Re-executar manualmente
prefect flow-run execute <flow-run-id>
```

### 7.2 Features Não Geram

```bash
# Verificar se dados existem
python scripts/verify_data.py --date 2024-01-15

# Ver logs de feature engineering
tail -f logs/feature_engineering.log

# Testar manualmente
python scripts/test_features.py --game-id 0022400001
```

### 7.3 Sinais Não Chegam ao Telegram

```bash
# Verificar se sinais estão no Redis
redis-cli LRANGE signals:pending 0 10

# Verificar logs do bot
tail -f logs/telegram_bot.log

# Testar bot manualmente
python scripts/test_telegram.py
```

---

## 8. LINKS CRUZADOS

- [[00_Master_Index/GETTING_STARTED]] ← Setup inicial
- [[04_Data_Engineering/PIPELINE_ETL_NBA]] → Pipeline detalhado
- [[05_Machine_Learning/XGBoost_BASELINE]] → Modelo
- [[07_Value_Detection/MOTOR_EDGE]] → Motor de decisão
- [[19_Telegram_System/INDEX]] → Telegram bot
- [[10_Monitoring/ARQUITETURA_MONITORIZACAO]] → Monitorização
