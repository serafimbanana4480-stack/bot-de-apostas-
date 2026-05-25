# 35_Financial_Tracking — INDEX

**ID:** `SEC-35` | **Fase:** #phase/3-10 | **Owner:** Financeiro | **Status:** #status/active

---

## 1. OBJETIVO

Implementar sistema de tracking financeiro para monitorizar receitas, despesas, PnL de apostas, e métricas de negócio em tempo real. O tracking financeiro é essencial para validar o modelo de negócio e garantir sustentabilidade.

---

## 2. COMPONENTES

### 2.1 Database de Transações

**Schema:**
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_type VARCHAR(50) NOT NULL,  -- 'revenue', 'expense', 'bet_pnl'
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    category VARCHAR(100),
    description TEXT,
    reference_id VARCHAR(255),  -- signal_id, subscription_id, etc.
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    subscriber_id INTEGER,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    subscription_tier VARCHAR(50),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(50),  -- 'active', 'cancelled', 'expired'
    stripe_subscription_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bets (
    id SERIAL PRIMARY KEY,
    signal_id VARCHAR(255) NOT NULL,
    game_id VARCHAR(255) NOT NULL,
    team VARCHAR(255) NOT NULL,
    market VARCHAR(50) NOT NULL,
    selection VARCHAR(255) NOT NULL,
    odd_placed DECIMAL(10, 2) NOT NULL,
    odd_executed DECIMAL(10, 2) NOT NULL,
    stake_placed DECIMAL(10, 2) NOT NULL,
    stake_executed DECIMAL(10, 2) NOT NULL,
    outcome VARCHAR(20),  -- 'win', 'loss', 'void', 'pending'
    pnl DECIMAL(10, 2),
    clv DECIMAL(5, 4),
    bet_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 API de Tracking

```python
# app/financial/api.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

class FinancialAPI:
    def __init__(self, db: Session):
        self.db = db
    
    def record_transaction(self, transaction_type: str, amount: float, 
                         category: str, description: str, reference_id: str = None):
        """Registra transação financeira"""
        transaction = Transaction(
            transaction_type=transaction_type,
            amount=amount,
            category=category,
            description=description,
            reference_id=reference_id,
            transaction_date=datetime.now().date()
        )
        
        self.db.add(transaction)
        self.db.commit()
        
        logger.info(f"Transação registrada: {transaction_type} {amount}€")
    
    def record_bet(self, signal_id: str, game_id: str, team: str, market: str,
                   selection: str, odd_placed: float, odd_executed: float,
                   stake_placed: float, stake_executed: float, clv: float):
        """Registra aposta"""
        bet = Bet(
            signal_id=signal_id,
            game_id=game_id,
            team=team,
            market=market,
            selection=selection,
            odd_placed=odd_placed,
            odd_executed=odd_executed,
            stake_placed=stake_placed,
            stake_executed=stake_executed,
            clv=clv,
            bet_date=datetime.now().date(),
            outcome='pending'
        )
        
        self.db.add(bet)
        self.db.commit()
        
        logger.info(f"Aposta registrada: {signal_id} {stake_executed}€")
    
    def settle_bet(self, bet_id: int, outcome: str, pnl: float):
        """Liquidata aposta"""
        bet = self.db.query(Bet).filter(Bet.id == bet_id).first()
        
        if bet:
            bet.outcome = outcome
            bet.pnl = pnl
            self.db.commit()
            
            # Registrar PnL como transação
            self.record_transaction(
                transaction_type='bet_pnl',
                amount=pnl,
                category='betting',
                description=f"Bet {bet.signal_id}",
                reference_id=bet.signal_id
            )
```

---

## 3. MÉTRICAS FINANCEIRAS

### 3.1 Métricas de Receita

| Métrica | Definição | Target |
|---------|-----------|--------|
| **MRR (Monthly Recurring Revenue)** | Receita recorrente mensal de subscrições | > 1.450€ (50 subscritores) |
| **ARPU (Average Revenue Per User)** | Receita média por subscritor | > 29€ |
| **CAC (Customer Acquisition Cost)** | Custo de aquisição de subscritor | < 50€ |
| **LTV (Lifetime Value)** | Valor total do subscritor | > 100€ |
| **Churn Rate** | Taxa de cancelamento mensal | < 5% |

### 3.2 Métricas de Apostas

| Métrica | Definição | Target |
|---------|-----------|--------|
| **ROI (Return on Investment)** | PnL total / Stake total | > 5% |
| **CLV Médio** | Edge médio de todas as apostas | > 2% |
| **Sharpe Ratio** | ROI médio / Desvio padrão de ROI | > 0.5 |
| **Max Drawdown** | Maior queda da banca | < 20% |
| **Win Rate** | % de apostas vencedas | > 52% |

### 3.3 Métricas de Custos

| Métrica | Definição | Target |
|---------|-----------|--------|
| **Custo VPS** | Custo mensal de infraestrutura | < 30€ |
| **Custo Dados** | Custo mensal de dados premium | < 50€ |
| **Custo Total** | Custo mensal total | < 100€ |
| **Break-even** | Número de subscritores para cobrir custos | < 10 |

---

## 4. DASHBOARDS FINANCEIROS

### 4.1 Dashboard de Receita

**Gráficos:**
- MRR ao longo do tempo (últimos 12 meses)
- ARPU ao longo do tempo
- Número de subscritores ao longo do tempo
- Churn rate mensal
- CAC vs LTV

### 4.2 Dashboard de Apostas

**Gráficos:**
- PnL cumulativo (últimos 30 dias)
- ROI mensal (últimos 12 meses)
- CLV médio rolling (últimos 100 apostas)
- Sharpe Ratio rolling (últimos 100 apostas)
- Max drawdown
- Win rate rolling (últimos 100 apostas)

### 4.3 Dashboard de Custos

**Gráficos:**
- Custos por categoria (VPS, dados, ferramentas)
- Custo total ao longo do tempo
- Custo por subscritor
- Break-even analysis

---

## 5. RELATÓRIOS

### 5.1 Relatório Mensal

**Conteúdo:**
- Resumo executivo
- Métricas de receita
- Métricas de apostas
- Custos detalhados
- PnL líquido (receita - custos - apostas)
- Análise de tendências
- Recomendações

**Distribuição:**
- Enviado por email no dia 1 de cada mês
- Disponível no dashboard

### 5.2 Relatório de PnL

**Conteúdo:**
- PnL detalhado por aposta
- PnL por mercado (Moneyline, Spread)
- PnL por equipa
- PnL por regime (regular season, playoffs)
- CLV analysis

**Distribuição:**
- Disponível no dashboard
- Exportável em CSV

---

## 6. BACKLOG DE FINANCIAL TRACKING

- [ ] Implementar schema de database
- [ ] Implementar API de tracking
- [ ] Implementar integração com Stripe
- [ ] Implementar dashboards Grafana
- [ ] Implementar relatórios mensais
- [ ] Implementar relatórios de PnL
- [ ] Configurar alertas financeiros
- [ ] Implementar reconciliação bancária
- [ ] Implementar forecasting de receita
- [ ] Implementar forecasting de custos

---

## 7. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[02_Business_Model/INDEX]] → Modelo de negócio
- [[02_Business_Model/PLANO_FINANCEIRO_6_MESES.md]] → Projeções financeiras
- [[36_KPIs/INDEX]] → KPIs do sistema
- [[37_CLV_Analytics/INDEX]] → Análise de CLV
