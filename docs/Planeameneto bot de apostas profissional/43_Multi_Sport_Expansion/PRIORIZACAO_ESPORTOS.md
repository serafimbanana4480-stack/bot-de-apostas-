# PRIORIZACAO_ESPORTOS — Matriz de Priorização

**ID:** `MSE-006` | **Fase:** #phase/7-12 | **Owner:** Product Manager | **Status:** #status/active | **Versão:** `2.0.0-VBQ-002`

---

## 1. OBJETIVO

Definir uma matriz sistemática para priorizar quais desportos expandir primeiro, baseado em ROI potencial, liquidez, complexidade e risco.

---

## 2. FRAMEWORK DE PRIORIZAÇÃO

### 2.1 Critérios de Avaliação

Cada desporto é avaliado em 5 dimensões:

| Critério | Peso | Descrição |
|----------|------|-----------|
| **ROI Potencial** | 30% | Edge estimado baseado em eficiência de mercado |
| **Liquidez** | 25% | Volume médio de aposta e limites das casas |
| **Complexidade** | 20% | Dificuldade de implementação (dados, modelo, execução) |
| **Risco** | 15% | Volatilidade, incerteza de dados, risco de execução |
| **Tempo de Validade** | 10% | Estabilidade de edge ao longo do tempo |

### 2.2 Escoring System

Cada critério é scored de 1-5:
- **5 = Excelente** (alto ROI, alta liquidez, baixa complexidade, baixo risco)
- **3 = Médio**
- **1 = Ruim** (baixo ROI, baixa liquidez, alta complexidade, alto risco)

**Score Final = Σ (Score × Peso)**

---

## 3. MATRIZ DE PRIORIZAÇÃO (VBQ-002)

### 3.1 Desportos Analisados - Fase Atual (VBQ-002)

| Desporto | ROI Potencial | Liquidez | Complexidade | Risco | Tempo Validade | Score Final | Prioridade | Fase |
|----------|---------------|----------|--------------|-------|----------------|-------------|------------|------|
| **Football** | 4 (4-6%) | 5 (Muito Alta) | 3 (Média) | 3 (Médio) | 4 (Estável) | **3.95** | **1** | 7-9 |
| **MMA/UFC** | 4 (5-8%) | 2 (Baixa) | 2 (Alta) | 2 (Alto) | 3 (Médio) | **2.85** | **2** | 10-12 |

### 3.2 Desportos Analisados - Futuro (VBQ-003)

| Desporto | ROI Potencial | Liquidez | Complexidade | Risco | Tempo Validade | Score Final | Prioridade | Fase |
|----------|---------------|----------|--------------|-------|----------------|-------------|------------|------|
| **NFL** | 4 (3-5%) | 4 (Alta) | 3 (Média) | 3 (Médio) | 4 (Estável) | **3.70** | **1** | 13-15 |
| **Tennis ATP** | 5 (4-6%) | 3 (Média) | 3 (Média) | 2 (Médio-Alto) | 3 (Médio) | **3.55** | **2** | 16-18 |
| **LoL Esports** | 5 (8-12%) | 2 (Média-Baixa) | 1 (Muito Alta) | 1 (Alto) | 1 (Baixo) | **2.75** | **3** | 19-21 |
| **Soccer EPL** | 2 (1-3%) | 5 (Muito Alta) | 1 (Muito Alta) | 3 (Médio) | 4 (Estável) | **2.70** | **4** | 22-24 |
| **MLB** | 3 (2-4%) | 4 (Alta) | 3 (Média) | 3 (Médio) | 4 (Estável) | **3.35** | **5** | 25-27 |
| **NHL** | 3 (2-4%) | 3 (Média) | 3 (Média) | 3 (Médio) | 4 (Estável) | **3.10** | **6** | 28-30 |
| **CS:GO** | 4 (6-10%) | 2 (Baixa) | 2 (Alta) | 1 (Alto) | 1 (Baixo) | **2.60** | **7** | 31-33 |

---

## 4. ANÁLISE DETALHADA - VBQ-002

### 4.1 Prioridade 1: Football (Score 3.95)

**Porquê Primeiro em VBQ-002?**
- ROI potencial alto (4-6%) com liquidez muito alta
- Complexidade gerível (modelo Poisson + XGBoost híbrido)
- Dados de qualidade disponíveis (FBref, Sportmonks, Understat)
- Mercado eficiente mas com ineficiências em ligas secundárias
- Edge maior em Asian Handicap e O/U 2.5

**Desafios:**
- Empates (0-0) aumentam complexidade de modelagem
- Lesões têm impacto maior que NBA
- Menos jogos que NBA (380/época vs 1230)
- Volatilidade de odds maior (mais movimentos de mercado)

**Timeline Estimada:** 3 meses até produção (Fase 7-9)

---

### 4.2 Prioridade 2: MMA/UFC (Score 2.85)

**Porquê Segundo em VBQ-002?**
- ROI potencial muito alto (5-8%) - maior dos dois
- Mercado ineficiente = oportunidades significativas
- Dados detalhados disponíveis (UFC Stats, Sherdog)
- Stylistic matchups criam edge previsível

**Desafios:**
- Liquidez baixa (especialmente em prelims)
- Complexidade alta (weight classes, styles, ring rust)
- Risco alto (volatilidade extrema em heavyweights)
- Menos dados (menos lutas que jogos NBA)
- Incerteza alta em lutadores novos (< 3 lutas)

**Timeline Estimada:** 3 meses até produção (Fase 10-12)

**Nota:** Apesar do score médio, o ROI muito alto justifica priorização após Football. Priorizar prelims e heavyweights para maximizar edge.

---

## 5. ANÁLISE DETALHADA - VBQ-003 (Futuro)

### 5.1 Prioridade 1: NFL (Score 3.70)

**Porquê Primeiro em VBQ-003?**
- Alto ROI potencial (3-5%) com liquidez excelente
- Complexidade gerível (similar à NBA em muitos aspetos)
- Dados de qualidade disponíveis
- Mercado eficiente mas com ineficiências exploráveis (clima, bye weeks)

**Desafios:**
- Menos jogos que NBA (272 vs 1230) = menos amostras
- Lesões têm impacto maior
- Clima é fator externo não modelável

**Timeline Estimada:** 4-5 meses até produção (Fase 13-15)

---

### 5.2 Prioridade 2: Tennis ATP (Score 3.55)

**Porquê Segundo em VBQ-003?**
- ROI potencial muito alto (4-6%)
- Desporto individual = mais previsível
- Menos liquidez = mais ineficiências
- Dados disponíveis (Tennis Abstract)

**Desafios:**
- Lesões frequentes e não reportadas
- Surface variability requer modelos separados
- Motivation variável em torneios menores
- Baixa liquidez em torneios ATP 250

**Timeline Estimada:** 4-5 meses até produção (Fase 16-18)

---

### 5.3 Prioridade 3: LoL Esports (Score 2.75)

**Porquê Terceiro em VBQ-003?**
- ROI potencial muito alto (8-12%) - maior de todos
- Mercado ineficiente = oportunidades significativas
- Dados detalhados disponíveis (Oracle's Elixir)

**Desafios:**
- Complexidade muito alta (patches, meta shifts)
- Risco alto (modelos obsoletos rapidamente)
- Liquidez média-baixa
- Tempo de validade baixo (patches mudam edge)

**Timeline Estimada:** 6-7 meses até produção (Fase 19-21)

**Nota:** Apesar do score médio, o ROI muito alto justifica priorização após validação de 1-2 desportos tradicionais.

---

### 5.4 Prioridade 4: Soccer EPL (Score 2.70)

**Porquê Quarto em VBQ-003?**
- Liquidez muito alta (maior do mundo)
- Dados abundantes (décadas de histórico)
- Infraestrutura madura

**Desafios:**
- ROI potencial muito baixo (1-3%)
- Mercado extremamente eficiente
- Complexidade muito alta (táticas, empates)
- Edge pequeno requer execução perfeita

**Timeline Estimada:** 7-8 meses até produção (Fase 22-24)

**Nota:** A baixa prioridade deve-se à dificuldade de encontrar edge em mercado tão eficiente. Apenas considerado após validação de outros desportos com edge mais claro.

---

## 6. ESTRATÉGIA DE EXPANSÃO

### 6.1 VBQ-002 (Fase 7-12)

**Sequência Atual:**
1. **Fase 7-9:** Football (após NBA baseline validado)
2. **Fase 10-12:** MMA/UFC (após Football validado)

### 6.2 VBQ-003 (Fase 13-30)

**Sequência Futura:**
1. **Fase 13-15:** NFL (após MMA/UFC validado)
2. **Fase 16-18:** Tennis ATP (após NFL validado)
3. **Fase 19-21:** LoL Esports (após Tennis validado)
4. **Fase 22-24:** Soccer EPL (após LoL validado)
5. **Fase 25-27:** MLB (opcional, se recursos disponíveis)
6. **Fase 28-30:** NHL (opcional, se recursos disponíveis)

### 6.3 Critérios de Progressão

Antes de adicionar novo desporto, o anterior deve:
- ✅ Ter ROI real > 3% (backtest + paper trading)
- ✅ Ter CLV > 2%
- ✅ Operar estável por 2+ meses
- ✅ Ter drawdown < 15%
- ✅ Passar todos os stress tests

**Se critérios não cumpridos:**
- 🔴 Pause expansão
- 🔴 Fix issues no desporto atual
- 🔴 Revalidar antes de continuar

### 6.4 Parallel Development (Futuro)

Após 3-4 desportos validados:
- Considerar parallel development de desportos similares
- Ex: NBA + MLB podem ser desenvolvidos em paralelo (ambos desportos de equipa americanos)
- Requer recursos adicionais (team size > 1)

---

## 7. ANÁLISE DE SENSIBILIDADE

### 7.1 Cenário Otimista
Se Football e MMA/UFC superam expectativas (ROI > 6%):
- Acelerar expansão para NFL
- Considerar adicionar MLB em paralelo
- Reavaliar LoL Esports (talvez edge maior que esperado)

### 7.2 Cenário Pessimista
Se Football ou MMA/UFC falham validação:
- Reavaliar framework de priorização
- Considerar desportos alternativos (NFL, NHL)
- Focar em otimizar NBA antes de expandir

### 7.3 Cenário Base
Assumindo ROI real de 4-5% para Football/MMA:
- Seguir sequência recomendada
- 1 novo desporto a cada 3 meses (VBQ-002)
- 2-3 desportos em produção após 12 meses

---

## 8. MÉTRICAS DE SUCESSO DA PRIORIZAÇÃO

### 8.1 Métricas de Curto Prazo (VBQ-002: 6-12 meses)
- **Número de Desportos Validados:** Target = 2 (Football + MMA/UFC)
- **ROI Agregado:** Target = 5-7%
- **Tempo até Novo Desporto:** Target = 3 meses por desporto
- **Custo de Desenvolvimento:** Target = < 150€/mês adicionais por desporto

### 8.2 Métricas de Longo Prazo (VBQ-003: 24 meses)
- **Número de Desportos em Produção:** Target = 5-6
- **ROI Agregado:** Target = 6-8%
- **Diversificação de Risco:** < 25% de P&L de um único desporto
- **Escalabilidade:** Capacidade de adicionar 1 desporto/3-4 meses com recursos atuais

---

## 9. REVISÃO E AJUSTE

### 9.1 Revisão Trimestral
A cada 3 meses, reavaliar matriz de priorização:
- Atualizar scores baseados em resultados reais
- Considerar novos desportos emergentes
- Ajustar pesos dos critérios se necessário

### 9.2 Trigger para Revisão Extraordinária
Revisão imediata se:
- ROI real desvia > 50% do estimado
- Liquidez de mercado muda drasticamente
- Novas fontes de dados disponíveis
- Regulações mudam em mercados específicos

---

## 10. LINKS CRUZADOS

- [[43_Multi_Sport_Expansion/INDEX]] ← Secção mãe
- [[43_Multi_Sport_Expansion/ROADMAP_EXPANSAO]] → Timeline 12 meses (VBQ-002)
- [[43_Multi_Sport_Expansion/FOOTBALL_INTEGRATION]] → Detalhes Football (VBQ-002)
- [[43_Multi_Sport_Expansion/MMA_INTEGRATION]] → Detalhes MMA/UFC (VBQ-002)
- [[43_Multi_Sport_Expansion/EXPANSAO_NFL]] → Detalhes NFL (VBQ-003)
- [[43_Multi_Sport_Expansion/EXPANSAO_TENNIS_ATP]] → Detalhes Tennis (VBQ-003)
- [[43_Multi_Sport_Expansion/EXPANSAO_ESPORTS_LOL]] → Detalhes LoL (VBQ-003)
- [[43_Multi_Sport_Expansion/EXPANSAO_SOCCER_EPL]] → Detalhes Soccer (VBQ-003)
- [[01_Vision_And_Strategy/FILOSOFIA_MVP]] → Regra: um desporto de cada vez
- [[02_Business_Model/PLANO_FINANCEIRO_6_MESES]] → Impacto financeiro

---

**Data de Criação:** 2026-05-13
**Última Atualização:** 2026-05-13 (VBQ-002)
**Revisão Obrigatória:** Trimestral (próxima: 2026-08-13)
**Owner:** Product Manager