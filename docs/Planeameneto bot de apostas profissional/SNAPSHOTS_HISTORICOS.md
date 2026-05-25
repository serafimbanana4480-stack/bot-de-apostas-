# SNAPSHOTS_HISTORICOS — Snapshots Históricos

**ID:** `OP-016` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Gerir snapshots históricos de dados para reprodutibilidade de backtests.

---

## 2. CRIAÇÃO DE SNAPSHOT

```python
def create_data_snapshot(date):
    """
    Cria snapshot dos dados numa data específica.
    
    Args:
        date: Data do snapshot
    
    Returns:
        ID do snapshot
    """
    snapshot_id = f"snapshot_{date.strftime('%Y%m%d')}"
    
    # 1. Exportar odds
    export_odds_to_s3(date, f"{snapshot_id}/odds")
    
    # 2. Exportar features
    export_features_to_s3(date, f"{snapshot_id}/features")
    
    # 3. Exportar resultados
    export_results_to_s3(date, f"{snapshot_id}/results")
    
    # 4. Metadados
    metadata = {
        'snapshot_id': snapshot_id,
        'date': date,
        'created_at': datetime.now()
    }
    save_metadata(snapshot_id, metadata)
    
    return snapshot_id
```

---

## 3. RESTAURAÇÃO DE SNAPSHOT

```python
def restore_snapshot(snapshot_id):
    """
    Restaura snapshot para replay.
    
    Args:
        snapshot_id: ID do snapshot
    
    Returns:
        Dados restaurados
    """
    # 1. Carregar odds
    odds = load_odds_from_s3(f"{snapshot_id}/odds")
    
    # 2. Carregar features
    features = load_features_from_s3(f"{snapshot_id}/features")
    
    # 3. Carregar resultados esperados
    results = load_results_from_s3(f"{snapshot_id}/results")
    
    return {
        'odds': odds,
        'features': features,
        'results': results
    }
```

---

## 4. RETENÇÃO

| Tipo | Retenção | Localização |
|------|----------|-------------|
| Diário | 30 dias | S3 |
| Semanal | 12 semanas | S3 + Glacier |
| Mensal | 12 meses | S3 + Glacier |

---

## 5. CRITÉRIOS

- **Snapshot diário** automático
- **Retenção mínima** 30 dias
- **S3 como storage** primário

---

## 6. LINKS CRUZADOS

- [[06_Backtesting/INDEX]]
- [[REPLAY_BACKTEST]]
