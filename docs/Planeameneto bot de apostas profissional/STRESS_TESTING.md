# STRESS_TESTING — Testes de Stress

**ID:** `OP-007` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Testar o sistema sob condições extremas para garantir robustez e identificar limites.

---

## 2. CENÁRIOS DE STRESS

| Cenário | Descrição | Objetivo |
|---------|-----------|---------|
| Volume elevado | 100+ sinais por dia | Testar capacidade |
| Odds voláteis | Odds mudam rapidamente | Testar timing |
| API timeouts | Bookmaker API lenta | Testar retry |
| Stake máximo | Apostas de 5% do bankroll | Testar limites |

---

## 3. TESTE DE VOLUME

```python
def stress_test_volume():
    """Testa sistema com volume elevado."""
    # Gerar 100 sinais fictícios
    mock_signals = generate_mock_signals(n=100)
    
    # Executar pipeline
    results = []
    for signal in mock_signals:
        try:
            result = execute_bet(signal)
            results.append({'status': 'success', 'signal': signal})
        except Exception as e:
            results.append({'status': 'failed', 'error': str(e), 'signal': signal})
    
    success_rate = sum(1 for r in results if r['status'] == 'success') / len(results)
    
    if success_rate < 0.95:
        print(f"⚠️ Success rate baixo: {success_rate:.1%}")
    
    return success_rate
```

---

## 4. TESTE DE ODDS VOLÁTEIS

```python
def stress_test_volatile_odds():
    """Testa sistema com odds que mudam rapidamente."""
    # Simular odds que mudam a cada segundo
    for _ in range(50):
        signal = generate_signal()
        original_odd = signal['odd']
        
        # Delay 1 segundo
        time.sleep(1)
        
        # Verificar se odds mudaram
        current_odd = fetch_current_odd(signal['game_id'])
        
        if abs(current_odd - original_odd) / original_odd > 0.02:
            print(f"Odds mudaram: {original_odd} → {current_odd}")
            # Sistema deve rejeitar aposta
```

---

## 5. TESTE DE API TIMEOUT

```python
def stress_test_api_timeout():
    """Testa retry logic com API timeouts."""
    # Simular timeouts
    with patch('betting_api.place_bet', side_effect=TimeoutError):
        try:
            place_bet_with_retry(mock_bet)
            print("❌ Deveria ter falhado após retries")
        except TimeoutError:
            print("✅ Retry funcionou corretamente")
```

---

## 6. CRITÉRIOS

- **Success rate > 95%** em testes de volume
- **Rejeitar apostas** se odds mudaram > 2%
- **Retry funcionar** após 3 tentativas
- **Sistema não crashar** sob stress

---

## 7. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[RETRY_LOGIC]]
