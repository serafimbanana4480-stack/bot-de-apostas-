# SOP_EXECUCAO_MANUAL — SOP de Execução Manual

**ID:** `SOP-004` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir procedimento para execução manual de apostas (se sistema automático falhar).

---

## 2. CONDIÇÕES PARA EXECUÇÃO MANUAL

- Sistema automático offline
- API bookmaker com problemas
- Situação de emergência
- Testes manuais

---

## 3. PROCEDIMENTO

```python
def manual_bet_execution():
    """
    Executa aposta manualmente.
    
    Passos:
    1. Obter sinal do modelo
    2. Calcular stake
    3. Verificar odds atuais
    4. Executar aposta manualmente
    5. Registar no sistema
    """
    # 1. Obter sinal
    signal = get_signal_from_model()
    
    # 2. Calcular stake
    stake = calculate_stake(signal['prob'], signal['odd'])
    
    # 3. Verificar odds
    current_odd = fetch_current_odd(signal['game_id'])
    
    if abs(current_odd - signal['odd']) / signal['odd'] > 0.02:
        logger.warning("Odds mudaram significativamente - rejeitar")
        return False
    
    # 4. Executar manualmente (instruções para operador)
    print(f"Executar aposta manual:")
    print(f"  Game: {signal['game_id']}")
    print(f"  Stake: €{stake:.2f}")
    print(f"  Odd: {current_odd}")
    
    # 5. Registar
    register_manual_bet(signal, stake, current_odd)
    
    return True
```

---

## 4. CHECKLIST

- [ ] Verificar que sistema automático está offline
- [ ] Obter sinal do modelo
- [ ] Calcular stake
- [ ] Verificar odds atuais
- [ ] Executar aposta no bookmaker
- [ ] Registar no sistema

---

## 5. CRITÉRIOS

- **Apenas se automático** falhar
- **Documentar** todas as apostas manuais
- **Revisar** após execução

---

## 6. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[STOP_SYSTEMS]]
