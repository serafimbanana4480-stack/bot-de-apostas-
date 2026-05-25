# Protocolo de A/B Testing e Significância Estatística de Modelos

**Versão:** 1.0.0  
**Status:** #status/active #priority/high  
**Área:** MLOps / Estatística

---

## 🎯 OBJETIVO
Definir o processo de validação de modelos concorrentes (Champion vs. Challenger) sob condições reais de mercado antes da promoção final de novos algoritmos de precificação de odds.

---

## 🛠️ MECANISMO DE ROTEAMENTO (DETALHADO)

Para evitar vazamento ou atribuição inconsistente de resultados, cada partida da NBA é deterministicamente atribuída a um dos fluxos do teste A/B:

```
Partida NBA (event_id)
         │
         ▼
SHA-256 / MD5 Hash
         │
         ▼
Módulo 1000 (0.000 - 1.000)
         ├── < Split Ratio (ex: 0.5) ──► Modelo Challenger (Aposta B)
         └── >= Split Ratio ───────────► Modelo Champion (Aposta A)
```

---

## 📊 TESTE-T SEQUENCIAL (WELCH)
O teste avalia se a média de PnL diário gerada pelo Challenger é estatisticamente diferente (e superior) à do Champion.

A estatística $t$ de Welch é calculada como:
$$t = \frac{\bar{X}_B - \bar{X}_A}{\sqrt{\frac{s^2_A}{n_A} + \frac{s^2_B}{n_b}}}$$

Onde:
- $\bar{X}_A, \bar{X}_B$: Retornos médios diários.
- $s^2_A, s^2_B$: Variância amostral dos retornos.
- $n_A, n_B$: Número de dias ou apostas avaliadas.

### Critério de Decisão de Promoção:
- **p-value < 0.05** AND **PnL Challenger > PnL Champion**: Modelo Challenger é aprovado e promovido via Validation Gate.
- **Caso Contrário**: O Challenger é retido em staging ou descartado.
