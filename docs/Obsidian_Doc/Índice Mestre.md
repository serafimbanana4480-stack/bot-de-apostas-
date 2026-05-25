# 🗂️ Índice Mestre - Obsidian Documentation

**Versão:** 1.0.0  
**Data:** 2026-05-19  
**Projeto:** VBQ-UNIFIED - Sistema Quantitativo de Value Betting

---

## 📋 Sobre Esta Documentação

Esta documentação foi criada para fornecer uma visão completa do projeto VBQ-UNIFIED no formato do Obsidian, utilizando wikilinks para navegação entre documentos.

**Estrutura:**
- [[README]] - Visão geral e introdução
- Documentos técnicos por componente
- Documentos estratégicos e de negócio
- Links cruzados entre componentes

---

## 🎯 Documentação Principal

### Visão Geral
- [[README]] - **COMECE AQUI** - Visão geral completa do projeto
- [[Visão e Estratégia]] - Filosofia, princípios e roadmap estratégico
- [[Modelo de Negócio]] - Monetização, subscrições e projeções financeiras

### Componentes Técnicos

#### Data & Features
- [[Ingestão de Dados]] - Coleta e processamento de dados NBA e odds
- [[Feature Engineering]] - Transformação de dados em features preditivas

#### Machine Learning & MLOps
- [[Machine Learning]] - Modelos preditivos, ensemble e calibração
- [[Pesquisa Avançada e Validação]] - RAG, Web Scraping, RLAIF e Self-Reflection
- [[MLOps e Retreinamento]] - Continuous Retraining e Champion vs Challenger
- [[Validação e Calibração]] - CLV Drift, Reliability e Model Disagreement
- [[Arquitetura de Experimentação]] - Feature Store, Regimes de Mercado e Counterfactuals

#### Risk & Execution
- [[Gestão de Risco]] - Kelly criterion, circuit breakers e gestão de bankroll
- [[Motor de Edge]] - Detecção de oportunidades e cálculo de CLV

#### Distribution
- [[Sistema de Telegram]] - Bot de Telegram e distribuição de sinais

---

## 🏗️ Arquitetura do Sistema

### Stack Tecnológico

| Camada | Tecnologia |
|--------|-----------|
| **API** | FastAPI + Uvicorn |
| **Autenticação** | JWT + bcrypt |
| **Banco de Dados** | PostgreSQL 15 + SQLAlchemy |
| **Cache** | Redis 7 |
| **Machine Learning** | XGBoost, LightGBM, CatBoost |
| **Experiment Tracking** | MLflow |
| **Orquestração** | Prefect 2.x |
| **Monitorização** | Prometheus + Grafana |
| **Distribuição** | Telegram Bot |
| **Odds** | Betfair API + Odds API |

### Estrutura de Código

```
Planeameneto bot de apostas profissional/
├── app/                    # FastAPI application
│   ├── routers/           # API endpoints
│   └── main.py            # Entry point
├── src/                   # Core source code
│   ├── api/              # Internal API routes
│   ├── auth/             # JWT authentication
│   ├── cache/            # Redis client
│   ├── database/         # SQLAlchemy models
│   ├── engine/           # Edge calculator
│   ├── features/         # Feature engineering
│   ├── ingestion/        # Data ingestion
│   ├── middleware/       # Rate limiting
│   ├── models/           # ML models
│   ├── pipeline/         # Prefect flows
│   ├── risk/             # Kelly criterion
│   ├── alerting/         # Alert manager
│   └── telegram/         # Bot implementation
├── tests/                # Test suite
├── alembic/              # Database migrations
└── monitoring/          # Monitoring configs
```

---

## 🚀 Roadmap de Implementação

### Fase 1: Fundações (Mês 1)
- [x] Infraestrutura base
- [x] Ingestão de dados NBA
- [x] Feature engineering (80+ features)
- [ ] Purged Cross-Validation
- [ ] Modelo baseline XGBoost

### Fase 2: Modelo com Meta-Labeling (Mês 2)
- [ ] Ensemble stacking
- [ ] Calibração isotônica
- [ ] Meta-labeling
- [ ] Walk-forward validation

### Fase 3: Shadow Mode (Mês 3)
- [ ] Simulação 3+ casas
- [ ] Documentos legais
- [ ] Telegram beta
- [ ] CLV shadow tracking

### Fase 4: Micro Banca (Mês 4)
- [ ] 500-1000€ Betfair
- [ ] Tracking rigoroso
- [ ] ROI real validação

### Fase 5: Lançamento Comercial (Mês 5)
- [ ] 50 subscritores
- [ ] Dashboard Streamlit
- [ ] Automação relatórios

### Fase 6: Expansão (Mês 6)
- [ ] Player Props NBA
- [ ] Deep links Betfair
- [ ] 100+ subscritores

---

## 📊 Estado Atual do Projeto

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
- **Brier Score:** < 0.25
- **Expected Calibration Error:** < 0.05
- **Log Loss:** Minimizado
- **AUC-ROC:** > 0.65

### Métricas de Negócio
- **ROI Real:** > 3%
- **CLV Médio:** > 2%
- **Drawdown Máximo:** < 20%
- **Sharpe Ratio:** > 1.0

### Métricas Operacionais
- **Latência de Predição:** < 1s
- **Uptime:** > 99.5%
- **Taxa de Falhas:** < 1%
- **Custo por Aposta:** < 0.01€

---

## 🔗 Links Rápidos

### Por Categoria

**Estratégia & Negócio:**
- [[Visão e Estratégia]]
- [[Modelo de Negócio]]

**Técnico - Data:**
- [[Ingestão de Dados]]
- [[Feature Engineering]]

**Técnico - ML:**
- [[Machine Learning]]
- [[Pesquisa Avançada e Validação]]

**Técnico - Risk:**
- [[Gestão de Risco]]
- [[Motor de Edge]]

**Técnico - Distribution:**
- [[Sistema de Telegram]]

### Por Ação

**Para entender o projeto:**
1. Comece com [[README]]
2. Leia [[Visão e Estratégia]]
3. Explore [[Modelo de Negócio]]

**Para entender a implementação:**
1. Leia [[Ingestão de Dados]]
2. Explore [[Feature Engineering]]
3. Estude [[Machine Learning]]

**Para entender as operações:**
1. Revise [[Gestão de Risco]]
2. Estude [[Motor de Edge]]
3. Configure [[Sistema de Telegram]]

---

## 📝 Notas Importantes

### Sobre o Formato Obsidian

Esta documentação usa:
- **Wikilinks:** `[[Nome do Arquivo]]` para links internos
- **Markdown:** Formatação padrão
- **Tags:** Para categorização (opcional)
- **Frontmatter:** Metadados (opcional)

### Como Usar

1. **Instale o Obsidian:** https://obsidian.md/
2. **Abra este diretório** como um vault no Obsidian
3. **Navegue** usando os wikilinks
4. **Personalize** conforme necessário

### Manutenção

- **Atualizações:** Mantenha os documentos sincronizados com o código
- **Versões:** Use controle de versão para documentação
- **Review:** Revise trimestralmente para atualizações

---

## 🚨 Avisos Importantes

### Legal & Compliance

- Este projeto é para uso educacional e privado
- Apostas desportivas envolvem risco financeiro
- Consulte regulamentação local antes de operar
- Nunca prometa retornos garantidos

### Técnico

- Sistema em desenvolvimento - não use em produção sem validação
- Testes rigorosos necessários antes de dinheiro real
- Backup e recovery plan são essenciais
- Security first - proteja credenciais

---

## 📞 Suporte

### Documentação Técnica
- Para detalhes técnicos, consulte os documentos específicos de cada componente
- Para troubleshooting, veja os arquivos de código e logs

### Documentação de Negócio
- Para questões de modelo de negócio, consulte [[Modelo de Negócio]]
- Para compliance e legal, consulte a documentação original

---

## 🔮 Roadmap da Documentação

### Planeado

- [ ] Adicionar diagramas de arquitetura
- [ ] Adicionar tutoriais passo-a-passo
- [ ] Adicionar FAQs
- [ ] Adicionar glossário de termos
- [ ] Adicionar study guides

### Futuro

- [ ] Documentação de multi-desporto
- [ ] Documentação de expansão
- [ ] Documentação de automação
- [ ] Documentação institucional

---

**Última atualização:** 2026-05-19  
**Versão:** 1.0.0  
**Status:** ✅ Completo