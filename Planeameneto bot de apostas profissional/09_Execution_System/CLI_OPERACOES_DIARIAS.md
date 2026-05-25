# CLI Operações Diárias

**ID:** `CLI-001` | **Fase:** #phase/4-8 | **Owner:** Operations Lead | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Interface de linha de comandos (CLI) para automação completa das operações diárias do sistema de value betting, incluindo ingestão de dados, geração de sinais, reconciliação de apostas e relatórios de performance. Baseado no CLI do projeto georgedouzas/sports-betting.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Automatizar operações diárias sem necessidade de código manual |
| **Linguagem** | Python (Click/Typer) |
| **Scheduling** | systemd/cron para execução automática |
| **Output** | Logs estruturados + notificações Telegram |

---

## 2. ARQUITETURA CLI

```
vbq-cli
├── ingest          # Ingestão de dados
│   ├── nba         # Jogos e resultados NBA
│   ├── odds        # Odds de casas (Betfair, Fanduel, etc.)
│   └── injuries    # Lesões e notícias
├── predict         # Geração de sinais
│   ├── today       # Sinais para jogos do dia
│   └── backtest    # Backtest de modelo
├── reconcile       # Reconciliação de apostas
│   ├── bets        # Apostas vs sinais
│   └── pnl         # Cálculo de PnL
├── report          # Relatórios
│   ├── daily       # Relatório diário
│   ├── weekly      # Relatório semanal
│   └── clv         # Relatório de CLV
└── system          # Operações de sistema
    ├── status      # Status do sistema
    ├── health      # Health check
    └── reset       # Reset de componentes
```

---

## 3. COMANDOS DETALHADOS

### 3.1 Comando: ingest

**Sintaxe:**
```bash
vbq-cli ingest [SUBCOMMAND] [OPTIONS]
```

#### 3.1.1 ingest nba
Ingestão de jogos e resultados da NBA.

```bash
vbq-cli ingest nba [OPTIONS]

Options:
  --date TEXT           Data específica (YYYY-MM-DD). Default: hoje
  --backfill INTEGER    Número de dias para backfill. Default: 0
  --force               Forçar re-ingestão mesmo se dados existirem
  --dry-run             Simular ingestão sem persistir dados
  --verbose             Output detalhado

Examples:
  # Ingerir jogos de hoje
  vbq-cli ingest nba

  # Ingerir jogos de uma data específica
  vbq-cli ingest nba --date 2024-01-15

  # Backfill dos últimos 30 dias
  vbq-cli ingest nba --backfill 30

  # Forçar re-ingestão (útil para correção de dados)
  vbq-cli ingest nba --date 2024-01-15 --force
```

**Output esperado:**
```
✅ Ingestão NBA iniciada às 2024-01-15 08:00:00
📊 Buscando jogos de 2024-01-15...
🏀 15 jogos encontrados
✅ 15 jogos ingeridos com sucesso
⏱️  Duração: 12.3s
📝 Log: /var/log/vbq/ingest_nba_20240115.log
```

#### 3.1.2 ingest odds
Ingestão de odds de casas de apostas.

```bash
vbq-cli ingest odds [OPTIONS]

Options:
  --date TEXT           Data específica (YYYY-MM-DD). Default: hoje
  --source TEXT         Fonte de odds (betfair/fanduel/draftkings/all). Default: all
  --backfill INTEGER    Número de dias para backfill. Default: 0
  --force               Forçar re-ingestão
  --dry-run             Simular ingestão
  --verbose             Output detalhado

Examples:
  # Ingerir odds de todas as fontes para hoje
  vbq-cli ingest odds

  # Ingerir odds apenas Betfair
  vbq-cli ingest odds --source betfair

  # Backfill de odds dos últimos 7 dias
  vbq-cli ingest odds --backfill 7
```

**Output esperado:**
```
✅ Ingestão Odds iniciada às 2024-01-15 08:05:00
📊 Buscando odds de 2024-01-15...
🎯 Betfair: 45 odds ingeridas
🎯 Fanduel: 43 odds ingeridas
🎯 DraftKings: 42 odds ingeridas
✅ 130 odds totais ingeridas com sucesso
⏱️  Duração: 23.7s
📝 Log: /var/log/vbq/ingest_odds_20240115.log
```

#### 3.1.3 ingest injuries
Ingestão de lesões e notícias.

```bash
vbq-cli ingest injuries [OPTIONS]

Options:
  --date TEXT           Data específica. Default: hoje
  --backfill INTEGER    Número de dias para backfill. Default: 0
  --force               Forçar re-ingestão
  --verbose             Output detalhado

Examples:
  # Ingerir lesões de hoje
  vbq-cli ingest injuries

  # Backfill de lesões dos últimos 14 dias
  vbq-cli ingest injuries --backfill 14
```

**Output esperado:**
```
✅ Ingestão Lesões iniciada às 2024-01-15 08:10:00
📊 Buscando lesões de 2024-01-15...
🏥 23 atualizações de lesões encontradas
✅ 23 atualizações ingeridas com sucesso
⏱️  Duração: 8.2s
📝 Log: /var/log/vbq/ingest_injuries_20240115.log
```

---

### 3.2 Comando: predict

**Sintaxe:**
```bash
vbq-cli predict [SUBCOMMAND] [OPTIONS]
```

#### 3.2.1 predict today
Gerar sinais para jogos do dia.

```bash
vbq-cli predict today [OPTIONS]

Options:
  --date TEXT           Data específica. Default: hoje
  --model TEXT          Modelo a usar (xgboost/ensemble/all). Default: ensemble
  --min-edge FLOAT      Edge mínimo para gerar sinal. Default: 0.04 (4%)
  --max-signals INTEGER Máximo de sinais por dia. Default: 10
  --telegram            Enviar sinais via Telegram
  --dry-run             Gerar sinais sem persistir
  --verbose             Output detalhado

Examples:
  # Gerar sinais para hoje com configuração padrão
  vbq-cli predict today

  # Gerar sinais com edge mínimo de 5%
  vbq-cli predict today --min-edge 0.05

  # Usar apenas modelo XGBoost
  vbq-cli predict today --model xgboost

  # Gerar sinais e enviar via Telegram
  vbq-cli predict today --telegram
```

**Output esperado:**
```
✅ Predição iniciada às 2024-01-15 10:00:00
📊 Processando 15 jogos de 2024-01-15...
🤖 Carregando modelo ensemble...
📈 Gerando features...
🎯 Avaliando oportunidades...

📊 RESULTADOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sinais gerados: 3/15 (20%)
Média de edge: 6.2%
Média de probabilidade: 58%

✅ 3 sinais aprovados:
1. BOS vs LAL - Moneyline BOS - Edge: 7.3% - Stake: 2.1%
2. GSW vs PHX - Spread GSW -5 - Edge: 5.8% - Stake: 1.8%
3. MIL vs CHI - Total Over 225.5 - Edge: 5.5% - Stake: 1.7%

⏱️  Duração: 45.2s
📝 Log: /var/log/vbq/predict_today_20240115.log
```

#### 3.2.2 predict backtest
Backtest de modelo em dados históricos.

```bash
vbq-cli predict backtest [OPTIONS]

Options:
  --start-date TEXT     Data início (YYYY-MM-DD). Obrigatório
  --end-date TEXT       Data fim (YYYY-MM-DD). Default: hoje
  --model TEXT          Modelo a usar. Default: ensemble
  --min-edge FLOAT      Edge mínimo. Default: 0.04
  --stake-pct FLOAT     Stake fixo ou Kelly. Default: 0.02
  --kelly               Usar Kelly Criterion
  --output FILE         Output CSV com resultados
  --verbose             Output detalhado

Examples:
  # Backtest de janeiro 2024
  vbq-cli predict backtest --start-date 2024-01-01 --end-date 2024-01-31

  # Backtest com Kelly Criterion
  vbq-cli predict backtest --start-date 2024-01-01 --kelly

  # Backtest e salvar resultados em CSV
  vbq-cli predict backtest --start-date 2024-01-01 --output results.csv
```

**Output esperado:**
```
✅ Backtest iniciado às 2024-01-15 11:00:00
📊 Período: 2024-01-01 a 2024-01-31 (31 dias)
🤖 Modelo: ensemble
💰 Stake: 2% fixo

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESULTADOS DO BACKTEST:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total de jogos: 423
Sinais gerados: 87 (20.6%)
Hit rate: 56.3%
ROI médio: 3.2%
PnL total: +€1,450.00 (+14.5% da banca)
Máximo drawdown: -8.2%
Sharpe ratio: 1.45

⏱️  Duração: 3m 12s
📝 Log: /var/log/vbq/backtest_20240115.log
💾 Resultados: results.csv
```

---

### 3.3 Comando: reconcile

**Sintaxe:**
```bash
vbq-cli reconcile [SUBCOMMAND] [OPTIONS]
```

#### 3.3.1 reconcile bets
Reconciliar apostas reais com sinais gerados.

```bash
vbq-cli reconcile bets [OPTIONS]

Options:
  --date TEXT           Data específica. Default: ontem
  --auto-corrigir       Corrigir divergências automaticamente
  --report-only         Apenas report, sem correções
  --verbose             Output detalhado

Examples:
  # Reconciliar apostas de ontem
  vbq-cli reconcile bets

  # Reconciliar e corrigir automaticamente
  vbq-cli reconcile bets --auto-corrigir

  # Apenas report de divergências
  vbq-cli reconcile bets --report-only
```

**Output esperado:**
```
✅ Reconciliação iniciada às 2024-01-15 09:00:00
📊 Data: 2024-01-14
🎯 Sinais gerados: 5
💰 Apostas executadas: 4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECONCILIAÇÃO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 4 apostas reconciliadas com sucesso
⚠️  1 sinal não executado (timeout odd)
⚠️  1 divergência de odd (slippage: 1.2%)

Divergências:
- SIG-20240114-003: Odd sinal 1.85, executada 1.82 (slippage 1.6%)

⏱️  Duração: 5.3s
📝 Log: /var/log/vbq/reconcile_bets_20240115.log
```

#### 3.3.2 reconcile pnl
Calcular PnL atualizado.

```bash
vbq-cli reconcile pnl [OPTIONS]

Options:
  --date TEXT           Data específica. Default: ontem
  --cumulative          PnL acumulado desde início
  --verbose             Output detalhado

Examples:
  # PnL de ontem
  vbq-cli reconcile pnl

  # PnL acumulado desde início
  vbq-cli reconcile pnl --cumulative
```

**Output esperado:**
```
✅ Cálculo de PnL iniciado às 2024-01-15 09:05:00
📊 Data: 2024-01-14

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PnL DO DIA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Apostas: 4
Vencidas: 2 (50%)
Perdidas: 2 (50%)
Volume: €100.00
PnL: -€5.00 (-5%)
PnL acumulado: +€1,450.00 (+14.5%)

⏱️  Duração: 3.1s
📝 Log: /var/log/vbq/reconcile_pnl_20240115.log
```

---

### 3.4 Comando: report

**Sintaxe:**
```bash
vbq-cli report [SUBCOMMAND] [OPTIONS]
```

#### 3.4.1 report daily
Gerar relatório diário completo.

```bash
vbq-cli report daily [OPTIONS]

Options:
  --date TEXT           Data específica. Default: ontem
  --output FILE         Output PDF/HTML. Default: stdout
  --telegram            Enviar via Telegram
  --verbose             Output detalhado

Examples:
  # Relatório diário de ontem
  vbq-cli report daily

  # Relatório diário e enviar via Telegram
  vbq-cli report daily --telegram

  # Salvar relatório em PDF
  vbq-cli report daily --output report_20240114.pdf
```

**Output esperado:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RELATÓRIO DIÁRIO - 2024-01-14
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 OPERAÇÕES:
- Sinais gerados: 5
- Apostas executadas: 4
- Taxa de execução: 80%

💰 FINANCEIRO:
- Volume: €100.00
- PnL do dia: -€5.00 (-5%)
- PnL acumulado: +€1,450.00 (+14.5%)
- ROI acumulado: +14.5%

🎯 PERFORMANCE:
- Hit rate: 50%
- CLV médio: +1.8%
- Edge médio: 5.2%

⚠️ ALERTAS:
- 1 sinal não executado (timeout odd)
- Slippage médio: 1.2%

⏱️  Duração: 8.4s
📝 Log: /var/log/vbq/report_daily_20240115.log
```

#### 3.4.2 report weekly
Gerar relatório semanal.

```bash
vbq-cli report weekly [OPTIONS]

Options:
  --week INTEGER        Semana específica (1-52). Default: semana atual
  --year INTEGER        Ano específico. Default: ano atual
  --output FILE         Output PDF/HTML
  --telegram            Enviar via Telegram

Examples:
  # Relatório da semana atual
  vbq-cli report weekly

  # Relatório da semana 3 de 2024
  vbq-cli report weekly --week 3 --year 2024
```

#### 3.4.3 report clv
Relatório detalhado de CLV.

```bash
vbq-cli report clv [OPTIONS]

Options:
  --days INTEGER        Número de dias. Default: 30
  --by-market           Quebrar por mercado
  --output FILE         Output CSV/HTML
  --verbose             Output detalhado

Examples:
  # CLV dos últimos 30 dias
  vbq-cli report clv

  # CLV dos últimos 90 dias por mercado
  vbq-cli report clv --days 90 --by-market
```

---

### 3.5 Comando: system

**Sintaxe:**
```bash
vbq-cli system [SUBCOMMAND] [OPTIONS]
```

#### 3.5.1 system status
Status do sistema.

```bash
vbq-cli system status [OPTIONS]

Options:
  --verbose             Output detalhado

Examples:
  # Status geral do sistema
  vbq-cli system status

  # Status detalhado
  vbq-cli system status --verbose
```

**Output esperado:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATUS DO SISTEMA - 2024-01-15 10:30:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ COMPONENTES:
- PostgreSQL: ✅ Online (latência: 5ms)
- Redis: ✅ Online (latência: 2ms)
- API: ✅ Online (latência: 15ms)
- Telegram Bot: ✅ Online

📊 DADOS:
- Última ingestão NBA: 2024-01-15 08:00:00 ✅
- Última ingestão Odds: 2024-01-15 08:05:00 ✅
- Última predição: 2024-01-15 10:00:00 ✅

💰 BANCA:
- Banca atual: €11,450.00
- Banca pico: €12,000.00
- Drawdown atual: -4.6%

⏱️  Duração: 2.1s
```

#### 3.5.2 system health
Health check detalhado.

```bash
vbq-cli system health [OPTIONS]

Options:
  --full                Health check completo (inclui testes)
  --verbose             Output detalhado

Examples:
  # Health check rápido
  vbq-cli system health

  # Health check completo com testes
  vbq-cli system health --full
```

#### 3.5.3 system reset
Reset de componentes (cuidado!).

```bash
vbq-cli system reset [SUBCOMMAND] [OPTIONS]

Options:
  --confirm             Confirmar reset (obrigatório)

Examples:
  # Reset cache Redis
  vbq-cli system reset redis --confirm

  # Reset fila de sinais
  vbq-cli system reset signals --confirm
```

---

## 4. SCHEDULING AUTOMÁTICO

### 4.1 Cron Jobs (Linux)

```bash
# Crontab para operações diárias

# Ingestão NBA (08:00 em dias de jogo)
0 8 * * 1-5 /usr/bin/vbq-cli ingest nba >> /var/log/vbq/cron_nba.log 2>&1

# Ingestão Odds (08:05 em dias de jogo)
5 8 * * 1-5 /usr/bin/vbq-cli ingest odds >> /var/log/vbq/cron_odds.log 2>&1

# Ingestão Lesões (08:10 em dias de jogo)
10 8 * * 1-5 /usr/bin/vbq-cli ingest injuries >> /var/log/vbq/cron_injuries.log 2>&1

# Predição (10:00 em dias de jogo)
0 10 * * 1-5 /usr/bin/vbq-cli predict today --telegram >> /var/log/vbq/cron_predict.log 2>&1

# Reconciliação (09:00 no dia seguinte)
0 9 * * 2-6 /usr/bin/vbq-cli reconcile bets >> /var/log/vbq/cron_reconcile.log 2>&1

# Relatório Diário (09:15 no dia seguinte)
15 9 * * 2-6 /usr/bin/vbq-cli report daily --telegram >> /var/log/vbq/cron_report.log 2>&1

# Health Check (a cada hora)
0 * * * * /usr/bin/vbq-cli system health >> /var/log/vbq/cron_health.log 2>&1
```

### 4.2 Systemd Service (Linux)

```ini
# /etc/systemd/system/vbq-ingest.service
[Unit]
Description=VBQ Daily Ingestion
After=network.target

[Service]
Type=oneshot
User=vbq
WorkingDirectory=/opt/vbq
ExecStart=/usr/bin/vbq-cli ingest nba --backfill 1
ExecStart=/usr/bin/vbq-cli ingest odds --backfill 1
ExecStart=/usr/bin/vbq-cli ingest injuries --backfill 1

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/vbq-ingest.timer
[Unit]
Description=VBQ Daily Ingestion Timer

[Timer]
OnCalendar=*-*-* 08:00:00
OnCalendar=*-*-* 12:00:00
OnCalendar=*-*-* 16:00:00

[Install]
WantedBy=timers.target
```

### 4.3 Windows Task Scheduler

```xml
<!-- Task Scheduler XML -->
<Task>
  <Triggers>
    <TimeTrigger>
      <StartBoundary>2024-01-01T08:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysOfWeek>
          <Monday />
          <Tuesday />
          <Wednesday />
          <Thursday />
          <Friday />
        </DaysOfWeek>
      </ScheduleByDay>
    </TimeTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>C:\Python311\Scripts\vbq-cli.exe</Command>
      <Arguments>ingest nba</Arguments>
    </Exec>
  </Actions>
</Task>
```

---

## 5. LOGGING E OUTPUT

### 5.1 Estrutura de Logs

```
/var/log/vbq/
├── ingest_nba_YYYYMMDD.log
├── ingest_odds_YYYYMMDD.log
├── ingest_injuries_YYYYMMDD.log
├── predict_today_YYYYMMDD.log
├── reconcile_bets_YYYYMMDD.log
├── reconcile_pnl_YYYYMMDD.log
├── report_daily_YYYYMMDD.log
└── system_health_YYYYMMDD.log
```

### 5.2 Formato de Log

```json
{
  "timestamp": "2024-01-15T08:00:00Z",
  "level": "INFO",
  "command": "ingest nba",
  "message": "Ingestão iniciada",
  "metadata": {
    "date": "2024-01-15",
    "games_count": 15
  }
}
```

### 5.3 Níveis de Verbosidade

- `--quiet`: Apenas erros críticos
- (default): INFO + WARN
- `--verbose`: INFO + WARN + DEBUG
- `--debug`: Todos os logs incluindo TRACE

---

## 6. INTEGRAÇÃO COM O SISTEMA

### 6.1 Dependências

O CLI depende de:
- PostgreSQL (dados)
- Redis (cache/filas)
- Modelos ML (ficheiros .pkl)
- Configuração (config.yaml)

### 6.2 Configuração

```yaml
# config.yaml
cli:
  default_date_format: "%Y-%m-%d"
  default_timezone: "Europe/Lisbon"
  log_level: "INFO"
  log_dir: "/var/log/vbq"
  
ingestion:
  nba_api_key: "${NBA_API_KEY}"
  betfair_api_key: "${BETFAIR_API_KEY}"
  
prediction:
  model_path: "/opt/vbq/models"
  default_model: "ensemble"
  min_edge: 0.04
  max_signals_per_day: 10
  
reporting:
  telegram_bot_token: "${TELEGRAM_BOT_TOKEN}"
  telegram_chat_id: "${TELEGRAM_CHAT_ID}"
```

---

## 7. MONITORIZAÇÃO

### 7.1 Métricas

| Métrica | Descrição | Threshold |
|---------|-----------|-----------|
| cli_execution_duration | Duração de execução CLI | < 60s |
| cli_errors_total | Total de erros CLI | < 1/hora |
| cli_ingestion_latency | Latência de ingestão | < 30s |

### 7.2 Alertas

- CLI falha 3x consecutivas → Alerta Telegram
- Ingestão falha → Alerta crítico
- Predição falha → Alerta crítico

---

## 8. TROUBLESHOOTING

### 8.1 CLI não responde

```bash
# Verificar se processo está a correr
ps aux | grep vbq-cli

# Verificar logs
tail -f /var/log/vbq/system_health_*.log

# Restart do serviço
systemctl restart vbq-ingest
```

### 8.2 Ingestão falha

```bash
# Verificar conexão à base de dados
vbq-cli system health --full

# Verificar credenciais API
vbq-cli ingest nba --dry-run --verbose

# Forçar re-ingestão
vbq-cli ingest nba --force --verbose
```

### 8.3 Predição não gera sinais

```bash
# Verificar se modelo existe
ls -lh /opt/vbq/models/

# Verificar se dados existem
vbq-cli ingest nba --date 2024-01-15 --dry-run

# Verificar features
vbq-cli predict today --dry-run --verbose
```

---

## 9. EXEMPLOS DE CÓDIGO

### 9.1 Estrutura do CLI (Click)

```python
# vbq_cli/__main__.py
import click
from datetime import datetime

@click.group()
def cli():
    """VBQ Value Betting CLI"""
    pass

@cli.group()
def ingest():
    """Comandos de ingestão de dados"""
    pass

@ingest.command()
@click.option('--date', default=None, help='Data específica (YYYY-MM-DD)')
@click.option('--backfill', default=0, help='Dias para backfill')
@click.option('--force', is_flag=True, help='Forçar re-ingestão')
def nba(date, backfill, force):
    """Ingestão de jogos NBA"""
    from vbq.ingestion.nba_ingester import NBAIngester
    from vbq.database import SessionLocal
    
    target_date = date or datetime.now().date()
    db = SessionLocal()
    
    try:
        ingester = NBAIngester(db)
        games = ingester.ingest_games(target_date, backfill=backfill, force=force)
        click.echo(f"✅ {len(games)} jogos ingeridos com sucesso")
    finally:
        db.close()

if __name__ == '__main__':
    cli()
```

### 9.2 Instalação

```bash
# Instalar CLI
pip install -e .

# Verificar instalação
vbq-cli --help

# Adicionar ao PATH (se necessário)
export PATH="$PATH:/usr/local/bin"
```

---

## 10. LINKS CRUZADOS

- [[09_Execution_System/INDEX]] ← Secção mãe
- [[04_Data_Engineering/PIPELINE_ETL_NBA]] → Ingestão detalhada
- [[07_Value_Detection/MOTOR_EDGE]] → Motor de predição
- [[08_Risk_Management/INDEX]] → Gestão de risco
- [[19_Telegram_System/INDEX]] → Notificações Telegram
- [[10_Infrastructure/MONITORIZACAO_INFRA]] → Monitorização

---

**Custo de implementação:** 0€ (CLI é software open-source)  
**Tempo estimado de implementação:** 2-3 semanas  
**Prioridade:** ALTA (fundamental para operações diárias)
