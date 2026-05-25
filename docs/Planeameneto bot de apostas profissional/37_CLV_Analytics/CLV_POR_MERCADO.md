# CLV por Mercado

**ID:** CLV-011 | **Fase:** #phase/4-15 | **Owner:** Principal Quant Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Análise do CLV (Closed Line Value) segmentado por tipo de mercado: Moneyline, Spread, Totals. A eficiência relativa dos mercados pode diferir significativamente.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Identificar eficiência relativa por mercado |
| **Métricas** | CLV médio, Brier Score, ROI por mercado |
| **Custo** | 0€ (análise) |

---

## 2. DEFINIÇÃO DE MERCADOS

### 2.1 Classificação

| Mercado | Definição | Exemplo |
|---------|-----------|---------|
| **Moneyline** | Vencedor do jogo | Lakers vs Wizards (Lakers 1.30) |
| **Spread** | Margem de vitória | Lakers -7.5 vs Wizards |
| **Totals** | Pontos totais | Over/Under 220.5 pontos |

**Regra:** Classificação baseada no tipo de aposta.

### 2.2 Distribuição Natural

```
Moneyline: ~40% do volume de apostas
Spread: ~35% do volume de apostas
Totals: ~25% do volume de apostas
```

---

## 3. PORQUE CLV DIFERE POR MERCADO

### 3.1 Moneyline

**Características:**
- Mais simples (binário)
- Mercado mais eficiente (mais volume)
- Menos espaço para edge
- Overround menor

**Desafios do Modelo:**
- Menos espaço para edge
- Mercado muito eficiente
- Calibração mais difícil

**Vantagens:**
- Mais simples de modelar
- Menos variáveis
- Liquidez maior

### 3.2 Spread

**Características:**
- Mais complexo (margem contínua)
- Mercado moderadamente eficiente
- Mais espaço para edge
- Overround moderado

**Vantagens do Modelo:**
- Mais espaço para edge
- Features de margem têm valor
- Calibração mais fácil

**Desafios:**
- Mais complexo de modelar
- Mais variáveis
- Push (empate no spread) possível

### 3.3 Totals

**Características:**
- Mais complexo (soma de pontuações)
- Mercado menos eficiente (menos volume)
- Mais espaço para edge
- Overround maior

**Vantagens do Modelo:**
- Mais espaço para edge
- Features de ritmo têm valor
- Calibração mais fácil

**Desafios:**
- Mais complexo de modelar
- Mais variáveis
- Dependência entre equipas

---

## 4. MÉTRICAS POR MERCADO

### 4.1 CLV Médio

```python
clv_por_mercado = df.groupby('mercado')['clv'].agg(['mean', 'std', 'count'])

# Thresholds
if clv_por_mercado.loc['moneyline', 'mean'] > 0.01:
    status_ml = "EXCELLENT"
elif clv_por_mercado.loc['moneyline', 'mean'] > 0.005:
    status_ml = "ACEITÁVEL"
else:
    status_ml = "FRACO"
```

### 4.2 Brier Score por Mercado

```python
brier_por_mercado = df.groupby('mercado').apply(
    lambda x: brier_score(x['prob'], x['outcome'])
)

# Thresholds
if brier_por_mercado['moneyline'] < 0.20:
    status_ml = "BEM CALIBRADO"
elif brier_por_mercado['moneyline'] < 0.25:
    status_ml = "ACEITÁVEL"
else:
    status_ml = "MAL CALIBRADO"
```

### 4.3 ROI por Mercado

```python
roi_por_mercado = df.groupby('mercado')['pnl'].sum() / df.groupby('mercado')['stake'].sum()

# Thresholds
if roi_por_mercado['moneyline'] > 0.03:
    status_ml = "EXCELLENT"
elif roi_por_mercado['moneyline'] > 0:
    status_ml = "LUCRATIVO"
else:
    status_ml = "PREJUÍZO"
```

---

## 5. ESTRATÉGIA POR MERCADO

### 5.1 Moneyline

**Recomendação:**
- Apostar se CLV > 1.5% (mais conservador)
- Limitar stake a 50% do Kelly recomendado
- Priorizar liquidez
- Verificar odds múltiplas

**Justificação:**
- Mercado muito eficiente
- Menos espaço para edge
- Risco de slippage

### 5.2 Spread

**Recomendação:**
- Apostar se CLV > 1.0% (moderado)
- Usar Kelly completo
- Priorizar features de margem
- Monitorizar movimentos de linha

**Justificação:**
- Mais espaço para edge
- Features têm mais valor
- Calibração mais fácil

### 5.3 Totals

**Recomendação:**
- Apostar se CLV > 1.2% (moderado)
- Usar Kelly completo
- Priorizar features de ritmo
- Verificar dependências

**Justificação:**
- Mais espaço para edge
- Features têm mais valor
- Calibração mais fácil

---

## 6. MONITORIZAÇÃO

### 6.1 Dashboard por Mercado

```
┌─────────────────────────────────────────────────────────────┐
│ CLV POR MERCADO - [DATA]                                  │
├─────────────────────────────────────────────────────────────┤
│ Moneyline: CLV 0.8% (target: >1.5%) ⚠️                     │
│ Spread: CLV 1.3% (target: >1.0%) ✅                       │
│ Totals: CLV 1.5% (target: >1.2%) ✅                       │
├─────────────────────────────────────────────────────────────┤
│ ROI por Mercado:                                           │
│ Moneyline: 1.2% ⚠️                                        │
│ Spread: 3.8% ✅                                            │
│ Totals: 4.5% ✅                                           │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Alertas

```python
# Alerta se CLV por mercado cair abaixo de threshold
for mercado in df['mercado'].unique():
    if clv_por_mercado[mercado] < threshold_por_mercado[mercado]:
        send_alert(f"CLV {mercado} baixo", clv_por_mercado[mercado])
```

---

## 7. FERRAMENTAS

```python
# vbq/analysis/clv_by_market.py
import pandas as pd

def analyze_clv_by_market(df: pd.DataFrame):
    """Analisa CLV por tipo de mercado"""
    
    # Métricas por mercado
    clv_por_mercado = df.groupby('mercado')['clv'].agg(['mean', 'std', 'count'])
    roi_por_mercado = df.groupby('mercado')['pnl'].sum() / df.groupby('mercado')['stake'].sum()
    brier_por_mercado = df.groupby('mercado').apply(
        lambda x: brier_score(x['prob'], x['outcome'])
    )
    
    return {
        'clv': clv_por_mercado,
        'roi': roi_por_mercado,
        'brier': brier_por_mercado
    }
```

---

## 8. LINKS CRUZADOS

- [[37_CLV_Analytics/INDEX]] ← Secção mãe
- [[03_Quant_Research/CLV_CLOSED_LINE_VALUE]] → Fundamentos de CLV
- [[37_CLV_Analytics/CLV_POR_REGIME]] → CLV por regime
- [[42_Player_Props/INDEX]] → Player Props (mercado avançado)

---

**Custo de implementação:** 0€ (análise)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** ALTA (fundamental para entender eficiência relativa)
