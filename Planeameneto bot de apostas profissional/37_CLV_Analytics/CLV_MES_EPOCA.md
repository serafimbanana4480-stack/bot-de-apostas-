# CLV por Mês da Época

**ID:** CLV-010 | **Fase:** #phase/4-15 | **Owner:** Principal Quant Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Análise do CLV (Closed Line Value) segmentado por mês da época. O ritmo de jogo, motivação, e eficiência do mercado podem mudar significativamente ao longo da época.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Identificar padrões de CLV ao longo da época |
| **Métricas** | CLV médio, Brier Score, ROI por mês |
| **Custo** | 0€ (análise) |

---

## 2. DEFINIÇÃO DE MESES

### 2.1 Classificação

| Mês | Jogos | Características |
|-----|-------|----------------|
| **Outubro** | 5-8 jogos | Início da época, rustiness |
| **Novembro** | 12-15 jogos | Ajuste ao ritmo |
| **Dezembro** | 12-15 jogos | Ritmo intenso, Natal |
| **Janeiro** | 12-15 jogos | Pós-Natal, trade deadline |
| **Fevereiro** | 10-12 jogos | All-Star break |
| **Março** | 15-18 jogos | Push para playoffs |
| **Abril** | 15-18 jogos | Fim da época, playoffs |
| **Playoffs** | Variável | Alta pressão, diferente |

**Regra:** Classificação baseada no mês UTC do jogo.

### 2.2 Distribuição Natural

```
Outubro: ~5% dos jogos
Novembro: ~15% dos jogos
Dezembro: ~15% dos jogos
Janeiro: ~15% dos jogos
Fevereiro: ~12% dos jogos
Março: ~18% dos jogos
Abril: ~20% dos jogos
```

---

## 3. PORQUE CLV DIFERE POR MÊS

### 3.1 Início da Época (Outubro-Novembro)

**Características:**
- Equipas ainda em ajuste
- Rotações experimentais
- Informação limitada
- Mercado menos eficiente

**Vantagens do Modelo:**
- Mais espaço para edge
- Features de forma inicial têm valor
- Calibração mais fácil

**Desafios:**
- Alta variabilidade
- Menos dados históricos
- Rotação imprevisível

### 3.2 Meio da Época (Dezembro-Janeiro)

**Características:**
- Equipas em ritmo
- Rotações estáveis
- Informação abundante
- Mercado moderadamente eficiente

**Equilíbrio:**
- Edge moderado
- Calibração estável
- Risco moderado

### 3.3 All-Star Break (Fevereiro)

**Características:**
- Quebra no ritmo
- Trade deadline
- Informação de mudanças
- Mercado incerto

**Vantagens:**
- Mais espaço para edge
- Features de mudanças têm valor
- Calibração mais fácil

### 3.4 Push Playoffs (Março-Abril)

**Características:**
- Alta motivação
- Equipas consolidadas
- Informação saturada
- Mercado mais eficiente

**Desafios do Modelo:**
- Menos espaço para edge
- Motivação difícil de modelar
- Calibração mais difícil

---

## 4. MÉTRICAS POR MÊS

### 4.1 CLV Médio

```python
clv_por_mes = df.groupby('mes')['clv'].agg(['mean', 'std', 'count'])

# Thresholds
if clv_por_mes.loc['outubro', 'mean'] > 0.012:
    status_outubro = "EXCELLENT"
elif clv_por_mes.loc['outubro', 'mean'] > 0.008:
    status_outubro = "ACEITÁVEL"
else:
    status_outubro = "FRACO"
```

### 4.2 Brier Score por Mês

```python
brier_por_mes = df.groupby('mes').apply(
    lambda x: brier_score(x['prob'], x['outcome'])
)

# Thresholds
if brier_por_mes['outubro'] < 0.20:
    status_outubro = "BEM CALIBRADO"
elif brier_por_mes['outubro'] < 0.25:
    status_outubro = "ACEITÁVEL"
else:
    status_outubro = "MAL CALIBRADO"
```

### 4.3 ROI por Mês

```python
roi_por_mes = df.groupby('mes')['pnl'].sum() / df.groupby('mes')['stake'].sum()

# Thresholds
if roi_por_mes['outubro'] > 0.03:
    status_outubro = "EXCELLENT"
elif roi_por_mes['outubro'] > 0:
    status_outubro = "LUCRATIVO"
else:
    status_outubro = "PREJUÍZO"
```

---

## 5. ESTRATÉGIA POR MÊS

### 5.1 Início da Época (Outubro-Novembro)

**Recomendação:**
- Apostar se CLV > 1.2% (mais conservador)
- Limitar stake a 70% do Kelly recomendado
- Priorizar features de forma inicial
- Monitorizar rotações

**Justificação:**
- Alta variabilidade
- Menos dados históricos
- Rotação imprevisível

### 5.2 Meio da Época (Dezembro-Janeiro)

**Recomendação:**
- Apostar se CLV > 1.0% (moderado)
- Usar Kelly completo
- Estratégia equilibrada
- Monitorizar padrões

**Justificação:**
- Edge moderado
- Calibração estável
- Risco moderado

### 5.3 All-Star Break (Fevereiro)

**Recomendação:**
- Apostar se CLV > 1.2% (mais conservador)
- Limitar stake a 80% do Kelly recomendado
- Priorizar features de mudanças
- Verificar trades

**Justificação:**
- Mercado incerto
- Mudanças de equipas
- Risco de ajuste

### 5.4 Push Playoffs (Março-Abril)

**Recomendação:**
- Apostar se CLV > 1.5% (mais conservador)
- Limitar stake a 60% do Kelly recomendado
- Priorizar features de motivação
- Verificar playoff race

**Justificação:**
- Menos espaço para edge
- Motivação difícil de modelar
- Risco de comportamento atípico

---

## 6. MONITORIZAÇÃO

### 6.1 Dashboard por Mês

```
┌─────────────────────────────────────────────────────────────┐
│ CLV POR MÊS DA ÉPOCA - [DATA]                              │
├─────────────────────────────────────────────────────────────┤
│ Outubro: CLV 1.6% (target: >1.2%) ✅                       │
│ Novembro: CLV 1.2% (target: >1.0%) ✅                       │
│ Dezembro: CLV 1.0% (target: >1.0%) ✅                      │
│ Janeiro: CLV 0.9% (target: >1.0%) ⚠️                        │
│ Fevereiro: CLV 1.3% (target: >1.2%) ✅                      │
│ Março: CLV 0.8% (target: >1.5%) ⚠️                         │
│ Abril: CLV 0.7% (target: >1.5%) ⚠️                         │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Alertas

```python
# Alerta se CLV por mês cair abaixo de threshold
for mes in df['mes'].unique():
    if clv_por_mes[mes] < threshold_por_mes[mes]:
        send_alert(f"CLV {mes} baixo", clv_por_mes[mes])
```

---

## 7. FERRAMENTAS

```python
# vbq/analysis/clv_by_month.py
import pandas as pd

def analyze_clv_by_month(df: pd.DataFrame):
    """Analisa CLV por mês da época"""
    
    # Extrair mês
    df['mes'] = pd.to_datetime(df['date']).dt.month_name()
    
    # Métricas por mês
    clv_por_mes = df.groupby('mes')['clv'].agg(['mean', 'std', 'count'])
    roi_por_mes = df.groupby('mes')['pnl'].sum() / df.groupby('mes')['stake'].sum()
    brier_por_mes = df.groupby('mes').apply(
        lambda x: brier_score(x['prob'], x['outcome'])
    )
    
    return {
        'clv': clv_por_mes,
        'roi': roi_por_mes,
        'brier': brier_por_mes
    }
```

---

## 8. LINKS CRUZADOS

- [[37_CLV_Analytics/INDEX]] ← Secção mãe
- [[03_Quant_Research/CLV_CLOSED_LINE_VALUE]] → Fundamentos de CLV
- [[37_CLV_Analytics/CLV_DIA_SEMANA]] → CLV por dia da semana
- [[EDGE_DECAY_REGIME]] → Edge decay ao longo do tempo

---

**Custo de implementação:** 0€ (análise)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** MÉDIA (útil para entender padrões sazonais)
