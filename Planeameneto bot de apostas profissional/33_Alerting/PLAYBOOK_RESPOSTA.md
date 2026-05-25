# PLAYBOOK_RESPOSTA — Playbooks de Resposta a Alertas

**ID:** `AL-003` | **Fase:** Todas | **Owner:** DevOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Fornecer playbooks específicos de resposta a cada tipo de alerta do sistema.

---

## 2. PLAYBOOKS POR TIPO DE ALERTA

### 2.1 Sistema Indisponível

**Sintomas:**
- API retorna 5xx
- Servidor não responde
- Database connection failed

**Diagnóstico:**
```bash
# Check server status
ssh user@vps "uptime"
ssh user@vps "systemctl status betting-bot"

# Check database
psql -h localhost -U betting_user -d betting_db -c "SELECT 1"

# Check logs
tail -f /var/log/betting-bot/app.log
```

**Resolução:**
1. Restart serviço: `systemctl restart betting-bot`
2. Se falhar, check logs para erro específico
3. Se database issue, restart PostgreSQL
4. Se recurso esgotado, escalar VPS

**Verificação:**
```bash
curl https://api.betting-bot.com/health
```

---

### 2.2 CLV Negativo Crítico

**Sintomas:**
- CLV médio < -5% nos últimos 3 dias
- ROI negativo sustentado

**Diagnóstico:**
```sql
-- Check CLV recente
SELECT 
  DATE(bet_time) as date,
  AVG(clv) as avg_clv,
  COUNT(*) as num_bets
FROM bets
WHERE bet_time >= NOW() - INTERVAL '3 days'
GROUP BY DATE(bet_time)
ORDER BY date DESC;
```

**Resolução:**
1. Pausar novas apostas: `UPDATE config SET paused = true`
2. Investigar drift de features
3. Verificar se odds reference mudou
4. Reavaliar modelo se necessário

**Verificação:**
- CLV volta a positivo em backtest recente

---

### 2.3 Drawdown Acelerado

**Sintomas:**
- Drawdown diário > 10%
- Perdas consecutivas > 5 dias

**Diagnóstico:**
```sql
-- Check drawdown
SELECT 
  bankroll,
  (bankroll - LAG(bankroll) OVER (ORDER BY date)) / LAG(bankroll) OVER (ORDER BY date) as daily_return
FROM bankroll_history
ORDER BY date DESC
LIMIT 7;
```

**Resolução:**
1. Ativar circuit breaker: `UPDATE config SET circuit_breaker = true`
2. Reduzir stake em 50%
3. Investigar causas específicas
4. Documentar em postmortem

**Verificação:**
- Drawdown estabiliza
- Stake reduzido aplicado

---

### 2.4 API Latency Alta

**Sintomas:**
- p95 latency > 2000ms
- Timeouts frequentes

**Diagnóstico:**
```bash
# Check response times
curl -w "@curl-format.txt" https://api.betting-bot.com/odds

# Check database queries
psql -h localhost -U betting_user -d betting_db -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10"
```

**Resolução:**
1. Identificar query lento
2. Adicionar índices se necessário
3. Implementar caching
4. Escalar VPS se necessário

**Verificação:**
- p95 latency < 500ms

---

### 2.5 Database Connection Pool Exhausted

**Sintomas:**
- Erro "connection pool exhausted"
- Novas conexões rejeitadas

**Diagnóstico:**
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check connection pool settings
SHOW max_connections;
```

**Resolução:**
1. Aumentar `max_connections` em PostgreSQL
2. Aumentar connection pool na aplicação
3. Implementar connection recycling
4. Investigar connection leaks

**Verificação:**
- Conexões estáveis
- Sem erros de pool

---

## 3. TEMPLATE DE PLAYBOOK

```markdown
## [Nome do Alerta]

**Sintomas:**
- 
- 

**Diagnóstico:**
```bash
# Comandos de diagnóstico
```

**Resolução:**
1. 
2. 
3. 

**Verificação:**
- 
- 

**Tempo Estimado:** X minutos
**Severidade:** P1/P2/P3/P4
```

---

## 4. BACKLOG

- [ ] Criar playbook para cada alerta específico
- [ ] Adicionar comandos de diagnóstico automatizados
- [ ] Implementar auto-remediação para casos simples

---

## 5. LINKS CRUZADOS

- [[33_Alerting/INDEX]] ← Secção mãe
- [[33_Alerting/THRESHOLDS_ALERTAS]] → Thresholds
- [[33_Alerting/ROTAS_ESCALADA]] → Rotas de escalação
- [[26_Runbooks/INDEX]] → Runbooks detalhados
