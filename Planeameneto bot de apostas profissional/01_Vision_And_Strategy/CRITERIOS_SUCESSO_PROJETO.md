# CRITÉRIOS DE SUCESSO DO PROJETO — O Que Significa "Vitória" em Cada Fase

**ID:** `STR-004` | **Fase:** Todas | **Owner:** Chief Systems Architect | **Status:** #status/active

---

## 1. OBJETIVO

Definir critérios de sucesso claros e mensuráveis para cada fase do projeto. Sucesso não é "fazer dinheiro" — é validar que o sistema tem edge matemático real e que o negócio é sustentável.

---

## 2. CRITÉRIOS POR FASE

### FASE 1 — FUNDAÇÕES COM RIGOR CIENTÍFICO (Mês 1)

**Critérios de Sucesso:**
- ✅ Infraestrutura operacional (VPS, PostgreSQL, Redis, Git)
- ✅ 5 épocas de dados NBA ingeridas e validadas
- ✅ Purged Walk-Forward CV implementado e testado
- ✅ Pipeline de feature engineering funcional (40-50 features)
- ✅ Todas as features passam testes ADF/KPSS (estacionariedade)
- ✅ Zero leakage temporal detectado em auditoria

**Critérios de Falha:**
- ❌ Dados históricos incompletos ou com qualidade < 90%
- ❌ Features com look-ahead detectadas
- ❌ Purged CV não implementado corretamente
- ❌ Infraestrutura instável (> 10% downtime)

**Métricas Chave:**
- Dados ingeridos: 5 épocas (~6000 jogos)
- Features engenhadas: 40-50
- Qualidade de dados: > 95% completeness
- Testes de estacionariedade: > 80% pass

---

### FASE 2 — MODELO COM META-LABELING (Mês 2)

**Critérios de Sucesso:**
- ✅ Modelo primário XGBoost treinado com purged CV
- ✅ Meta-modelo de filtragem implementado
- ✅ Calibração isotónica por regime (3 regimes)
- ✅ Backtest rigoroso com todos os critérios de passagem
- ✅ CLV médio > 2.0% no set de teste final
- ✅ ROI simulado > 5% após custos
- ✅ Sharpe Ratio > 0.5
- ✅ Brier Score < Brier_mercado
- ✅ ECE < 0.05 por regime

**Critérios de Falha:**
- ❌ CLV < 1.0% (edge insuficiente)
- ❌ ROI simulado < 0% (modelo perde dinheiro)
- ❌ Sharpe < 0.3 (retornos muito voláteis)
- ❌ Overfitting detectado (performance treino >> validação)
- ❌ Leakage temporal não detectado antes

**Métricas Chave:**
- CLV médio: > 2.0%
- ROI simulado: > 5%
- Sharpe Ratio: > 0.5
- Brier Score improvement: > 10% vs mercado
- Número de apostas/mês: 50-100

---

### FASE 3 — SHADOW MODE MULTI-CASA (Mês 3)

**Critérios de Sucesso:**
- ✅ Shadow betting operacional em 3+ casas
- ✅ True CLV calculado e > 1.5%
- ✅ Dispersão de CLV entre casas < 2%
- ✅ Fill rate simulado > 80%
- ✅ Canal Telegram criado para beta testers
- ✅ Documentos legais preparados (ToS, Privacy, Disclaimer)
- ✅ Página de tracking pública configurada

**Critérios de Falha:**
- ❌ True CLV < 0.5% (edge não existe em casas reais)
- ❌ Dispersão de CLV > 5% (edge muito dependente da casa)
- ❌ Fill rate < 50% (sinais não são executáveis)
- ❌ Beta testers não recrutados (mínimo 5)

**Métricas Chave:**
- True CLV médio: > 1.5%
- Dispersão CLV: < 2%
- Fill rate shadow: > 80%
- Beta testers ativos: 5-10
- Sinais gerados/dia: 2-5

---

### FASE 4 — MICRO BANCA E VALIDAÇÃO REAL (Mês 4)

**Critérios de Sucesso:**
- ✅ Conta Betfair aberta com 500-1000€
- ✅ Todas as apostas executadas manualmente
- ✅ ROI real > 0% (não negativo)
- ❌ ROI real dentro de IC 95% do ROI simulado
- ✅ Slippage real < 1.0%
- ✅ Zero violações de gestão de risco
- ✅ Tracking público atualizado diariamente

**Critérios de Falha:**
- ❌ ROI real < -5% (modelo falha catastroficamente)
- ❌ Slippage > 2.0% (backtest otimista)
- ❌ Violação de limites de stake (erro operacional)
- ❌ < 50% dos sinais executados (operacionalidade falha)

**Métricas Chave:**
- ROI real: > 0% (ideal > 3%)
- Slippage médio: < 1.0%
- Fill rate real: > 70%
- Apostas executadas: 50-100
- Banca final: > inicial (não negativo)

---

### FASE 5 — ESTABILIZAÇÃO E LANÇAMENTO TIPSTER (Mês 5)

**Critérios de Sucesso:**
- ✅ ROI real consistente > 3% por 2 meses
- ✅ Sistema de pagamentos configurado (Stripe/Paddle)
- ✅ 25-50 subscritores ativos
- ✅ Receita mensal > custos operacionais
- ✅ Relatórios automáticos funcionando
- ✅ Alertas operacionais configurados
- ✅ Documentação de suporte completa

**Critérios de Falha:**
- ❌ ROI real cai < 0% (edge desaparece)
- ❌ < 10 subscritores (interesse insuficiente)
- ❌ Receita < custos (modelo insustentável)
- ❌ Churn rate > 20%/mês (produto ruim)

**Métricas Chave:**
- Subscritores ativos: 25-50
- MRR: 750-1500€ (29€/subscritor)
- CAC: < 15€
- Churn rate: < 15%/mês
- ROI real: > 3%

---

### FASE 6 — PRIMEIRA EXPANSÃO E AUTOMATIZAÇÃO (Mês 6)

**Critérios de Sucesso:**
- ✅ Player Props NBA implementados
- ✅ One-click betting funcional (deep links)
- ✅ Modelo Player Props com CLV > 2%
- ✅ Monitorização avançada (Prometheus + Grafana)
- ✅ 50+ subscritores
- ✅ Receita > 2x custos
- ✅ Sistema estável (< 5% downtime)

**Critérios de Falha:**
- ❌ Player Props não alcançam CLV > 1%
- ❌ One-click betting tem taxa de erro > 10%
- ❌ Downtime > 10% (infraestrutura instável)
- ❌ Subscritores < 30 (crescimento estagnado)

**Métricas Chave:**
- Mercados ativos: 3 (ML, Spread, Player Props)
- Subscritores: 50+
- MRR: 1500+€
- Uptime: > 95%
- ROI combinado: > 3%

---

## 3. CRITÉRIOS DE ABANDONO DO PROJETO

O projeto deve ser abandonado se:

1. **Fase 2:** CLV < 0.5% após múltiplas iterações de features
2. **Fase 4:** ROI real < -10% após 100 apostas (edge não existe)
3. **Fase 5:** < 10 subscritores após 3 meses de marketing (interesse nulo)
4. **Qualquer fase:** Violação legal ou de compliance que não pode ser corrigida
5. **Qualquer fase:** Drawdown > 50% da banca (risco insustentável)

**Regra de ouro:** É melhor abandonar cedo do que persistir num projeto sem edge. O tempo e dinheiro são finitos.

---

## 4. CRITÉRIOS DE SUCESSO FINAL (Mês 12)

**Sucesso Estratégico:**
- ✅ ROI real > 5% consistente por 6+ meses
- ✅ 100+ subscritores recorrentes
- ✅ Receita > 5000€/mês
- ✅ Banca própria > 10.000€
- ✅ Sistema multi-mercado estável
- ✅ Segundo desporto em desenvolvimento
- ✅ Custo por aposta < 0.10€

**Sucesso Financeiro:**
- Receita anual > 60.000€
- Lucro líquido > 30.000€
- Payback do investimento inicial < 18 meses
- Valuation do negócio > 150.000€ (se vendido)

---

## 5. MÉTRICAS DE SAÚDE DO PROJETO

| Métrica | Sinal Verde | Sinal Amarelo | Sinal Vermelho |
|---------|-------------|---------------|----------------|
| CLV médio | > 2.0% | 1.0-2.0% | < 1.0% |
| ROI real | > 3% | 0-3% | < 0% |
| Sharpe Ratio | > 0.5 | 0.3-0.5 | < 0.3 |
| Subscritores | Crescimento > 10%/mês | Estável | Decrescendo |
| Churn rate | < 10%/mês | 10-20%/mês | > 20%/mês |
| Uptime sistema | > 99% | 95-99% | < 95% |
| Custo por aposta | < 0.10€ | 0.10-0.20€ | > 0.20€ |

---

## 6. LINKS CRUZADOS

- [[01_Vision_And_Strategy/INDEX]] ← Secção mãe
- [[36_KPIs/INDEX]] → KPIs detalhados por perspectiva
- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[24_Product_Roadmap/INDEX]] → Roadmap de produto