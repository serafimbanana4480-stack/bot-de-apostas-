# SYSTEM_ARCHITECTURE — Arquitetura do Sistema

**ID:** `ARCH-001` | **Fase:** #phase/1 | **Owner:** System Architect | **Status:** #status/active

---

## 1. OBJETIVO

Documentar a arquitetura do sistema de apostas quantitativas.

---

## 2. COMPONENTES PRINCIPAIS

```
┌─────────────────┐
│  Data Sources   │
│ (Odds, Stats)   │
└────────┬────────┘
         │
┌────────▼────────┐
│ Data Engineering │
│ (Bronze/Silver)  │
└────────┬────────┘
         │
┌────────▼────────┐
│ Feature Eng.    │
│ (Gold Layer)    │
└────────┬────────┘
         │
┌────────▼────────┐
│ ML Models       │
│ (XGBoost)       │
└────────┬────────┘
         │
┌────────▼────────┐
│ Signal Gen.     │
│ + Meta-Labeling │
└────────┬────────┘
         │
┌────────▼────────┐
│ Risk Management │
│ (Stake Calc)    │
└────────┬────────┘
         │
┌────────▼────────┐
│ Execution Engine│
│ (API Client)    │
└────────┬────────┘
         │
┌────────▼────────┐
│ Monitoring      │
│ + Alerting      │
└─────────────────┘
```

---

## 3. COMPONENTES DETALHADOS

### 3.1 Data Engineering
- Ingestão de odds em tempo real
- Camadas Bronze (raw), Silver (cleaned), Gold (features)
- Validação com Great Expectations

### 3.2 Machine Learning
- Modelo XGBoost primário
- Meta-modelo para filtragem
- Retraining automático

### 3.3 Execution
- Geração de sinais
- Cálculo de stakes (Kelly)
- Execução via API do bookmaker

### 3.4 Monitoring
- Dashboards em tempo real
- Alertas via Telegram
- Reconciliação diária

---

## 4. INFRAESTRUTURA

| Componente | Tecnologia |
|------------|-----------|
| Database | PostgreSQL |
| Cache | Redis |
| Queue | RabbitMQ |
| ML Tracking | MLflow |
| Dashboard | Grafana |

---

## 5. LINKS CRUZADOS

- [[01_Vision_And_Strategy/INDEX]]
- [[11_MLOps/INDEX]]
