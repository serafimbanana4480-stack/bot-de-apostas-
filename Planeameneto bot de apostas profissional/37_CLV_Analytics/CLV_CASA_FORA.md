# CLV Casa vs Fora

**ID:** CLV-007 | **Fase:** #phase/4-15 | **Owner:** Principal Quant Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Análise do CLV (Closed Line Value) segmentado por contexto de jogo: casa vs fora. O contexto altera a eficiência do mercado e a calibração do modelo pode diferir significativamente.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Identificar diferenças de edge entre jogos em casa e fora |
| **Métricas** | CLV médio, Brier Score, ROI por contexto |
| **Custo** | 0€ (análise) |

---

## 2. DEFINIÇÃO DE CONTEXTO

### 2.1 Classificação

| Contexto | Definição | Exemplo |
|----------|-----------|---------|
| **Casa** | Equipa joga no seu pavilhão | Lakers @ Lakers |
| **Fora** | Equipa joga no pavilhão adversário | Lakers @ Celtics |

**Regra:** Classificação baseada na localização do jogo.

### 2.2 Distribuição Natural

```
Casa: 50% dos jogos (cada equipa joga 41 jogos em casa)
Fora: 50% dos jogos (cada equipa joga 41 jogos fora)
```

---

## 3. PORQUE CLV DIFERE POR CONTEXTO

### 3.1 Jogos em Casa

**Características:**
- Vantagem de casa documentada (≈3-4 pontos)
- Odds iniciais podem ser menos eficientes
- Informação local (lesões, rotação) assimétrica
- Volume de apostas pode ser maior

**Vantagens do Modelo:**
- Mais espaço para edge
- Features locais têm mais valor
- Calibração mais fácil

### 3.2 Jogos Fora

**Características:**
- Desvantagem de viajamento (fadiga, fusos horários)
- Odds podem ser mais eficientes
- Informação menos assimétrica
- Volume de apostas pode ser menor

**Desafios do Modelo:**
- Menos espaço para edge
- Features de fadiga mais importantes
- Calibração mais difícil

---

## 4. MÉTRICAS POR CONTEXTO

### 4.1 CLV Médio

```python
clv_por_contexto = df.groupby('contexto')['clv'].agg(['mean', 'std', 'count'])

# Thresholds
if clv_por_contexto.loc['casa', 'mean'] > 0.01:
    status_casa = "EXCELLENT"
elif clv_por_contexto.loc['casa', 'mean'] > 0.005:
    status_casa = "ACEITÁVEL"
else:
    status_casa = "FRACO"
```

### 4.2 Brier Score por Contexto

```python
brier_por_contexto = df.groupby('contexto').apply(
    lambda x: brier_score(x['prob'], x['outcome'])
)

# Thresholds
if brier_por_contexto['casa'] < 0.20:
    status_casa = "BEM CALIBRADO"
elif brier_por_contexto['casa'] < 0.25:
    status_casa = "ACEITÁVEL"
else:
    status_casa = "MAL CALIBRADO"
```

### 4.3 ROI por Contexto

```python
roi_por_contexto = df.groupby('contexto')['pnl'].sum() / df.groupby('contexto')['stake'].sum()

# Thresholds
if roi_por_contexto['casa'] > 0.03:
    status_casa = "EXCELLENT"
elif roi_por_contexto['casa'] > 0:
    status_casa = "LUCRATIVO"
else:
    status_casa = "PREJUÍZO"
```

---

## 5. ESTRATÉGIA POR CONTEXTO

### 5.1 Jogos em Casa

**Recomendação:**
- Apostar se CLV > 1.0% (moderado)
- Usar Kelly completo
- Priorizar features locais
- Monitorizar informação de lesões

**Justificação:**
- Maior oportunidade de edge
- Features locais têm mais valor
- Calibração mais fácil

### 5.2 Jogos Fora

**Recomendação:**
- Apostar se CLV > 1.2% (mais conservador)
- Limitar stake a 80% do Kelly recomendado
- Priorizar features de fadiga
- Verificar fusos horários

**Justificação:**
- Menos espaço para edge
- Fadiga mais impactante
- Calibração mais difícil

---

## 6. MONITORIZAÇÃO

### 6.1 Dashboard por Contexto

```
┌─────────────────────────────────────────────────────────────┐
│ CLV POR CONTEXTO - [DATA]                                  │
├─────────────────────────────────────────────────────────────┤
│ Casa: CLV 1.3% (target: >1.0%) ✅                           │
│ Fora: CLV 1.1% (target: >1.0%) ✅                           │
├─────────────────────────────────────────────────────────────┤
│ ROI por Contexto:                                           │
│ Casa: 3.5% ✅                                               │
│ Fora: 2.8% ✅                                               │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Alertas

```python
# Alerta se CLV por contexto cair abaixo de threshold
if clv_por_contexto['casa'] < 0.01:
    send_alert("CLV casa baixo", clv_por_contexto['casa'])

# Alerta se ROI por contexto negativo
if roi_por_contexto['fora'] < 0:
    send_alert("ROI fora negativo", roi_por_contexto['fora'])
```

---

## 7. FERRAMENTAS

```python
# vbq/analysis/clv_by_context.py
import pandas as pd

def analyze_clv_by_context(df: pd.DataFrame):
    """Analisa CLV por contexto (casa vs fora)"""
    
    # Métricas por contexto
    clv_por_contexto = df.groupby('contexto')['clv'].agg(['mean', 'std', 'count'])
    roi_por_contexto = df.groupby('contexto')['pnl'].sum() / df.groupby('contexto')['stake'].sum()
    brier_por_contexto = df.groupby('contexto').apply(
        lambda x: brier_score(x['prob'], x['outcome'])
    )
    
    return {
        'clv': clv_por_contexto,
        'roi': roi_por_contexto,
        'brier': brier_por_contexto
    }
```

---

## 8. LINKS CRUZADOS

- [[37_CLV_Analytics/INDEX]] ← Secção mãe
- [[03_Quant_Research/CLV_CLOSED_LINE_VALUE]] → Fundamentos de CLV
- [[37_CLV_Analytics/CLV_POR_REGIME]] → CLV por regime
- [[37_CLV_Analytics/CLV_BACK_TO_BACK]] → CLV back-to-back

---

**Custo de implementação:** 0€ (análise)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** MÉDIA (útil para entender contexto)
