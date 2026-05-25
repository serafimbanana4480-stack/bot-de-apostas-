# FILTROS_QUALIDADE — Filtros de Qualidade

**ID:** `DE-009` | **Fase:** #phase/2 | **Owner:** Data Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir filtros de qualidade para dados antes de treino.

---

## 2. FILTROS POR CAMPO

| Campo | Filtro | Threshold |
|-------|--------|-----------|
| Odds | Min/Max | 1.01 - 100 |
| Probabilidade | Min/Max | 0.01 - 0.99 |
| Liquidez | Mínimo | €10,000 |
| Time to game | Mínimo | 1 hora |
| Histórico | Mínimo jogos | 10 jogos |

---

## 3. IMPLEMENTAÇÃO

```python
def apply_quality_filters(data):
    """
    Aplica filtros de qualidade aos dados.
    
    Args:
        data: DataFrame de dados brutos
    
    Returns:
        DataFrame filtrado
    """
    df = data.copy()
    
    # 1. Filtro de odds
    df = df[(df['odd'] >= 1.01) & (df['odd'] <= 100)]
    
    # 2. Filtro de probabilidade
    df = df[(df['prob'] >= 0.01) & (df['prob'] <= 0.99)]
    
    # 3. Filtro de liquidez
    df = df[df['liquidity'] >= 10000]
    
    # 4. Filtro de tempo
    df = df[df['time_to_game'] >= 3600]  # 1 hora
    
    # 5. Filtro de histórico
    team_games = df.groupby('team_id').size()
    valid_teams = team_games[team_games >= 10].index
    df = df[df['team_id'].isin(valid_teams)]
    
    logger.info(f"Filtrados {len(data)} -> {len(df)} linhas")
    
    return df
```

---

## 4. REPORT DE QUALIDADE

```python
def generate_quality_report(original, filtered):
    """
    Gera report de qualidade dos filtros.
    
    Args:
        original: DataFrame original
        filtered: DataFrame filtrado
    
    Returns:
        Report de qualidade
    """
    report = {
        'original_rows': len(original),
        'filtered_rows': len(filtered),
        'retention_rate': len(filtered) / len(original),
        'dropped_rows': len(original) - len(filtered)
    }
    
    return report
```

---

## 5. CRITÉRIOS

- **Aplicar filtros** antes de treino
- **Retenção > 80%** ideal
- **Revisar** se retenção < 50%

---

## 6. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]]
- [[VALIDACAO_DADOS]]
