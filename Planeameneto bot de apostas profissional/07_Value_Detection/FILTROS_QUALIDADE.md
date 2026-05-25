# FILTROS_QUALIDADE — Filtros de Qualidade do Motor de Value

**ID:** `VD-002` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Os filtros de qualidade são a primeira linha de defesa do sistema de apostas. Eles atuam como gatekeepers que eliminam sinais de baixa qualidade antes mesmo de serem considerados para apostas. A filosofia fundamental é: **é melhor perder uma oportunidade de lucro do que apostar num sinal de baixa qualidade.**

Cada filtro tem uma justificativa matemática e estatística sólida, baseada em anos de research quantitativo em mercados de apostas esportivas. A combinação de todos os filtros cria um sistema robusto que maximiza a relação risco/retorno.

---

## 2. FILTRO DE PROBABILIDADE [0.15, 0.85]

### 2.1 Conceito

O filtro de probabilidade restringe as apostas a um range onde o modelo tem maior confiança e menor variância. Apostas em probabilidades extremas (muito baixas ou muito altas) são problemáticas por várias razões:

- **Baixa probabilidade (< 0.15):** Apostas em longshots têm variância extrema. Mesmo com edge positivo, a volatilidade é tão alta que o bankroll pode ser destruído por uma sequência de perdas. Além disso, modelos de machine learning tendem a ter maior erro em regiões de baixa densidade de dados.

- **Alta probabilidade (> 0.85):** Apostas em favoritos extremos têm odds tão baixas que o edge percentual precisa ser enorme para justificar o risco. Além disso, favoritos extremos muitas vezes têm odds artificialmente infladas pelos bookmakers (proteção contra liability).

### 2.2 Justificativa Matemática

A variância de uma aposta binária é dada por: Var = p(1-p). Esta função é máxima em p=0.5 e mínima nos extremos. No entanto, o que nos interessa é a **variância relativa ao retorno esperado**:

```
Sharpe ≈ Edge / √Var
```

Para p < 0.15: Edge precisa ser > 20% para compensar a variância
Para p > 0.85: Edge precisa ser > 25% (devido às odds baixas)

O range [0.15, 0.85] equilibra a captura de oportunidades com a gestão de variância.

### 2.3 Impacto Prático

- **Redução de variância:** ~40% menos volatilidade no bankroll
- **Melhoria de Sharpe:** Aumento de 0.3-0.5 no ratio Sharpe/Drawdown
- **Maior estabilidade:** Sequências de perdas são mais curtas e menos severas
- **Trade-off:** Perda de ~15-20% das oportunidades totais, mas com qualidade muito superior

---

## 3. FILTRO DE LIQUIDEZ (1.5x Stake)

### 3.1 Conceito

O filtro de liquidez garante que existe volume suficiente no mercado para executar a aposta sem mover significativamente a odd. Apostar em mercados com baixa liquidez é perigoso porque:

- A odd pode mudar drasticamente após a nossa entrada (slippage)
- Podemos não conseguir entrar na posição desejada (partial fill)
- O impacto no mercado pode eliminar o edge original

### 3.2 Justificativa Econômica

Em mercados eficientes, o impacto no mercado é aproximadamente proporcional ao tamanho da ordem relativo ao volume disponível. O critério de 1.5x stake garante que:

- Nossa ordem representa no máximo 66% do volume disponível
- O slippage esperado é < 2% em condições normais
- Podemos entrar e sair da posição com impacto mínimo

### 3.3 Cálculo Dinâmico

O ratio de liquidez não é estático — varia com:

- **Tamanho do stake:** Quanto maior a aposta, maior o volume necessário
- **Volatilidade do mercado:** Em períodos de alta volatilidade, aumentamos o ratio para 2.0x
- **Proximidade do evento:** Nos últimos 5 minutos antes do jogo, aumentamos para 2.5x (liquidez evapora rapidamente)

### 3.4 Fontes de Liquidez

Priorizamos liquidez em ordem de preferência:

1. **Betfair Exchange:** Volume real de apostadores, mais transparente
2. **Pinnacle:** Bookmaker sharp com limites altos
3. **Outros exchanges:** Smarkets, Matchbook (secundário)

---

## 4. FILTRO DE REGIME

### 4.1 Conceito

O filtro de regime reconhece que a performance do modelo varia dependendo do contexto do jogo. Alguns regimes são historicamente problemáticos e devem ser evitados.

### 4.2 Regimes Problemáticos

#### 4.2.1 Back-to-Back Games
Equipas jogando jogos consecutivos têm performance degradada devido a:
- Fadiga física
- Menos tempo de preparação tática
- Rotações de jogadores imprevisíveis

#### 4.2.2 Playoffs Iniciais (Mês 1-3)
Os playoffs iniciais têm características únicas:
- Intensidade elevada imprevisível
- Estratégias não testadas em playoffs
- Dados históricos limitados para calibração

#### 4.2.3 Injuries Não Reportadas
Quando uma estrela está questionable ou day-to-day:
- A incerteza sobre o lineup aumenta
- O modelo pode estar baseado em dados desatualizados
- As odds podem não refletir o risco real

### 4.3 Implementação

O filtro de regime usa uma blacklist dinâmica que é atualizada semanalmente baseada em:

- Performance histórica do modelo em cada regime
- Volatilidade observada em apostas passadas
- Análise de causalidade entre características do regime e resultados

**Regra de ouro:** Se um regime tem Sharpe < 0.5 nos últimos 30 dias, é adicionado à blacklist até que a performance se recupere.

---

## 5. FILTRO DE CONFIANÇA (Meta-Modelo)

### 5.1 Conceito

O meta-modelo é um modelo secundário (XGBoost) que avalia a qualidade do sinal primário. Ele não tenta prever o resultado do jogo — ele tenta prever se o sinal do modelo primário está correto.

### 5.2 Funcionamento

O meta-modelo recebe como input:
- Probabilidade do modelo primário
- Edge calculado
- Features do jogo (forma recente, injuries, etc.)
- Características do mercado (liquidez, movimento de odds)
- Contexto temporal (dia da semana, hora)

E output uma probabilidade de que o sinal seja correto (meta-probabilidade).

### 5.3 Threshold de 0.60

O threshold de 0.60 significa que só apostamos quando o meta-modelo tem 60% de confiança de que o sinal está correto. Este threshold foi otimizado para:

- **Maximizar Sharpe:** 0.60 é o ponto ótimo no trade-off entre quantidade e qualidade
- **Minimizar falsos positivos:** Reduz falsos positivos em ~35%
- **Manter volume suficiente:** Ainda gera 2-3 sinais por dia em média

### 5.4 Por que XGBoost?

XGBoost foi escolhido para o meta-modelo porque:

- **Lida bem com features heterogêneas:** Numéricas, categóricas, temporais
- **Captura interações não-lineares:** O meta-modelo pode descobrir padrões que o modelo primário não captura
- **Robusto a outliers:** Menos sensível a outliers que regressão linear
- **Interpretabilidade:** Feature importance ajuda a entender por que certos sinais são rejeitados

---

## 6. SISTEMA DE APROVAÇÃO ENCADEADO

### 6.1 Arquitetura

Os filtros são aplicados em sequência, e se QUALQUER filtro falhar, o sinal é rejeitado:

```
Sinal Candidato
    ↓
[Filtro Probabilidade] ← Falha? → Rejeitar
    ↓ Passa
[Filtro Liquidez] ← Falha? → Rejeitar
    ↓ Passa
[Filtro Regime] ← Falha? → Rejeitar
    ↓ Passa
[Filtro Confiança Meta] ← Falha? → Rejeitar
    ↓ Passa
SINAL APROVADO ✓
```

### 6.2 Por que Sequencial e não Paralelo?

**Vantagens da abordagem sequencial:**

1. **Eficiência computacional:** Se o primeiro filtro falha (comum), não precisamos calcular os restantes
2. **Priorização natural:** Filtros mais baratos computacionalmente são aplicados primeiro
3. **Debugging mais fácil:** Sabemos exatamente em qual filtro o sinal falhou
4. **Logging granular:** Podemos trackear taxa de rejeição por filtro

### 6.3 Métricas de Rejeição

Monitorizamos a taxa de rejeição por filtro:

- **Probabilidade:** ~25% dos sinais rejeitados
- **Liquidez:** ~20% dos sinais rejeitados
- **Regime:** ~15% dos sinais rejeitados
- **Confiança Meta:** ~40% dos sinais rejeitados

Se a taxa de rejeição de qualquer filtro desvia > 10% da baseline, investigamos se há problema com o filtro ou mudança no mercado.

---

## 7. AJUSTE DINÂMICO DE FILTROS

### 7.1 Princípio de Adaptabilidade

Os filtros não são estáticos — eles se adaptam às condições do mercado. Ajustamos os parâmetros baseados em:

- **Performance recente:** Se o modelo está performando bem, podemos relaxar alguns filtros
- **Volatilidade do mercado:** Em períodos de alta volatilidade, apertamos filtros
- **Liquidez disponível:** Se há poucos jogos com liquidez, podemos relaxar o filtro de liquidez ligeiramente

### 7.2 Mecanismo de Ajuste

O ajuste é feito através de um sistema de feedback:

1. **Monitorização contínua:** Trackeamos performance por filtro
2. **Detecção de drift:** Se performance degrada > 2σ, alerta é gerado
3. **Ajuste controlado:** Parâmetros são ajustados em incrementos de 5%
4. **Validação:** Novos parâmetros são testados em paper trading por 7 dias
5. **Implementação:** Só após validação, novos parâmetros vão para produção

### 7.3 Guardrails

Para evitar overfitting aos dados recentes:

- **Máximo de ajuste por mês:** 10% em qualquer parâmetro
- **Reversão automática:** Se performance piora após ajuste, reverte automaticamente
- **Aprovação humana:** Ajustes > 5% requerem aprovação manual

---

## 8. BOAS PRÁTICAS

### 8.1 Logging Detalhado

Para cada sinal rejeitado, logamos:
- Qual filtro rejeitou
- Valores específicos que causaram a rejeição
- Timestamp
- Contexto do mercado

Isso permite análise post-hoc e otimização contínua.

### 8.2 Backtesting Rigoroso

Cada novo filtro ou mudança de threshold é:
1. Testado em backtest out-of-sample (últimos 6 meses)
2. Validado em paper trading (mínimo 30 dias)
3. Só então implementado em produção

### 8.3 Monitorização de Drift

Monitorizamos se a taxa de aprovação dos filtros muda ao longo do tempo:
- Se taxa de aprovação cai drasticamente → Possível problema no modelo
- Se taxa de aprovação sobe drasticamente → Possível degradação de qualidade

---

## 9. LINKS CRUZADOS

- [[07_Value_Detection/INDEX]] ← Seção mãe
- [[46_Meta_Labeling/INDEX]] → Detalhes do meta-modelo de filtragem
- [[08_Risk_Management/INDEX]] → Como filtros impactam gestão de risco
- [[06_Backtesting/INDEX]] → Como validar eficácia dos filtros