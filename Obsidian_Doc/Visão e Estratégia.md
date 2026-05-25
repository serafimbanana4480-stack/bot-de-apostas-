# 🎯 Visão e Estratégia

**Componente:** Strategy  
**Status:** ✅ Definido  
**Responsável:** Chief Systems Architect  
**Última atualização:** 2026-05-19

---

## 🎯 Visão Global

Construir um sistema quantitativo de value betting sustentável e escalável, começando com NBA e expandindo progressivamente para múltiplos desportos, mantendo rigor estatístico e foco em lucro real antes de escala.

---

## 🏗️ Filosofia Central

### MVP → Validação → Lucro → Automação → Escala → Sofisticação

**Princípios Fundamentais:**

1. **Simplicidade Primeiro** - Stack simples, features essenciais
2. **Validação Rápida** - Feedback loop curto (dias, não meses)
3. **Lucro Real** - ROI comprovado antes de qualquer expansão
4. **Rigor Estatístico** - Ciência, não gambling
5. **Execução Progressiva** - Manual → One-click → Automática

---

## 📋 Princípios de Decisão

### 5 Perguntas Críticas

Antes de qualquer decisão técnica ou de negócio:

1. **Valida ou impede o edge?**
   - Se impede → **REJEITADA**

2. **Reduz ou aumenta o time-to-validation?**
   - Se aumenta → **PRECISA DE JUSTIFICAÇÃO EXTRAORDINÁRIA**

3. **Aumenta ou reduz a variância do sistema?**
   - Se aumenta → **PRECISA DE MITIGAÇÃO**

4. **Quanto custa em tempo e dinheiro?**
   - Se > 1 semana ou > 200€ → **APROVAÇÃO EXPLÍCITA**

5. **Pode ser revertido?**
   - Se irreversível → **CONSENSO NECESSÁRIO**

---

## 🚫 Decisões Irreversíveis

### Decisões Já Tomadas

| Decisão | Justificativa | Data |
|---------|---------------|------|
| **Python 3.11+** | Stack ML maduro, ecossistema rico | 2026-05-13 |
| **PostgreSQL 15** | Relacional, ACID, JSON support | 2026-05-13 |
| **XGBoost/LightGBM** | State-of-art em tabular data | 2026-05-13 |
| **NBA como foco inicial** | Dados abundantes, mercado eficiente | 2026-05-13 |
| **Moneyline + Spread** | Mercados líquidos, edge mensurável | 2026-05-13 |

### Decisões Reversíveis

| Decisão | Pode ser revertida | Custo |
|---------|-------------------|-------|
| **VPS específico** | ✅ Sim | Baixo |
| **API específica** | ✅ Sim | Médio |
| **Modelo específico** | ✅ Sim | Médio |
| **Bookmaker específico** | ✅ Sim | Baixo |

---

## ⚖️ Trade-offs Arquiteturais

### Trade-offs Documentados

#### 1. Latência vs Accuracy
**Decisão:** Priorizar accuracy sobre latência
**Justificativa:** Em apostas desportivas, accuracy > velocidade
**Mitigação:** Cache de features, batch inference

#### 2. Complexidade vs Maintainability
**Decisão:** Priorizar maintainability
**Justificativa:** Sistema de longo prazo precisa ser manutenível
**Mitigação:** Code quality standards, documentação

#### 3. Cost vs Performance
**Decisão:** Cost consciente, performance adequada
**Justificativa:** Bootstrapping, ROI positivo obrigatório
**Mitigação:** Free tiers, otimização de recursos

#### 4. Speed to Market vs Rigor
**Decisão:** Rigor estatístico > speed
**Justificativa:** Edge real precisa de validação científica
**Mitigação:** MVP com features essenciais, rigor total

---

## 🎯 Critérios de Sucesso

### Por Fase

#### Fase 1: Fundações (Mês 1)
- [x] Infraestrutura operacional
- [x] Ingestão de dados NBA funcional
- [x] 80+ features implementadas
- [ ] Purged CV implementado
- [ ] Modelo baseline XGBoost treinado

#### Fase 2: Modelo com Meta-Labeling (Mês 2)
- [ ] Ensemble stacking funcional
- [ ] Calibração isotônica implementada
- [ ] Meta-labeling reduz falsos positivos em 30%
- [ ] Walk-forward CV passando
- [ ] Brier score < 0.25

#### Fase 3: Shadow Mode (Mês 3)
- [ ] Simulação em 3+ casas funcional
- [ ] Documentos legais prontos
- [ ] Sistema de subscrições Telegram beta
- [ ] CLV shadow > 1.5%
- [ ] 10 beta testers ativos

#### Fase 4: Micro Banca (Mês 4)
- [ ] 500-1000€ Betfair integrados
- [ ] Tracking rigoroso implementado
- [ ] ROI real > 2%
- [ ] CLV real > 1.5%
- [ ] 50+ apostas reais executadas

#### Fase 5: Lançamento Comercial (Mês 5)
- [ ] Automação de relatórios
- [ ] 50 subscritores pagantes
- [ ] Dashboard Streamlit funcional
- [ ] ROI real > 3%
- [ ] MRR > 1000€

#### Fase 6: Expansão (Mês 6)
- [ ] Player Props NBA funcional
- [ ] Deep links Betfair integrados
- [ ] Execução one-click operacional
- [ ] 100+ subscritores
- [ ] MRR > 2500€

---

## 🧠 Estado Mental Operacional

### Como Pensar Sobre o Sistema

#### 1. É Ciência, Não Gambling
- **Mentalidade:** Pesquisa quantitativa, não sorte
- **Abordagem:** Hipótese → Teste → Validação → Escala
- **Métricas:** Estatísticas, não intuição

#### 2. Edge é Frágil
- **Realidade:** Edge desaparece se explorado
- **Consequência:** Proteger edge, não partilhar publicamente
- **Ação:** Shadow mode, validação rigorosa

#### 3. Longo Prazo > Curto Prazo
- **Mentalidade:** Sobrevivência a longo prazo
- **Decisões:** Gestão de risco rigorosa
- **Resultado:** Consistência > spikes

#### 4. Simplificar Sempre
- **Princípio:** Complexidade só quando necessário
- **Ação:** Questionar cada feature
- **Resultado:** Sistema manutenível

#### 5. Documentar Tudo
- **Regra:** Decisão sem documento = não existe
- **Ação:** Documentar antes de implementar
- **Resultado:** Traceability completo

---

## 📈 Roadmap Estratégico

### 12 Meses: Fases 1-6

```
FASE 1 — FUNDAÇÕES (Mês 1)
├─ Infraestrutura
├─ Dados NBA
├─ Features (80+)
├─ Purged CV
└─ Modelo Baseline

FASE 2 — MODELO (Mês 2)
├─ Ensemble Stacking
├─ Calibração Isotônica
├─ Meta-labeling
├─ Walk-forward CV
└─ Validação Rigorosa

FASE 3 — SHADOW MODE (Mês 3)
├─ Simulação 3+ Casas
├─ Documentos Legais
├─ Telegram Beta
├─ CLV Shadow
└─ Beta Testers

FASE 4 — MICRO BANCA (Mês 4)
├─ 500-1000€ Betfair
├─ Tracking Rigoroso
├─ ROI Real
├─ CLV Real
└─ 50+ Apostas

FASE 5 — COMERCIAL (Mês 5)
├─ Automação Relatórios
├─ 50 Subscritores
├─ Dashboard Streamlit
├─ ROI > 3%
└─ MRR > 1000€

FASE 6 — EXPANSÃO (Mês 6)
├─ Player Props NBA
├─ Deep Links Betfair
├─ One-click Execution
├─ 100+ Subscritores
└─ MRR > 2500€
```

### 24 Meses: Fases 7-12 (Planeamento Futuro)

```
FASE 7-9 — MULTI-DESPORTO (Mês 7-9)
├─ Football
├─ UFC/MMA
├─ Tennis
└─ Esports

FASE 10-12 — AUTOMAÇÃO (Mês 10-12)
├─ Execução Automática
├─ 200+ Subscritores
├─ MRR > 5000€
└─ Institucional
```

---

## 🎯 Foco Estratégico

### O Que Fazer

- **Foco NBA** até validação completa
- **Rigor estatístico** desde o dia 1
- **Gestão de risco** conservadora
- **Documentação** completa
- **Lucro real** antes de escala

### O Que Não Fazer

- **Expansão prematura** sem validação
- **Over-engineering** sem justificação
- **Promessas de retornos** a subscritores
- **Segredos hardcoded** em código
- **Decisões irreversíveis** sem consenso

---

## 📊 Métricas de Sucesso do Projeto

### Métricas Técnicas
- **Uptime:** > 99.5%
- **Latência:** < 1s
- **Taxa de falhas:** < 1%
- **Coverage de testes:** > 80%

### Métricas de Modelo
- **Brier Score:** < 0.25
- **ECE:** < 0.05
- **AUC-ROC:** > 0.65
- **Log Loss:** Minimizado

### Métricas de Negócio
- **ROI Real:** > 3%
- **CLV Real:** > 2%
- **Drawdown:** < 20%
- **Sharpe Ratio:** > 1.0

### Métricas de Produto
- **Subscritores:** Crescimento mensal
- **Churn:** < 5% mensal
- **NPS:** > 50
- **MRR:** Crescimento consistente

---

## 🚨 Riscos e Mitigações

### Riscos Principais

#### 1. Edge Desaparece
**Probabilidade:** Alta  
**Impacto:** Crítico  
**Mitigação:**
- Diversificação de mercados
- Melhoria contínua de modelos
- Monitorização de CLV
- Shadow mode constante

#### 2. Regulamentação
**Probabilidade:** Média  
**Impacto:** Alto  
**Mitigação:**
- Compliance desde o início
- Consultoria legal
- Jurisdições favoráveis
- Documentação completa

#### 3. Overfitting
**Probabilidade:** Média  
**Impacto:** Alto  
**Mitigação:**
- Purged CV rigoroso
- Walk-forward validation
- Meta-labeling
- Monitorização de drift

#### 4. Falhas Técnicas
**Probabilidade:** Média  
**Impacto:** Médio  
**Mitigação:**
- Redundância de sistemas
- Backups automáticos
- Monitorização 24/7
- Runbooks completos

---

## 📝 Próximos Passos Estratégicos

### Imediatos (1-2 semanas)
- [ ] Completar Fase 1 implementação
- [ ] Validar pipeline de dados
- [ ] Treinar modelo baseline
- [ ] Setup shadow mode

### Curto Prazo (1-2 meses)
- [ ] Validar edge real
- [ ] Implementar meta-labeling
- [ ] Lançar beta testing
- [ ] Preparar documentos legais

### Médio Prazo (3-6 meses)
- [ ] Micro banca real
- [ ] Lançamento comercial
- [ ] Expansão de mercados
- [ ] Automação de operações

---

## 🔗 Links Relacionados

- [[Modelo de Negócio]] - Monetização e SaaS
- [[Índice Mestre]] - Documentação completa
- [[Roadmap de Implementação]] - Detalhes técnicos
- [[Critérios de Sucesso]] - Métricas por fase

---

**Última atualização:** 2026-05-19  
**Responsável:** Chief Systems Architect  
**Status:** ✅ Definido