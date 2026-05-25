# CLV (Closed Line Value) — A Métrica Suprema

**ID:** `QUANT-001` | **Área:** #area/quant | **Fase:** #phase/1-15 | **Status:** #status/active

---

## 1. O QUE É

O **Closed Line Value (CLV)** mede a diferença percentual entre a odd em que apostámos e a odd de fecho do mercado (tipicamente Pinnacle).

Se apostarmos a 2.10 e o mercado fecha a 2.00, o nosso CLV é:
```
CLV = (2.10 / 2.00) - 1 = 5.0%
```

Significa que o mercado reconheceu o nosso edge e moveu as odds contra nós. **Um CLV positivo consistente é a única prova irrefutável de que temos vantagem.**

---

## 2. PORQUE EXISTE

O mercado de apostas é eficiente a longo prazo. A odd de fecho da Pinnacle é considerada o melhor preditor não-enviesado do outcome real. Se conseguimos apostar a odds superiores às odds de fecho consistentemente, estamos a "comprar" probabilidades subvalorizadas.

**O CLV não pode ser manipulado pelo resultado da aposta.** Uma aposta pode perder mas ter CLV positivo (foi boa decisão). Uma aposta pode ganhar mas ter CLV negativo (foi má decisão mas tivemos sorte).

---

## 3. PORQUE FOI ESCOLHIDO COMO MÉTRICA PRINCIPAL

| Alternativa | Problema |
|-------------|----------|
| ROI simples | Enviesado por variância de curto prazo; não distingue skill de luck |
| Yield | Não considera o valor da odd relativa ao mercado |
| Win rate | Ignora completamente o preço pago |
| Profit/loss absoluto | Depende do stake e da banca |

O CLV é independente do stake, do resultado individual, e da variância de curto prazo. É a métrica que hedge funds quantitativos usam para validar edge.

---

## 4. COMO CALCULAR

### 4.1 CLV por aposta
```python
def calculate_clv(odd_taken: float, odd_close: float) -> float:
    """
    odd_taken: odd em que a aposta foi colocada
    odd_close: odd de fecho do mercado (Pinnacle)
    """
    return (odd_taken / odd_close) - 1.0
```

### 4.2 CLV Médio (janela móvel)
```python
def rolling_clv(clv_series: pd.Series, window: int = 50) -> pd.Series:
    return clv_series.rolling(window=window).mean()
```

### 4.3 True CLV (multi-casa)
```python
def calculate_true_clv(odd_taken: float, odd_close_pinny: float, 
                       odd_close_betfair: float, odd_close_other: float) -> float:
    # Média das odds de fecho disponíveis
    avg_close = np.mean([odd_close_pinny, odd_close_betfair, odd_close_other])
    return (odd_taken / avg_close) - 1.0
```

### 4.4 CLV Ajustado ao Overround
```python
def clv_adjusted_for_overround(odd_taken: float, odd_close_raw: float, overround: float) -> float:
    # Remover overround da odd de fecho para obter "fair close"
    prob_close = 1 / odd_close_raw
    prob_fair = prob_close / overround
    odd_fair = 1 / prob_fair
    return (odd_taken / odd_fair) - 1.0
```

---

## 5. THRESHOLDS E DECISÕES

| CLV Médio (últimas 50 apostas) | Interpretação | Ação |
|-------------------------------|---------------|------|
| > 3.0% | Edge forte | Manter stakes normais; considerar aumento gradual |
| 1.5% - 3.0% | Edge confirmado | Operar normalmente |
| 0.5% - 1.5% | Edge marginal | Reduzir stakes 25%; investigar model drift |
| 0% - 0.5% | Edge zero | Reduzir stakes 50%; pausar novas apostas |
| < 0% | Sem edge / Negative edge | PARAR TUDO. Circuit breaker ativado. Revisão obrigatória. |

---

## 6. INTERVALO DE CONFIANÇA DO CLV

Usar block bootstrap para calcular IC 95%:
```python
def bootstrap_clv_ci(clv_series: pd.Series, n_bootstrap: int = 10000, 
                     block_size: int = 10, confidence: float = 0.95) -> tuple:
    n = len(clv_series)
    bootstrap_means = []
    
    for _ in range(n_bootstrap):
        # Block resampling para preservar autocorrelação temporal
        blocks = []
        for _ in range(n // block_size + 1):
            start = np.random.randint(0, n - block_size + 1)
            blocks.append(clv_series.iloc[start:start+block_size])
        sample = pd.concat(blocks)[:n]
        bootstrap_means.append(sample.mean())
    
    lower = np.percentile(bootstrap_means, (1-confidence)/2 * 100)
    upper = np.percentile(bootstrap_means, (1+confidence)/2 * 100)
    return lower, upper
```

**Regra:** Se o IC 95% do CLV incluir 0, não há evidência estatística de edge.

---

## 7. CLV POR REGIME

O CLV não é uniforme. Deve ser segmentado:

| Regime | Porque Segmentar |
|--------|------------------|
| Casa vs Fora | O modelo pode ter edge num e não no outro |
| Grande favorito (prob > 65%) | Liquidez diferente; movimento de odds diferente |
| Equilibrado (35-65%) | Mercado mais eficiente; edge mais difícil |
| Underdog (< 35%) | Variância alta; edge pode existir mas não ser sustentável |
| Back-to-back | Contexto físico muda a eficiência do modelo |
| Segunda-feira vs Sexta | Padrões de mercado diferentes |

**Dashboard obrigatório:** CLV médio por regime em [[37_CLV_Analytics/INDEX]].

---

## 8. ESTRATÉGIA DE ODDS DE FECHO (C-008)

### 8.1 Problema: Pinnacle Não Disponível

A API Pinnacle é paga, restrita geograficamente, e não disponível para apostadores em Portugal. Repositórios públicos de closing odds são limitados.

### 8.2 Solução: Estratégia Híbrida

**Opção 1 (Primária): Betfair Starting Price (SP)**
- **Custo:** Gratuito via Betfair Exchange API
- **Vantagem:** Disponível para todos os mercados Betfair
- **Limitação:** SP não é exatamente closing line, mas é um proxy razoável
- **Implementação:** Usar Betfair SP como proxy de closing line para CLV calculation

**Opção 2 (Secundária): The Odds API Standard**
- **Custo:** $9/mês (~8€) para plano Standard
- **Vantagem:** Fornece closing odds de múltiplas casas
- **Limitação:** Cobertura limitada para NBA
- **Implementação:** Usar como validação cruzada do Betfair SP

**Custo adicional ao PLANO_FINANCEIRO:**
- Mês 1-3: 0€ (apenas Betfair SP)
- Mês 4-6: 8€/mês (The Odds API Standard para validação)
- **Total adicional:** 48€/6 meses

### 8.3 Implementação

```python
def calculate_clv_hybrid(odd_taken: float, betfair_sp: float, 
                        odds_api_close: float = None) -> float:
    """
    Calcula CLV usando estratégia híbrida Betfair SP + Odds API.
    
    Args:
        odd_taken: odd em que a aposta foi colocada
        betfair_sp: Betfair Starting Price (proxy de closing)
        odds_api_close: closing odds do The Odds API (opcional, validação)
    """
    # Primário: usar Betfair SP
    clv = (odd_taken / betfair_sp) - 1.0
    
    # Secundário: validação cruzada se disponível
    if odds_api_close:
        clv_validation = (odd_taken / odds_api_close) - 1.0
        # Se diferença > 2%, usar média ponderada
        if abs(clv - clv_validation) > 0.02:
            clv = (clv + clv_validation) / 2
    
    return clv
```

### 8.4 Riscos e Limitações

1. **Betfair SP não é closing line:** SP é calculado no momento do off, não no closing. Diferença típica: 0.5-1.5%.
2. **Latência:** Se demoramos 5 min a colocar aposta, a odd pode já ter mudado. CLV deve ser medido contra a odd no momento da execução.
3. **Discrepância de mercados:** Betfair pode ter liquidez diferente de Pinnacle para certos jogos.

---

## 9. DECOMPOSIÇÃO DE PnL

```
PnL_total = PnL_skill + PnL_luck + PnL_market

PnL_skill = turnover * CLV_avg * (1 - comissão)
PnL_luck = PnL_total - PnL_skill - PnL_market
PnL_market = efeito de movimentos de mercado não capturados pelo CLV
```

Implementar em [[37_CLV_Analytics/INDEX]].

---

## 10. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]] ← Secção mãe
- [[06_Backtesting/INDEX]] → Validação temporal do CLV
- [[37_CLV_Analytics/INDEX]] → Dashboard e análise detalhada
- [[47_Shadow_Betting/INDEX]] → True CLV multi-casa
