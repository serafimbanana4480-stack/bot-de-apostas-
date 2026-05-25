# MONITORIZACAO_RISCO_JOGO — Monitorização de Risco por Jogo

**ID:** `RM-005` | **Fase:** #phase/3 | **Owner:** Risk Manager | **Status:** #status/active

---

## 1. OBJETIVO

Monitorizar risco por jogo individual para evitar overexposure.

---

## 2. MÉTRICAS POR JOGO

| Métrica | Limite | Ação |
|---------|--------|------|
| Stake máximo por jogo | 5% do bankroll | Reduzir stake |
| Apostas por jogo | 1 (moneyline) | Rejeitar adicional |
| Exposição por equipa | 10% do bankroll/dia | Parar apostas |

---

## 3. VERIFICAÇÃO

```python
def check_game_risk(game_id, proposed_stake):
    """
    Verifica se aposta excede limites por jogo.
    
    Args:
        game_id: ID do jogo
        proposed_stake: Stake proposto
    
    Returns:
        Boolean se aposta permitida
    """
    # 1. Verificar stake máximo por jogo
    max_stake_per_game = bankroll * 0.05
    
    if proposed_stake > max_stake_per_game:
        logger.warning(f"Stake excede máximo por jogo: {proposed_stake} > {max_stake_per_game}")
        return False
    
    # 2. Verificar se já existe aposta neste jogo
    existing_bets = get_bets_for_game(game_id)
    
    if len(existing_bets) > 0:
        logger.warning(f"Já existe aposta no jogo {game_id}")
        return False
    
    return True
```

---

## 4. EXPOSIÇÃO POR EQUIPA

```python
def check_team_exposure(team_id, proposed_stake):
    """
    Verifica exposição por equipa.
    
    Args:
        team_id: ID da equipa
        proposed_stake: Stake proposto
    
    Returns:
        Exposição total após aposta
    """
    # Obter apostas existentes para equipa hoje
    team_bets = get_bets_for_team_today(team_id)
    current_exposure = sum(b['stake'] for b in team_bets)
    
    total_exposure = current_exposure + proposed_stake
    max_exposure = bankroll * 0.10
    
    if total_exposure > max_exposure:
        logger.warning(f"Exposição por equipa excede limite: {total_exposure} > {max_exposure}")
        return None
    
    return total_exposure
```

---

## 5. CRITÉRIOS

- **Máximo 5%** por jogo
- **Máximo 1 aposta** por jogo
- **Máximo 10%** por equipa/dia

---

## 6. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]]
- [[EXPOSURE_LIMITS]]
