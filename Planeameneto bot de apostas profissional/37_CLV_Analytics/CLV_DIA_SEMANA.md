# CLV por Dia da Semana

**ID:** CLV-008 | **Fase:** #phase/4-15 | **Owner:** Principal Quant Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Análise do CLV (Closed Line Value) segmentado por dia da semana. Padrões de mercado podem variar ao longo da semana devido a volume de informação, fadiga das equipas, e comportamento dos apostadores.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Identificar padrões de CLV por dia da semana |
| **Métricas** | CLV médio, Brier Score, ROI por dia |
| **Custo** | 0€ (análise) |

---

## 2. DEFINIÇÃO DE DIAS

### 2.1 Classificação

| Dia | Jogos NBA | Características |
|-----|-----------|----------------|
| **Segunda** | 0-2 jogos | Recuperação pós-fim de semana |
| **Terça** | 5-8 jogos | Volume médio |
| **Quarta** | 5-8 jogos | Volume médio |
| **Quinta** | 8-12 jogos | Volume alto |
| **Sexta** | 8-12 jogos | Volume alto |
| **Sábado** | 10-15 jogos | Volume máximo |
| **Domingo** | 5-10 jogos | Volume médio-alto |

**Regra:** Classificação baseada na data UTC do jogo.

### 2.2 Distribuição Natural

```
Segunda: ~5% dos jogos
Terça: ~15% dos jogos
Quarta: ~15% dos jogos
Quinta: ~20% dos jogos
Sexta: ~20% dos jogos
Sábado: ~15% dos jogos
Domingo: ~10% dos jogos
```

---

## 3. PORQUE CLV DIFERE POR DIA

### 3.1 Dias de Volume Baixo (Segunda)

**Características:**
- Menos jogos (menos dados para o mercado)
- Equipas mais descansadas
- Informação de lesões mais recente
- Mercado menos eficiente

**Vantagens do Modelo:**
- Mais espaço para edge
- Features de descanso têm mais valor
- Calibração mais fácil

### 3.2 Dias de Volume Médio (Terça-Quarta-Domingo)

**Características:**
- Volume equilibrado
- Equipas em ritmo normal
- Informação estável
- Mercado moderadamente eficiente

**Equilíbrio:**
- Edge moderado
- Calibração estável
- Risco moderado

### 3.3 Dias de Volume Alto (Quinta-Sexta-Sábado)

**Características:**
- Muitos jogos (mais dados para o mercado)
- Equipas podem estar fatigadas
- Informação saturada
- Mercado mais eficiente

**Desafios do Modelo:**
- Menos espaço para edge
- Features de fadiga mais importantes
- Calibração mais difícil

---

## 4. MÉTRICAS POR DIA

### 4.1 CLV Médio

```python
clv_por_dia = df.groupby('dia_semana')['clv'].agg(['mean', 'std', 'count'])

# Thresholds
if clv_por_dia.loc['segunda', 'mean'] > 0.01:
    status_segunda = "EXCELLENT"
elif clv_por_dia.loc['segunda', 'mean'] > 0.005:
    status_segunda = "ACEITÁVEL"
else:
    status_segunda = "FRACO"
```

### 4.2 Brier Score por Dia

```python
brier_por_dia = df.groupby('dia_semana').apply(
    lambda x: brier_score(x['prob'], x['outcome'])
)

# Thresholds
if brier_por_dia['segunda'] < 0.20:
    status_segunda = "BEM CALIBRADO"
elif brier_por_dia['segunda'] < 0.25:
    status_segunda = "ACEITÁVEL"
else:
    status_segunda = "MAL CALIBRADO"
```

### 4.3 ROI por Dia

```python
roi_por_dia = df.groupby('dia_semana')['pnl'].sum() / df.groupby('dia_semana')['stake'].sum()

# Thresholds
if roi_por_dia['segunda'] > 0.03:
    status_segunda = "EXCELLENT"
elif roi_por_dia['segunda'] > 0:
    status_segunda = "LUCRATIVO"
else:
    status_segunda = "PREJUÍZO"
```

---

## 5. ESTRATÉGIA POR DIA

### 5.1 Dias de Volume Baixo (Segunda)

**Recomendação:**
- Apostar se CLV > 0.8% (mais agressivo)
- Usar Kelly completo
- Priorizar features de descanso
- Monitorizar volume de apostas

**Justificação:**
- Mais espaço para edge
- Mercado menos eficiente
- Risco de liquidez

### 5.2 Dias de Volume Médio (Terça-Quarta-Domingo)

**Recomendação:**
- Apostar se CLV > 1.0% (moderado)
- Usar Kelly completo
- Estratégia equilibrada
- Monitorizar padrões

**Justificação:**
- Edge moderado
- Calibração estável
- Risco moderado

### 5.3 Dias de Volume Alto (Quinta-Sexta-Sábado)

**Recomendação:**
- Apostar se CLV > 1.2% (mais conservador)
- Limitar stake a 80% do Kelly recomendado
- Priorizar features de fadiga
- Verificar liquidez

**Justificação:**
- Menos espaço para edge
- Mercado mais eficiente
- Risco de slippage

---

## 6. MONITORIZAÇÃO

### 6.1 Dashboard por Dia

```
┌─────────────────────────────────────────────────────────────┐
│ CLV POR DIA DA SEMANA - [DATA]                             │
├─────────────────────────────────────────────────────────────┤
│ Segunda: CLV 1.5% (target: >0.8%) ✅                       │
│ Terça: CLV 1.1% (target: >1.0%) ✅                         │
│ Quarta: CLV 1.0% (target: >1.0%) ✅                        │
│ Quinta: CLV 0.9% (target: >1.2%) ⚠️                         │
│ Sexta: CLV 0.8% (target: >1.2%) ⚠️                         │
│ Sábado: CLV 0.7% (target: >1.2%) ⚠️                         │
│ Domingo: CLV 1.2% (target: >1.0%) ✅                        │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Alertas

```python
# Alerta se CLV por dia cair abaixo de threshold
for dia in df['dia_semana'].unique():
    if clv_por_dia[dia] < threshold_por_dia[dia]:
        send_alert(f"CLV {dia} baixo", clv_por_dia[dia])
```

---

## 7. FERRAMENTAS

```python
# vbq/analysis/clv_by_day.py
import pandas as pd

def analyze_clv_by_day(df: pd.DataFrame):
    """Analisa CLV por dia da semana"""
    
    # Extrair dia da semana
    df['dia_semana'] = pd.to_datetime(df['date']).dt.day_name()
    
    # Métricas por dia
    clv_por_dia = df.groupby('dia_semana')['clv'].agg(['mean', 'std', 'count'])
    roi_por_dia = df.groupby('dia_semana')['pnl'].sum() / df.groupby('dia_semana')['stake'].sum()
    brier_por_dia = df.groupby('dia_semana').apply(
        lambda x: brier_score(x['prob'], x['outcome'])
    )
    
    return {
        'clv': clv_por_dia,
        'roi': roi_por_dia,
        'brier': brier_por_dia
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
**Prioridade:** MÉDIA (útil para entender padrões semanais)
