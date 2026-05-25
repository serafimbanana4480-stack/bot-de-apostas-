# 07_Value_Detection — INDEX

**ID:** `SEC-07` | **Fase:** #phase/2-3 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

O **Motor de Value** é o coração do sistema. Recebe as probabilidades calibradas do modelo e as odds do mercado, calcula o edge, aplica filtros de qualidade (meta-labeling), e gera sinais de apostas com stakes recomendados.

Um sinal só é emitido se passar por TODOS os filtros. **Nenhuma exceção.**

---

## 2. NOTAS FUNDAMENTAIS

- [[MOTOR_EDGE]] — Fórmula de edge, thresholds dinâmicos, ajustes
- [[SISTEMA_DECISAO_APOSTAS]] — Sistema de decisão multi-camadas (Edge → Qualidade Odds → CLV → Exposição)
- [[FILTROS_QUALIDADE]] — Probabilidade, liquidez, regime, meta-labeling
- [[ODDS_NORMALIZACAO]] — Remoção de overround, fair odds
- [[SINAI_GENERATION]] — Pipeline de geração de sinais, formato, delivery
- [[THRESHOLD_OPTIMIZATION]] — Otimização de thresholds com validação walk-forward
- [[FALSE_POSITIVE_FILTER]] — Como o meta-modelo reduz falsos positivos

**Documentação Detalhada:**
- [[FILTROS_QUALIDADE.md]] — Explicação detalhada dos filtros de qualidade
- [[ODDS_NORMALIZACAO.md]] — Explicação detalhada da normalização de odds
- [[SINAI_GENERATION.md]] — Explicação detalhada do pipeline de geração de sinais
- [[THRESHOLD_OPTIMIZATION.md]] — Explicação detalhada da otimização de thresholds
- [[FALSE_POSITIVE_FILTER.md]] — Explicação detalhada do filtro de falsos positivos

---

## 3. ARQUITETURA DO MOTOR DE VALUE

```
Entradas:
  ├── prob_calibrada (do modelo primário + calibração)
  ├── odd_mercado (Pinnacle/Betfair em tempo real)
  ├── volume_liquidez (Betfair API)
  ├── regime_jogo (casa/fora, back-to-back, etc.)
  └── prob_meta (do meta-modelo)

Processamento:
  1. Calcular edge = (prob * odd) - 1
  2. Verificar edge > threshold_min (default: 0.04)
  3. Verificar prob ∈ [0.15, 0.85] (evitar extremos)
  4. Verificar volume_liquidez > stake * 1.5
  5. Verificar prob_meta > 0.60
  6. Verificar regime não está em blacklist (ex: playoffs sem histórico)
  
Saída (se TODOS passarem):
  ├── SINAL_APROVADO
  ├── equipa, mercado, odd_recomendada
  ├── edge_estimado, prob_modelo
  ├── stake_recomendada (Kelly fracionado)
  ├── confidence_score (produto de todos os filtros)
  └── timestamp_de_expiração (odd válida por X minutos)
```

---

## 4. FÓRMULAS DE EDGE

### 4.1 Edge Bruto
```python
edge_bruto = (prob_calibrada * odd_mercado) - 1.0
```

### 4.2 Edge Ajustado à Liquidez
```python
def edge_ajustado_liquidez(edge_bruto: float, volume_disponivel: float, 
                            stake_planeada: float) -> float:
    if volume_disponivel < stake_planeada * 1.5:
        return 0.0  # Rejeitar por falta de liquidez
    liquidez_factor = min(1.0, volume_disponivel / (stake_planeada * 3.0))
    return edge_bruto * liquidez_factor
```

### 4.3 Edge Ajustado ao Meta-Modelo
```python
edge_efetivo = edge_bruto * prob_meta * confidence_regime
```

---

## 5. THRESHOLDS E REGRAS

| Parâmetro | Valor Inicial | Range de Otimização | Critério de Ajuste |
|-----------|---------------|---------------------|---------------------|
| edge_minimo | 0.04 | [0.02, 0.08] | Maximizar Sharpe no backtest |
| prob_minima | 0.15 | [0.10, 0.30] | Evitar apostas de variância extrema |
| prob_maxima | 0.85 | [0.70, 0.90] | Evitar apostas em favoritos caros |
| prob_meta_min | 0.60 | [0.50, 0.70] | Filtrar falsos positivos |
| liquidez_min_ratio | 1.5x stake | [1.0x, 3.0x] | Garantir execução sem mover mercado |
| blacklist_regimes | playoffs (mês 1-3) | Variável | Só apostar em regimes com histórico suficiente |

**Regra de ajuste:** Thresholds só podem ser reotimizados a cada mês, usando apenas dados até ao mês anterior (nunca com dados futuros).

---

## 6. FORMATO DO SINAL

```json
{
  "signal_id": "SIG-20261015-001",
  "timestamp_gerado": "2026-10-15T18:30:00Z",
  "timestamp_expiracao": "2026-10-15T18:35:00Z",
  "jogo": {
    "equipa_casa": "Boston Celtics",
    "equipa_fora": "LA Lakers",
    "data": "2026-10-15",
    "hora": "20:00"
  },
  "mercado": "moneyline",
  "selecao": "Boston Celtics",
  "odd_recomendada": 1.85,
  "prob_modelo": 0.58,
  "edge_estimado": 0.073,
  "prob_meta": 0.72,
  "confidence_score": 0.85,
  "stake_recomendada": 25.00,
  "unidade_banca": 0.025,
  "rationale": "Edge 7.3% em favorito moderado. Meta-modelo confiante (72%). Celtics em forma (eFG% 58% últimos 5 jogos). Lakers em back-to-back."
}
```

---

## 7. BACKLOG TÉCNICO
x] Documentar sistema de decisão de apostas
- [
- [ ] Implementar cálculo de edge em tempo real (a cada 5 minutos)
- [ ] Criar sistema de expiry de sinais (auto-cancelar se odd mudar > 2%)
- [ ] Implementar otimização de thresholds com Optuna (walk-forward)
- [ ] Criar blacklist dinâmica de regimes (baseada em performance histórica)
- [ ] Integrar com meta-modelo para scoring de confiança
- [ ] Implementar tracking de fill rate (quantos sinais foram realmente apostados)

---

## 8. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[05_Machine_Learning/INDEX]] → Modelos que fornecem probabilidades
- [[08_Risk_Management/INDEX]] → Kelly e sizing que consomem os sinais
- [[09_Execution_System/INDEX]] → Sistema que executa os sinais
- [[46_Meta_Labeling/INDEX]] → Meta-modelo de filtragem
