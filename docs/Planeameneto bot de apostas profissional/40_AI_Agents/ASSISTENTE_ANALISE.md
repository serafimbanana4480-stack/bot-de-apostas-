# ASSISTENTE_ANALISE — AI Agent para Analise de Performance

**ID:** `AI-001` | **Fase:** #phase/8 | **Owner:** Chief Systems Architect | **Status:** #status/pending

---

## 1. OBJETIVO

Criar um agente de IA que analisa a performance do sistema, identifica padroes, e sugere melhorias.

---

## 2. FUNCIONALIDADES

### 2.1 Analise Diaria
- Resumo de PnL, CLV, ROI do dia
- Comparacao com expectativa (backtest)
- Identificacao de outliers

### 2.2 Analise Semanal
- Tendencias de CLV por regime
- Feature importance drift
- Sugestoes de ajuste de thresholds

### 2.3 Alertas Inteligentes
- "CLV em apostas de underdogs esta a cair ha 3 dias"
- "Feature X tem PSI de 0.25; recomendo retraining"

---

## 3. IMPLEMENTACAO

```python
class PerformanceAnalyst:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def daily_summary(self, date):
        bets = self.get_bets(date)
        return {
            'pnl': bets['pnl'].sum(),
            'clv': bets['clv'].mean(),
            'n_bets': len(bets),
            'anomalies': self.detect_anomalies(bets)
        }
    
    def detect_anomalies(self, bets):
        # Usar Isolation Forest ou regras simples
        return bets[bets['clv'] < -0.05]  # CLV muito negativo
```

---

## 4. BACKLOG

- [ ] Definir prompt templates para analise
- [ ] Implementar geracao automatica de relatorios
- [ ] Criar interface conversacional (Telegram)

---

## 5. LINKS CRUZADOS

- [[40_AI_Agents/INDEX]] ← Secao mae
- [[10_Monitoring/INDEX]] → Dados consumidos pelo agente
