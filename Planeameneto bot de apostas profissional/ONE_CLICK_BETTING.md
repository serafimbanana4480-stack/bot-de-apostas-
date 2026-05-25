# ONE_CLICK_BETTING — One-Click Betting

**ID:** `OP-020` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Permitir execução de aposta com um clique para operações rápidas.

---

## 2. FLUXO

1. Sistema gera sinal
2. Operador revê
3. Clique "Apostar"
4. Sistema executa automaticamente
5. Confirmação imediata

---

## 3. IMPLEMENTAÇÃO

```python
def one_click_bet(signal_id):
    """
    Executa aposta com um clique.
    
    Args:
        signal_id: ID do sinal a apostar
    
    Returns:
        Resultado da execução
    """
    # 1. Obter sinal
    signal = get_signal(signal_id)
    
    # 2. Verificar odds atuais
    current_odd = fetch_current_odd(signal['game_id'])
    
    # 3. Verificar se odds mudou
    if abs(current_odd - signal['odd']) / signal['odd'] > 0.02:
        return {'status': 'rejected', 'reason': 'Odds mudaram'}
    
    # 4. Calcular stake
    stake = calculate_stake(signal['prob'], current_odd)
    
    # 5. Executar aposta
    result = execute_bet(signal['game_id'], stake, current_odd)
    
    # 6. Registar
    register_bet(signal_id, stake, current_odd, result)
    
    return result
```

---

## 4. UI

Interface simples com:
- Lista de sinais pendentes
- Botão "Apostar" por sinal
- Status em tempo real
- Confirmação visual

---

## 5. CRITÉRIOS

- **Verificar odds** antes de executar
- **Rejeitar se odds mudou** > 2%
- **Confirmação imediata** após execução

---

## 6. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[RETRY_LOGIC]]
