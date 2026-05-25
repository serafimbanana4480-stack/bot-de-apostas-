# MULTIPLE_TESTING_CORRECTION — Problema de Múltiplas Comparações

**ID:** `BT-003` | **Fase:** #phase/2 | **Owner:** Quant Research Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar o problema de múltiplas comparações em backtesting e fornecer métodos estatísticos para corrigir os p-values, evitando falsos positivos. Quando testamos múltiplas estratégias, features ou hiperparâmetros, a probabilidade de encontrar pelo menos um "significativo" por sorte aumenta dramaticamente — este documento explica como controlar esse risco.

---

## 2. DEFINIÇÃO E IMPORTÂNCIA

### 2.1 O Problema de Múltiplas Comparações

**Definição:** Quando realizamos múltiplos testes estatísticos simultaneamente, a probabilidade de cometer pelo menos um erro do Tipo I (falso positivo) aumenta com o número de testes.

**Exemplo Intuitivo:**
- Se testamos 1 estratégia com α = 0.05, probabilidade de falso positivo = 5%
- Se testamos 20 estratégias independentes com α = 0.05:
  - Probabilidade de NENHUM falso positivo = (1 - 0.05)^20 = 0.358
  - Probabilidade de PELO MENOS 1 falso positivo = 1 - 0.358 = **64.2%**

**Conclusão:** Com 20 testes, é mais provável encontrar pelo menos um falso positivo que não encontrar nenhum verdadeiro positivo!

### 2.2 Por Que É Crítico em Backtesting?

Em desenvolvimento de estratégias de apostas, é comum:

- Testar dezenas de features diferentes
- Experimentar múltiplos modelos (XGBoost, LightGBM, Neural Networks)
- Tunar dezenas de hiperparâmetros
- Testar diferentes janelas temporais
- Experimentar diferentes combinações de filtros

Cada uma destas variações é um "teste estatístico" independente. Sem correção, quase garantidamente encontraremos algo "significativo" por sorte pura.

**Custo de Falsos Positivos:**
- Implementar infraestrutura para estratégia sem edge
- Perder capital real em apostas
- Tempo desperdiçado em desenvolvimento
- Dano reputacional em serviço comercial

---

## 3. CONCEITOS FUNDAMENTAIS

### 3.1 Erro do Tipo I (Falso Positivo)

**Definição:** Rejeitar a hipótese nula quando ela é verdadeira.

**Em Backtesting:** Concluir que uma estratégia tem edge quando na realidade não tem.

**Taxa de Erro (α):** Probabilidade de cometer erro Tipo I em um único teste (tipicamente 0.05 ou 5%).

### 3.2 Family-Wise Error Rate (FWER)

**Definição:** Probabilidade de cometer PELO MENOS UM erro Tipo I em uma família de testes.

**Fórmula:**
```
FWER = 1 - (1 - α)^m
```
Onde:
- α = taxa de erro por teste
- m = número de testes

**Exemplo:**
- α = 0.05, m = 20
- FWER = 1 - (1 - 0.05)^20 = 1 - 0.358 = 0.642 (64.2%)

**Objetivo:** Controlar FWER a um nível aceitável (tipicamente 0.05 ou 0.10).

### 3.3 False Discovery Rate (FDR)

**Definição:** Proporção esperada de falsos positivos entre todas as descobertas (rejeições).

**Diferença vs FWER:**
- **FWER:** Controla probabilidade de QUALQUER falso positivo
- **FDR:** Controla PROPORÇÃO de falsos positivos

**Exemplo:**
- Se rejeitamos 10 hipóteses e FDR = 0.10:
  - Esperamos que 1 seja falso positivo
  - Esperamos que 9 sejam verdadeiros positivos

**Vantagem:** FDR é menos conservador que FWER, permitindo mais descobertas com controle de qualidade.

### 3.4 p-value

**Definição:** Probabilidade de observar um resultado tão extremo ou mais extremo assumindo que a hipótese nula é verdadeira.

**Interpretação:**
- p-value < α: Rejeitamos hipótese nula (resultado "significativo")
- p-value ≥ α: Não rejeitamos hipótese nula (resultado "não significativo")

**Importante:** p-value NÃO é a probabilidade de a hipótese nula ser verdadeira!

---

## 4. MÉTODOS DE CORREÇÃO

### 4.1 Bonferroni Correction

**Conceito:** Dividir o nível de significância α pelo número de testes m.

**Fórmula:**
```
α_corrected = α / m
p_corrected = p_original × m
```

**Exemplo:**
- α = 0.05, m = 20 testes
- α_corrected = 0.05 / 20 = 0.0025
- Só rejeitamos se p_original < 0.0025

**Vantagens:**
- Simples de implementar
- Controla FWER estritamente
- Garante que FWER ≤ α

**Desvantagens:**
- Muito conservador (especialmente com muitos testes)
- Baixo poder estatístico (muitos falsos negativos)
- Pode perder descobertas genuínas

**Quando Usar:**
- Número pequeno de testes (m < 10)
- Quando custo de falso positivo é muito alto
- Quando precisamos de controle estrito de FWER

**Exemplo Prático:**
```
Testamos 10 features, cada uma com p-value:
Feature 1: p = 0.001 ✓
Feature 2: p = 0.003 ✓
Feature 3: p = 0.010 ✗
Feature 4: p = 0.025 ✗
Feature 5: p = 0.040 ✗
...

Bonferroni correction (α = 0.05, m = 10):
α_corrected = 0.05 / 10 = 0.005

Resultado: Apenas Features 1 e 2 são significativas
```

### 4.2 Holm-Bonferroni (Step-Down)

**Conceito:** Versão menos conservadora de Bonferroni que ordena os p-values.

**Algoritmo:**
1. Ordenar p-values: p(1) ≤ p(2) ≤ ... ≤ p(m)
2. Para cada p(i), calcular α_i = α / (m - i + 1)
3. Rejeitar enquanto p(i) < α_i
4. Parar no primeiro p(i) ≥ α_i

**Vantagens:**
- Menos conservador que Bonferroni
- Ainda controla FWER
- Mais poder estatístico

**Desvantagens:**
- Ainda relativamente conservador
- Requer ordenação de p-values

**Exemplo Prático:**
```
Testamos 5 features com p-values ordenados:
p(1) = 0.001
p(2) = 0.008
p(3) = 0.015
p(4) = 0.025
p(5) = 0.040

α = 0.05, m = 5

i=1: α_1 = 0.05 / 5 = 0.010, p(1)=0.001 < 0.010 ✓ Rejeitar
i=2: α_2 = 0.05 / 4 = 0.0125, p(2)=0.008 < 0.0125 ✓ Rejeitar
i=3: α_3 = 0.05 / 3 = 0.0167, p(3)=0.015 < 0.0167 ✓ Rejeitar
i=4: α_4 = 0.05 / 2 = 0.025, p(4)=0.025 = 0.025 ✗ Parar

Resultado: Features 1, 2, 3 são significativas
(Bonferroni teria rejeitado apenas Feature 1)
```

### 4.3 Benjamini-Hochberg (BH Procedure)

**Conceito:** Controla FDR em vez de FWER, permitindo mais descobertas.

**Algoritmo:**
1. Ordenar p-values: p(1) ≤ p(2) ≤ ... ≤ p(m)
2. Para cada p(i), calcular threshold: (i / m) × α
3. Encontrar maior k tal que p(k) ≤ (k / m) × α
4. Rejeitar todas as hipóteses 1, 2, ..., k

**Vantagens:**
- Muito mais poderoso que Bonferroni
- Controla FDR (proporção de falsos positivos)
- Balance entre descobertas e qualidade
- Padrão na literatura científica moderna

**Desvantagens:**
- Não controla FWER (pode haver falsos positivos)
- Requer independência ou dependência positiva entre testes

**Quando Usar:**
- Grande número de testes (m > 10)
- Exploratory analysis (procurando descobertas)
- Quando custo de falso negativo é alto
- Quando FDR é aceitável em vez de FWER

**Exemplo Prático:**
```
Testamos 10 features com p-values ordenados:
p(1) = 0.001
p(2) = 0.003
p(3) = 0.008
p(4) = 0.015
p(5) = 0.020
p(6) = 0.025
p(7) = 0.030
p(8) = 0.040
p(9) = 0.050
p(10) = 0.070

α = 0.05, m = 10, FDR = 0.05

Calcular thresholds (i/m × α):
i=1: 0.1 × 0.05 = 0.005, p(1)=0.001 < 0.005 ✓
i=2: 0.2 × 0.05 = 0.010, p(2)=0.003 < 0.010 ✓
i=3: 0.3 × 0.05 = 0.015, p(3)=0.008 < 0.015 ✓
i=4: 0.4 × 0.05 = 0.020, p(4)=0.015 < 0.020 ✓
i=5: 0.5 × 0.05 = 0.025, p(5)=0.020 < 0.025 ✓
i=6: 0.6 × 0.05 = 0.030, p(6)=0.025 < 0.030 ✓
i=7: 0.7 × 0.05 = 0.035, p(7)=0.030 < 0.035 ✓
i=8: 0.8 × 0.05 = 0.040, p(8)=0.040 = 0.040 ✓
i=9: 0.9 × 0.05 = 0.045, p(9)=0.050 > 0.045 ✗ Parar

Resultado: Features 1-8 são significativas
(Bonferroni teria rejeitado apenas Features 1-2)
```

### 4.4 Benjamini-Yekutieli (BY Procedure)

**Conceito:** Versão mais conservadora de BH que funciona com dependência arbitrária entre testes.

**Fórmula:**
```
Threshold = (i / m) × (α / H(m))
```
Onde H(m) = Σ(1/j) para j=1 até m (número harmónico)

**Vantagens:**
- Funciona com qualquer estrutura de dependência
- Ainda controla FDR
- Mais robusto que BH

**Desvantagens:**
- Mais conservador que BH
- Menos poder estatístico

**Quando Usar:**
- Quando testes não são independentes
- Quando há dependência negativa entre testes
- Quando BH é muito liberal para o contexto

---

## 5. APLICAÇÃO EM BACKTESTING

### 5.1 Cenário 1: Seleção de Features

**Problema:** Testamos 50 features para ver quais têm poder preditivo.

**Abordagem:**
1. Calcular p-value para cada feature (ex: via teste de importância)
2. Aplicar Benjamini-Hochberg com FDR = 0.10
3. Selecionar features com p-value < threshold BH

**Justificativa:**
- m = 50 (grande número de testes)
- Exploratory analysis (procurando features úteis)
- FDR = 0.10 é aceitável (esperamos 10% de falsos positivos)
- BH é mais poderoso que Bonferroni

**Exemplo:**
```
50 features testadas
BH com FDR = 0.10
Resultado: 12 features significativas
Esperamos: ~1.2 falsos positivos entre as 12
```

### 5.2 Cenário 2: Comparação de Modelos

**Problema:** Comparamos 5 modelos diferentes (XGBoost, LightGBM, Random Forest, SVM, Neural Network).

**Abordagem:**
1. Calcular p-value para cada modelo vs baseline
2. Aplicar Holm-Bonferroni com α = 0.05
3. Selecionar modelos com p-value < threshold Holm

**Justificativa:**
- m = 5 (número pequeno de testes)
- Comparação confirmatória (validando modelos)
- Custo de falso positivo é alto (implementar modelo ruim)
- Holm é menos conservador que Bonferroni mas ainda controla FWER

### 5.3 Cenário 3: Tuning de Hiperparâmetros

**Problema:** Testamos 100 combinações de hiperparâmetros para XGBoost.

**Abordagem:**
1. Calcular performance para cada combinação
2. Aplicar Benjamini-Hochberg com FDR = 0.15
3. Selecionar top combinações com p-value < threshold BH

**Justificativa:**
- m = 100 (muito grande)
- Exploratory (procurando boas combinações)
- FDR = 0.15 é aceitável no tuning
- BH é o único método prático com m tão grande

**Nota:** Em prática, tuning de hiperparâmetros é melhor feito via validação cruzada com held-out set, não via testes estatísticos.

### 5.4 Cenário 4: White's Reality Check com Múltiplas Estratégias

**Problema:** Testamos 20 estratégias diferentes via White's Reality Check.

**Abordagem:**
1. Calcular p-value WRC para cada estratégia
2. Aplicar Benjamini-Hochberg com FDR = 0.10
3. Selecionar estratégias com p-value < threshold BH

**Justificativa:**
- m = 20 (número moderado)
- Exploratory (procurando estratégias viáveis)
- FDR = 0.10 é aceitável
- BH é apropriado para múltiplas estratégias

---

## 6. BOAS PRÁTICAS

### 6.1 Quando Usar Cada Método

| Método | Número de Testes | Controle | Conservadorismo | Uso Recomendado |
|--------|------------------|----------|-----------------|-----------------|
| **Bonferroni** | Pequeno (m < 10) | FWER | Muito alto | Validação crítica |
| **Holm** | Pequeno (m < 20) | FWER | Alto | Comparação de modelos |
| **BH** | Grande (m > 10) | FDR | Moderado | Seleção de features |
| **BY** | Qualquer | FDR | Alto | Dependência desconhecida |

### 6.2 Escolha do Nível de Significância

**FWER (Bonferroni, Holm):**
- α = 0.01: Muito conservador, custo alto de falso positivo
- α = 0.05: Padrão, balanceado
- α = 0.10: Menos conservador, aceitável em alguns contextos

**FDR (BH, BY):**
- FDR = 0.05: Muito conservador, similar a FWER
- FDR = 0.10: Padrão em literatura científica
- FDR = 0.15-0.20: Aceitável em exploratory analysis
- FDR = 0.25-0.30: Muito liberal, usar com cautela

### 6.3 Planeamento de Testes

**Pré-registro:**
- Definir número de testes ANTES de executar
- Definir método de correção ANTES de ver resultados
- Evitar "p-hacking" (adicionar testes até encontrar significância)

**Hierarquia de Testes:**
- Testes primários (confirmatórios): usar métodos mais conservadores
- Testes secundários (exploratórios): usar métodos mais liberais
- Documentar claramente a hierarquia

### 6.4 Interpretação de Resultados

**Com Correção:**
- Resultado significativo: Evidência mais forte de edge real
- Resultado não significativo: Não necessariamente sem edge, pode ser falta de poder

**Sem Correção:**
- Resultado significativo: Pode ser falso positivo
- Resultado não significativo: Mais confiável

**Regra de Ouro:**
> "Se não é significativo com correção, não é significativo. Se é significativo sem correção, verifique se é significativo com correção."

---

## 7. EXEMPLOS PRÁTICOS

### 7.1 Exemplo Completo: Seleção de Features

**Cenário:** Temos 30 features potenciais para um modelo de apostas NBA.

**Passo 1: Calcular Importância**
```
Feature 1: importance = 0.15, p-value = 0.001
Feature 2: importance = 0.12, p-value = 0.003
Feature 3: importance = 0.10, p-value = 0.008
Feature 4: importance = 0.08, p-value = 0.015
Feature 5: importance = 0.07, p-value = 0.020
Feature 6: importance = 0.06, p-value = 0.025
Feature 7: importance = 0.05, p-value = 0.030
Feature 8: importance = 0.04, p-value = 0.040
Feature 9: importance = 0.03, p-value = 0.050
Feature 10: importance = 0.02, p-value = 0.070
Feature 11-30: importance < 0.02, p-value > 0.10
```

**Passo 2: Aplicar Bonferroni**
```
α = 0.05, m = 30
α_corrected = 0.05 / 30 = 0.00167

Significativas: Feature 1 (p=0.001)
```

**Passo 3: Aplicar Holm-Bonferroni**
```
α = 0.05, m = 30

i=1: α_1 = 0.05/30 = 0.00167, p=0.001 < 0.00167 ✓
i=2: α_2 = 0.05/29 = 0.00172, p=0.003 > 0.00172 ✗ Parar

Significativas: Feature 1
```

**Passo 4: Aplicar Benjamini-Hochberg**
```
α = 0.05, m = 30, FDR = 0.10

i=1: threshold = 0.033, p=0.001 < 0.033 ✓
i=2: threshold = 0.067, p=0.003 < 0.067 ✓
i=3: threshold = 0.100, p=0.008 < 0.100 ✓
i=4: threshold = 0.133, p=0.015 < 0.133 ✓
i=5: threshold = 0.167, p=0.020 < 0.167 ✓
i=6: threshold = 0.200, p=0.025 < 0.200 ✓
i=7: threshold = 0.233, p=0.030 < 0.233 ✓
i=8: threshold = 0.267, p=0.040 < 0.267 ✓
i=9: threshold = 0.300, p=0.050 < 0.300 ✓
i=10: threshold = 0.333, p=0.070 < 0.333 ✓
i=11: threshold = 0.367, p=0.120 > 0.367 ✗ Parar

Significativas: Features 1-10
Esperamos ~1 falso positivo entre as 10
```

**Decisão:**
- Se for validation crítica: usar Features 1 apenas (Bonferroni)
- Se for exploratory: usar Features 1-10 (BH)
- Se for middle ground: usar Features 1-5 (BH com FDR=0.05)

### 7.2 Exemplo: Comparação de Modelos

**Cenário:** Comparamos 4 modelos vs baseline.

```
Modelo A: p-value = 0.003
Modelo B: p-value = 0.015
Modelo C: p-value = 0.025
Modelo D: p-value = 0.040
```

**Bonferroni (α = 0.05, m = 4):**
```
α_corrected = 0.05 / 4 = 0.0125
Significativas: Modelo A apenas
```

**Holm-Bonferroni (α = 0.05, m = 4):**
```
i=1: α_1 = 0.05/4 = 0.0125, p=0.003 < 0.0125 ✓
i=2: α_2 = 0.05/3 = 0.0167, p=0.015 < 0.0167 ✓
i=3: α_3 = 0.05/2 = 0.0250, p=0.025 = 0.0250 ✓
i=4: α_4 = 0.05/1 = 0.0500, p=0.040 < 0.0500 ✓

Significativas: Modelos A, B, C, D
```

**Decisão:** Usar Holm-Bonferroni (todos os 4 modelos são significativos)

---

## 8. REFERÊNCIAS E BOAS PRÁTICAS

### 8.1 Literatura Recomendada

- **"Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing"** — Benjamini & Hochberg (1995)
- **"The Control of the False Discovery Rate in Multiple Testing Under Dependency"** — Benjamini & Yekutieli (2001)
- **"Multiple Comparisons and Multiple Tests Using SAS"** — Westfall et al. (2011)
- **"Multiple Hypothesis Testing in Exploratory Research"** — Bender & Lange (2001)

### 8.2 Ferramentas Úteis

- **Statsmodels:** multipletests (implementa Bonferroni, BH, BY, Holm)
- **R:** p.adjust (função similar)
- **Python:** scipy.stats (implementações básicas)
- **Custom:** Implementações específicas para contextos de backtesting

### 8.3 Regras de Ouro

1. **Sempre aplicar correção quando m > 1:** Nunca assumir que um teste isolado é válido
2. **Escolher método apropriado ao contexto:** FWER para validação crítica, FDR para exploração
3. **Pré-registrar testes:** Definir método antes de ver resultados
4. **Documentar tudo:** Número de testes, método usado, parâmetros
5. **Ser conservador:** É melhor perder uma descoberta que aceitar um falso positivo

---

## 9. LINKS CRUZADOS

- [[06_Backtesting/INDEX]] ← Secção mãe
- [[06_Backtesting/OVERFITTING_TESTS]] → Testes complementares de robustez
- [[06_Backtesting/LEAKAGE_TEMPORAL]] → Detecção de leakage
- [[05_Machine_Learning/INDEX]] → Feature engineering e seleção
- [[03_Quant_Research/INDEX]] → Fundamentos estatísticos

---

## 10. GLOSSÁRIO

- **Multiple testing problem:** Aumento da probabilidade de falsos positivos com múltiplos testes
- **Family-Wise Error Rate (FWER):** Probabilidade de pelo menos um falso positivo
- **False Discovery Rate (FDR):** Proporção esperada de falsos positivos entre descobertas
- **Bonferroni correction:** Método conservador que divide α pelo número de testes
- **Holm-Bonferroni:** Versão step-down menos conservadora de Bonferroni
- **Benjamini-Hochberg (BH):** Procedimento que controla FDR, mais poderoso
- **Benjamini-Yekutieli (BY):** Versão de BH para dependência arbitrária
- **p-value:** Probabilidade de resultado extremo assumindo hipótese nula
- **α (alpha):** Nível de significância, taxa de erro Tipo I aceitável
- **p-hacking:** Prática de adicionar testes até encontrar significância