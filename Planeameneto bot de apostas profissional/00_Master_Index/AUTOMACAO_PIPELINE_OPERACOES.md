# Automação Completa do Pipeline de Operações

**ID:** AUTO-001 | **Fase:** #phase/4-8 | **Owner:** DevOps Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Pipeline orquestrado completo para automação de todas as operações diárias, desde ingestão de dados até distribuição de sinais, com Prefect para orquestração, systemd/cron para scheduling, e integração com todos os componentes documentados anteriormente.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Automatizar 100% das operações diárias sem intervenção manual |
| **Orquestrador** | Prefect (OSS) |
| **Scheduler** | systemd/cron |
| **Frequência** | A cada 2 horas em dias de jogo NBA |
| **Componentes** | 8 módulos integrados |
| **Custo** | 0€ (Prefect OSS + systemd) |

---

## 2. ARQUITETURA DO PIPELINE

### 2.1 Diagrama de Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    SCHEDULER (cron/systemd)                 │
│              Dispara pipeline a cada 2 horas               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    PREFECT FLOW                             │
│              Orquestração e monitorização                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            TASK 1: INGESTÃO DE DADOS                      │
│  • CLI ingest nba                                         │
│  • CLI ingest odds (multi-source)                         │
│  • CLI ingest injuries                                    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            TASK 2: FEATURE ENGINEERING                    │
│  • Gerar features para jogos do dia                       │
│  • Validar qualidade de features                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            TASK 3: PREDIÇÃO DO MODELO                      │
│  • Carregar modelo ensemble                               │
│  • Inferência para jogos do dia                           │
│  • Calibração isotónica                                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            TASK 4: SISTEMA DE DECISÃO                      │
│  • Filtrar por edge (Camada 1)                             │
│  • Filtrar por qualidade odds (Camada 2)                  │
│  • Filtrar por CLV histórico (Camada 3)                   │
│  • Filtrar por exposição (Camada 4)                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            TASK 5: KELLY CRITERIUM                         │
│  • Calcular stake automático                              │
│  • Ajustar por drawdown e volatilidade                    │
│  • Verificar limites de exposição                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            TASK 6: RANKING E SELEÇÃO                       │
│  • Rankear oportunidades por pontuação                    │
│  • Selecionar top N (configurável)                        │
│  • Garantir diversificação                                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            TASK 7: DISTRIBUIÇÃO DE SINAIS                 │
│  • Persistir no PostgreSQL                                │
│  • Publicar no Redis (para consumidores)                  │
│  • Enviar via Telegram Bot                                 │
│  • Log para Prometheus                                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            TASK 8: MONITORIZAÇÃO E ALERTAS                │
│  • Verificar health do sistema                            │
│  • Enviar alertas se necessário                           │
│  • Gerar relatório diário                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. ORQUESTRAÇÃO COM PREFECT

### 3.1 Definição do Flow Principal

```python
# vbq/orchestration/daily_pipeline.py
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import datetime, timedelta
import hashlib

@task(cache_key_fn=task_input_hash)
def ingest_nba_data(date: datetime) -> dict:
    """
    Task de ingestão de dados NBA.
    
    Usa CLI: vbq-cli ingest nba --date {date}
    """
    from vbq.ingestion.nba_ingester import NBAIngester
    from vbq.database import SessionLocal
    
    db = SessionLocal()
    try:
        ingester = NBAIngester(db)
        games = ingester.ingest_games(date)
        return {
            'status': 'success',
            'games_count': len(games),
            'date': date.isoformat()
        }
    finally:
        db.close()

@task(cache_key_fn=task_input_hash)
def ingest_odds_data(date: datetime) -> dict:
    """
    Task de ingestão de odds multi-source.
    
    Usa CLI: vbq-cli ingest odds --date {date} --source all
    """
    from vbq.odds.ingester import OddsIngester
    from vbq.database import SessionLocal
    
    db = SessionLocal()
    try:
        ingester = OddsIngester(db)
        odds = ingester.ingest_odds_all_sources(date)
        return {
            'status': 'success',
            'odds_count': len(odds),
            'date': date.isoformat()
        }
    finally:
        db.close()

@task(cache_key_fn=task_input_hash)
def ingest_injuries(date: datetime) -> dict:
    """
    Task de ingestão de lesões.
    
    Usa CLI: vbq-cli ingest injuries --date {date}
    """
    from vbq.ingestion.injury_ingester import InjuryIngester
    from vbq.database import SessionLocal
    
    db = SessionLocal()
    try:
        ingester = InjuryIngester(db)
        injuries = ingester.ingest_injuries(date)
        return {
            'status': 'success',
            'injuries_count': len(injuries),
            'date': date.isoformat()
        }
    finally:
        db.close()

@task
def generate_features(date: datetime) -> dict:
    """
    Task de geração de features.
    
    Usa CLI: vbq-cli features generate --date {date}
    """
    from vbq.features.feature_engineer import FeatureEngineer
    from vbq.database import SessionLocal
    
    db = SessionLocal()
    try:
        engineer = FeatureEngineer(db)
        games = engineer.get_games_for_date(date)
        
        features_count = 0
        for game in games:
            features = engineer.generate_features(game['game_id'])
            if engineer.validate_features(features):
                engineer.persist_features(features)
                features_count += 1
        
        return {
            'status': 'success',
            'features_count': features_count,
            'date': date.isoformat()
        }
    finally:
        db.close()

@task
def run_predictions(date: datetime) -> dict:
    """
    Task de predição do modelo.
    
    Usa CLI: vbq-cli predict today --date {date}
    """
    from vbq.inference.predictor import ModelPredictor
    from vbq.database import SessionLocal
    
    db = SessionLocal()
    try:
        predictor = ModelPredictor(db)
        predictions = predictor.predict_for_date(date)
        
        return {
            'status': 'success',
            'predictions_count': len(predictions),
            'date': date.isoformat()
        }
    finally:
        db.close()

@task
def apply_decision_system(predictions: list) -> dict:
    """
    Task de sistema de decisão.
    
    Usa CLI: vbq-cli decision evaluate
    """
    from vbq.decision.decision_engine import DecisionEngine
    from vbq.database import SessionLocal
    
    db = SessionLocal()
    try:
        engine = DecisionEngine(db)
        opportunities = engine.evaluate_opportunities(predictions)
        
        approved = [o for o in opportunities if o['approved']]
        
        return {
            'status': 'success',
            'total_opportunities': len(opportunities),
            'approved_count': len(approved),
            'rejection_rate': (len(opportunities) - len(approved)) / len(opportunities) if opportunities else 0
        }
    finally:
        db.close()

@task
def calculate_kelly_stakes(approved_opportunities: list) -> dict:
    """
    Task de cálculo de Kelly Criterion.
    
    Usa CLI: vbq-cli kelly calculate
    """
    from vbq.risk.kelly_engine import KellyEngine
    from vbq.database import SessionLocal
    
    db = SessionLocal()
    try:
        engine = KellyEngine(db)
        
        stakes = []
        for opp in approved_opportunities:
            stake_result = engine.calculate_stake_for_signal(
                opp['game_id'],
                opp['probability'],
                opp['odds']
            )
            stakes.append(stake_result)
        
        return {
            'status': 'success',
            'stakes_count': len(stakes),
            'total_stake': sum(s['stake'] for s in stakes)
        }
    finally:
        db.close()

@task
def rank_and_select(opportunities_with_stakes: list) -> dict:
    """
    Task de ranking e seleção.
    
    Usa CLI: vbq-cli decision ranking
    """
    from vbq.decision.opportunity_ranker import OpportunityRanker
    from vbq.database import SessionLocal
    
    db = SessionLocal()
    try:
        ranker = OpportunityRanker(db)
        ranked = ranker.rank_opportunities(opportunities_with_stakes)
        
        max_signals = 10  # Configurável
        selected = ranked[:max_signals]
        
        return {
            'status': 'success',
            'total_ranked': len(ranked),
            'selected_count': len(selected)
        }
    finally:
        db.close()

@task
def distribute_signals(selected_signals: list) -> dict:
    """
    Task de distribuição de sinais.
    
    Usa CLI: vbq-cli signal distribute
    """
    from vbq.signals.signal_distributor import SignalDistributor
    from vbq.database import SessionLocal
    
    db = SessionLocal()
    try:
        distributor = SignalDistributor()
        
        distributed_count = 0
        for signal in selected_signals:
            distributor.distribute_signal(signal)
            distributed_count += 1
        
        return {
            'status': 'success',
            'distributed_count': distributed_count
        }
    finally:
        db.close()

@task
def generate_daily_report(date: datetime) -> dict:
    """
    Task de geração de relatório diário.
    
    Usa CLI: vbq-cli report daily --date {date}
    """
    from vbq.reporting.daily_report import DailyReportGenerator
    from vbq.database import SessionLocal
    
    db = SessionLocal()
    try:
        generator = DailyReportGenerator(db)
        report = generator.generate(date)
        
        return {
            'status': 'success',
            'report_generated': True,
            'date': date.isoformat()
        }
    finally:
        db.close()

@flow(name="Daily Value Betting Pipeline")
def daily_pipeline(date: datetime = None):
    """
    Flow principal diário.
    
    Pipeline completo:
    1. Ingestão de dados (NBA, odds, lesões)
    2. Feature engineering
    3. Predição do modelo
    4. Sistema de decisão
    5. Kelly Criterion
    6. Ranking e seleção
    7. Distribuição de sinais
    8. Relatório diário
    """
    if date is None:
        date = datetime.now().date()
    
    print(f"🚀 Iniciando pipeline para {date}")
    
    # Task 1: Ingestão de dados (paralelo)
    nba_result = ingest_nba_data(date)
    odds_result = ingest_odds_data(date)
    injuries_result = ingest_injuries(date)
    
    # Task 2: Feature engineering
    features_result = generate_features(date)
    
    # Task 3: Predição
    predictions_result = run_predictions(date)
    
    # Task 4: Sistema de decisão
    decision_result = apply_decision_system(predictions_result['predictions'])
    
    # Task 5: Kelly Criterion
    kelly_result = calculate_kelly_stakes(decision_result['approved'])
    
    # Task 6: Ranking e seleção
    ranking_result = rank_and_select(kelly_result['opportunities'])
    
    # Task 7: Distribuição
    distribution_result = distribute_signals(ranking_result['selected'])
    
    # Task 8: Relatório
    report_result = generate_daily_report(date)
    
    # Resumo
    summary = {
        'date': date.isoformat(),
        'games': nba_result['games_count'],
        'odds': odds_result['odds_count'],
        'features': features_result['features_count'],
        'predictions': predictions_result['predictions_count'],
        'approved': decision_result['approved_count'],
        'distributed': distribution_result['distributed_count'],
        'status': 'completed'
    }
    
    print(f"✅ Pipeline concluído: {summary}")
    
    return summary
```

---

## 4. SCHEDULING AUTOMÁTICO

### 4.1 Cron Job (Linux)

```bash
# /etc/cron.d/vbq-pipeline

# Executar pipeline a cada 2 horas em dias de jogo NBA
# Horários: 08:00, 10:00, 12:00, 14:00, 16:00, 18:00 UTC
0 8,10,12,14,16,18 * * 1-5 vbq /usr/bin/python /opt/vbq/scripts/run_pipeline.py >> /var/log/vbq/pipeline.log 2>&1

# Relatório diário às 09:00 UTC (dia seguinte)
0 9 * * 2-6 vbq /usr/bin/vbq-cli report daily --telegram >> /var/log/vbq/report.log 2>&1

# Health check a cada hora
0 * * * * vbq /usr/bin/vbq-cli system health >> /var/log/vbq/health.log 2>&1
```

### 4.2 Systemd Service (Linux)

```ini
# /etc/systemd/system/vbq-pipeline.service
[Unit]
Description=VBQ Daily Pipeline
After=network.target postgresql.service redis.service

[Service]
Type=oneshot
User=vbq
Group=vbq
WorkingDirectory=/opt/vbq
Environment="PATH=/opt/vbq/venv/bin:/usr/local/bin"
ExecStart=/opt/vbq/venv/bin/python /opt/vbq/scripts/run_pipeline.py

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/vbq-pipeline.timer
[Unit]
Description=VBQ Daily Pipeline Timer

[Timer]
OnCalendar=*-*-* 08,10,12,14,16,18:00:00
OnCalendar=*-*-* 09:00:00  # Relatório diário

[Install]
WantedBy=timers.target
```

### 4.3 Habilitar Services

```bash
# Habilitar timer
sudo systemctl enable vbq-pipeline.timer

# Iniciar timer
sudo systemctl start vbq-pipeline.timer

# Verificar status
sudo systemctl status vbq-pipeline.timer
sudo systemctl list-timers
```

---

## 5. INTEGRAÇÃO COM COMPONENTES

### 5.1 Mapeamento de CLI para Tasks

| Task | CLI Command | Documento |
|------|-------------|-----------|
| Ingestão NBA | `vbq-cli ingest nba` | CLI_OPERACOES_DIARIAS.md |
| Ingestão Odds | `vbq-cli ingest odds` | INTEGRACAO_ODDS_CASAS.md |
| Ingestão Lesões | `vbq-cli ingest injuries` | CLI_OPERACOES_DIARIAS.md |
| Features | `vbq-cli features generate` | CLI_OPERACOES_DIARIAS.md |
| Predição | `vbq-cli predict today` | CLI_OPERACOES_DIARIAS.md |
| Decisão | `vbq-cli decision evaluate` | SISTEMA_DECISAO_APOSTAS.md |
| Kelly | `vbq-cli kelly calculate` | KELLY_CRITERIO_AUTOMATICO.md |
| Ranking | `vbq-cli decision ranking` | SISTEMA_DECISAO_APOSTAS.md |
| Distribuição | `vbq-cli signal distribute` | CLI_OPERACOES_DIARIAS.md |
| Relatório | `vbq-cli report daily` | CLI_OPERACOES_DIARIAS.md |

---

## 6. MONITORIZAÇÃO DO PIPELINE

### 6.1 Métricas do Pipeline

| Métrica | Descrição | Threshold |
|---------|-----------|-----------|
| pipeline_duration | Duração total do pipeline | < 15 min |
| pipeline_success_rate | Taxa de sucesso | > 95% |
| task_failure_rate | Taxa de falha por task | < 5% |
| pipeline_latency | Latência entre trigger e execução | < 1 min |

### 6.2 Dashboard de Pipeline

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PIPELINE DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 STATUS ATUAL:
- Última execução: 2024-01-15 14:00:00 ✅
- Duração: 8m 32s
- Status: Success

📊 PERFORMANCE:
- Duração média (7 dias): 7m 45s
- Taxa de sucesso (30 dias): 98.2%
- Tasks falhados: 0

📊 DETALHES DA ÚLTIMA EXECUÇÃO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Ingestão NBA: ✅ 15 jogos (1m 12s)
2. Ingestão Odds: ✅ 130 odds (2m 34s)
3. Ingestão Lesões: ✅ 23 lesões (45s)
4. Features: ✅ 15 features (1m 23s)
5. Predição: ✅ 15 predições (1m 05s)
6. Decisão: ✅ 3 aprovados (45s)
7. Kelly: ✅ 3 stakes (23s)
8. Ranking: ✅ 3 selecionados (12s)
9. Distribuição: ✅ 3 sinais (34s)
10. Relatório: ✅ Gerado (18s)

⚠️ ALERTAS:
- Nenhum

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 7. ERROR HANDLING E RETRY

### 7.1 Retry Logic

```python
from prefect import task
from tenacity import retry, stop_after_attempt, wait_exponential

@task(retries=3, retry_delay_seconds=60)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def ingest_nba_data_with_retry(date: datetime) -> dict:
    """
    Task de ingestão com retry automático.
    
    Se falhar, tenta novamente após 60s, até 3 vezes.
    """
    return ingest_nba_data(date)
```

### 7.2 Fallback Strategies

```python
@task
def ingest_odds_with_fallback(date: datetime) -> dict:
    """
    Task de ingestão de odds com fallback.
    
    Se todas as fontes falharem, usa cache ou dados antigos.
    """
    try:
        # Tentar ingestão normal
        result = ingest_odds_data(date)
        return result
    except Exception as e:
        log_error(f"Falha na ingestão de odds: {e}")
        
        # Fallback 1: Usar cache Redis
        cached = get_cached_odds(date)
        if cached:
            log_warning("Usando odds em cache")
            return {'status': 'success', 'source': 'cache', 'odds_count': len(cached)}
        
        # Fallback 2: Usar dados mais recentes do DB
        latest_odds = get_latest_odds_from_db(days=1)
        if latest_odds:
            log_warning("Usando odds antigas do DB")
            return {'status': 'success', 'source': 'db_fallback', 'odds_count': len(latest_odds)}
        
        # Fallback 3: Continuar sem odds (modelo usa odds simuladas)
        log_critical("Impossível obter odds, continuando sem odds")
        return {'status': 'warning', 'source': 'none', 'odds_count': 0}
```

---

## 8. CONFIGURAÇÃO

### 8.1 Configuração do Pipeline

```yaml
# config/pipeline.yaml
pipeline:
  name: "Daily Value Betting Pipeline"
  timezone: "Europe/Lisbon"
  
  # Scheduling
  schedule:
    enabled: true
    cron_expression: "0 8,10,12,14,16,18 * * 1-5"
  
  # Retries
  retries:
    enabled: true
    max_retries: 3
    retry_delay_seconds: 60
  
  # Limits
  max_signals_per_day: 10
  max_games_per_run: 50
  
  # Notifications
  notifications:
    telegram:
      enabled: true
      on_success: true
      on_failure: true
      chat_id: "${TELEGRAM_CHAT_ID}"
  
  # Monitoring
  monitoring:
    prometheus:
      enabled: true
    mlflow:
      enabled: true
      experiment_name: "vbq-pipeline"
```

---

## 9. DEPLOY DO PIPELINE

### 9.1 Script de Deploy

```bash
#!/bin/bash
# scripts/deploy_pipeline.sh

echo "🚀 Deploy do VBQ Pipeline..."

# 1. Criar virtual environment
python -m venv /opt/vbq/venv
source /opt/vbq/venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Instalar Prefect
pip install prefect

# 4. Registrar flow no Prefect
python -m vbq.orchestration.daily_pipeline

# 5. Criar systemd service
sudo cp /opt/vbq/systemd/vbq-pipeline.service /etc/systemd/system/
sudo cp /opt/vbq/systemd/vbq-pipeline.timer /etc/systemd/system/

# 6. Habilitar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable vbq-pipeline.timer
sudo systemctl start vbq-pipeline.timer

# 7. Verificar status
sudo systemctl status vbq-pipeline.timer

echo "✅ Pipeline deploy concluído!"
```

---

## 10. EXEMPLOS DE CÓDIGO

### 10.1 Script de Execução Manual

```python
# scripts/run_pipeline.py
import sys
from datetime import datetime
from vbq.orchestration.daily_pipeline import daily_pipeline

def main():
    # Obter data (argumento ou hoje)
    if len(sys.argv) > 1:
        date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    else:
        date = datetime.now().date()
    
    # Executar pipeline
    result = daily_pipeline(date)
    
    # Exit code baseado no resultado
    if result['status'] == 'completed':
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
```

---

## 11. TROUBLESHOOTING

### 11.1 Pipeline Falha

```bash
# Verificar logs do Prefect
prefect flow-run ls --name "daily-value-betting-pipeline"

# Ver logs específicos
prefect flow-run inspect <flow-run-id>

# Re-executar manualmente
python /opt/vbq/scripts/run_pipeline.py 2024-01-15
```

### 11.2 Task Específico Falha

```bash
# Verificar logs de task específico
tail -f /var/log/vbq/pipeline.log | grep "ingest_nba_data"

# Testar task manualmente
python -c "from vbq.orchestration.daily_pipeline import ingest_nba_data; ingest_nba_data(datetime.now().date())"
```

---

## 12. LINKS CRUZADOS

- [[00_Master_Index/INTEGRATION_GUIDE]] ← Documentação de integração base
- [[09_Execution_System/CLI_OPERACOES_DIARIAS]] → CLI para operações
- [[14_APIs/INTEGRACAO_ODDS_CASAS]] → Integração de odds
- [[08_Risk_Management/KELLY_CRITERIO_AUTOMATICO]] → Kelly automático
- [[07_Value_Detection/SISTEMA_DECISAO_APOSTAS]] → Sistema de decisão
- [[10_Infrastructure/MONITORIZACAO_INFRA]] → Monitorização

---

**Custo de implementação:** 0€ (Prefect OSS + systemd são gratuitos)  
**Tempo estimado de implementação:** 2-3 semanas  
**Prioridade:** ALTA (fundamental para operação automatizada)
