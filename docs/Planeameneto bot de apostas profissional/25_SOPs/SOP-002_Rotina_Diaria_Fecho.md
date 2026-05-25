# SOP-002 — Rotina Diária de Fecho

**ID:** `SOP-002` | **Fase:** Todas | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Estabelecer a rotina diária de fecho do sistema de apostas.

---

## 2. CHECKLIST

- [ ] Parar bot de apostas
- [ ] Verificar todas as apostas executadas
- [ ] Reconciliar PnL
- [ ] Verificar CLV do dia
- [ ] Gerar relatório diário
- [ ] Backup do database
- [ ] Documentar incidentes
- [ ] Preparar próximo turno

---

## 3. PROCEDIMENTO DETALHADO

### 3.1 Parar Motor de Decisão (1 min)

```bash
# Verificar sinais pendentes
python scripts/check_pending_signals.py

# Se não houver sinais pendentes: parar motor
python scripts/stop_decision_engine.py

# Confirmar paragem
docker compose ps | grep api
```

**Critério de passagem:** Motor reporta "STOPPED", nenhuma aposta em aberto sem resultado.

### 3.2 Verificar Apostas Executadas (2 min)

```bash
# Listar apostas do dia
python scripts/get_daily_bets.py --date $(date +%Y-%m-%d)

# Verificar se todas têm resultado
python scripts/check_bet_results.py
```

**Critério de passagem:** 100% das apostas do dia têm resultado (WIN/LOSS/PUSH/VOID).

### 3.3 Reconciliar PnL (3 min)

```bash
# Calcular PnL real do dia
python scripts/calculate_daily_pnl.py

# Comparar com PnL esperado pelo modelo
python scripts/compare_expected_vs_real_pnl.py
```

**Critério de passagem:** Divergência entre PnL real e esperado < 5% (explicável por slippage).

### 3.4 Verificar CLV do Dia (2 min)

```bash
# Calcular CLV médio do dia
python scripts/calculate_daily_clv.py

# Comparar com benchmark
python scripts/compare_clv_benchmark.py
```

**Critério de passagem:** CLV médio > 0% (edge positivo confirmado).

### 3.5 Gerar Relatório Diário (2 min)

```bash
# Gerar relatório automatizado
python scripts/generate_daily_report.py --date $(date +%Y-%m-%d)

# Enviar para Telegram
python scripts/send_report_telegram.py --report daily_$(date +%Y-%m-%d).md
```

**Critério de passagem:** Relatório enviado, contém: nº apostas, PnL, CLV, drawdown atual.

### 3.6 Backup do Database (3 min)

```bash
# Executar backup manual (além do automático)
/opt/valuebetting/scripts/backup.sh

# Verificar se backup foi criado
ls -lh /opt/backups/ | tail -5
```

**Critério de passagem:** Ficheiro `.tar.gz` criado nas últimas 5 minutos, tamanho > 1MB.

### 3.7 Documentar Incidentes

- Se ocorreu algum incidente: criar nota em `27_Postmortems/`
- Se PnL < -5% do bankroll: notificar Risk Manager
- Se CLV < 0% por 3 dias consecutivos: criar alerta para reavaliação do modelo

### 3.8 Preparar Próximo Turno

- Verificar calendário NBA para amanhã
- Identificar jogos com potencial de valor (alto volume esperado)
- Ajustar limites de exposição se necessário (após consulta Risk Manager)

---

## 4. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
