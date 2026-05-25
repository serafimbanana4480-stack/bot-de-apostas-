# 🎯 VBQ-UNIFIED - Sistema Quantitativo de Value Betting

**Versão:** 4.0.0-FINAL  
**Data:** 2026-05-19  
**Status:** Sistema em Desenvolvimento  
**Objetivo:** Sistema completo de apostas desportivas quantitativas focado em NBA

---

## 📋 Visão Geral

O VBQ-UNIFIED é um sistema sofisticado de value betting que utiliza aprendizado de máquina, engenharia de features avançada, gestão de risco rigorosa e pipelines automatizados para identificar e executar oportunidades de apostas com valor esperado positivo.

### 🎯 Foco Principal
- **Desporto:** NBA (National Basketball Association)
- **Mercados:** Moneyline e Spread (expansão prevista para Player Props)
- **Estratégia:** Value betting baseado em Closed Line Value (CLV)
- **Abordagem:** Quantitativa com rigor estatístico

---

## 🏗️ Arquitetura do Sistema

### Stack Tecnológico

| Camada | Tecnologia | Propósito |
|--------|-----------|-----------|
| **API** | FastAPI + Uvicorn | REST API endpoints |
| **Autenticação** | JWT + bcrypt | Segurança de acesso |
| **Banco de Dados** | PostgreSQL 15 + SQLAlchemy | Persistência de dados |
| **Cache** | Redis 7 | Cache e rate limiting |
| **Machine Learning** | XGBoost, LightGBM, CatBoost | Modelos preditivos |
| **Experiment Tracking** | MLflow | Rastreamento de experimentos |
| **Orquestração** | Prefect 2.x | Pipeline automatizado |
| **Monitorização** | Prometheus + Grafana | Métricas e dashboards |
| **Distribuição** | Telegram Bot | Envio de sinais |
| **Odds** | Betfair API + Odds API | Dados de odds |

### Estrutura de Diretórios

```
Planeameneto bot de apostas profissional/
├── app/                          # FastAPI application
│   ├── routers/                  # API endpoints
│   └── main.py                   # Entry point
├── src/                          # Core source code
│   ├── api/                      # Internal API routes
│   ├── auth/                     # JWT authentication
│   ├── cache/                    # Redis client
│   ├── database/                 # SQLAlchemy models
│   ├── engine/                   # Edge calculator
│   ├── features/                 # Feature engineering
│   ├── ingestion/                # Data ingestion
│   ├── middleware/               # Rate limiting
│   ├── models/                   # ML models
│   ├── pipeline/                 # Prefect flows
│   ├── risk/                     # Kelly criterion
│   ├── alerting/                 # Alert manager
│   └── telegram/                 # Bot implementation
├── tests/                        # Test suite
├── alembic/                      # Database migrations
├── monitoring/                   # Monitoring configs
└── 00_Master_Index/             # Documentação completa
```

---

## 🚀 Roadmap de Implementação

### Fase 1: Fundações com Rigor Científico (Mês 1)
- [x] Infraestrutura base
- [x] Ingestão de dados NBA
- [x] Feature engineering (80+ features)
- [x] Purged Cross-Validation
- [ ] Modelo baseline XGBoost

### Fase 2: Modelo com Meta-Labeling (Mês 2)
- [ ] Ensemble stacking
- [ ] Calibração isotônica
- [ ] Meta-labeling para filtrar falsos positivos
- [ ] Walk-forward validation

### Fase 3: Shadow Mode e Tipster Beta (Mês 3)
- [ ] Simulação em 3+ casas
- [ ] Documentos legais
- [ ] Sistema de subscrições Telegram
- [ ] Tracking de CLV real

### Fase 4: Micro Banca e Validação Real (Mês 4)
- [ ] 500-1000€ Betfair
- [ ] Tracking rigoroso
- [ ] Validação de edge real
- [ ] Análise de slippage

### Fase 5: Estabilização e Lançamento Comercial (Mês 5)
- [ ] Automação de relatórios
- [ ] 50 subscritores
- [ ] Dashboard Streamlit
- [ ] Sistema de pagamentos

### Fase 6: Expansão e One-Click (Mês 6)
- [ ] Player Props NBA
- [ ] Deep links Betfair
- [ ] Execução one-click
- [ ] 100+ subscritores

---

## 📊 Componentes Principais

### 1. [[Ingestão de Dados]]
- NBA API (dados de jogos)
- Betfair API (odds em tempo real)
- Odds API (fallback)
- Scraping de Basketball-Reference
- Pipeline ETL automatizado

### 2. [[Feature Engineering]]
- Features de forma (rolling averages)
- Features de contexto (home/away, back-to-back)
- Features de mercado (movimento de odds)
- Features de lookahead (agenda futura)
- 80+ features totais

### 3. [[Machine Learning]]
- **Modelos:** XGBoost, LightGBM, CatBoost
- **Técnica:** Ensemble stacking
- **Validação:** Walk-forward CV com purged periods
- **Calibração:** Isotonic regression
- **Meta-labeling:** Filtro de falsos positivos

### 4. [[Gestão de Risco]]
- **Kelly Criterion:** Dimensionamento de stakes
- **Circuit Breakers:** Proteção contra drawdown
- **Bankroll Management:** Sobrevivência a longo prazo
- **Exposure Limits:** Limite de risco por jogo

### 5. [[Motor de Edge]]
- Cálculo de Closed Line Value (CLV)
- Detecção de oportunidades de value
- Thresholds dinâmicos
- Normalização de odds multi-casa

### 6. [[Sistema de Telegram]]
- Bot para distribuição de sinais
- Sistema de subscrições
- Notificações em tempo real
- Comandos de gestão

---

## 🎯 Princípios Inalteráveis

1. **Lucro comprovado antes de escala** - ROI real > 3% e CLV > 2%
2. **Um desporto, dois mercados** - NBA Moneyline + Spread até mês 6
3. **Stack simples e barato** - Python, PostgreSQL, Redis, XGBoost
4. **Execução progressiva** - Manual → One-click → Automática
5. **Rigor estatístico desde o dia 1** - Purged CV, embargo periods
6. **Meta-labeling desde o início** - Filtro de qualidade
7. **Tipster model desde a primeira aposta** - Monetização paralela
8. **Shadow mode multi-casa** - Simulação antes de dinheiro real
9. **Nenhum segredo hardcoded** - Credenciais em environment variables
10. **Documentação viva** - Alterações registadas antes de commits

---

## 📈 Métricas de Sucesso

### Métricas de Modelo
- **Brier Score:** < 0.25 (calibração)
- **Expected Calibration Error:** < 0.05
- **Log Loss:** Minimizado
- **AUC-ROC:** > 0.65

### Métricas de Negócio
- **ROI Real:** > 3% (após 500+ apostas)
- **CLV Médio:** > 2%
- **Drawdown Máximo:** < 20%
- **Sharpe Ratio:** > 1.0

### Métricas Operacionais
- **Latência de Predição:** < 1s
- **Uptime:** > 99.5%
- **Taxa de Falhas:** < 1%
- **Custo por Aposta:** < 0.01€

---

## 🔒 Segurança e Compliance

### Segurança
- Autenticação JWT com bcrypt
- Rate limiting com Redis
- Segredos em environment variables
- Audit logging de todas as operações
- CORS configurado

### Compliance
- Documentos legais para subscrições
- Disclaimers de risco
- Regulamentação SRIJ (Portugal)
- Política de privacidade
- Termos e condições

---

## 🛠️ Setup e Instalação

### Pré-requisitos
- Python 3.11+
- Docker Desktop
- PostgreSQL 15
- Redis 7
- MLflow
- API keys (NBA, Betfair, Telegram)

### Instalação Rápida
```bash
# 1. Clonar repositório
git clone <repositório>
cd Planeameneto\ bot\ de\ apostas\ profissional

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar environment
cp .env.example .env
# Editar .env com credenciais

# 5. Subir infraestrutura
docker-compose up -d postgres redis mlflow

# 6. Executar migrações
alembic upgrade head

# 7. Iniciar API
uvicorn app.main:app --reload
```

---

## 📚 Documentação Detalhada

### Documentação Principal
- [[Visão e Estratégia]] - Filosofia e princípios
- [[Modelo de Negócio]] - Monetização e SaaS
- [[Engenharia de Dados]] - Pipelines ETL
- [[Machine Learning]] - Modelos e validação
- [[Backtesting]] - Validação histórica
- [[Gestão de Risco]] - Kelly e circuit breakers
- [[Sistema de Apostas]] - Execução e operações
- [[Infraestrutura]] - VPS, Docker, DevOps
- [[Monitorização]] - Métricas e alertas
- [[Telegram]] - Bot e distribuição

### Guias Operacionais
- [[Guia de Setup]] - Instalação completa
- [[Guia de Onboarding]] - Para novos desenvolvedores
- [[SOPs]] - Procedimentos operacionais
- [[Runbooks]] - Resolução de problemas
- [[Troubleshooting]] - Diagnóstico de issues

---

## 🚨 Estado Atual

| Componente | Status | Progresso |
|------------|--------|-----------|
| Documentação geral | ✅ Completo | 95% |
| Backend core NBA | 🚧 Em desenvolvimento | 82% |
| Auth JWT | ✅ Completo | 90% |
| Telegram Bot | 🚧 Em desenvolvimento | 80% |
| Pipeline E2E | 🚧 Em desenvolvimento | 78% |
| Alertas | 🚧 Em desenvolvimento | 80% |
| Dashboard/Frontend | ❌ Não iniciado | 0% |
| Player Props NBA | ❌ Não iniciado | 0% |
| Multi-Desporto | ❌ Não iniciado | 0% |

---

## 🔗 Links Importantes

- [[Índice Mestre]] - Documentação completa original
- [[Plano de Implementação]] - Roadmap detalhado
- [[Análise de Lacunas]] - Melhorias pendentes
- [[Relatório de Auditoria]] - Análise sistemática
- [[Validação Cruzada]] - Verificação de fluxos

---

## 👥 Equipa e Responsabilidades

- **Chief Systems Architect** - Arquitetura e estratégia
- **Principal Quant Engineer** - Modelos e pesquisa
- **Data Engineer** - Pipelines e ingestão
- **ML Engineer** - Treino e validação
- **DevOps Engineer** - Infraestrutura e deploy
- **Operations Manager** - Operações diárias

---

## 📞 Suporte e Contacto

Para questões técnicas:
- Documentação: [[Troubleshooting]]
- Runbooks: [[Runbooks]]
- Incidentes: [[Postmortems]]

Para questões de negócio:
- Modelo: [[Modelo de Negócio]]
- Compliance: [[Compliance]]
- Legal: [[Legal]]

---

## 📝 Notas

- Este documento é um resumo executivo do sistema completo
- Para detalhes técnicos, consulte a documentação específica de cada componente
- O sistema segue uma abordagem progressiva: validar antes de escalar
- Todas as decisões técnicas são documentadas com justificação

---

**Última atualização:** 2026-05-19  
**Próxima revisão:** 2026-06-19