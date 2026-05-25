# RECONCILIACAO — Reconciliação de Apostas

**ID:** `OP-005` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Reconciliar apostas executadas pelo sistema com o histórico do bookmaker para garantir precisão.

---

## 2. PROCESSO

```python
def reconcile_bets(system_bets, bookmaker_history):
    """
    Reconcilia apostas do sistema com histórico do bookmaker.
    
    Args:
        system_bets: Apostas registradas pelo sistema
        bookmaker_history: Histórico do bookmaker
    
    Returns:
        Reconciliado, não reconciliado, divergências
    """
    reconciled = []
    unreconciled = []
    divergences = []
    
    for system_bet in system_bets:
        # Procurar aposta correspondente no histórico
        match = bookmaker_history[
            (bookmaker_history['game_id'] == system_bet['game_id']) &
            (bookmaker_history['timestamp'] == system_bet['timestamp'])
        ]
        
        if len(match) == 1:
            # Verificar se valores coincidem
            bk_bet = match.iloc[0]
            
            if (abs(bk_bet['stake'] - system_bet['stake']) < 0.01 and
                abs(bk_bet['odd'] - system_bet['odd']) < 0.01):
                reconciled.append(system_bet)
            else:
                divergences.append({
                    'system': system_bet,
                    'bookmaker': bk_bet
                })
        else:
            unreconciled.append(system_bet)
    
    return reconciled, unreconciled, divergences
```

---

## 3. DIVERGÊNCIAS COMUNS

| Tipo | Causa | Ação |
|------|-------|------|
| Stake diferente | Slippage ou rounding | Aceitar se < 1% |
| Odd diferente | Odds mudaram | Investigar |
| Aposta não encontrada | Falha de execução | Revisar logs |
| Aposta extra | Erro de sistema | Remover |

---

## 4. AUTOMAÇÃO

```python
def auto_reconcile():
    """Executa reconciliação automática diária."""
    system_bets = get_system_bets(yesterday)
    bk_history = fetch_bookmaker_history(yesterday)
    
    reconciled, unreconciled, divergences = reconcile_bets(system_bets, bk_history)
    
    # Atualizar status
    update_bet_status(reconciled, 'reconciled')
    update_bet_status(unreconciled, 'unreconciled')
    
    # Alertas
    if len(unreconciled) > 0:
        send_alert(f"⚠️ {len(unreconciled)} apostas não reconciliadas")
    
    if len(divergences) > 0:
        send_alert(f"⚠️ {len(divergences)} divergências encontradas")
```

---

## 5. CRITÉRIOS

- **100% reconciliado** ideal
- **< 5% não reconciliado** aceitável
- **Investigar se > 10%** não reconciliado

---

## 6. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[RECONCILIACAO_DIARIA]]
