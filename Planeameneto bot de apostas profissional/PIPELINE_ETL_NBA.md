# PIPELINE_ETL_NBA — Pipeline ETL para NBA

**ID:** `DE-006` | **Fase:** #phase/2 | **Owner:** Data Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir pipeline ETL para ingestão de dados NBA.

---

## 2. FONTES DE DADOS

| Fonte | Dados | Frequência |
|-------|-------|------------|
| NBA API | Jogos, resultados | Diário |
| Stats API | Estatísticas de jogadores | Diário |
| Bookmaker API | Odds | Em tempo real |

---

## 3. PIPELINE

```python
def nba_etl_pipeline(date):
    """
    Executa pipeline ETL para NBA.
    
    Args:
        date: Data dos dados a processar
    
    Returns:
        Status da execução
    """
    # 1. Extract
    games = extract_nba_games(date)
    stats = extract_nba_stats(date)
    odds = extract_odds(date)
    
    # 2. Transform
    games_clean = clean_games(games)
    stats_clean = clean_stats(stats)
    odds_clean = clean_odds(odds)
    
    # 3. Load
    load_to_bronze(games_clean, 'games')
    load_to_bronze(stats_clean, 'stats')
    load_to_bronze(odds_clean, 'odds')
    
    # 4. Validate
    validate_data(date)
    
    return {'status': 'success', 'date': date}
```

---

## 4. CAMADAS

### Bronze (Raw)
- Dados brutos das APIs
- Sem transformações
- Retenção: 30 dias

### Silver (Cleaned)
- Dados limpos e validados
- Tipos consistentes
- Retenção: 90 dias

### Gold (Features)
- Features para ML
- Prontos para treino
- Retenção: 12 meses

---

## 5. CRITÉRIOS

- **Executar diariamente** após jogos
- **Validação** com Great Expectations
- **Retenção** por camada

---

## 6. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]]
- [[VALIDACAO_DADOS]]
