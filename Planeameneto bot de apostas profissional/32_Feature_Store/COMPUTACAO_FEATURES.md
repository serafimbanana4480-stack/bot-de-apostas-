# COMPUTACAO_FEATURES — Computação de Features (Batch vs Streaming)

**ID:** `FEAT-003` | **Fase:** #phase/1-6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir a estratégia de computação de features, equilibrando entre processamento batch (para treino e backtest) e streaming (para inferência em tempo real). Garantir que features são calculadas de forma eficiente, consistente e com latência apropriada para cada caso de uso.

---

## 2. CONTEXTO

Em value betting, diferentes casos de uso requerem diferentes estratégias de computação:

**Batch Computing:**
- Treino de modelos (histórico completo)
- Backtesting de estratégias
- Análise exploratória
- Recálculo de features com novas fórmulas

**Streaming Computing:**
- Inferência em tempo real (previsões antes do jogo)
- Atualização de features com novos dados
- Monitorização de eventos em tempo real
- Alertas baseados em features

O desafio é manter consistência entre ambos os modos enquanto otimiza para cada caso de uso.

---

## 3. BATCH COMPUTING

### 3.1 Casos de Uso

| Caso de Uso | Frequência | Latência Aceitável | Volume |
|-------------|------------|-------------------|--------|
| Treino de modelos | Mensal/Semanal | Minutos-Horas | TB |
| Backtesting | Sob demanda | Minutos-Horas | GB-TB |
| Recálculo de features | Diário | Horas | GB |
| Análise exploratória | Ad-hoc | Segundos-Minutos | GB |

### 3.2 Arquitetura Batch

```
┌─────────────────────────────────────────────────────────────┐
│                    BATCH PIPELINE                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Schedule   │───→│  Orquestra  │───→│  Compute    │    │
│  │  (Cron)     │    │  (Prefect)  │    │  (Python)   │    │
│  └─────────────┘    └─────────────┘    └──────┬──────┘    │
│                                            │               │
│                                            ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Validate   │←───│  Transform  │←───│  Extract    │    │
│  │ (Great Exp) │    │  (Pandas)   │    │ (PostgreSQL)│    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                                            │               │
│                                            ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Archive    │←───│  Write      │←───│  Aggregate  │    │
│  │  (Parquet)  │    │  (Feature   │    │  (Window)   │    │
│  │             │    │   Store)    │    │             │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Implementação com Prefect

```python
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta
import pandas as pd
import psycopg2

@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(hours=1))
def extract_raw_data(table: str, date_range: tuple) -> pd.DataFrame:
    """Extrai dados brutos de uma tabela."""
    query = f"""
        SELECT * FROM {table}
        WHERE game_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
    """
    conn = psycopg2.connect(DATABASE_URL)
    return pd.read_sql(query, conn)

@task
def transform_rolling_stats(df: pd.DataFrame, window: int, halflife: float) -> pd.DataFrame:
    """Calcula estatísticas rolling com decaimento exponencial."""
    def decayed_mean(series, halflife):
        weights = np.array([0.5**(i/halflife) for i in range(len(series))])
        weights = weights / weights.sum()
        return np.average(series, weights=weights)
    
    result = df.groupby('team_id').apply(
        lambda x: x.rolling(window).apply(
            lambda y: decayed_mean(y, halflife)
        )
    )
    return result

@task
def aggregate_features(features_list: list) -> pd.DataFrame:
    """Agrega múltiplas features num único DataFrame."""
    return pd.concat(features_list, axis=1)

@task
def validate_features(df: pd.DataFrame, validation_rules: dict) -> bool:
    """Valida features contra regras de qualidade."""
    for col, rules in validation_rules.items():
        if 'min' in rules and (df[col] < rules['min']).any():
            raise ValueError(f"{col} has values below minimum")
        if 'max' in rules and (df[col] > rules['max']).any():
            raise ValueError(f"{col} has values above maximum")
        if 'not_null' in rules and df[col].isnull().any():
            raise ValueError(f"{col} has null values")
    return True

@task
def write_to_feature_store(df: pd.DataFrame, table: str):
    """Escreve features para Offline Store."""
    conn = psycopg2.connect(DATABASE_URL)
    df.to_sql(table, conn, if_exists='append', index=False)

@flow(name="compute_batch_features")
def compute_batch_features_flow(date_range: tuple):
    """Flow principal de computação batch."""
    
    # Extrair dados brutos
    games_df = extract_raw_data("clean_games", date_range)
    stats_df = extract_raw_data("clean_team_game_stats", date_range)
    odds_df = extract_raw_data("clean_odds", date_range)
    
    # Transformar features
    home_win_rate = transform_rolling_stats(games_df, window=20, halflife=5)
    efg_pct = transform_rolling_stats(stats_df, window=20, halflife=5)
    market_features = transform_market_features(odds_df)
    
    # Agregar
    all_features = aggregate_features([home_win_rate, efg_pct, market_features])
    
    # Validar
    validation_rules = get_validation_rules()
    validate_features(all_features, validation_rules)
    
    # Escrever
    write_to_feature_store(all_features, "feature_store.features")
    
    # Sincronizar para Online Store
    sync_to_online_store(all_features)
```

### 3.4 Otimizações Batch

**1. Partitioning:**
```python
# Processar por partição (ex: por mês)
for month in get_months_in_range(date_range):
    month_data = extract_raw_data(table, month)
    month_features = compute_features(month_data)
    write_to_feature_store(month_features)
```

**2. Parallel Processing:**
```python
from concurrent.futures import ThreadPoolExecutor

def compute_feature_parallel(feature_configs):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(compute_single_feature, config)
            for config in feature_configs
        ]
        results = [f.result() for f in futures]
    return results
```

**3. Incremental Updates:**
```python
# Apenas reprocessar dados novos
last_processed = get_last_processed_timestamp()
new_data = extract_data_since(last_processed)
incremental_features = compute_features(new_data)
append_to_feature_store(incremental_features)
```

**4. Materialized Views:**
```sql
-- Criar view pré-agregada para queries frequentes
CREATE MATERIALIZED VIEW feature_store.team_form_summary AS
SELECT 
    team_id,
    AVG(home_win_rate_decay5) as avg_win_rate,
    STDDEV(home_win_rate_decay5) as std_win_rate,
    COUNT(*) as games_count
FROM feature_store.features
WHERE feature_id = 'home_win_rate_decay5'
GROUP BY team_id;

-- Refresh diariamente
REFRESH MATERIALIZED VIEW feature_store.team_form_summary;
```

---

## 4. STREAMING COMPUTING

### 4.1 Casos de Uso

| Caso de Uso | Frequência | Latência Requerida | Volume |
|-------------|------------|-------------------|--------|
| Inferência em tempo real | Por jogo | <1 segundo | KB |
| Atualização de odds | Minutos | <1 minuto | MB |
| Monitorização de lesões | Horas | <1 hora | MB |
| Alertas de anomalias | Contínuo | Segundos | MB |

### 4.2 Arquitetura Streaming

```
┌─────────────────────────────────────────────────────────────┐
│                   STREAMING PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Event      │───→│  Ingest     │───→│  Process    │    │
│  │  Source     │    │  (Kafka/    │    │  (Flink/    │    │
│  │  (NBA API)  │    │   Redis)    │    │   Streams)  │    │
│  └─────────────┘    └─────────────┘    └──────┬──────┘    │
│                                            │               │
│                                            ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Stateful   │←───│  Windowed   │←───│  Transform  │    │
│  │  Aggregation│    │  Operator  │    │  Operator   │    │
│  │  (Redis)    │    │            │    │             │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                                            │               │
│                                            ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Alert      │←───│  Write      │←───│  Validate   │    │
│  │  (Slack)    │    │  (Online    │    │  (Real-time)│    │
│  │             │    │   Store)    │    │             │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Implementação com Python Streams

```python
import redis
from datetime import datetime, timedelta
import json
from collections import deque

class StreamingFeatureComputer:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.state = {}  # Estado em memória para agregações
        
    def process_game_event(self, event: dict):
        """Processa um evento de jogo em tempo real."""
        game_id = event['game_id']
        home_team = event['home_team']
        away_team = event['away_team']
        
        # Atualizar estado rolling
        self._update_rolling_state(home_team, event)
        self._update_rolling_state(away_team, event)
        
        # Computar features
        features = {
            'home_win_rate_decay5': self._compute_win_rate(home_team),
            'away_win_rate_decay5': self._compute_win_rate(away_team),
            'home_efg_pct_decay5': self._compute_efg_pct(home_team),
            'away_efg_pct_decay5': self._compute_efg_pct(away_team),
        }
        
        # Escrever para Online Store
        self._write_to_online_store(game_id, features)
        
        return features
    
    def _update_rolling_state(self, team_id: str, event: dict):
        """Atualiza estado rolling para uma equipa."""
        if team_id not in self.state:
            self.state[team_id] = {
                'games': deque(maxlen=20),
                'stats': deque(maxlen=20)
            }
        
        # Adicionar jogo ao estado
        self.state[team_id]['games'].append({
            'date': event['game_date'],
            'is_home': event['is_home'],
            'won': event['won']
        })
        
        # Persistir estado no Redis
        self.redis.setex(
            f"state:rolling:{team_id}",
            86400,  # 24 horas
            json.dumps(self.state[team_id])
        )
    
    def _compute_win_rate(self, team_id: str, halflife: int = 5) -> float:
        """Computa win rate com decaimento exponencial."""
        if team_id not in self.state:
            return 0.5
        
        games = list(self.state[team_id]['games'])
        if len(games) < 5:  # Mínimo de jogos
            return 0.5
        
        weights = np.array([0.5**(i/halflife) for i in range(len(games))])
        weights = weights / weights.sum()
        
        wins = np.array([g['won'] for g in games])
        return np.average(wins, weights=weights)
    
    def _compute_efg_pct(self, team_id: str, halflife: int = 5) -> float:
        """Computa eFG% com decaimento exponencial."""
        # Implementação similar
        pass
    
    def _write_to_online_store(self, entity_id: str, features: dict):
        """Escreve features para Online Store."""
        key = f"entity:features:{entity_id}:{datetime.now().isoformat()}"
        self.redis.setex(
            key,
            3600,  # 1 hora TTL
            json.dumps(features)
        )
```

### 4.4 Implementação com Kafka (Opcional)

Para escalabilidade maior:

```python
from kafka import KafkaConsumer, KafkaProducer
import json

class KafkaFeatureProcessor:
    def __init__(self, bootstrap_servers: str):
        self.consumer = KafkaConsumer(
            'nba_game_events',
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        self.feature_computer = StreamingFeatureComputer(redis_client)
    
    def process_events(self):
        """Processa eventos em loop contínuo."""
        for message in self.consumer:
            event = message.value
            try:
                features = self.feature_computer.process_game_event(event)
                
                # Publicar features para downstream
                self.producer.send(
                    'computed_features',
                    value={
                        'game_id': event['game_id'],
                        'features': features,
                        'timestamp': datetime.now().isoformat()
                    }
                )
                
            except Exception as e:
                logger.error(f"Error processing event: {e}")
```

---

## 5. CONSISTÊNCIA BATCH ↔ STREAMING

### 5.1 Desafios de Consistência

- **Resultados diferentes:** Batch e streaming podem produzir valores ligeiramente diferentes
- **Timing:** Batch usa snapshots, streaming usa eventos contínuos
- **Estado:** Batch tem estado completo, streaming tem estado parcial
- **Janelas:** Batch pode usar janelas fixas, streaming usa janelas deslizantes

### 5.2 Estratégias de Consistência

**1. Mesma Lógica:**
```python
# Compartilhar lógica entre batch e streaming
class FeatureCalculator:
    @staticmethod
    def win_rate_decay(games: list, halflife: int = 5) -> float:
        """Lógica compartilhada para batch e streaming."""
        weights = np.array([0.5**(i/halflife) for i in range(len(games))])
        weights = weights / weights.sum()
        wins = np.array([g['won'] for g in games])
        return np.average(wins, weights=weights)

# Usar em batch
batch_features = FeatureCalculator.win_rate_decay(batch_games)

# Usar em streaming
streaming_features = FeatureCalculator.win_rate_decay(streaming_games)
```

**2. Reconciliation:**
```python
def reconcile_batch_streaming(feature_id: str, date: str):
    """Compara resultados batch vs streaming."""
    batch_value = get_batch_feature(feature_id, date)
    streaming_value = get_streaming_feature(feature_id, date)
    
    diff = abs(batch_value - streaming_value)
    
    if diff > 0.01:  # Threshold
        alert(f"Significant difference in {feature_id}: {diff}")
        log_discrepancy(feature_id, date, batch_value, streaming_value)
```

**3. Hybrid Approach:**
```python
# Streaming para atualizações rápidas, Batch para correções
def get_feature_hybrid(feature_id: str, entity_id: str, timestamp: str):
    """Tenta streaming primeiro, fallback para batch."""
    # Tentar Online Store (streaming)
    streaming_value = redis_client.get(f"feature:{feature_id}:{entity_id}")
    
    if streaming_value is not None:
        return json.loads(streaming_value)
    
    # Fallback para Offline Store (batch)
    batch_value = query_offline_store(feature_id, entity_id, timestamp)
    
    if batch_value is not None:
        # Cache para futuras consultas
        redis_client.setex(
            f"feature:{feature_id}:{entity_id}",
            3600,
            json.dumps(batch_value)
        )
        return batch_value
    
    raise FeatureNotFoundError(feature_id, entity_id, timestamp)
```

---

## 6. PERFORMANCE E OTIMIZAÇÃO

### 6.1 Métricas de Performance

| Métrica | Batch | Streaming | Target |
|---------|-------|-----------|--------|
| Latência de computação | Minutos | Segundos | <5s (streaming) |
| Throughput | GB/hora | MB/minuto | >1000 features/s |
| Uso de CPU | 80% | 40% | <90% |
| Uso de memória | 16GB | 4GB | <32GB |

### 6.2 Otimizações

**1. Vectorization:**
```python
# Ruim: Loop
results = []
for i in range(len(df)):
    results.append(complex_calculation(df.iloc[i]))

# Bom: Vectorized
results = df.apply(complex_calculation, axis=1)

# Melhor: NumPy
results = np.vectorize(complex_calculation)(df.values)
```

**2. Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_lookup(team_id: str) -> dict:
    """Cache lookups frequentes."""
    return query_database(team_id)
```

**3. Lazy Evaluation:**
```python
# Usar generators em vez de listas
def process_large_dataset(data):
    for item in data:
        yield transform(item)  # Não carrega tudo em memória

# Processar em chunks
for chunk in pd.read_csv('large_file.csv', chunksize=10000):
    process_chunk(chunk)
```

**4. Parallel Computing:**
```python
from multiprocessing import Pool

def parallel_compute(features_config):
    with Pool(processes=4) as pool:
        results = pool.map(compute_single_feature, features_config)
    return results
```

---

## 7. MONITORIZAÇÃO DE COMPUTAÇÃO

### 7.1 Métricas a Monitorizar

```python
class ComputationMonitor:
    def __init__(self):
        self.metrics = {
            'batch_jobs_completed': 0,
            'batch_jobs_failed': 0,
            'batch_avg_duration': 0,
            'streaming_events_processed': 0,
            'streaming_events_failed': 0,
            'streaming_avg_latency': 0,
            'feature_compute_time': {},
            'feature_error_rate': {}
        }
    
    def record_batch_job(self, duration: float, success: bool):
        """Registra métricas de job batch."""
        if success:
            self.metrics['batch_jobs_completed'] += 1
        else:
            self.metrics['batch_jobs_failed'] += 1
        
        # Atualizar média móvel
        n = self.metrics['batch_jobs_completed']
        self.metrics['batch_avg_duration'] = (
            (self.metrics['batch_avg_duration'] * (n-1) + duration) / n
        )
    
    def record_streaming_event(self, latency: float, success: bool):
        """Registra métricas de evento streaming."""
        self.metrics['streaming_events_processed'] += 1
        if not success:
            self.metrics['streaming_events_failed'] += 1
        
        n = self.metrics['streaming_events_processed']
        self.metrics['streaming_avg_latency'] = (
            (self.metrics['streaming_avg_latency'] * (n-1) + latency) / n
        )
```

### 7.2 Alertas

```python
def setup_alerts():
    """Configura alertas para problemas de computação."""
    
    # Alerta se job batch falhar
    alert_on_condition(
        condition=lambda: monitor.metrics['batch_jobs_failed'] > 0,
        message="Batch job failed",
        severity="HIGH"
    )
    
    # Alerta se latência streaming > 5s
    alert_on_condition(
        condition=lambda: monitor.metrics['streaming_avg_latency'] > 5,
        message="Streaming latency too high",
        severity="MEDIUM"
    )
    
    # Alerta se taxa de erro > 5%
    alert_on_condition(
        condition=lambda: calculate_error_rate() > 0.05,
        message="Feature computation error rate too high",
        severity="HIGH"
    )
```

---

## 8. BOAS PRÁTICAS

### 8.1 Batch

- **Processar em ordem cronológica** para evitar problemas de temporalidade
- **Validar antes de escrever** para evitar dados corrompidos
- **Usar transações** para garantir atomicidade
- **Archivar dados intermediários** para debugging
- **Documentar dependências** entre features

### 8.2 Streaming

- **Manter estado mínimo** para reduzir latência
- **Usar TTL apropriado** para evitar memória infinita
- **Implementar backpressure** para evitar overload
- **Log eventos de erro** para troubleshooting
- **Testar com dados históricos** antes de produção

### 8.3 Geral

- **Isolar lógica de computação** da infraestrutura
- **Versionar código de computação** junto com features
- **Testar em staging** antes de produção
- **Monitorizar continuamente** performance e qualidade
- **Documentar edge cases** e assumptions

---

## 9. BACKLOG TÉCNICO

- [ ] Implementar pipeline batch com Prefect
- [ ] Criar sistema de estado streaming com Redis
- [ ] Implementar reconciliação batch/streaming
- [ ] Adicionar parallel computing para batch
- [ ] Implementar materialized views para queries frequentes
- [ ] Criar sistema de monitorização de computação
- [ ] Implementar alertas automáticos
- [ ] Adicionar caching inteligente
- [ ] Implementar incremental updates
- [ ] Criar dashboard de performance

---

## 10. LINKS CRUZADOS

- [[32_Feature_Store/INDEX]] ← Secção mãe
- [[32_Feature_Store/ARQUITETURA_FEATURE_STORE]] → Arquitetura geral
- [[32_Feature_Store/FEATURES_COMPLETAS]] → Catálogo de features específicas
- [[32_Feature_Store/GESTAO_VERSOES]] → Gestão de versões
- [[32_Feature_Store/SERVICO_FEATURES]] → API de serviço de features
- [[04_Data_Engineering/INDEX]] → Fontes de dados
- [[05_Machine_Learning/INDEX]] → Consumidores das features