# MICRO_BANCA_PROTOCOL — Protocolo de Micro-Banca

**ID:** `RM-004` | **Fase:** #phase/3 | **Owner:** Risk Manager | **Status:** #status/active

---

## 1. OBJETIVO

Definir protocolo para operar com micro-banca (banca pequena) durante fase de validação inicial.

---

## 2. CONCEITO

Micro-banca é uma banca pequena (ex: €100-500) usada para validar o sistema em produção antes de escalar.

---

## 3. CONFIGURAÇÃO

```python
MICRO_BANKROLL = 200  # €200 para micro-banca
MICRO_DURATION_WEEKS = 4  # 4 semanas de validação
MIN_STAKE_EUR = 1  # Mínimo €1 por aposta
MAX_STAKE_PCT = 0.05  # Máximo 5% por aposta
```

---

## 4. CÁLCULO DE STAKE

```python
def micro_bank_stake(prob, odd, bankroll):
    """
    Calcula stake para micro-banca.
    
    Ajusta para stake mínimo de €1.
    """
    kelly_stake_pct = fractional_kelly(prob, odd, 0.25)  # Kelly 0.25 (conservador)
    kelly_stake_pct = min(kelly_stake_pct, MAX_STAKE_PCT)
    
    stake = bankroll * kelly_stake_pct
    
    # Ajustar para mínimo €1
    stake = max(stake, MIN_STAKE_EUR)
    
    return stake
```

---

## 5. OBJETIVOS DA MICRO-BANCA

| Objetivo | Critério | Sucesso |
|----------|----------|---------|
| ROI positivo | > 0% | ✅ |
| CLV positivo | > 1% | ✅ |
| Sem bugs técnicos | 0 erros | ✅ |
| Volume suficiente | > 50 apostas | ✅ |

---

## 6. ESCALA

Se micro-banca bem-sucedida:

```python
def scale_from_micro(micro_bankroll, target_bankroll):
    """
    Calcula fator de escala.
    """
    scale_factor = target_bankroll / micro_bankroll
    return scale_factor

# Exemplo: €200 → €2000 = fator 10x
```

---

## 7. CRITÉRIOS

- **ROI > 0%** após 4 semanas
- **Mínimo 50 apostas** executadas
- **Sem erros críticos** de execução
- **CLV > 1%** consistente

---

## 8. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]]
- [[22_Real_Money_Operations]]
