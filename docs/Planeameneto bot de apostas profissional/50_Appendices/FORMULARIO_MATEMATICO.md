# FORMULÁRIO MATEMÁTICO — Fórmulas Chave do Sistema

**ID:** `APP-002` | **Fase:** Todas | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. PROBABILIDADES E ODDS

### 1.1 Probabilidade Implícita

```
P_implícita = 1 / odd
```

**Exemplo:** Odd 2.0 → P = 1/2.0 = 0.5 (50%)

### 1.2 Overround (Margem da Casa)

```
Overround = (Σ P_implícita) - 1
```

**Exemplo:** Odds 1.9, 2.1 → P = 0.526 + 0.476 = 1.002 → Overround = 0.2%

### 1.3 Probabilidade Normalizada (Sem Overround)

```
P_normalizada = P_implícita / Σ P_implícita
```

---

## 2. EDGE E VALUE

### 2.1 Edge Bruto

```
edge = (P_modelo × odd_mercado) - 1
```

**Exemplo:** P_modelo = 0.55, odd = 1.9 → edge = (0.55 × 1.9) - 1 = 0.045 (4.5%)

### 2.2 Edge Ajustado à Liquidez

```
edge_ajustado = edge × min(1.0, volume / (stake × 3.0))
```

### 2.3 Edge Efetivo (com Meta-Modelo)

```
edge_efetivo = edge × P_meta × confidence_regime
```

---

## 3. KELLY CRITERION

### 3.1 Kelly Fracionado

```
f = K × (P × odd - 1) / (odd - 1)
stake = f × bankroll
```

Onde:
- K = fração de Kelly (ex: 0.5 para meio Kelly)
- P = probabilidade do modelo
- odd = odd do mercado

**Exemplo:** K=0.5, P=0.55, odd=1.9, bankroll=1000€
```
f = 0.5 × (0.55 × 1.9 - 1) / (1.9 - 1) = 0.5 × 0.045 / 0.9 = 0.025
stake = 0.025 × 1000 = 25€
```

### 3.2 Limites de Stake

```
stake_final = min(
    stake_kelly,
    0.02 × bankroll,        # Máximo 2% por aposta
    0.12 × bankroll - exposição_atual  # Máximo 12% por dia
)
```

---

## 4. CALIBRAÇÃO DE PROBABILIDADES

### 4.1 Brier Score

```
Brier = (1/N) × Σ (P_i - O_i)²
```

Onde:
- P_i = probabilidade prevista
- O_i = outcome real (1 ou 0)
- N = número de previsões

**Range:** [0, 1], menor é melhor

### 4.2 Expected Calibration Error (ECE)

```
ECE = Σ (n_k / N) × |P_avg_k - O_avg_k|
```

Onde:
- n_k = número de previsões no bin k
- N = total de previsões
- P_avg_k = probabilidade média no bin k
- O_avg_k = frequência observada no bin k

**Range:** [0, 1], menor é melhor

### 4.3 Calibração Isotónica por Regime

Dividir em 3 regimes baseados em P_modelo:
- Favorito: P ≥ 0.65
- Equilibrado: 0.35 < P < 0.65
- Underdog: P ≤ 0.35

Aplicar calibrador isotónico separado a cada regime.

---

## 5. MÉTRICAS DE PERFORMANCE

### 5.1 ROI (Return on Investment)

```
ROI = (Lucro / Investimento) × 100
```

### 5.2 ROI Simulado (com Custos)

```
ROI_sim = (Σ PnL - comissões - slippage) / Σ stakes × 100
```

### 5.3 Sharpe Ratio

```
Sharpe = ROI_médio / σ(ROI)
```

Onde σ(ROI) é o desvio padrão dos retornos.

**Interpretação:**
- Sharpe > 1.0: Excelente
- Sharpe > 0.5: Aceitável
- Sharpe < 0.3: Ruim

### 5.4 Calmar Ratio

```
Calmar = ROI_anual / Max_Drawdown
```

### 5.5 Drawdown

```
Drawdown = (Peak - Trough) / Peak
```

### 5.6 CLV (Closed Line Value)

```
CLV = (odd_aposta - odd_fecho) / odd_fecho
```

Ou em probabilidade:
```
CLV = P_fecho - P_aposta
```

**Exemplo:** Apostei a 2.0, fecho a 1.8
```
CLV = (2.0 - 1.8) / 1.8 = 0.111 (11.1%)
```

---

## 6. FEATURE ENGINEERING

### 6.1 Média Móvel Exponencial (EMA)

```
EMA_t = α × X_t + (1 - α) × EMA_{t-1}
```

Onde α = 2 / (n + 1), n = período

**Half-life:** Quando o peso cai para 50%
```
α = 1 - exp(-ln(2) / half_life)
```

### 6.2 Four Factors (NBA)

```
eFG% = (FG + 0.5 × 3P) / FGA
TOV% = TOV / (FGA + 0.44 × FTA + TOV)
ORB% = ORB / (ORB + DRB_oponente)
FT/FGA = FT / FGA
```

### 6.3 Net Rating

```
Net_Rating = Rating_Ofensivo - Rating_Defensivo
```

### 6.4 Pace

```
Pace = 48 × (Possessões / Minutos)
```

---

## 7. TESTES ESTATÍSTICOS

### 7.1 Teste ADF (Augmented Dickey-Fuller)

H₀: Série tem raiz unitária (não estacionária)
H₁: Série é estacionária

Rejeitar H₀ se p-value < 0.05

### 7.2 Teste KPSS

H₀: Série é estacionária
H₁: Série tem raiz unitária

Rejeitar H₀ se p-value < 0.05

### 7.3 Teste Kolmogorov-Smirnov (KS)

Compara duas distribuições (ex: treino vs teste)

```
D = max |F₁(x) - F₂(x)|
```

Rejeitar H₀ (distribuições iguais) se D > crítico

### 7.4 Population Stability Index (PSI)

```
PSI = Σ ((%_esperado - %_observado) × ln(%_esperado / %_observado))
```

**Interpretação:**
- PSI < 0.1: Sem drift
- 0.1 < PSI < 0.2: Drift leve
- PSI > 0.2: Drift severo

---

## 8. GESTÃO DE RISCO

### 8.1 Probabilidade de Ruína (RoR)

Para Kelly fracionado:
```
RoR ≈ ((1 - f × edge) / (1 + f × edge))^(bankroll / stake)
```

### 8.2 Valor Esperado (EV)

```
EV = P × lucro - (1 - P) × stake
```

**Exemplo:** P=0.55, stake=25€, odd=1.9
```
EV = 0.55 × 22.5 - 0.45 × 25 = 12.375 - 11.25 = 1.125€
```

---

## 9. XGBOOST

### 9.1 Função Objetivo (Binary:logistic)

```
L = Σ l(y_i, ŷ_i) + Σ Ω(f_k)
```

Onde:
- l = loss function (log loss)
- Ω = termo de regularização

### 9.2 Log Loss

```
LogLoss = -Σ [y_i × log(ŷ_i) + (1 - y_i) × log(1 - ŷ_i)]
```

### 9.3 Feature Importance (Gain)

```
Importância_j = Σ (ΔLoss ao usar feature j)
```

---

## 10. SIMULAÇÃO MONTE CARLO

### 10.1 Simulação de Resultados

```
Para i em 1 a N_simulações:
    Para cada aposta:
        resultado = Bernoulli(P_modelo)
        PnL = resultado × (odd - 1) - (1 - resultado)
        bankroll += PnL × stake
    Guardar bankroll_final_i
```

### 10.2 Distribuição de Drawdown

```
Drawdown_i = (max(bankroll[0:i]) - bankroll[i]) / max(bankroll[0:i])
```

Calcular percentis: p50, p95, p99 dos drawdowns

---

## LINKS CRUZADOS

- [[50_Appendices/INDEX]] ← Secção mãe
- [[GLOSSARIO]] → Definições de termos
- [[03_Quant_Research/INDEX]] → Fundamentos estatísticos