# SOP-004 — Resposta a Circuit Breaker

**ID:** `SOP-004` | **Fase:** Todas | **Owner:** Risk Manager | **Status:** #status/pending

---

## 1. OBJETIVO

Procedimento para responder quando o circuit breaker é ativado.

---

## 2. CHECKLIST

- [ ] Identificar causa do circuit breaker
- [ ] Verificar drawdown atual
- [ ] Verificar CLV recente
- [ ] Investigar anomalias no modelo
- [ ] Decidir: pausar ou continuar com stake reduzido
- [ ] Documentar decisão
- [ ] Notificar stakeholders
- [ ] Monitorizar recuperação

---

## 3. PROCEDIMENTO DETALHADO

### 3.1 Identificar Circuit Breaker Ativado (1 min)

```bash
# Verificar qual circuit breaker disparou
python scripts/check_circuit_breaker.py

# Ou consultar dashboard Grafana: http://vps-ip:3000/d/circuit-breakers
```

| Circuit Breaker | Trigger | Ação Automática |
|----------------|---------|-----------------|
| **Alpha** | Drawdown > 15% | Stakes cortadas 50% |
| **Beta** | 5 perdas consecutivas | Pausa 1h, notificação |
| **Gamma** | Feed offline > 5 min | Nenhum sinal novo |
| **Delta** | CLV 3d < 0% | Alerta, revisão modelo |
| **Epsilon** | Execution errors > 10/dia | Pausa execução |
| **Zeta** | Bankroll < 50% inicial | STOP total |

### 3.2 Responder por Tipo de Circuit Breaker

#### Alpha — Drawdown > 15%
1. Verificar drawdown atual: `python scripts/get_drawdown.py`
2. Se drawdown < 20%: continuar com stakes 50% até recovery < 10%
3. Se drawdown 20-30%: reduzir stakes para 25%, notificar Risk Manager
4. Se drawdown > 30%: STOP total, convocar reunião de emergência

#### Beta — 5 Perdas Consecutivas
1. Verificar se as 5 perdas são estatisticamente anómalas (p-value < 0.05)
2. Se anómalo: pausa 1h + análise de modelo drift
3. Se esperado (variância normal): reduzir stakes 25% por 24h
4. Se 10 perdas consecutivas: escalonar para CTO

#### Gamma — Feed Offline
1. Verificar conectividade: `ping api.betfair.com`, `curl nba-api`
2. Se problema temporário (< 15 min): aguardar retorno
3. Se problema prolongado: ativar fonte de dados secundária (Basketball-Reference scraping)
4. Se > 30 min offline: cancelar sinais do dia, notificar subscritores

#### Delta — CLV 3d Negativo
1. Calcular CLV dos últimos 7 dias: `python scripts/get_clv_7d.py`
2. Se CLV 7d > 0%: possível variância, manter operações
3. Se CLV 7d < 0%: iniciar análise de modelo drift (ver `48_Data_Drift/`)
4. Se CLV 30d < 0%: considerar paper trading até re-treino

#### Epsilon — Execution Errors
1. Verificar logs: `docker compose logs api | grep ERROR | tail -20`
2. Identificar padrão: API timeout? Auth fail? Parse error?
3. Corrigir causa raiz antes de retomar
4. Se não resolvido em 30 min: escalonar para DevOps

#### Zeta — Bankroll Crítico
1. Verificar bankroll: `python scripts/get_bankroll.py`
2. STOP total de todas as operações com dinheiro real
3. Reavaliar estratégia de bankroll management
4. Considerar pausa de 1-2 semanas + re-treino completo

### 3.3 Documentar e Comunicar

- Criar nota em `27_Postmortems/` com: timestamp, circuit breaker, causa, ação, decisão
- Notificar subscritores via Telegram se impacto > 1h de pausa
- Atualizar `08_Risk_Management/INDEX.md` com lições aprendidas

---

## 4. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Circuit breakers
