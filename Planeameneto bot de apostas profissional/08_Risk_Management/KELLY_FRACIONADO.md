# KELLY_FRACIONADO — Sizing de Apostas

**ID:** `RM-001` | **Fase:** #phase/2 | **Owner:** Risk Manager | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar um sistema de dimensionamento de apostas baseado no critério de Kelly fracionado que maximiza o crescimento esperado da banca enquanto controla o risco de ruína. O objetivo não é maximizar o lucro de curto prazo — isso requereria Kelly completo que é perigosamente agressivo — mas encontrar o equilíbrio ótimo entre crescimento e sobrevivência. Kelly fracionado é a ferramenta matemática que permite este equilíbrio.

---

## 2. TEORIA DE KELLY

### 2.1 Origem e Fundamentação

O critério de Kelly foi desenvolvido por John L. Kelly Jr. em 1956 na Bell Labs. A fórmula determina a fração ótima da banca a apostar para maximizar o crescimento esperado a longo prazo, assumindo que as probabilidades de sucesso são conhecidas com precisão. Kelly provou matematicamente que apostar esta fração ótima maximiza o logaritmo da riqueza esperada, o que é equivalente a maximizar o crescimento geométrico da banca.

### 2.2 A Fórmula de Kelly

A fórmula original de Kelly para uma aposta simples é:

```
f* = (bp - q) / b
```

Onde:
- f* = fração ótima da banca a apostar
- b = odds decimais - 1 (o "bounty" ou payoff neto)
- p = probabilidade de sucesso
- q = probabilidade de falha = 1 - p

Em termos mais intuitivos para apostas desportivas com odds decimais:

```
f* = (probabilidade × odd - 1) / (odd - 1)
```

Se o resultado é negativo ou zero, não há edge matemático e a aposta deve ser zero.

### 2.3 Interpretação Intuitiva

Kelly diz para apostar uma fração da banca proporcional ao edge (vantagem matemática). Se o edge é pequeno, aposte pouco. Se o edge é grande, aposte mais. Mas nunca aposte mais do que o edge justifica. Isto faz sentido intuitivo: se temos uma pequena vantagem, não devemos arriscar muito capital. Se temos uma grande vantagem, podemos arriscar mais.

---

## 3. POR QUE KELLY FRACIONADO

### 3.1 Perigos do Kelly Completo

Kelly completo (K=1.0) é matematicamente ótimo para maximizar crescimento a longo prazo, MAS assume:
1. Probabilidades perfeitamente conhecidas
2. Apostas independentes
3. Capacidade de apostar infinitamente pequenas frações
4. Sem custos de transação
5. Sem restrições de liquidez

Na prática, nenhuma destas assunções é verdadeira em apostas desportivas. Como resultado, Kelly completo é extremamente volátil e pode levar a drawdowns severos. Um erro pequeno na estimativa de probabilidade pode levar a stakes excessivos e potencial ruína.

### 3.2 Vantagens do Kelly Fracionado

Kelly fracionado (multiplicar a fração de Kelly por um fator K < 1) reduz drasticamente a volatilidade enquanto mantém a maior parte do crescimento esperado. Por exemplo, meio Kelly (K=0.5) reduz a volatilidade em cerca de 70% enquanto reduz o crescimento esperado em apenas 25%. Esta relação favorável entre redução de risco e redução de retorno é por que Kelly fracionado é preferido na prática.

**Benefícios:**
- Redução drástica de drawdowns
- Maior tolerância a erros na estimativa de probabilidade
- Maior resiliência a sequências de perdas
- Crescimento ainda muito superior a stake fixo
- Menor stress psicológico para o operador

---

## 4. ESCOLHA DO FATOR DE FRACIONAMENTO

### 4.1 Kelly Completo (K=1.0)

**Características:** Máximo crescimento esperado, máxima volatilidade.

**Quando usar:** Quase nunca. Apenas em simulações ou paper trading onde não há dinheiro real em risco.

**Riscos:** Drawdowns de 50%+ são comuns. Probabilidade de ruína significativa mesmo com edge positivo. Requer estimativas de probabilidade extremamente precisas.

**Probabilidade de ruína:** Para banca de €1,000 com edge 3%, probabilidade de ruína ≈ 13.5%.

---

### 4.2 Meio Kelly (K=0.5)

**Características:** Bom equilíbrio entre crescimento e risco. É o padrão recomendado para a maioria das situações.

**Quando usar:** Operação normal com edge confirmado e estável. Quando o modelo é bem validado e as probabilidades são confiáveis.

**Riscos:** Drawdowns de 20-30% ainda podem ocorrer. Requer disciplina para não aumentar para Kelly completo durante winning streaks.

**Probabilidade de ruína:** Para banca de €1,000 com edge 3%, probabilidade de ruína ≈ 1.8%.

---

### 4.3 Quarter Kelly (K=0.25)

**Características:** Muito conservador. Baixa volatilidade, crescimento moderado.

**Quando usar:** Fases iniciais (micro banca), quando edge é marginal ou incerto, durante drawdowns significativos, ou quando a tolerância a risco é baixa.

**Riscos:** Crescimento mais lento. Pode parecer "muito conservador" durante winning streaks.

**Probabilidade de ruína:** Para banca de €1,000 com edge 3%, probabilidade de ruína ≈ 0.13%.

---

### 4.4 Eighth Kelly (K=0.125)

**Características:** Extremamente conservador. Mínima volatilidade.

**Quando usar:** Fases de teste extremamente conservadoras, quando edge é muito baixo ou incerto, ou quando a prioridade absoluta é preservação de capital.

**Riscos:** Crescimento muito lento. Pode não justificar o esforço de operar o sistema.

**Probabilidade de ruína:** Para banca de €1,000 com edge 3%, probabilidade de ruína ≈ 0.01%.

---

## 5. CÁLCULO DE STAKE

### 5.1 Fórmula Completa

O stake é calculado em três passos:

1. Calcular Kelly óteo usando probabilidade e odd
2. Aplicar fator de fracionamento (K)
3. Aplicar limites absolutos (hard caps)

**Fórmula:**
```
Stake = min(K × Kelly_Otimo, Hard_Cap)
```

Onde Hard_Cap é tipicamente 2% da banca por aposta, independentemente do que Kelly sugira.

### 5.2 Exemplos Práticos

| Banca | Prob | Odd | Edge | Kelly Full | Meio Kelly | Quarter Kelly | Stake Final (max 2%) |
|-------|------|-----|------|------------|------------|---------------|---------------------|
| €1,000 | 0.55 | 2.00 | 10% | 10.0% | 5.0% | 2.5% | €50 |
| €1,000 | 0.60 | 1.80 | 8% | 7.5% | 3.75% | 1.875% | €37.50 |
| €1,000 | 0.52 | 2.10 | 9.2% | 9.2% | 4.6% | 2.3% | €46 (limitado a €20 por hard cap) |
| €1,000 | 0.50 | 2.00 | 0% | 0.0% | 0.0% | 0.0% | €0 (sem edge) |
| €5,000 | 0.58 | 1.90 | 10.2% | 10.8% | 5.4% | 2.7% | €135 (limitado a €100 por hard cap) |

**Nota:** No terceiro exemplo, Quarter Kelly sugere 2.3% da banca (€23), mas o hard cap de 2% limita a €20. Este hard cap é uma proteção adicional contra overbetting mesmo com Kelly fracionado.

---

## 6. LIMITES DE EXPOSIÇÃO

### 6.1 Por Aposta

**Limite:** Máximo 2% da banca por aposta individual.

**Justificativa:** Mesmo uma aposta com edge muito alto não deve arriscar mais de 2% da banca. Isto limita o dano máximo que uma única aposta errada pode causar. Se uma aposta de 2% for perdida, a banca cai para 98% — recuperável. Se uma aposta de 10% for perdida, a banca cai para 90% — muito mais difícil de recuperar.

**Implementação:** Após calcular Kelly fracionado, aplicar min(stake_calculado, banca × 0.02).

---

### 6.2 Por Jogo

**Limite:** Máximo 4% da banca total no mesmo jogo (soma de todos os mercados).

**Justificativa:** Apostas no mesmo jogo são correlacionadas. Se apostamos em Moneyline e Spread do mesmo jogo, e o time perde, ambas as apostas perdem. Limitar a 4% evita concentração excessiva em um único evento.

**Implementação:** Antes de cada aposta, verificar exposição atual no jogo. Se exposição + nova aposta > 4%, rejeitar ou reduzir stake.

---

### 6.3 Por Dia

**Limite:** Máximo 12% da banca total em apostas num único dia.

**Justificativa:** Apostar muito num dia concentra risco temporalmente. Se todos os sinais do dia falharem (por exemplo, devido a problema sistêmico não detetado), o dano é limitado. 12% permite diversificação razoável (6-8 apostas típicas) sem exposição excessiva.

**Implementação:** Contador diário de stakes. Se stake acumulado > 12%, rejeitar novos sinais até o dia seguinte.

---

### 6.4 Por Mercado

**Limite:** Máximo 6% da banca num tipo específico de mercado (ex: todos os Moneylines).

**Justificação:** Diferentes mercados podem ter correlações não óbvias. Limitar exposição por tipo de mercado adiciona outra camada de diversificação.

**Implementação:** Contador por tipo de mercado. Se exposição em Moneyline > 6%, rejeitar novos sinais de Moneyline até exposição reduzir.

---

## 7. AJUSTE DINÂMICO DE KELLY

### 7.1 Ajuste por Drawdown

Quando ocorre drawdown significativo, o fator de Kelly deve ser reduzido automaticamente para proteger a banca:

- Drawdown 0-10%: Kelly normal (meio Kelly)
- Drawdown 10-15%: Kelly × 0.75
- Drawdown > 15%: Kelly × 0.5

Esta redução dinâmica é implementada automaticamente pelo sistema de gestão de drawdown e não pode ser sobreposta manualmente.

### 7.2 Ajuste por Confiança do Modelo

Se a confiança do modelo é baixa (por exemplo, PSI de features alto, calibração pobre), o fator de Kelly pode ser reduzido:

- Confiança alta (calibração excelente, PSI < 0.1): Kelly normal
- Confiança moderada (calibração aceitável, PSI 0.1-0.2): Kelly × 0.75
- Confiança baixa (calibração pobre, PSI > 0.2): Kelly × 0.5

Isto permite o sistema ser mais conservador quando a qualidade das predições é questionável.

---

## 8. PSICOLOGIA DO SIZING

### 8.1 A Tentação de Aumentar Stakes

Durante winning streaks, há uma forte tentação psicológica de aumentar os stakes beyond do que Kelly sugere. "Estou num roll, vou aumentar para capitalizar." Esta é uma armadilha perigosa. Winning streaks são estatisticamente esperadas e não indicam que o modelo ficou "melhor". Aumentar stakes durante winning streaks é garantir que a próxima losing streak será muito mais dolorosa.

Kelly fracionado ajuda a contrariar este impulso porque mesmo durante winning streaks, o sistema mantém o mesmo fator de fracionamento. O crescimento vem do edge, não de aumentar a agressividade.

### 8.2 A Tentação de Reduzir Stakes

Durante losing streaks, há a tentação oposta: reduzir stakes drasticamente ou parar completamente. "O modelo está quebrado, vou reduzir para minimizar danos." Se o edge ainda existe (CLV positivo), reduzir stakes abaixo do Kelly fracionado recomendado é sub-ótimo. O sistema está desenhado para lidar com losing streaks através de drawdown control, não através de redução arbitrária de stakes.

A exceção é quando o circuit breaker de drawdown ativa (DD > 15%) — neste caso, a redução de stakes é automática e justificada, não emocional.

---

## 9. BACKLOG TÉCNICO

- [ ] Implementar cálculo de Kelly com ajuste dinâmico de drawdown
- [ ] Implementar ajuste de Kelly por confiança do modelo
- [ ] Criar dashboard de exposição em tempo real
- [ ] Implementar alerta de aproximação a limites de exposição
- [ ] Adicionar validação de hard caps antes de cada aposta
- [ ] Implementar logging de todos os cálculos de stake para audit
- [ ] Criar relatórios mensais de análise de sizing vs performance

---

## 10. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]] ← Secção mãe
- [[08_Risk_Management/DRAWDOWN_CONTROL]] → Ajuste de Kelly por drawdown
- [[08_Risk_Management/BANKROLL_SURVIVAL]] → Análise de sobrevivência
- [[08_Risk_Management/EXPOSURE_LIMITS]] → Limites de exposição detalhados
