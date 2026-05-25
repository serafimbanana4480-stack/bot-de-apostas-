# SOP-001 — Rotina Diária de Abertura

**ID:** `SOP-001` | **Fase:** Todas | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Estabelecer a rotina diária de abertura do sistema de apostas.

---

## 2. CHECKLIST

- [ ] Verificar status do servidor
- [ ] Verificar conexão com database
- [ ] Verificar conexão com APIs externas
- [ ] Verificar bankroll atual
- [ ] Verificar limites de stake
- [ ] Iniciar bot de apostas
- [ ] Verificar alertas Telegram
- [ ] Documentar anomalias

---

## 3. PROCEDIMENTO DETALHADO

### 3.1 Verificar Status do Servidor (2 min)

```bash
# Verificar uptime e carga
docker compose ps

# Verificar uso de recursos
docker stats --no-stream

# Verificar espaço em disco
df -h
```

**Critério de passagem:** Todos os containers `Up` há > 5 minutos, CPU < 80%, disco > 10% livre.

### 3.2 Verificar Conexão com Database (1 min)

```bash
# Testar conexão PostgreSQL
docker compose exec -T postgres psql -U vb_admin -d valuebetting -c "SELECT 1;"

# Verificar tabelas principais
docker compose exec -T postgres psql -U vb_admin -d valuebetting -c "SELECT COUNT(*) FROM bronze.raw_odds;"
```

**Critério de passagem:** Query retorna resultado sem erro.

### 3.3 Verificar Conexão com APIs Externas (2 min)

```bash
# Testar NBA API
python scripts/test_nba_api.py

# Testar Betfair API (se configurada)
python scripts/test_betfair_api.py
```

**Critério de passagem:** APIs respondem com status 200, rate limits não excedidos.

### 3.4 Verificar Bankroll e Limites (1 min)

```bash
# Verificar bankroll atual
python scripts/get_bankroll.py

# Verificar limites de exposição
python scripts/check_exposure_limits.py
```

**Critério de passagem:** Bankroll > 0, exposição diária < 12% do bankroll.

### 3.5 Iniciar Motor de Decisão (1 min)

```bash
# Verificar se motor está parado
python scripts/check_decision_engine.py

# Iniciar motor
python scripts/start_decision_engine.py
```

**Critério de passagem:** Motor reporta "RUNNING", healthcheck passa.

### 3.6 Verificar Alertas Telegram (1 min)

- Abrir app Telegram, canal `ops_alertas`
- Verificar se há alertas não reconhecidos das últimas 12h
- Se houver alertas: investigar antes de iniciar operações

**Critério de passagem:** 0 alertas CRITICAL/HIGH não investigados.

### 3.7 Documentar Anomalias

- Se algum passo falhou: anotar no `daily_log_YYYY-MM-DD.md`
- Incluir: hora, sintoma, ação tomada, decisão
- Se anomalia grave: notificar Risk Manager via Telegram

---

## 4. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
