# ODDS_NORMALIZACAO — Normalização de Odds e Remoção de Overround

**ID:** `VD-003` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

As odds oferecidas pelos bookmakers não refletem probabilidades verdadeiras — elas incluem uma margem de lucro conhecida como "overround" ou "vig". O objetivo da normalização de odds é remover esta margem e converter odds de mercado em probabilidades imparciais (fair probabilities) que possam ser comparadas com as previsões do modelo.

Sem normalização, estaríamos comparando probabilidades de modelo (imparciais) com odds de mercado (viciadas), levando a cálculos de edge incorretos e decisões de apostas subótimas.

---

## 2. CONCEITO DE OVERROUND

### 2.1 Definição

Overround é a margem que os bookmakers adicionam às odds para garantir lucro independentemente do resultado. Num mercado perfeitamente eficiente com probabilidades verdadeiras, a soma das probabilidades seria 1.0 (100%). Com overround, a soma é > 1.0.

### 2.2 Exemplo Prático

Num jogo de basquete com duas equipas:

```
Celtics: Odd 1.85 → Probabilidade implícita = 1/1.85 = 0.5405 (54.05%)
Lakers:  Odd 2.10 → Probabilidade implícita = 1/2.10 = 0.4762 (47.62%)

Soma = 0.5405 + 0.4762 = 1.0167 (101.67%)
Overround = 1.67%
```

Este 1.67% é o lucro garantido do bookmaker, independentemente do resultado.

### 2.3 Impacto no Edge

Se não removermos o overround:

```
Probabilidade modelo Celtics = 0.55 (55%)
Edge não normalizado = (0.55 × 1.85) - 1 = 0.0175 (1.75%)

Mas a probabilidade real do mercado é 0.5405/1.0167 = 0.5317 (53.17%)
Edge verdadeiro = (0.55 / 0.5317) - 1 = 0.0344 (3.44%)
```

**Conclusão:** Sem normalização, subestimamos o edge em quase 50%!

---

## 3. MÉTODOS DE REMOÇÃO DE OVERROUND

### 3.1 Normalização Multiplicativa (Padrão)

A normalização multiplicativa é o método mais simples e amplamente utilizado. Cada probabilidade implícita é dividida pela soma total.

**Fórmula:**
```
P_fair(i) = P_implícita(i) / Σ(P_implícita)
```

**Exemplo:**
```
P_fair(Celtics) = 0.5405 / 1.0167 = 0.5317 (53.17%)
P_fair(Lakers)  = 0.4762 / 1.0167 = 0.4683 (46.83%)

Soma = 1.0 (100%) ✓
```

**Vantagens:**
- Simples de implementar
- Mantém a ordem relativa das probabilidades
- Funciona bem para mercados com overround uniforme

**Limitações:**
- Assume que o overround é distribuído uniformemente (nem sempre verdade)
- Não considera que bookmakers podem aplicar overround diferenciado

### 3.2 Normalização Aditiva

A normalização aditiva subtrai uma quantia igual de cada probabilidade para que a soma seja 1.0.

**Fórmula:**
```
Overround_por_saida = (ΣP - 1) / n
P_fair(i) = P_implícita(i) - Overround_por_saida
```

**Exemplo:**
```
Overround_por_saida = (1.0167 - 1) / 2 = 0.00835
P_fair(Celtics) = 0.5405 - 0.00835 = 0.53215 (53.22%)
P_fair(Lakers)  = 0.4762 - 0.00835 = 0.46785 (46.78%)
```

**Vantagens:**
- Mais intuitiva (subtrai a mesma quantia de cada resultado)
- Funciona bem quando o overround é uniforme

**Limitações:**
- Pode resultar em probabilidades negativas em extremos
- Menos usada na prática

### 3.3 Normalização por Poder (Power Normalization)

Este método eleva as probabilidades a um poder e renormaliza, permitindo ajustar a distribuição do overround.

**Fórmula:**
```
P_power(i) = P_implícita(i)^α
P_fair(i) = P_power(i) / ΣP_power
```

O parâmetro α é tipicamente < 1 e é otimizado para maximizar a calibração.

**Vantagens:**
- Mais flexível — pode modelar distribuições de overround não uniformes
- Pode capturar que bookmakers aplicam mais overround a favoritos ou underdogs

**Limitações:**
- Requer otimização do parâmetro α
- Mais complexa de implementar
- Risco de overfitting se α não for validado

---

## 4. FAIR ODDS

### 4.1 Conceito

Fair odds são as odds que seriam oferecidas num mercado sem overround, ou seja, odds que refletem as probabilidades verdadeiras.

**Fórmula:**
```
Odd_fair(i) = 1 / P_fair(i)
```

**Exemplo:**
```
Odd_fair(Celtics) = 1 / 0.5317 = 1.881
Odd_fair(Lakers)  = 1 / 0.4683 = 2.135
```

Comparando com as odds de mercado:
- Celtics: 1.85 → Fair: 1.881 (mercado está oferecendo odd pior que fair)
- Lakers: 2.10 → Fair: 2.135 (mercado está oferecendo odd pior que fair)

### 4.2 Uso no Cálculo de Edge

Com fair odds, o edge é calculado como:

```
Edge = (Prob_modelo × Odd_mercado) - 1
```

Ou equivalentemente:
```
Edge = (Prob_modelo / Prob_fair_mercado) - 1
```

Ambas as fórmulas são matematicamente equivalentes quando as probabilidades são normalizadas.

---

## 5. CONSIDERAÇÕES POR TIPO DE MERCADO

### 5.1 Mercados Binários (2 Resultados)

Exemplos: Moneyline, Over/Under

- **Normalização simples:** Divisão pela soma funciona perfeitamente
- **Overround tipicamente uniforme:** Bookmakers distribuem margem igualmente
- **Método recomendado:** Normalização multiplicativa

### 5.2 Mercados Multi-Resultado (3+ Resultados)

Exemplos: 1X2 (futebol), Resultado exato

- **Overround pode ser não uniforme:** Bookmakers muitas vezes aplicam mais margem a resultados improváveis
- **Normalização multiplicativa ainda funciona:** Mas pode subestimar edge em resultados longshot
- **Método recomendado:** Normalização multiplicativa com validação, ou power normalization se overround for muito não uniforme

### 5.3 Mercados de Handicap/Spread

Exemplos: Spread de pontos, Asian handicap

- **Complexidade adicional:** Múltiplas linhas de handicap com diferentes odds
- **Normalização por linha:** Cada linha é normalizada independentemente
- **Consideração de draw:** Em Asian handicap, o empate é possível (push), o que afeta a normalização

### 5.4 Mercados de Proposições (Player Props)

Exemplos: Pontos de um jogador, assists

- **Overround tipicamente alto:** Bookmakers aplicam margens maiores em props
- **Menos liquidez:** Normalização pode ser menos precisa
- **Método recomendado:** Normalização multiplicativa com ajuste conservador (assumir overround maior)

---

## 6. ODDS DE EXCHANGE vs BOOKMAKER

### 6.1 Diferenças Fundamentais

**Bookmaker (Pinnacle, Bet365, etc.):**
- Odds fixadas pelo bookmaker
- Overround explícito (margem de lucro)
- Liquidez limitada pelos limites do bookmaker

**Exchange (Betfair, Smarkets):**
- Odds determinadas pelo mercado (oferta e procura)
- Overround implícito na comissão (tipicamente 2-5%)
- Liquidez determinada por outros apostadores

### 6.2 Normalização em Exchanges

Em exchanges, a normalização é diferente porque:

1. **Comissão em vez de overround:** A "margem" é uma comissão sobre lucros
2. **Odds variam por lado:** Back odds e lay odds podem diferir
3. **Liquidez é dinâmica:** Volume disponível afeta odds executáveis

**Fórmula ajustada para comissão:**
```
Prob_back = 1 / Odd_back
Prob_lay = 1 - (1 / Odd_lay)

Após comissão (c):
Prob_back_ajustada = Prob_back × (1 - c)
Prob_lay_ajustada = Prob_lay × (1 - c)
```

### 6.3 Preferência por Exchanges

Preferimos odds de exchange (especialmente Betfair) porque:

- **Mais eficientes:** Odds refletem consenso de mercado, não opinião de bookmaker
- **Mais transparentes:** Volume disponível é visível em tempo real
- **Overround menor:** Comissão tipicamente menor que margem de bookmakers
- **Liquidez real:** Volume representa apostas reais, não limites artificiais

---

## 7. IMPLEMENTAÇÃO PRÁTICA

### 7.1 Pipeline de Normalização

```
1. Receber odds de múltiplas fontes (Pinnacle, Betfair, etc.)
2. Calcular probabilidades implícitas: P = 1/odd
3. Somar probabilidades: ΣP
4. Verificar overround: Se ΣP ≈ 1.0, odds já normalizadas
5. Aplicar normalização multiplicativa: P_fair = P / ΣP
6. Calcular fair odds: Odd_fair = 1 / P_fair
7. Validar: ΣP_fair deve ser 1.0 (dentro de tolerância numérica)
8. Usar P_fair no cálculo de edge
```

### 7.2 Tratamento de Erros

**Casos especiais:**

- **Odds = 1.0:** Probabilidade implícita = 1.0, indicando erro de dados → Rejeitar
- **Odds < 1.0:** Impossível em mercados legítimos → Rejeitar
- **ΣP < 0.95:** Overround negativo (arbitragem possível) → Investigar, pode ser erro
- **ΣP > 1.20:** Overround extremo → Provavelmente mercado de baixa qualidade → Rejeitar

### 7.3 Tolerâncias Numéricas

Devido a precisão de ponto flutuante:

- **Tolerância para ΣP = 1.0:** ±0.0001
- **Probabilidade mínima válida:** 0.001 (0.1%)
- **Probabilidade máxima válida:** 0.999 (99.9%)

---

## 8. VALIDAÇÃO DA NORMALIZAÇÃO

### 8.1 Testes de Calibração

Após normalização, validamos que as probabilidades são calibradas:

- **Brier score:** Mede a precisão das probabilidades
- **Calibration plot:** Probabilidade prevista vs frequência observada
- **Expected Value:** EV médio deve ser próximo de zero para apostas aleatórias

### 8.2 Backtest Comparativo

Comparamos performance com e sem normalização:

- **Sem normalização:** Edge médio, Sharpe, drawdown
- **Com normalização:** Edge médio, Sharpe, drawdown

Esperamos ver:
- Edge médio mais alto (correção da subestimação)
- Sharpe mais alto (melhor qualidade de sinais)
- Drawdown menor (redução de apostas de baixa qualidade)

---

## 9. OTIMIZAÇÃO CONTÍNUA

### 9.1 Monitorização de Overround

Monitorizamos o overround médio por:
- **Bookmaker:** Pinnacle tipicamente tem menor overround
- **Tipo de mercado:** Props têm overround maior
- **Hora do dia:** Overround pode variar com atividade
- **Proximidade do evento:** Overround tende a diminuir perto do evento

### 9.2 Ajuste de Método

Se a normalização multiplicativa não performar bem em certos mercados:

- **Investigar:** Overround é não uniforme?
- **Testar alternativas:** Power normalization, normalização aditiva
- **Validar:** Comparar performance em backtest
- **Implementar:** Só após validação rigorosa

---

## 10. BOAS PRÁTICAS

### 10.1 Sempre Normalizar

**Regra de ouro:** Nunca calcular edge sem normalização prévia. Comparar probabilidades de modelo com odds não normalizadas é como comparar maçãs com laranjas.

### 10.2 Documentar Método

Documentar claramente:
- Qual método de normalização é usado
- Por que foi escolhido
- Quais validações foram feitas
- Limitações conhecidas

### 10.3 Versionamento

Versionar o código de normalização:
- Mudanças no método devem ser versionadas
- Backtests devem ser refeitos após mudanças
- Performance deve ser comparada antes/depois

---

## 11. LINKS CRUZADOS

- [[07_Value_Detection/INDEX]] ← Seção mãe
- [[07_Value_Detection/MOTOR_EDGE]] → Como edge é calculado após normalização
- [[04_Data_Engineering/INDEX]] → Fontes de dados de odds
- [[06_Backtesting/INDEX]] → Validar impacto da normalização