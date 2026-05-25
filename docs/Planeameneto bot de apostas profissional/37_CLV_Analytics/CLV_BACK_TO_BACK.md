# CLV Back-to-Back

**ID:** CLV-009 | **Fase:** #phase/4-15 | **Owner:** Principal Quant Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Análise do CLV (Closed Line Value) segmentado por jogos back-to-back (consecutivos). A fadiga física e mental pode afetar a performance das equipas e a eficiência do mercado.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Identificar impacto de back-to-back no CLV |
| **Métricas** | CLV médio, Brier Score, ROI por situação |
| **Custo** | 0€ (análise) |

---

## 2. DEFINIÇÃO DE SITUAÇÕES

### 2.1 Classificação

| Situação | Definição | Exemplo |
|----------|-----------|---------|
| **Back-to-Back** | Jogo anterior no dia anterior | Lakers jogou ontem, joga hoje |
| **2 em 2 Dias** | Jogo anterior há 2 dias | Lakers jogou anteontem |
| **3+ Dias Descanso** | 3+ dias desde jogo anterior | Lakers jogou há 4 dias |
| **Primeiro Jogo** | Primeiro jogo após break | Lakers após All-Star break |

**Regra:** Classificação baseada nos dias desde o jogo anterior.

### 2.2 Distribuição Natural

```
Back-to-Back: ~20% dos jogos
2 em 2 Dias: ~30% dos jogos
3+ Dias Descanso: ~40% dos jogos
Primeiro Jogo: ~10% dos jogos
```

---

## 3. PORQUE CLV DIFERE POR FADIGA

### 3.1 Back-to-Back

**Características:**
- Fadiga física significativa
- Menos tempo para preparação
- Informação de lesões mais recente
- Mercado pode subestimar impacto

**Vantagens do Modelo:**
- Mais espaço para edge
- Features de fadiga têm mais valor
- Calibração mais fácil

**Desafios:**
- Variabilidade alta (alguns jogadores lidam melhor)
- Risco de lesões maior
- Rotação pode ser imprevisível

### 3.2 2 em 2 Dias

**Características:**
- Fadiga moderada
- Tempo de preparação adequado
- Informação estável
- Mercado moderadamente eficiente

**Equilíbrio:**
- Edge moderado
- Calibração estável
- Risco moderado

### 3.3 3+ Dias Descanso

**Características:**
- Fadiga mínima
- Tempo de preparação máximo
- Informação saturada
- Mercado mais eficiente

**Desafios do Modelo:**
- Menos espaço para edge
- Features de fadiga menos relevantes
- Calibração mais difícil

### 3.4 Primeiro Jogo

**Características:**
- Fadiga mínima
- Ferrugem possível
- Informação de treino limitada
- Mercado incerto

**Vantagens:**
- Mais espaço para edge
- Features de break têm valor
- Calibração mais fácil

---

## 4. MÉTRICAS POR SITUAÇÃO

### 4.1 CLV Médio

```python
clv_por_situacao = df.groupby('situacao_fadiga')['clv'].agg(['mean', 'std', 'count'])

# Thresholds
if clv_por_situacao.loc['back_to_back', 'mean'] > 0.01:
    status_b2b = "EXCELLENT"
elif clv_por_situacao.loc['back_to_back', 'mean'] > 0.005:
    status_b2b = "ACEITÁVEL"
else:
    status_b2b = "FRACO"
```

### 4.2 Brier Score por Situação

```python
brier_por_situacao = df.groupby('situacao_fadiga').apply(
    lambda x: brier_score(x['prob'], x['outcome'])
)

# Thresholds
if brier_por_situacao['back_to_back'] < 0.20:
    status_b2b = "BEM CALIBRADO"
elif brier_por_situacao['back_to_back'] < 0.25:
    status_b2b = "ACEITÁVEL"
else:
    status_b2b = "MAL CALIBRADO"
```

### 4.3 ROI por Situação

```python
roi_por_situacao = df.groupby('situacao_fadiga')['pnl'].sum() / df.groupby('situacao_fadiga')['stake'].sum()

# Thresholds
if roi_por_situacao['back_to_back'] > 0.03:
    status_b2b = "EXCELLENT"
elif roi_por_situacao['back_to_back'] > 0:
    status_b2b = "LUCRATIVO"
else:
    status_b2b = "PREJUÍZO"
```

---

## 5. ESTRATÉGIA POR SITUAÇÃO

### 5.1 Back-to-Back

**Recomendação:**
- Apostar se CLV > 1.2% (mais conservador)
- Limitar stake a 70% do Kelly recomendado
- Priorizar features de fadiga
- Verificar status de lesões

**Justificação:**
- Variabilidade alta
- Risco de lesões
- Rotação imprevisível

### 5.2 2 em 2 Dias

**Recomendação:**
- Apostar se CLV > 1.0% (moderado)
- Usar Kelly completo
- Estratégia equilibrada
- Monitorizar padrões

**Justificação:**
- Edge moderado
- Calibração estável
- Risco moderado

### 5.3 3+ Dias Descanso

**Recomendação:**
- Apostar se CLV > 1.2% (mais conservador)
- Limitar stake a 80% do Kelly recomendado
- Priorizar features de forma
- Verificar ferrugem

**Justificação:**
- Menos espaço para edge
- Mercado mais eficiente
- Risco de ferrugem

### 5.4 Primeiro Jogo

**Recomendação:**
- Apostar se CLV > 0.8% (mais agressivo)
- Usar Kelly completo
- Priorizar features de break
- Monitorizar ritmo

**Justificação:**
- Mais espaço para edge
- Mercado incerto
- Risco de ferrugem

---

## 6. MONITORIZAÇÃO

### 6.1 Dashboard por Situação

```
┌─────────────────────────────────────────────────────────────┐
│ CLV POR SITUAÇÃO DE FADIGA - [DATA]                       │
├─────────────────────────────────────────────────────────────┤
│ Back-to-Back: CLV 1.4% (target: >1.2%) ✅                  │
│ 2 em 2 Dias: CLV 1.0% (target: >1.0%) ✅                   │
│ 3+ Dias: CLV 0.9% (target: >1.2%) ⚠️                       │
│ Primeiro Jogo: CLV 1.6% (target: >0.8%) ✅                │
├─────────────────────────────────────────────────────────────┤
│ ROI por Situação:                                           │
│ Back-to-Back: 4.2% ✅                                      │
│ 2 em 2 Dias: 2.8% ✅                                       │
│ 3+ Dias: 1.5% ⚠️                                           │
│ Primeiro Jogo: 5.1% ✅                                     │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Alertas

```python
# Alerta se CLV por situação cair abaixo de threshold
if clv_por_situacao['back_to_back'] < 0.012:
    send_alert("CLV back-to-back baixo", clv_por_situacao['back_to_back'])
```

---

## 7. FERRAMENTAS

```python
# vbq/analysis/clv_by_fatigue.py
import pandas as pd

def analyze_clv_by_fatigue(df: pd.DataFrame):
    """Analisa CLV por situação de fadiga"""
    
    # Classificar situação de fadiga
    df['situacao_fadiga'] = df.apply(classify_fatigue_situation, axis=1)
    
    # Métricas por situação
    clv_por_situacao = df.groupby('situacao_fadiga')['clv'].agg(['mean', 'std', 'count'])
    roi_por_situacao = df.groupby('situacao_fadiga')['pnl'].sum() / df.groupby('situacao_fadiga')['stake'].sum()
    brier_por_situacao = df.groupby('situacao_fadiga').apply(
        lambda x: brier_score(x['prob'], x['outcome'])
    )
    
    return {
        'clv': clv_por_situacao,
        'roi': roi_por_situacao,
        'brier': brier_por_situacao
    }

def classify_fatigue_situation(row):
    """Classifica situação de fadiga baseado em dias desde jogo anterior"""
    dias_descanso = row['dias_descanso']
    
    if dias_descanso == 1:
        return 'back_to_back'
    elif dias_descanso == 2:
        return '2_em_2_dias'
    elif dias_descanso >= 3:
        return '3_mais_dias'
    else:
        return 'primeiro_jogo'
```

---

## 8. LINKS CRUZADOS

- [[37_CLV_Analytics/INDEX]] ← Secção mãe
- [[03_Quant_Research/CLV_CLOSED_LINE_VALUE]] → Fundamentos de CLV
- [[37_CLV_Analytics/CLV_CASA_FORA]] → CLV casa vs fora
- [[42_Player_Props/USAGE_ROLE_CHANGES]] → Mudanças de uso e rotação

---

**Custo de implementação:** 0€ (análise)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** MÉDIA (útil para entender impacto de fadiga)
