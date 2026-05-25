# META_LABELING_MODELO — Modelo Secundário de Filtragem de Qualidade

**ID:** `ML-015` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

O meta-labeling é um modelo secundário XGBoost que filtra as predições do modelo primário. Em vez de confiar cegamente em todas as apostas com edge positivo, o meta-modelo responde à pergunta: "Dado este edge e este contexto, qual a probabilidade de esta aposta ter CLV positivo ex-post?"

---

## 2. POR QUE META-LABELING?

### 2.1 Problema do Modelo Primário

O modelo primário pode ter edge médio de 3%, mas nem todas as apostas com edge > 3% são igualmente boas:
- Algumas têm variância excessiva (overconfidence)
- Outras ocorrem em regimes onde o modelo é mal calibrado
- Algumas são "falsos positivos" causados por noise nos dados

### 2.2 Solução: Meta-Modelo como Filtro

O meta-modelo aprende a distinguir:
- **Verdadeiros positivos:** Apostas com edge genuíno que mantêm CLV positivo
- **Falsos positivos:** Apostas com edge aparente mas que perdem dinheiro

**Resultado esperado:**
- Redução de 20-40% no número de apostas
- Aumento de 0.5-1.0% no CLV médio das apostas restantes
- Sharpe Ratio aumenta significativamente

---

## 3. ARQUITETURA DO META-MODELO

### 3.1 Features de Entrada

```python
meta_features = {
    # Features do modelo primário
    "prob_primario": float,        # Probabilidade do modelo primário
    "edge_estimado": float,        # Edge = (prob * odd) - 1
    
    # Métricas de confiança
    "entropy": float,              # Entropia da distribuição
    "confidence_score": float,     # Score composto de confiança
    
    # Contexto do jogo
    "regime": str,                 # favorito / equilibrado / underdog
    "is_home": bool,               # Casa ou fora
    "is_back_to_back": bool,       # Back-to-back
    "rest_days": int,              # Dias de descanso
    
    # Qualidade dos dados
    "feature_coverage": float,     # % de features disponíveis
    "data_freshness": int,         # Horas desde última atualização
    
    # Mercado
    "liquidity": float,            # Volume disponível na odd
    "odd": float,                  # Odd do mercado
    "spread_market_prob": float,   # Probabilidade no mercado de spread (correlação)
}
```

### 3.2 Target

```python
meta_target = 1 if CLV_expost > 0 else 0
```

O target é binário: a aposta teve CLV positivo (odd de fecho > odd usada)?

### 3.3 Modelo

- **Algoritmo:** XGBoost com objetivo binary:logistic
- **Hiperparâmetros:** Mais conservadores que o primário
  - max_depth = 3 (menos complexo)
  - learning_rate = 0.03 (mais lento)
  - min_child_weight = 100 (mais robusto)
- **Validação:** Mesmo esquema de purged walk-forward CV que o primário
- **Threshold:** prob_meta > 0.60 para aprovar aposta

---

## 4. PROCESSO DE TREINAMENTO

### 4.1 Dados de Treino

Requer dados históricos com:
- Previsões do modelo primário
- Odds usadas e odds de fecho
- Resultados reais
- Features de contexto

Mínimo: 2 épocas completas (~2500 jogos)

### 4.2 Pipeline

```
1. Para cada aposta histórica:
   - Obter probabilidade do modelo primário na época
   - Calcular edge no momento da aposta
   - Calcular entropia e outras métricas
   - Obter contexto (regime, calendário, etc.)
   - Calcular CLV ex-post (odd_fecho / odd_usada - 1)
   - Se CLV > 0 → target = 1, senão target = 0

2. Dividir em treino/validação/teste com purged CV

3. Treinar XGBoost com hiperparâmetros conservadores

4. Calibrar output (opcional, raramente necessário)

5. Validar:
   - AUC-ROC > 0.60 (modelo deve ter skill)
   - Precision > 0.70 (evitar muitos falsos positivos)
   - Recall balanceado (não filtrar tudo)
```

### 4.3 Otimização de Threshold

Threshold default: 0.60

Otimizar com walk-forward:
- Range: [0.50, 0.75]
- Métrica: Maximizar Sharpe Ratio no backtest
- Trade-off: Threshold mais alto → menos apostas mas melhor qualidade

---

## 5. INTEGRAÇÃO EM PRODUÇÃO

### 5.1 Pipeline Completo

```python
def gerar_sinal(features_jogo, odd_betfair):
    # 1. Modelo primário
    prob_primario = modelo_primario.predict(features_jogo)
    
    # 2. Calibração
    prob_calibrada = calibrador.calibrate(prob_primario)
    
    # 3. Cálculo de edge
    edge = (prob_calibrada * odd_betfair) - 1
    
    # 4. Filtro de edge
    if edge < 0.04:
        return None  # Sem sinal
    
    # 5. Meta-features
    meta_features = build_meta_features(
        prob_primario, edge, features_jogo, odd_betfair
    )
    
    # 6. Meta-modelo
    prob_meta = meta_modelo.predict(meta_features)
    
    # 7. Filtro de qualidade
    if prob_meta < 0.60:
        return None  # Falso positivo provável
    
    # 8. Sinal aprovado
    return {
        "prob_primario": prob_primario,
        "prob_calibrada": prob_calibrada,
        "edge": edge,
        "prob_meta": prob_meta,
        "stake": calcular_stake(edge, prob_calibrada)
    }
```

### 5.2 Monitorização do Meta-Modelo

Métricas em produção:
- Taxa de aprovação (% de sinais primários que passam meta)
- CLV médio dos sinais aprovados vs rejeitados
- Win rate dos sinais aprovados vs rejeitados
- Distribuição de prob_meta

Se taxa de aprovação < 20% ou > 80%:
- Investigar se threshold está otimizado
- Reavaliar features do meta-modelo
- Retreinar se necessário

---

## 6. IMPACTO ESPERADO

### 6.1 Antes do Meta-Labeling

- Apostas/mês: 100
- CLV médio: 2.0%
- ROI: 5%
- Sharpe Ratio: 0.45

### 6.2 Depois do Meta-Labeling

- Apostas/mês: 60-80 (redução de 20-40%)
- CLV médio: 2.5-3.0% (aumento de 0.5-1.0%)
- ROI: 6-7% (devido a melhor qualidade)
- Sharpe Ratio: 0.55-0.65 (devido a menor volatilidade)

**Conclusão:** Menos apostas, mas de melhor qualidade, resultando em performance ajustada ao risco superior.

---

## 7. MANUTENÇÃO

### 7.1 Retreino do Meta-Modelo

- **Frequência:** Mensal (mesma frequência do modelo primário)
- **Dados:** Últimos 3 meses + validação walk-forward
- **Critério de promoção:** Melhoria > 0.5% no Sharpe Ratio em shadow mode

### 7.2 Monitorização Contínua

- Taxa de aprovação deve estar entre 20-80%
- Se taxa < 20%: threshold muito alto, perder oportunidades
- Se taxa > 80%: threshold muito baixo, pouco valor adicionado
- Ajustar threshold dinamicamente se necessário

---

## 8. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]] ← Secção mãe
- [[46_Meta_Labeling/INDEX]] → Detalhes do meta-labeling
- [[07_Value_Detection/INDEX]] → Motor de edge que consome o filtro