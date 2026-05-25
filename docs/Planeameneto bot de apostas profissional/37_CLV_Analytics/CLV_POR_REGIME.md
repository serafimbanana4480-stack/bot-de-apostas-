# CLV por Regime

**ID:** CLV-006 | **Fase:** #phase/4-15 | **Owner:** Principal Quant Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Análise do CLV (Closed Line Value) segmentado por regime de jogo: favorito, equilibrado, underdog. A calibração do modelo pode diferir significativamente entre regimes, e o edge pode ser mais forte em alguns do que em outros.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Identificar onde o edge é mais forte por regime |
| **Métricas** | CLV médio, Brier Score, ROI por regime |
| **Custo** | 0€ (análise) |

---

## 2. DEFINIÇÃO DE REGIMES

### 2.1 Classificação

| Regime | Definição | Exemplo |
|--------|-----------|---------|
| **Favorito** | Odd < 1.50 | Lakers vs Wizards (Lakers 1.30) |
| **Equilibrado** | Odd 1.50 - 2.50 | Celtics vs Bucks (1.80) |
| **Underdog** | Odd > 2.50 | Hornets vs Suns (3.00) |

**Regra:** Classificação baseada na odd de fecho da Pinnacle.

### 2.2 Distribuição Natural

```
Favorito: ~35% dos jogos
Equilibrado: ~45% dos jogos
Underdog: ~20% dos jogos
```

---

## 3. PORQUE CLV DIFERE POR REGIME

### 3.1 Favoritos

**Características:**
- Odds mais estáveis (menor volatilidade)
- Mercado mais eficiente (mais volume)
- Diferença entre odd de abertura e fecho menor
- Edge teórico mais difícil de encontrar

**Desafios do Modelo:**
- Mercados de favoritos são mais eficientes
- Informação assimétrica menos relevante
- Modelos tendem a ser mais conservadores

### 3.2 Equilibrados

**Características:**
- Maior volatilidade de odds
- Mercado menos eficiente (volume médio)
- Maior oportunidade de edge
- Informação de lesões mais impactante

**Vantagens do Modelo:**
- Mais espaço para edge
- Features de contexto têm mais valor
- Calibração mais fácil

### 3.3 Underdogs

**Características:**
- Odds muito voláteis
- Mercado menos eficiente (volume baixo)
- Maior risco de liquidez
- Overround mais alto

**Desafios do Modelo:**
- Menos dados históricos (underdogs mudam)
- Alta variância
- Calibração mais difícil

---

## 4. MÉTRICAS POR REGIME

### 4.1 CLV Médio

```python
clv_por_regime = df.groupby('regime')['clv'].agg(['mean', 'std', 'count'])

# Thresholds
if clv_por_regime.loc['favorito', 'mean'] > 0.01:
    status_favorito = "EXCELLENT"
elif clv_por_regime.loc['favorito', 'mean'] > 0.005:
    status_favorito = "ACEITÁVEL"
else:
    status_favorito = "FRACO"
```

### 4.2 Brier Score por Regime

```python
brier_por_regime = df.groupby('regime').apply(
    lambda x: brier_score(x['prob'], x['outcome'])
)

# Thresholds
if brier_por_regime['favorito'] < 0.20:
    status_favorito = "BEM CALIBRADO"
elif brier_por_regime['favorito'] < 0.25:
    status_favorito = "ACEITÁVEL"
else:
    status_favorito = "MAL CALIBRADO"
```

### 4.3 ROI por Regime

```python
roi_por_regime = df.groupby('regime')['pnl'].sum() / df.groupby('regime')['stake'].sum()

# Thresholds
if roi_por_regime['favorito'] > 0.03:
    status_favorito = "EXCELLENT"
elif roi_por_regime['favorito'] > 0:
    status_favorito = "LUCRATIVO"
else:
    status_favorito = "PREJUÍZO"
```

---

## 5. ESTRATÉGIA POR REGIME

### 5.1 Favoritos

**Recomendação:**
- Apostar apenas se CLV > 1.5% (mais conservador)
- Limitar stake a 50% do Kelly recomendado
- Verificar liquidez antes de apostar
- Priorizar casas com melhor liquidez

**Justificação:**
- Mercado mais eficiente
- Edge menor
- Risco de slippage maior

### 5.2 Equilibrados

**Recomendação:**
- Apostar se CLV > 1.0% (moderado)
- Usar Kelly completo
- Priorizar informação de contexto
- Monitorizar movimentos de linha

**Justificação:**
- Maior oportunidade de edge
- Features têm mais valor
- Calibração mais fácil

### 5.3 Underdogs

**Recomendação:**
- Apostar se CLV > 2.0% (mais agressivo)
- Limitar stake a 30% do Kelly recomendado
- Verificar liquidez cuidadosamente
- Considerar apenas se volume > €1000

**Justificação:**
- Alta variância
- Menos dados históricos
- Risco de liquidez

---

## 6. MONITORIZAÇÃO

### 6.1 Dashboard por Regime

```
┌─────────────────────────────────────────────────────────────┐
│ CLV POR REGIME - [DATA]                                    │
├─────────────────────────────────────────────────────────────┤
│ Favorito: CLV 0.8% (target: >1.0%) ⚠️                       │
│ Equilibrado: CLV 1.5% (target: >1.0%) ✅                   │
│ Underdog: CLV 2.3% (target: >2.0%) ✅                     │
├─────────────────────────────────────────────────────────────┤
│ ROI por Regime:                                             │
│ Favorito: 1.2% ✅                                           │
│ Equilibrado: 3.8% ✅                                        │
│ Underdog: 5.1% ✅                                           │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Alertas

```python
# Alerta se CLV por regime cair abaixo de threshold
if clv_por_regime['favorito'] < 0.01:
    send_alert("CLV favorito baixo", clv_por_regime['favorito'])

# Alerta se ROI por regime negativo
if roi_por_regime['equilibrado'] < 0:
    send_alert("ROI equilibrado negativo", roi_por_regime['equilibrado'])
```

---

## 7. FERRAMENTAS

```python
# vbq/analysis/clv_by_regime.py
import pandas as pd

def analyze_clv_by_regime(df: pd.DataFrame):
    """Analisa CLV por regime"""
    
    # Classificar regime
    df['regime'] = df['odd_close'].apply(classify_regime)
    
    # Métricas por regime
    clv_por_regime = df.groupby('regime')['clv'].agg(['mean', 'std', 'count'])
    roi_por_regime = df.groupby('regime')['pnl'].sum() / df.groupby('regime')['stake'].sum()
    brier_por_regime = df.groupby('regime').apply(
        lambda x: brier_score(x['prob'], x['outcome'])
    )
    
    return {
        'clv': clv_por_regime,
        'roi': roi_por_regime,
        'brier': brier_por_regime
    }

def classify_regime(odd: float) -> str:
    """Classifica regime baseado na odd"""
    if odd < 1.50:
        return 'favorito'
    elif odd < 2.50:
        return 'equilibrado'
    else:
        return 'underdog'
```

---

## 8. LINKS CRUZADOS

- [[37_CLV_Analytics/INDEX]] ← Secção mãe
- [[03_Quant_Research/CLV_CLOSED_LINE_VALUE]] → Fundamentos de CLV
- [[EDGE_DECAY_REGIME]] → Edge decay por regime
- [[37_CLV_Analytics/CLV_POR_MERCADO]] → CLV por mercado

---

**Custo de implementação:** 0€ (análise)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** ALTA (fundamental para entender onde o edge é mais forte)
