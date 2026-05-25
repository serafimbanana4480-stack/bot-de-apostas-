# ROADMAP_EXPANSAO — Timeline 12 Meses Multi-Desporto (VBQ-002)

**ID:** `MSE-007` | **Fase:** #phase/7-12 | **Owner:** Product Manager | **Status:** #status/pending | **Versão:** `2.0.0-12MONTH`

---

## 1. OBJETIVO

Definir o timeline detalhado de 12 meses para expansão do sistema de value betting para NBA (baseline), Football e MMA/UFC, incluindo milestones, deliverables e critérios de sucesso para cada fase.

---

## 2. PREMISSAS

### 2.1 Premissas Base
- **NBA Baseline:** Assume que NBA está validado com ROI > 12% antes de iniciar expansão
- **Recursos:** 1 FTE (Full-Time Equivalent) dedicado
- **Orçamento:** 200-300€/mês adicionais por novo desporto (dados, infraestrutura)
- **Progressão Faseada:** Regra absoluta - não iniciar próximo desporto até anterior validado

### 2.2 Critérios de Validação
Antes de considerar um desporto "validado":
- ✅ Backtest 3+ temporadas com ROI > 5%
- ✅ CLV > 2% (NBA/Football) ou > 3% (MMA)
- ✅ Paper trading 1-2 meses com ROI > 3%
- ✅ Micro-banca 1 mês com ROI > 2%
- ✅ Drawdown < 15%
- ✅ Sistema operacional estável sem bugs críticos

---

## 3. ROADMAP GERAL (12 MESES)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           TIMELINE 12 MESES                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Mês 0-6:    [████████████] NBA (Baseline - já validado)                │
│              ├─ Ensemble stacking implementado                         │
│              ├─ Feature engineering expandido (80-100 features)          │
│              ├─ Online learning (EWA/Kalman)                             │
│              ├─ Player Props NBA                                        │
│              └─ Execução algorítmica Betfair                            │
│                                                                         │
│  Mês 7-9:    [████████████] Football Expansion (Fase 1)                │
│              ├─ Mês 7: Research & Data Pipeline                          │
│              ├─ Mês 8: Model Development (Poisson + XGBoost)             │
│              └─ Mês 9: Validation & Shadow Mode                          │
│                                                                         │
│  Mês 10-12:  [████████████] MMA/UFC Expansion (Fase 2)                │
│              ├─ Mês 10: Research & Data Pipeline                          │
│              ├─ Mês 11: Model Development (Bayesian)                      │
│              └─ Mês 12: Validation & Shadow Mode                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. FASE 1: NBA ENHANCEMENT (Meses 0-6)

### 4.1 Overview
- **Duração:** 6 meses
- **Prioridade:** 0 (Baseline)
- **ROI Esperado:** 15-25%
- **Liquidez:** Alta

### 4.2 Milestones

#### Mês 1-2: Ensemble Stacking
**Deliverables:**
- [ ] Implementar XGBoost + LightGBM + CatBoost ensemble
- [ ] Adicionar meta-modelo linear (Logistic Regression)
- [ ] Validar com walk-forward CV
- [ ] Documentar ganho de CLV (+1-2%)

**Critérios de Sucesso:**
- Ensemble implementado e testado
- CLV melhorado vs modelo único
- Documentação completa

#### Mês 3-4: Feature Engineering Expandido
**Deliverables:**
- [ ] Expandir para 80-100 features
- [ ] Adicionar features de rest assimétrico
- [ ] Adicionar features On/Off (impacto de jogador)
- [ ] Adicionar features de microestrutura de mercado
- [ ] Seleção de features baseada em significância

**Critérios de Sucesso:**
- 80-100 features implementadas
- Features selecionadas com correlação < 0.95
- CLV melhorado (+1-2%)

#### Mês 5: Online Learning
**Deliverables:**
- [ ] Implementar EWA (Exponentially Weighted Average)
- [ ] Implementar Kalman Filter
- [ ] Atualização de ratings após cada jogo
- [ ] Integração com pipeline de treino

**Critérios de Sucesso:**
- Online learning funcional
- Ratings atualizados em < 50ms
- Adaptabilidade validada

#### Mês 6: Player Props + Execução Algorítmica
**Deliverables:**
- [ ] Implementar Player Props NBA (points, rebounds, assists, PRA)
- [ ] Implementar execução algorítmica via Betfair API
- [ ] Adicionar slippage control
- [ ] Adicionar verificação de liquidez
- [ ] Shadow mode test

**Critérios de Sucesso:**
- Player props implementados
- Execução algorítmica funcional
- Shadow mode validado

---

## 5. FASE 2: FOOTBALL EXPANSION (Meses 7-9)

### 5.1 Overview
- **Duração:** 3 meses
- **Prioridade:** 1
- **ROI Esperado:** 4-6%
- **Liquidez:** Alta

### 5.2 Milestones

#### Mês 7: Research & Data Pipeline
**Deliverables:**
- [ ] Documento de requirements Football
- [ ] Análise de fontes de dados (Football-Data.org, API-Football)
- [ ] Estudo de modelo Poisson + XGBoost híbrido
- [ ] Definição de feature set (60-70 features)
- [ ] Ingestão de dados históricos (3+ temporadas)
- [ ] Data pipeline automatizado

**Critérios de Sucesso:**
- Fontes de dados identificadas e validadas
- 3+ temporadas de dados ingeridas
- Pipeline automatizado operacional

#### Mês 8: Model Development
**Deliverables:**
- [ ] Implementar modelo Poisson para goals
- [ ] Implementar XGBoost para outcome
- [ ] Ensemble de Poisson + XGBoost
- [ ] Walk-forward CV implementado
- [ ] Calibração de probabilidades
- [ ] Model documentation

**Critérios de Sucesso:**
- Modelo treinado com 3+ temporadas
- CV results: ROI > 6%, CLV > 4%
- Modelo documentado

#### Mês 9: Validation & Shadow Mode
**Deliverables:**
- [ ] Backtest completo (3 temporadas)
- [ ] Paper trading (2 semanas)
- [ ] Shadow mode (2 semanas)
- [ ] Stress test (injury scenarios)
- [ ] Documentação de resultados
- [ ] Go/No-Go decision

**Critérios de Sucesso:**
- Backtest ROI > 6%, CLV > 4%
- Paper trading ROI > 4%
- Drawdown < 18%
- Go decision para produção

---

## 6. FASE 3: MMA/UFC EXPANSION (Meses 10-12)

### 6.1 Overview
- **Duração:** 3 meses
- **Prioridade:** 2
- **ROI Esperado:** 5-8%
- **Liquidez:** Média

### 6.2 Milestones

#### Mês 10: Research & Data Pipeline
**Deliverables:**
- [ ] Documento de requirements MMA/UFC
- [ ] Análise de fontes de dados (UFC Stats, Sherdog, Tapology)
- [ ] Estudo de modelo Bayesiano
- [ ] Foco em nichos (UFC prelims, heavyweights)
- [ ] Definição de feature set (50-60 features)
- [ ] Ingestão de dados históricos (2+ temporadas)
- [ ] Data pipeline automatizado

**Critérios de Sucesso:**
- Fontes de dados identificadas e validadas
- 2+ temporadas de dados ingeridas
- Nichos de alto edge identificados

#### Mês 11: Model Development
**Deliverables:**
- [ ] Implementar modelo Bayesiano hierárquico
- [ ] Adicionar features de incerteza (std_dev_prob, effective_sample_size)
- [ ] Meta-labeling com incerteza
- [ ] Walk-forward CV implementado
- [ ] Calibração de probabilidades
- [ ] Retreino pós-evento (após cada card)
- [ ] Model documentation

**Critérios de Sucesso:**
- Modelo treinado com 2+ temporadas
- CV results: ROI > 7%, CLV > 5%
- Incerteza features implementadas
- Retreino pós-evento funcional

#### Mês 12: Validation & Shadow Mode
**Deliverables:**
- [ ] Backtest completo (2 temporadas)
- [ ] Paper trading (1 semana)
- [ ] Shadow mode (1 semana)
- [ ] Stress test (injury scenarios)
- [ ] Documentação de resultados
- [ ] Go/No-Go decision

**Critérios de Sucesso:**
- Backtest ROI > 7%, CLV > 5%
- Paper trading ROI > 5%
- Drawdown < 20%
- Go decision para produção

---

## 7. INTEGRAÇÃO MULTI-DESPORTO (Meses 10-12)

### 7.1 Overview
- **Duração:** 3 meses (paralelo com MMA)
- **Prioridade:** 1.5
- **Objetivo:** Motor de decisão unificado + gestão de risco global

### 7.2 Milestones

#### Mês 10: Motor de Decisão Unificado
**Deliverables:**
- [ ] Implementar agregação de sinais por desporto
- [ ] Implementar ranking de sinais por edge
- [ ] Implementar alocação de capital por desporto
- [ ] Documentação de arquitetura

**Critérios de Sucesso:**
- Motor unificado funcional
- Alocação de capital implementada
- Documentação completa

#### Mês 11: Gestão de Risco Global
**Deliverables:**
- [ ] Implementar limites por desporto
- [ ] Implementar limites de exposição global
- [ ] Implementar circuit breaker global
- [ ] Exit criteria por desporto
- [ ] Documentação de protocolos

**Critérios de Sucesso:**
- Gestão de risco global funcional
- Circuit breaker implementado
- Exit criteria documentados

#### Mês 12: Monitorização e Compliance Multi-Desporto
**Deliverables:**
- [ ] Atualizar dashboard para multi-desporto
- [ ] Adicionar alertas por desporto
- [ ] Atualizar audit trail para multi-desporto
- [ ] Documentação de compliance

**Critérios de Sucesso:**
- Dashboard multi-desporto funcional
- Alertas configurados
- Compliance documentado

---

## 8. GATE REVIEWS

### 8.1 Gate 1: NBA Enhancement Complete (Mês 6)
**Decision Criteria:**
- Ensemble CLV > modelo único ✅/❌
- Feature expansion CLV gain > 1% ✅/❌
- Online learning adaptativo ✅/❌
- Player props CLV > 3% ✅/❌
- Execução algorítmica estável ✅/❌

**Decision:**
- **GO:** Iniciar Football expansion
- **NO-GO:** Fix issues, revalidate

### 8.2 Gate 2: Football Go/No-Go (Mês 9)
**Decision Criteria:**
- Backtest ROI > 6% ✅/❌
- CLV > 4% ✅/❌
- Paper trading ROI > 4% ✅/❌
- Drawdown < 18% ✅/❌
- System stability ✅/❌

**Decision:**
- **GO:** Iniciar MMA/UFC expansion
- **NO-GO:** Fix issues, revalidate, reconsider timeline

### 8.3 Gate 3: MMA/UFC Go/No-Go (Mês 12)
**Decision Criteria:**
- Backtest ROI > 7% ✅/❌
- CLV > 5% ✅/❌
- Paper trading ROI > 5% ✅/❌
- Drawdown < 20% ✅/❌
- Multi-sport integration funcional ✅/❌

**Decision:**
- **GO:** Operar com 3 desportos em produção
- **NO-GO:** Fix issues, revalidate, considerar VBQ-003

---

## 9. RISCOS E MITIGAÇÃO

### 9.1 Risco: Atraso em Validação
**Probabilidade:** Média
**Impacto:** Alto
**Mitigação:**
- Buffer de 2 semanas entre fases
- Parallel development de componentes compartilhados
- Revisão mensal de timeline

### 9.2 Risco: ROI Real < Estimado
**Probabilidade:** Média
**Impacto:** Alto
**Mitigação:**
- Estimativas conservadoras (15-25% NBA, 4-6% Football, 5-8% MMA)
- Critérios de Go/No-Go rigorosos
- Flexibilidade para pausar expansão

### 9.3 Risco: Correlação Entre Desportos
**Probabilidade:** Média
**Impacto:** Médio
**Mitigação:**
- Monitorização de correlação em tempo real
- Limites de exposição por desporto
- Diversificação forçada (< 40% de qualquer desporto)

### 9.4 Risco: Escassez de Recursos
**Probabilidade:** Baixa
**Impacto:** Médio
**Mitigação:**
- Orçamento conservador (200-300€/mês por desporto)
- Priorização clara de features
- Reutilização máxima de componentes

---

## 10. MÉTRICAS DE PROGRESSO

### 10.1 Métricas de Timeline
- **On-Time Delivery:** % de milestones concluídos no prazo
- **Cycle Time:** Tempo médio por fase (target: 3 meses)
- **Velocity:** Número de desportos validados por ano (target: 2)

### 10.2 Métricas de Qualidade
- **Validation Success Rate:** % de desportos que passam Go/No-Go (target: > 80%)
- **ROI Accuracy:** Diferença entre ROI estimado vs real (target: < 20%)
- **Bug Rate:** Número de bugs críticos por fase (target: 0)

### 10.3 Métricas de Negócio
- **ROI Agregado:** ROI ponderado por desporto (target: 15-20% após 3 desportos)
- **Diversificação:** % de P&L por desporto (target: < 40% de qualquer desporto)
- **Custo por Desporto:** Custo total / desportos validados (target: < 1000€/desporto)

---

## 11. REVISÃO E AJUSTE

### 11.1 Revisão Mensal
- Progresso vs timeline
- Blockers e riscos
- Ajustes de prazo se necessário

### 11.2 Revisão Trimestral
- Revisão completa de roadmap
- Ajuste de priorizações
- Reavaliação de orçamento

### 11.3 Revisão Final (Mês 12)
- Avaliação completa de VBQ-002
- Decisão sobre VBQ-003 (Phase 2 Advanced Expansion)
- Planeamento de próximos passos

---

## 12. LINKS CRUZADOS

- [[43_Multi_Sport_Expansion/INDEX]] ← Secção mãe
- [[43_Multi_Sport_Expansion/FOOTBALL_INTEGRATION]] → Detalhes Football
- [[43_Multi_Sport_Expansion/MMA_INTEGRATION]] → Detalhes MMA
- [[43_Multi_Sport_Expansion/UNIFIED_DECISION_ENGINE]] → Motor unificado
- [[05_Machine_Learning/ENSEMBLE_STACKING]] → Ensemble NBA
- [[05_Machine_Learning/FEATURE_ENGINEERING_EXPANDED]] → Features NBA
- [[05_Machine_Learning/ONLINE_LEARNING]] → Online learning NBA
- [[42_Player_Props/PLAYER_PROPS_NBA]] → Player Props NBA
- [[44_Exchange_Execution/BETFAIR_API_EXECUTION]] → Execução algorítmica
- [[08_Risk_Management/EXIT_CRITERIA_SPORT]] → Exit criteria
- [[08_Risk_Management/WHAT_HAPPENS_WHEN_WE_LOSE]] → Stress scenarios

---

**Data de Criação:** 2026-05-13
**Versão:** 2.0.0-12MONTH (VBQ-002)
**Revisão Obrigatória:** Mensal
**Owner:** Product Manager