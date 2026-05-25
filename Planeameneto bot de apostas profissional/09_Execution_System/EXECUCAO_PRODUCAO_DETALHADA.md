# EXECUÇÃO EM PRODUÇÃO DETALHADA — PASSO A PASSO

**ID:** `OPS-001` | **Fase:** #phase/4-6 | **Owner:** Operations Lead + DevOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar o funcionamento diário do sistema em produção, desde a ingestão de dados até a distribuição de sinais e registo de resultados.

---

## 2. AGENDA DIÁRIA (DIAS DE JOGOS NBA)

```
08:00 — Ingestão inicial de dados
10:00 — Motor de decisão (execução 1)
12:00 — Motor de decisão (execução 2)
14:00 — Motor de decisão (execução 3)
16:00 — Motor de decisão (execução 4)
18:00+ — Monitorização contínua
Pós-jogo — Registo de resultados e PnL
```

---

## 3. FLUXO DETALHADO POR EXECUÇÃO

### 3.1 Ingestão de Dados (08:00)

**Script:** `ingest_data.py`

**Passos:**
```python
def morning_ingestion():
    # 1. Recolher odds iniciais da Betfair
    odds_betfair = betfair_api.get_odds(
        market_ids=nba_market_ids,
        event_type_id='NBA'
    )
    
    # 2. Atualizar estatísticas pré-jogo
    stats = nba_api.get_team_stats()
    
    # 3. Atualizar lesões
    injuries = espn_api.get_injuries()
    
    # 4. Calcular distâncias de viagem
    distances = calculate_travel_distances()
    
    # 5. Validar integridade
    validate_data_integrity([odds_betfair, stats, injuries, distances])
    
    # 6. Persistir em PostgreSQL
    save_to_postgreSQL({
        'odds': odds_betfair,
        'stats': stats,
        'injuries': injuries,
        'distances': distances
    })
    
    # 7. Enviar heartbeat
    send_telegram_alert("Ingestão matinal completada ✅")
```

**Validação de Integridade:**
```python
def validate_data_integrity(data_sources):
    for source in data_sources:
        if source.is_empty():
            raise ValueError(f"{source.name} está vazio")
        if source.has_nulls(critical_columns):
            raise ValueError(f"{source.name} tem nulls em colunas críticas")
        if source.has_duplicates():
            raise ValueError(f"{source.name} tem duplicados")
```

### 3.2 Motor de Decisão (10:00, 12:00, 14:00, 16:00)

**Script:** `decision_engine.py`

**Passos:**
```python
def run_decision_engine():
    # 1. Carregar jogos do dia
    games = load_games_for_today()
    
    signals = []
    
    for game in games:
        # 2. Calcular features atualizadas
        features = calculate_features(game, include_decay=True)
        
        # 3. Inferência do modelo primário
        p_modelo = primary_model.predict_proba(features)[1]
        
        # 4. Aplicar calibração isotónica
        p_calibrated = calibrate_probability(p_modelo, game['regime'])
        
        # 5. Obter odd mais recente da Betfair
        odd_betfair = betfair_api.get_latest_odd(game['market_id'])
        
        # 6. Calcular edge
        edge = p_calibrated * odd_betfair - 1
        
        # 7. Se edge > 4%, consultar meta-modelo
        if edge > 0.04:
            meta_features = build_meta_features(
                p_calibrated, edge, game['context']
            )
            p_meta = meta_model.predict_proba(meta_features)[1]
            
            # 8. Se P_meta > 0.6, preparar sinal
            if p_meta > 0.60:
                # 9. Calcular stake (Kelly fraccionado)
                stake = calculate_kelly_stake(
                    p_calibrated, 
                    odd_betfair, 
                    current_bankroll
                )
                
                # 10. Aplicar limites de exposição
                stake = apply_exposure_limits(
                    stake,
                    game['team'],
                    game['date']
                )
                
                signal = {
                    'game_id': game['id'],
                    'market': game['market'],
                    'selection': game['selection'],
                    'odd': odd_betfair,
                    'edge': edge,
                    'p_modelo': p_calibrated,
                    'p_meta': p_meta,
                    'stake_percent': stake * 100,
                    'stake_euros': stake * current_bankroll
                }
                
                signals.append(signal)
    
    # 11. Enviar sinais para Redis
    cache_signals(signals)
    
    # 12. Registar sinais em PostgreSQL
    save_signals_to_db(signals)
    
    # 13. Enviar resumo via Telegram
    send_signal_summary(signals)
    
    return signals
```

### 3.3 Distribuição de Sinais (Imediato após Motor de Decisão)

**Script:** `telegram_bot.py`

**Passos:**
```python
def distribute_signals(signals):
    for signal in signals:
        # 1. Formatar mensagem
        message = format_signal_message(signal)
        
        # 2. Enviar para Telegram de subscritores
        for subscriber in active_subscribers:
            telegram_bot.send_message(
                chat_id=subscriber['telegram_id'],
                text=message
            )
        
        # 3. Enviar email de resumo (opcional)
        if subscriber['email_notifications']:
            sendgrid.send_email(
                to=subscriber['email'],
                subject=f"Novo Sinal: {signal['game']}",
                body=message
            )
```

**Formato da Mensagem:**
```python
def format_signal_message(signal):
    return f"""
🏀 NOVO SINAL NBA

📊 {signal['game']}
🎯 Mercado: {signal['market']}
💰 Odd: {signal['odd']:.2f}
📈 Edge: {signal['edge']*100:.1f}%
🔮 Confiança: {signal['p_meta']*100:.0f}%
💵 Stake: {signal['stake_percent']:.1f}% ({signal['stake_euros']:.0f}€)

⚠️ Aposte apenas o que pode perder.
    """.strip()
```

### 3.4 Execução Manual pelo Utilizador

**Fluxo do Utilizador:**
1. Recebe mensagem Telegram
2. Abre aplicação Betfair
3. Navega para mercado especificado
4. Verifica odd atual (pode ter mudado)
5. Coloca aposta manualmente
6. Confirma execução

**Compliance:** O sistema NUNCA coloca apostas automaticamente na fase manual (Mês 4-5).

### 3.5 Registo de Resultados (Pós-Jogo)

**Script:** `record_results.py`

**Passos:**
```python
def record_game_results():
    # 1. Obter jogos finalizados
    finished_games = get_finished_games()
    
    for game in finished_games:
        # 2. Obter resultado oficial
        result = nba_api.get_game_result(game['id'])
        
        # 3. Obter odds de fecho da Betfair
        odds_close = betfair_api.get_closing_odd(game['market_id'])
        
        # 4. Calcular PnL para cada sinal
        signals = get_signals_for_game(game['id'])
        
        for signal in signals:
            # 5. Verificar se aposta foi executada
            bet_executed = check_if_bet_was_placed(signal)
            
            if bet_executed:
                # 6. Calcular slippage real
                slippage = (bet_executed['odd'] - signal['odd']) / signal['odd']
                
                # 7. Calcular PnL
                if result['winner'] == signal['selection']:
                    pnl = bet_executed['stake'] * (bet_executed['odd'] - 1) * (1 - 0.05)
                else:
                    pnl = -bet_executed['stake']
                
                # 8. Calcular CLV real
                clv = (odds_close - signal['odd']) / signal['odd']
                
                # 9. Registar em BD
                save_bet_result({
                    'signal_id': signal['id'],
                    'game_id': game['id'],
                    'result': result['winner'],
                    'pnl': pnl,
                    'clv': clv,
                    'slippage': slippage,
                    'timestamp': datetime.now()
                })
        
        # 10. Atualizar bankroll
        update_bankroll(calculate_total_pnl())
```

---

## 4. GESTÃO DE CIRCUIT BREAKERS

### 4.1 Circuit Breaker de Drawdown

```python
def check_drawdown_circuit_breaker():
    current_drawdown = calculate_current_drawdown()
    
    if current_drawdown > 0.15:  # 15%
        # Ativar circuit breaker
        activate_circuit_breaker('drawdown')
        
        # Reduzir todos os stakes em 50%
        reduce_all_stakes(0.5)
        
        # Enviar alerta
        send_telegram_alert(
            f"⚠️ CIRCUIT BREAKER ATIVADO\n"
            f"Drawdown: {current_drawdown*100:.1f}%\n"
            f"Stakes reduzidos em 50%"
        )
        
        # Notificar para revisão manual
        notify_manual_review_needed()
        
        return True
    
    elif current_drawdown < 0.10:  # 10%
        # Desativar circuit breaker
        deactivate_circuit_breaker('drawdown')
        restore_normal_stakes()
        
        send_telegram_alert("✅ Circuit breaker desativado")
        
        return False
    
    return False
```

### 4.2 Circuit Breaker de Perdas Consecutivas

```python
def check_consecutive_losses():
    consecutive_losses = get_consecutive_losses()
    
    if consecutive_losses >= 7:
        # Pausar sistema por 2 horas
        pause_system(duration_hours=2)
        
        send_telegram_alert(
            f"⚠️ 7 PERDAS CONSECUTIVAS\n"
            f"Sistema pausado por 2 horas\n"
            f"Revisão manual necessária"
        )
        
        notify_manual_review_needed()
        return True
    
    return False
```

### 4.3 Circuit Breaker de Feed Offline

```python
def check_feed_health():
    last_odds_update = get_last_odds_update_timestamp()
    time_since_update = datetime.now() - last_odds_update
    
    if time_since_update > timedelta(minutes=5):
        # Feed offline
        pause_system()
        block_new_signals()
        
        send_telegram_alert(
            f"⚠️ FEED DE ODDS OFFLINE\n"
            f"Última atualização: {time_since_update}\n"
            f"Sistema pausado"
        )
        
        return True
    
    return False
```

---

## 5. CÁLCULO DE STAKES (KELLY FRACCIONADO)

### 5.1 Fórmula

```python
def calculate_kelly_stake(p_modelo, odd, bankroll, k=0.5):
    """
    k: fração de Kelly (0.5 = meio Kelly)
    """
    edge = p_modelo * odd - 1
    
    if edge <= 0:
        return 0.0
    
    # Fórmula de Kelly
    kelly_fraction = k * edge / (odd - 1)
    
    # Calcular stake em euros
    stake_euros = kelly_fraction * bankroll
    
    return stake_euros
```

### 5.2 Limites de Exposição

```python
def apply_exposure_limits(stake_euros, team, date):
    current_bankroll = get_current_bankroll()
    
    # Limite 1: Máximo 2% do bankroll por aposta
    max_stake = 0.02 * current_bankroll
    stake_euros = min(stake_euros, max_stake)
    
    # Limite 2: Máximo 4% do bankroll por jogo
    total_exposure_game = get_total_exposure_for_game(team, date)
    remaining_exposure = 0.04 * current_bankroll - total_exposure_game
    stake_euros = min(stake_euros, max(0, remaining_exposure))
    
    # Limite 3: Máximo 12% do bankroll por dia
    total_exposure_day = get_total_exposure_for_date(date)
    remaining_exposure_day = 0.12 * current_bankroll - total_exposure_day
    stake_euros = min(stake_euros, max(0, remaining_exposure_day))
    
    return stake_euros
```

---

## 6. MONITORIZAÇÃO EM TEMPO REAL

### 6.1 Métricas Monitorizadas

| Métrica | Frequência | Alerta se |
|---------|------------|-----------|
| Status do feed Betfair | A cada 5 min | Offline > 5 min |
| Status do feed NBA | A cada 5 min | Offline > 5 min |
| Número de sinais gerados | A cada execução | < 2 ou > 20 |
| CLV médio (últimas 50) | Diário | < 0% |
| Drawdown atual | Diário | > 15% |
| Bankroll | Diário | < 50% do inicial |

### 6.2 Dashboard (Grafana)

**Painéis:**
1. ROI acumulado vs tempo
2. CLV médio rolling (7, 30, 90 dias)
3. Win rate por regime
4. Drawdown atual e máximo
5. Status dos feeds (uptime, latência)
6. Número de sinais por dia
7. Bankroll evolution

---

## 7. MANUTENÇÃO PROGRAMADA

### 7.1 Diária

- [ ] Verificar heartbeat dos scripts
- [ ] Verificar integridade dos dados
- [ ] Verificar espaço em disco
- [ ] Revisar logs de erros

### 7.2 Semanal

- [ ] Retreinar modelo (segunda-feira)
- [ ] Analisar drift de features (PSI)
- [ ] Revisar métricas de performance
- [ ] Backup da base de dados
- [ ] Atualizar documentação se necessário

### 7.3 Mensal

- [ ] Revisão completa de performance
- [ ] Análise de regressão com backtest
- [ ] Atualização de dependências
- [ ] Auditoria de segurança
- [ ] Relatório financeiro

---

## 8. PROCEDIMENTOS DE EMERGÊNCIA

### 8.1 Feed Offline

**Passos:**
1. Verificar conectividade com Betfair API
2. Verificar se API key expirou
3. Verificar se há rate limit atingido
4. Se problema persistir > 30 min, notificar suporte Betfair

### 8.2 Banco de Dados Down

**Passos:**
1. Verificar se serviço PostgreSQL está running
2. Verificar espaço em disco
3. Verificar logs de erros
4. Se necessário, restaurar do backup mais recente

### 8.3 Telegram Bot Falha

**Passos:**
1. Verificar token do bot
2. Verificar conectividade com API Telegram
3. Verificar se bot foi banido
4. Ativar backup (email notifications)

---

## 9. BACKLOG

- [ ] Implementar script de ingestão matinal
- [ ] Implementar motor de decisão
- [ ] Implementar distribuição de sinais via Telegram
- [ ] Implementar registo de resultados
- [ ] Implementar circuit breakers
- [ ] Implementar dashboard Grafana
- [ ] Implementar alertas automáticos
- [ ] Criar runbooks de emergência

---

## 10. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[18_Operations/INDEX]] → Operações diárias
- [[25_SOPs/INDEX]] → Procedimentos padrão
- [[26_Runbooks/INDEX]] → Resposta a incidentes
- [[33_Alerting/INDEX]] → Sistema de alertas
