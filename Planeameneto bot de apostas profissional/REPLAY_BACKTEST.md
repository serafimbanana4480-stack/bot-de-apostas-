# REPLAY_BACKTEST — Reprodução de Backtest

**ID:** `BT-001` | **Fase:** #phase/3 | **Owner:** Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Reproduzir backtests exatamente como foram executados originalmente para verificar resultados e debugging.

---

## 2. CONCEITO

Replay backtest usa snapshots de dados e configurações para re-executar o backtest e comparar resultados com o original.

---

## 3. IMPLEMENTAÇÃO

```python
def replay_backtest(snapshot_file, model_version, config):
    """
    Reproduz backtest a partir de snapshot.
    
    Args:
        snapshot_file: Arquivo de snapshot de dados
        model_version: Versão do modelo
        config: Configuração original do backtest
    
    Returns:
        Métricas do replay
    """
    # Carregar snapshot
    snapshot = joblib.load(snapshot_file)
    data = snapshot['data']
    
    # Carregar modelo
    model = load_model_version(model_version)
    
    # Re-executar backtest
    results = run_backtest(data, model, config)
    
    return results
```

---

## 4. COMPARAÇÃO DE RESULTADOS

```python
def compare_backtests(original_results, replay_results, tolerance=0.001):
    """
    Compara resultados originais vs replay.
    
    Returns:
        Boolean se resultados são iguais dentro da tolerância
    """
    metrics = ['roi', 'clv', 'sharpe', 'n_bets']
    
    for metric in metrics:
        diff = abs(original_results[metric] - replay_results[metric])
        if diff > tolerance:
            print(f"Diferença em {metric}: {diff:.4f}")
            return False
    
    return True
```

---

## 5. DEBUGGING

Se replay difere do original:

1. **Verificar versões** de código e modelo
2. **Verificar snapshot** - dados completos?
3. **Verificar seeds** - random state fixo?
4. **Verificar configuração** - parâmetros idênticos?

---

## 6. CRITÉRIOS

- **Replay deve ser idêntico** ao original (tolerância < 0.1%)
- **Snapshot versionado** com git commit
- **Configuração registrada** em MLflow

---

## 7. LINKS CRUZADOS

- [[06_Backtesting/INDEX]]
- [[REPRODUCIBILITY]]
