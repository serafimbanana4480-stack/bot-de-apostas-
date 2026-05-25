# Exposure Limits

**ID:** RM-005 | **Fase:** Fase 4+ | **Owner:** Risk Manager

---

## 1. OBJETIVO

Definir limites de exposição para controlar risco agregado e evitar concentração excessiva em mercados, times, ou períodos.

---

## 2. PRINCÍPIOS

1. **Diversificação:** Nunca concentrar > 20% da banca em um único tipo de exposição
2. **Correlação:** Ajustar stakes baseado em correlação entre apostas
3. **Tempo:** Limitar exposição por dia/semana/mês
4. **Liquidez:** Nunca apostar > 10% do volume disponível

---

## 3. LIMITES DE EXPOSIÇÃO

### 3.1 Por Mercado

| Mercado | Exposição Máxima | Stake Máximo por Aposta |
|---------|------------------|-------------------------|
| NBA Moneyline | 15% da banca | 2% Kelly |
| NBA Spread | 20% da banca | 2.5% Kelly |
| NBA Totals | 15% da banca | 2% Kelly |
| Player Props | 10% da banca | 1.5% Kelly |
| NFL Moneyline | 10% da banca | 2% Kelly |

### 3.2 Por Time

| Cenário | Limite |
|---------|--------|
| Mesmo time em apostas diferentes | 10% da banca |
| Mesmo jogo (multi-bets) | 5% da banca |
| Back-to-back games mesmo time | 8% da banca |

### 3.3 Por Período

| Período | Exposição Máxima | Apostas Máximas |
|---------|------------------|-----------------|
| Dia | 25% da banca | 10 apostas |
| Semana | 60% da banca | 40 apostas |
| Mês | 100% da banca | 150 apostas |

### 3.4 Por Liquidez

| Volume Disponível | Stake Máximo |
|-------------------|--------------|
| < €1,000 | 0.5% Kelly |
| €1,000 - €5,000 | 1% Kelly |
| €5,000 - €20,000 | 1.5% Kelly |
| > €20,000 | 2% Kelly |

---

## 4. CÁLCULO DE EXPOSIÇÃO AGREGADA

### 4.1 Fórmula

```python
def calculate_aggregated_exposure(bets):
    """
    Calcula exposição agregada considerando correlações
    """
    total_exposure = 0
    
    for bet in bets:
        # Exposição base = stake
        base_exposure = bet['stake']
        
        # Ajuste por correlação
        correlation_factor = 1.0
        for other_bet in bets:
            if bet['game_id'] == other_bet['game_id']:
                correlation_factor *= 0.7  # Penalização por mesmo jogo
            elif bet['team_id'] == other_bet['team_id']:
                correlation_factor *= 0.85  # Penalização por mesmo time
        
        adjusted_exposure = base_exposure * correlation_factor
        total_exposure += adjusted_exposure
    
    return total_exposure
```

### 4.2 Validação

```python
def validate_exposure_limits(new_bet, current_bets, bankroll):
    """
    Valida se nova aposta respeita todos os limites de exposição
    """
    # Calcular exposição atual
    current_exposure = calculate_aggregated_exposure(current_bets)
    
    # Calcular exposição com nova aposta
    all_bets = current_bets + [new_bet]
    new_exposure = calculate_aggregated_exposure(all_bets)
    
    # Validar limites
    checks = {
        'market_exposure': new_exposure <= get_market_limit(new_bet['market']) * bankroll,
        'team_exposure': check_team_exposure(all_bets, new_bet['team_id'], bankroll),
        'daily_exposure': check_daily_exposure(all_bets, bankroll),
        'liquidity': new_bet['stake'] <= new_bet['available_volume'] * 0.10
    }
    
    return all(checks.values()), checks
```

---

## 5. SISTEMA DE APROVAÇÃO

### 5.1 Níveis de Aprovação

| Exposição | Nível de Aprovação |
|-----------|-------------------|
| < 10% da banca | Automático |
| 10-20% da banca | Warning (requer confirmação) |
| > 20% da banca | Bloqueado (requer aprovação manual) |

### 5.2 Warnings

**Se exposição > 15% da banca:**
- Alerta no dashboard
- Notificação Telegram
- Requer confirmação explícita

**Se exposição > 20% da banca:**
- Bloqueio automático
- Revisão manual obrigatória
- Justificação em audit log

---

## 6. MONITORAMENTO

### 6.1 Dashboard de Exposição

**Métricas em Tempo Real:**
- Exposição total atual
- Exposição por mercado
- Exposição por time
- Exposição por período (dia/semana/mês)
- Capacidade disponível

### 6.2 Alertas

| Condição | Severidade | Ação |
|----------|------------|------|
| Exposição > 20% da banca | CRITICAL | Parar novas apostas |
| Exposição > 15% da banca | HIGH | Warning |
| 5+ apostas mesmo dia | MEDIUM | Warning |
| Liquidez < 50% do normal | HIGH | Reduzir stakes |

---

## 7. AJUSTES DINÂMICOS

### 7.1 Ajuste por Volatilidade

```python
def adjust_stake_by_volatility(base_kelly_stake, market_volatility):
    """
    Ajusta stake baseado na volatilidade do mercado
    """
    if market_volatility > 2.0:  # Alta volatilidade
        return base_kelly_stake * 0.5
    elif market_volatility > 1.5:  # Volatilidade moderada
        return base_kelly_stake * 0.75
    else:  # Volatilidade normal
        return base_kelly_stake
```

### 7.2 Ajuste por Confiança do Modelo

```python
def adjust_stake_by_confidence(base_kelly_stake, confidence_score):
    """
    Ajusta stake baseado na confiança do modelo
    """
    if confidence_score < 0.6:  # Baixa confiança
        return base_kelly_stake * 0.5
    elif confidence_score < 0.8:  # Confiança moderada
        return base_kelly_stake * 0.75
    else:  # Alta confiança
        return base_kelly_stake
```

---

## 8. BACKLOG TÉCNICO

- [ ] Implementar sistema de cálculo de exposição agregada
- [ ] Criar dashboard de exposição em tempo real
- [ ] Configurar alertas de exposição
- [ ] Implementar ajustes dinâmicos de stake
- [ ] Adicionar validação de liquidez
- [ ] Criar audit log de violações de limites

---

## 9. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]] ← Índice principal
- [[08_Risk_Management/KELLY_FRACIONADO]] → Cálculo de Kelly
- [[08_Risk_Management/DRAWDOWN_CONTROL]] → Controle de drawdown
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Circuit breakers
