# SUGESTAO_MODELO — Sugestão de Modelo

**ID:** `ML-014` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar sugestões e recomendações para melhorias do modelo.

---

## 2. PROCESSO DE SUGESTÃO

```python
def suggest_model_improvements(metrics, feedback):
    """
    Gera sugestões baseadas em métricas e feedback.
    
    Args:
        metrics: Métricas atuais do modelo
        feedback: Feedback de stakeholders
    
    Returns:
        Lista de sugestões priorizadas
    """
    suggestions = []
    
    # Baseado em métricas
    if metrics['clv'] < 0.02:
        suggestions.append({
            'priority': 'high',
            'suggestion': 'Adicionar features de forma recente',
            'rationale': 'CLV abaixo do target'
        })
    
    if metrics['calibration'] > 0.05:
        suggestions.append({
            'priority': 'medium',
            'suggestion': 'Aplicar calibração isotônica',
            'rationale': 'Calibração ruim'
        })
    
    # Baseado em feedback
    for feedback_item in feedback:
        if feedback_item['category'] == 'feature_request':
            suggestions.append({
                'priority': 'medium',
                'suggestion': feedback_item['description'],
                'rationale': 'Solicitado por usuário'
            })
    
    return suggestions
```

---

## 3. PRIORIZAÇÃO

| Prioridade | Critério | Ação |
|------------|----------|------|
| Alta | Impacto > 10% CLV | Implementar na próxima sprint |
| Média | Impacto 5-10% CLV | Implementar no próximo trimestre |
| Baixa | Impacto < 5% CLV | Backlog |

---

## 4. TRACKING

```python
def track_suggestion(suggestion_id, status):
    """
    Atualiza status de sugestão.
    
    Status: pending, in_progress, completed, rejected
    """
    update_suggestion_status(suggestion_id, status)
```

---

## 5. CRITÉRIOS

- **Sugestões documentadas** com justificativa
- **Priorização baseada** em impacto
- **Review trimestral** do backlog

---

## 6. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]]
- [[OPTUNA_TUNING]]
