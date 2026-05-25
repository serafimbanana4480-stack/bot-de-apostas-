# API_INTERNAL — Documentação da API Interna

**ID:** `OP-027` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar API interna para comunicação entre componentes.

---

## 2. ENDPOINTS

### POST /api/v1/predict
Gera predição para um jogo.

```python
def predict(game_id):
    """
    Gera predição para um jogo.
    
    Args:
        game_id: ID do jogo
    
    Returns:
        Dict com probabilidade e confiança
    """
    response = requests.post(
        'http://localhost:8000/api/v1/predict',
        json={'game_id': game_id}
    )
    
    return response.json()
```

### POST /api/v1/bet
Executa aposta no bookmaker.

```python
def execute_bet_api(bet_request):
    """
    Executa aposta via API.
    
    Args:
        bet_request: Pedido de aposta
    
    Returns:
        Resultado da execução
    """
    response = requests.post(
        'http://localhost:8000/api/v1/bet',
        json=bet_request
    )
    
    return response.json()
```

### GET /api/v1/health
Health check do sistema.

```python
def health_check_api():
    """Health check via API."""
    response = requests.get('http://localhost:8000/api/v1/health')
    return response.json()
```

---

## 3. MODELOS

### PredictionResponse
```json
{
    "game_id": "GS-LAL-20240115",
    "prob": 0.45,
    "confidence": 0.72,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### BetRequest
```json
{
    "game_id": "GS-LAL-20240115",
    "stake": 100.0,
    "odd": 2.50,
    "market": "moneyline"
}
```

---

## 4. CRITÉRIOS

- **Autenticação** com API keys
- **Rate limiting** por cliente
- **Logs** para todas as requests

---

## 5. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[SYSTEM_ARCHITECTURE]]
