# THRESHOLD_OPTIMIZATION — Otimização de Thresholds com Walk-Forward

**ID:** `VD-005` | **Fase:** #phase/2-3 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

A otimização de thresholds é o processo de encontrar os valores ideais para os parâmetros do motor de value (edge mínimo, probabilidade mínima/máxima, etc.) que maximizam a performance do sistema. Diferente de uma otimização estática, usamos validação walk-forward para garantir que os thresholds são robustos e não overfitted aos dados históricos.

O objetivo não é maximizar o retorno absoluto, mas sim encontrar o ponto ótimo no trade-off entre retorno, risco (Sharpe) e consistência (drawdown).

---

## 2. CONCEITO DE WALK-FORWARD

### 2.1 Definição

Walk-forward validation é uma técnica de validação que simula como o modelo performaria em produção. Ao contrário de uma simples divisão train/test, walk-forward usa janelas deslizantes de tempo para validar o modelo de forma mais realista.

### 2.2 Por que Walk-Forward e não Simple Split?

**Simple Split (Train/Test):**
- Divide dados em 70% train / 30% test
- Problema: O modelo pode overfit ao período de teste específico
- Não captura mudanças estruturais no mercado ao longo do tempo
- Não simula a realidade de produção (onde sempre estamos no "futuro")

**Walk-Forward:**
- Usa múltiplas janelas de treino e validação
- Cada validação usa dados estritamente futuros ao treino
- Captura performance em diferentes regimes de mercado
- Simula a realidade de atualização contínua do modelo

### 2.3 Arquitetura Walk-Forward

```
Dados: [Jan|Fev|Mar|Abr|Mai|Jun|Jul|Ago|Set|Out|Nov|Dez]

Window 1:
  Train: Jan-Mai (5 meses)
  Validate: Jun (1 mês)
  
Window 2:
  Train: Fev-Jun (5 meses)
  Validate: Jul (1 mês)
  
Window 3:
  Train: Mar-Jul (5 meses)
  Validate: Ago (1 mês)
  
...continua até cobrir todo o período
```

**Resultado:** Média de performance across all windows é a estimativa robusta de performance em produção.

---

## 3. PARÂMETROS OTIMIZADOS

### 3.1 Thresholds Primários

| Parâmetro | Valor Inicial | Range de Otimização | Step |
|-----------|---------------|---------------------|------|
| edge_minimo | 0.04 | [0.02, 0.08] | 0.005 |
| prob_minima | 0.15 | [0.10, 0.30] | 0.02 |
| prob_maxima | 0.85 | [0.70, 0.90] | 0.02 |
| prob_meta_min | 0.60 | [0.50, 0.70] | 0.02 |

### 3.2 Thresholds de Liquidez

| Parâmetro | Valor Inicial | Range de Otimização | Step |
|-----------|---------------|---------------------|------|
| liquidez_min_ratio | 1.5x | [1.0x, 3.0x] | 0.1x |
| volume_minimo_eur | 500 | [100, 2000] | 100 |

### 3.3 Thresholds de Regime

| Parâmetro | Valor Inicial | Range de Otimização | Step |
|-----------|---------------|---------------------|------|
| dias_minimos_historico | 30 | [10, 90] | 5 |
| sharpe_minimo_regime | 0.5 | [0.3, 1.0] | 0.1 |

---

## 4. FUNÇÃO OBJETIVO

### 4.1 Métricas de Otimização

Não otimizamos por uma única métrica — usamos uma função composta que balanceia múltiplos objetivos:

```
Score = w1 × Sharpe_Normalizado + w2 × Retorno_Normalizado 
      - w3 × Drawdown_Normalizado - w4 × Volatilidade_Normalizada
```

**Pesos típicos:**
- w1 (Sharpe) = 0.40
- w2 (Retorno) = 0.25
- w3 (Drawdown) = 0.25
- w4 (Volatilidade) = 0.10

### 4.2 Por que Sharpe como Métrica Principal?

Sharpe ratio é a métrica mais importante porque:

- **Normaliza pelo risco:** Retorno por unidade de risco
- **Comparável:** Permite comparar estratégias com diferentes volatilidades
- **Robusto:** Menos sensível a outliers que retorno absoluto
- **Padrão da indústria:** Usado universalmente em hedge funds

### 4.3 Métricas Secundárias

Monitorizamos também (mas não otimizamos diretamente):

- **Maximum Drawdown:** Não deve exceder 20% da banca
- **Win Rate:** Deve estar entre 45-55% (dependendo do edge médio)
- **Average Holding Period:** Apostas não devem ser muito longas
- **Turnover:** Número de apostas por dia (equilíbrio entre volume e qualidade)

---

## 5. PROCESSO DE OTIMIZAÇÃO

### 5.1 Preparação de Dados

**Requisitos de dados:**
- Mínimo de 2 anos de dados históricos
- Dados de odds em tempo real (não closing odds)
- Resultados reais (não estimados)
- Features completas para o período

**Limpeza de dados:**
- Remover outliers (odds erradas, jogos cancelados)
- Imputar missing values (se < 5% dos dados)
- Validar integridade (timestamps, IDs únicos)

### 5.2 Configuração de Walk-Forward

**Parâmetros da janela:**
- Tamanho da janela de treino: 6 meses
- Tamanho da janela de validação: 1 mês
- Step: 1 mês (janela desliza mês a mês)
- Mínimo de janelas: 12 (cobrir 1 ano mínimo)

**Justificativa:**
- 6 meses de treino: Suficiente para capturar padrões sazonais
- 1 mês de validação: Período representativo de condições de mercado
- Step de 1 mês: Balanceia detalhe e custo computacional

### 5.3 Algoritmo de Otimização

Usamos **Optuna** (framework de otimização hiperparamétrica) com:

- **Sampler:** TPE (Tree-structured Parzen Estimator) - eficiente para espaços de busca discretos
- **Pruner:** Median Pruner - para interromper trials não promissores cedo
- **Número de trials:** 100 por janela (1200 total)
- **Timeout:** 2 horas por janela (24 horas total)

**Pseudocódigo:**
```
Para cada janela walk-forward:
    Para cada trial (até 100):
        Gerar combinação de thresholds
        Aplicar thresholds aos dados de treino
        Calcular métricas de performance
        Calcular score composto
        Pruner decide se continua ou para
    Selecionar melhor threshold da janela
Aplicar thresholds médios across janelas
Validar em hold-out set (últimos 3 meses)
```

### 5.4 Validação Final

Após otimização walk-forward, validamos em um hold-out set:

- **Período:** Últimos 3 meses (não usados em nenhuma janela)
- **Thresholds:** Média dos thresholds ótimos de cada janela
- **Critério de aprovação:** Sharpe no hold-out ≥ 80% do Sharpe médio walk-forward

Se o hold-out falhar:
- Investigar overfitting
- Aumentar tamanho da janela de treino
- Reduzir complexidade do espaço de busca
- Repetir otimização

---

## 6. ANÁLISE DE SENSIBILIDADE

### 6.1 Heatmaps de Performance

Para cada par de thresholds, geramos heatmaps mostrando performance:

```
          prob_min
          0.10  0.15  0.20  0.25  0.30
edge 0.02  0.8   1.2   1.5   1.3   0.9
min  0.03  0.9   1.4   1.8   1.5   1.1
     0.04  1.0   1.6   2.1   1.7   1.2
     0.05  0.8   1.3   1.7   1.4   1.0
     0.06  0.6   1.0   1.3   1.1   0.8
     0.07  0.4   0.7   0.9   0.8   0.6
     0.08  0.2   0.4   0.5   0.4   0.3
```

Neste exemplo, edge=0.04, prob_min=0.20 é ótimo (Sharpe=2.1).

### 6.2 Superfícies de Resposta

Geramos superfícies 3D para visualizar trade-offs:

- Eixo X: edge_minimo
- Eixo Y: prob_meta_min
- Eixo Z: Sharpe

Isso ajuda a identificar "planaltos" de performance onde pequenas mudanças não afetam muito a performance (robustez).

### 6.3 Análise de Elbow

Para cada threshold, plotamos performance vs valor do threshold:

```
Sharpe
  |
2.1|           *
  |          *
2.0|         *
  |        *
1.9|       *
  |      *
1.8|_____*_________________
      0.02  0.04  0.06  edge_min
```

O "elbow" (ponto de inflexão) indica onde ganhos marginais diminuem — este é frequentemente o ponto ótimo de robustez.

---

## 7. GUARDRAILS E RESTRIÇÕES

### 7.1 Restrições de Negócio

Além da otimização matemática, impomos restrições de negócio:

- **Volume mínimo:** Pelo menos 2 sinais por dia (para manter atividade)
- **Volume máximo:** No máximo 10 sinais por dia (para manter qualidade)
- **Stake médio:** Entre 0.5% e 3% da banca por aposta
- **Exposição máxima:** Não mais que 15% da banca em jogos simultâneos

### 7.2 Restrições de Risco

- **Maximum Drawdown:** < 20% em qualquer janela de validação
- **Volatilidade:** < 30% anualizada
- **Correlação:** < 0.7 entre sinais simultâneos (diversificação)

### 7.3 Restrições Operacionais

- **Latência:** Thresholds não podem exigir cálculos > 5 segundos
- **Complexidade:** Não mais que 5 thresholds ativos simultaneamente
- **Interpretabilidade:** Thresholds devem ser explicáveis a stakeholders

---

## 8. FREQUÊNCIA DE REOTIMIZAÇÃO

### 8.1 Ciclo Mensal

Thresholds são reotimizados mensalmente:

- **Dia 1 do mês:** Inicia otimização walk-forward
- **Dia 2-3:** Otimização roda (24 horas)
- **Dia 4:** Validação em hold-out
- **Dia 5:** Aprovação humana e implementação
- **Dia 6:** Novos thresholds em produção

### 8.2 Por que Mensal e não Diário/Semanal?

**Muito frequente (diário):**
- Overfitting a ruído de curto prazo
- Custo computacional alto
- Instabilidade operacional (thresholds mudando constantemente)

**Muito infrequente (trimestral/anual):**
- Não adapta a mudanças de mercado
- Perde oportunidades de melhoria
- Risco de degradação de performance

**Mensal (ótimo):**
- Balanceia adaptação e estabilidade
- Captura mudanças sazonais
- Custo computacional gerenciável

### 8.3 Reotimização Emergencial

Reotimizamos imediatamente se:

- **Performance cai drasticamente:** Sharpe < 0.5 por 2 semanas consecutivas
- **Mudança estrutural:** Nova regra da liga, mudança no formato
- **Alerta de drift:** Detecção de data drift significativo

---

## 9. MONITORIZAÇÃO CONTÍNUA

### 9.1 Dashboard de Thresholds

Monitorizamos em tempo real:

- **Thresholds atuais:** Valores em produção
- **Thresholds ótimos:** Valores da última otimização
- **Gap:** Diferença entre atuais e ótimos
- **Performance atual:** Sharpe, retorno, drawdown
- **Performance esperada:** Baseado na última otimização

### 9.2 Alertas de Degradação

Alertas se:

- **Sharpe atual < 80% do esperado:** Possível problema
- **Sharpe atual < 60% do esperado:** Ação imediata necessária
- **Drawdown > 15%:** Investigar imediatamente
- **Volume de sinais < 50% do esperado:** Thresholds muito conservadores

### 9.3 Análise de Regime

Trackeamos performance por regime:

- **Por mês:** Performance varia sazonalmente?
- **Por dia da semana:** Padrões semanais?
- **Por tipo de mercado:** Alguns mercados performam melhor?

Se performance varia muito por regime, consideramos thresholds específicos por regime.

---

## 10. BOAS PRÁTICAS

### 10.1 Nunca Otimizar em Dados Futuros

**Regra de ouro:** A otimização só pode usar dados até o momento da "decisão". Nunca usar resultados futuros para otimizar thresholds passados.

Exemplo de erro:
- Otimizar thresholds para 2023 usando dados de 2024
- Isso é overfitting puro e resultará em performance desastrosa em produção

### 10.2 Versionamento de Thresholds

Cada versão de thresholds é:
- Versionada (v1.0, v1.1, etc.)
- Armazenada em banco de dados
- Rastreável (quem aprovou, quando, por que)
- Reversível (pode rollback para versão anterior)

### 10.3 Documentação de Decisões

Para cada otimização, documentamos:
- Dados usados (período, fonte)
- Configuração walk-forward (tamanho das janelas)
- Thresholds anteriores e novos
- Justificativa para mudanças
- Performance esperada vs observada

### 10.4 Validação Independente

A otimização é validada por:
- **Revisão por pares:** Outro quant engenheiro revisa
- **Paper trading:** Testado em ambiente de simulação por 30 dias
- **Aprovação final:** Head of Quant aprova antes de produção

---

## 11. LINKS CRUZADOS

- [[07_Value_Detection/INDEX]] ← Seção mãe
- [[06_Backtesting/INDEX]] → Framework de backtesting usado na otimização
- [[29_Experiment_Tracking/INDEX]] → Rastreamento de experimentos de otimização
- [[48_Data_Drift/INDEX]] → Detecção de drift que pode trigger reotimização