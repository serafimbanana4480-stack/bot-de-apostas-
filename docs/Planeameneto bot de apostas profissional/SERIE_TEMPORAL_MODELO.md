# SERIE_TEMPORAL_MODELO — Modelo de Série Temporal

**ID:** `QR-017` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar uso de modelos de série temporal para previsão de odds.

---

## 2. MODELOS APLICÁVEIS

| Modelo | Uso | Pros | Cons |
|--------|-----|------|------|
| ARIMA | Previsão de odds curto prazo | Simples | Linear apenas |
| LSTM | Sequências longas | Captura padrões complexos | Requer muitos dados |
| Prophet | Sazonalidade | Fácil de usar | Menos preciso |

---

## 3. IMPLEMENTAÇÃO ARIMA

```python
from statsmodels.tsa.arima.model import ARIMA

def fit_arima(odds_series, order=(5,1,0)):
    """
    Ajusta modelo ARIMA a odds.
    
    Args:
        odds_series: Série de odds
        order: Ordem (p,d,q)
    
    Returns:
        Modelo ajustado
    """
    model = ARIMA(odds_series, order=order)
    fitted_model = model.fit()
    
    return fitted_model

def forecast_odds(model, steps=1):
    """
    Previsão de odds.
    
    Args:
        model: Modelo ajustado
        steps: Passos à frente
    
    Returns:
        Previsão
    """
    forecast = model.forecast(steps=steps)
    return forecast
```

---

## 4. VALIDAÇÃO

```python
def validate_arima(model, test_data):
    """
    Valida modelo ARIMA.
    
    Args:
        model: Modelo ajustado
        test_data: Dados de teste
    
    Returns:
        Métricas de validação
    """
    forecast = model.forecast(steps=len(test_data))
    
    mae = np.mean(np.abs(forecast - test_data))
    rmse = np.sqrt(np.mean((forecast - test_data)**2))
    
    return {'mae': mae, 'rmse': rmse}
```

---

## 5. CRITÉRIOS

- **Usar para previsão** de odds curto prazo
- **Validar** com dados de teste
- **RMSE < 5%** para aceitação

---

## 6. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[STOCHASTIC_PROCESSES]]
