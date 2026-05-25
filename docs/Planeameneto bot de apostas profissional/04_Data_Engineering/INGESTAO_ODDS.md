# INGESTÃO DE ODDS — Betfair Exchange API

**ID:** `SEC-04-01` | **Fase:** #phase/1 | **Owner:** Data Engineer | **Status:** #status/pending  
**Última Atualização:** `2026-05-13`

---

## 1. FONTE DE DADOS

| Fonte | Tipo | Custo | Endpoint | Uso |
|-------|------|-------|----------|-----|
| Betfair Exchange API | Odds em tempo real + histórico | Gratuita (com conta) | `listMarketBook`, `listMarketCatalogue` | Odds em tempo real para execução |
| Betfair Starting Price (SP) | Odds de fecho (proxy) | Gratuito via API | `listMarketCatalogue` (SP) | CLV calculation (proxy de closing line) |
| The Odds API Standard | Agregador multi-casa | $9/mês (~8€) após Mês 3 | REST JSON | Validação cruzada de closing odds |
| NBA API (sportsradar/balldontlie) | Resultados e stats | Gratuita | REST JSON | Resultados e estatísticas |

**Prioridade:** Betfair Exchange API como fonte primária de odds (é onde apostamos). Betfair SP como proxy de closing line para CLV. The Odds API como validação cruzada a partir do Mês 4.

---

## 2. ARQUITETURA DE INGESTÃO

```
Betfair API / The Odds API
        │
        ▼
  Ingestion Layer (FastAPI worker)
        │   • Rate limiting (10 req/s Betfair)
        │   • Retry com exponential backoff
        │   • Deduplicação por market_id + timestamp
        ▼
  Bronze Layer (PostgreSQL — raw)
        │   • Dados imutáveis — nunca alterar
        │   • Particionado por data (PARTITION BY RANGE)
        │   • Retenção: indefinida
        ▼
  Validation Layer (Great Expectations)
        │   • Schema validation
        │   • Range checks (odds entre 1.01 e 1000)
        │   • Null checks, duplicate checks
        ▼
  Silver Layer (PostgreSQL — cleaned)
        │   • Odds normalizadas (removido overround)
        │   • Probabilidades implícitas calculadas
        │   • Retenção: 5 anos
        ▼
  Gold Layer (Feature Store)
        │   • Features calculadas para modelos
        │   • Pronto para treino e inferência
```

---

## 3. FREQUÊNCIA DE INGESTÃO

| Contexto | Frequência | Justificação |
|----------|-----------|--------------|
| Dias sem jogos NBA | A cada 60 minutos | Odds pré-jogo abrem com antecedência |
| Dias com jogos (> 4h antes) | A cada 30 minutos | Odds começam a mover |
| Dias com jogos (1-4h antes) | A cada 10 minutos | Mercado mais ativo |
| Dias com jogos (< 1h antes) | A cada 2 minutos | Closing line captura |
| Durante o jogo (live) | Não (fora do scope MVP) | In-play fora do MVP |

**Scheduler:** Cron via Prefect ou APScheduler.

---

## 4. SCHEMA — TABELA `raw_odds` (Bronze)

```sql
CREATE TABLE raw_odds (
    id              BIGSERIAL PRIMARY KEY,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    market_id       VARCHAR(50) NOT NULL,   -- Betfair market ID
    market_type     VARCHAR(20) NOT NULL,   -- MATCH_ODDS, ASIAN_HANDICAP, etc.
    event_id        VARCHAR(50) NOT NULL,   -- Betfair event ID
    game_date       DATE NOT NULL,
    home_team       VARCHAR(100) NOT NULL,
    away_team       VARCHAR(100) NOT NULL,
    selection_id    BIGINT NOT NULL,        -- Betfair selection ID
    selection_name  VARCHAR(100) NOT NULL,
    best_back_price DECIMAL(8,3),           -- Melhor odd de back
    available_back  DECIMAL(12,2),          -- Volume disponível para back
    best_lay_price  DECIMAL(8,3),           -- Melhor odd de lay
    available_lay   DECIMAL(12,2),
    source          VARCHAR(20) NOT NULL,   -- 'betfair', 'theoddsapi'
    raw_payload     JSONB                   -- Payload original para auditoria
) PARTITION BY RANGE (game_date);

CREATE INDEX idx_raw_odds_market ON raw_odds(market_id, ingested_at);
CREATE INDEX idx_raw_odds_game ON raw_odds(game_date, home_team, away_team);
```

---

## 5. SCHEMA — TABELA `odds_cleaned` (Silver)

```sql
CREATE TABLE odds_cleaned (
    id              BIGSERIAL PRIMARY KEY,
    raw_odds_id     BIGINT REFERENCES raw_odds(id),
    market_id       VARCHAR(50) NOT NULL,
    game_date       DATE NOT NULL,
    home_team       VARCHAR(100) NOT NULL,
    away_team       VARCHAR(100) NOT NULL,
    market_type     VARCHAR(20) NOT NULL,
    selection_name  VARCHAR(100) NOT NULL,
    odd_back        DECIMAL(8,3) NOT NULL,
    odd_lay         DECIMAL(8,3),
    implied_prob    DECIMAL(8,6) NOT NULL,   -- Prob sem overround (Shin method)
    overround       DECIMAL(6,4),            -- Overround do mercado
    is_closing_line BOOLEAN DEFAULT FALSE,   -- Última odd antes do jogo
    processed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 6. NORMALIZAÇÃO DE ODDS (Remoção de Overround)

```python
def remove_overround_shin(odds: list[float]) -> list[float]:
    """
    Método de Shin para remover overround das odds.
    Mais robusto que normalização simples para mercados NBA.

    odds: lista de odds decimais de todas as seleções do mercado
    returns: probabilidades verdadeiras (sem overround)
    """
    raw_probs = [1 / o for o in odds]
    overround = sum(raw_probs)

    # Shin method iterativo
    z = 0.0
    for _ in range(100):
        z_new = sum(
            (p / overround - z) ** 2
            for p in raw_probs
        ) / (2 * (1 - z))
        if abs(z_new - z) < 1e-10:
            break
        z = z_new

    true_probs = [
        (z + (p / overround - z) ** 0.5) / (2 * z + 1)
        if z > 0 else p / overround
        for p in raw_probs
    ]
    return true_probs
```

---

## 7. TRATAMENTO DE LATE ARRIVING DATA

```python
def handle_late_odds(market_id: str, game_start: datetime) -> None:
    """
    Odds que chegam após o início do jogo são descartadas para modelação
    mas guardadas em raw para auditoria.
    """
    cutoff = game_start - timedelta(minutes=5)
    # Marcar odds após cutoff como late
    # Não usar para closing line calculation
    # Guardar em raw_odds com flag late_arrival=True
```

---

## 8. VALIDAÇÕES CRÍTICAS

| Validação | Regra | Ação se Falhar |
|-----------|-------|----------------|
| Odds válidas | 1.01 ≤ odd ≤ 1000 | Descartar registro, alertar |
| Overround razoável | 0.02 ≤ overround ≤ 0.15 | Warning — overround incomum |
| Equipa reconhecida | nome em tabela de equipas NBA | Mapear ou descartar |
| Duplicado | market_id + selection_id + hora | Ignorar duplicado |
| Volume mínimo | available_back > 50€ | Flag baixa liquidez |

---

## 9. MONITORIZAÇÃO

```python
# Métricas Prometheus
odds_ingested_total = Counter('odds_ingested_total', 'Total odds records ingested', ['source', 'market_type'])
odds_validation_failures = Counter('odds_validation_failures_total', 'Validation failures', ['rule'])
ingestion_latency = Histogram('odds_ingestion_latency_seconds', 'Time to ingest odds batch')
last_ingestion_timestamp = Gauge('odds_last_ingestion_timestamp', 'Unix timestamp of last successful ingestion')
```

**Alerta crítico:** Se `last_ingestion_timestamp` > 45 minutos em dias de jogo → Telegram imediato.

---

## 10. BACKLOG

- [ ] Implementar worker de ingestão Betfair (Fase 1, Semana 1-2)
- [ ] Criar tabelas raw_odds e odds_cleaned em PostgreSQL
- [ ] Implementar remoção de overround (Shin method)
- [ ] Configurar frequências de ingestão com APScheduler
- [ ] Implementar métricas Prometheus
- [ ] Testar com dados históricos (5 épocas NBA)

---

## 11. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]] ← Secção mãe
- [[04_Data_Engineering/VALIDACAO_DADOS]] → Great Expectations para odds
- [[04_Data_Engineering/SNAPSHOTS_HISTORICOS]] → Versionamento de dados
- [[03_Quant_Research/INDEX]] → Uso das odds em modelos
- [[15_Database/INDEX]] → Schema PostgreSQL completo
