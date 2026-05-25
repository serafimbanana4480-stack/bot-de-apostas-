# 09_Execution_System — INDEX

**ID:** `SEC-09` | **Fase:** #phase/4-8 | **Owner:** Operations Lead + DevOps | **Status:** #status/active

---

## 1. OBJETIVO

Transformar sinais gerados pelo motor de value em apostas reais (ou simuladas), garantindo que a execução reflete fielmente o plano de risco, e documentando todas as divergências.

O sistema de execução tem **3 fases de maturidade**, nunca saltáveis:

---

## 2. NOTAS FUNDAMENTAIS

- [[EXECUCAO_MANUAL]] — Fase 1: Sinais via Telegram, operador coloca manualmente
- [[ONE_CLICK_BETTING]] — Fase 2: Deep links para Betfair, pré-preenchimento
- [[EXECUCAO_AUTOMATICA]] — Fase 3: Betfair API, limit orders, gestão de ordens
- [[RECONCILIACAO]] — Verificação de que execução = sinal
- [[SLIPPAGE_TRACKING]] — Medição real de slippage vs simulado
- [[LATENCIA_EXECUCAO]] — Medição de tempo entre sinal e execução
- [[FILL_PROBABILITY]] — Probabilidade de preenchimento da ordem

---

## 3. FASES DE EXECUÇÃO

### FASE 1: Sinais Manuais (Mês 1-4)
```
Motor de value → Sinal aprovado
                    ↓
              Telegram Bot + Email
                    ↓
              Operador lê o sinal
                    ↓
              Coloca aposta manualmente na Betfair
                    ↓
              Confirmação no Telegram (screenshot ou comando)
                    ↓
              Sistema regista a aposta na base de dados
```

**Especificação do Sinal Telegram:**
```
🎯 SINAL APROVADO #SIG-20261015-001
🏀 Boston Celtics vs LA Lakers
📊 Mercado: Moneyline | Celtics
💰 Odd: 1.85 (mínima aceitável: 1.83)
📈 Edge: 7.3% | Prob: 58%
💵 Stake: €25.00 (2.5% da banca)
⏰ Expira em: 5 minutos
⚠️ NÃO APOSTAR se odd < 1.83
```

### FASE 2: One-Click via Deep Links (Mês 5-8, opcional)
```
Sinal aprovado → Web app gera deep link Betfair
                    ↓
              Operador clica no link
                    ↓
              App Betfair abre com slip pré-preenchido
                    ↓
              Operador confirma com 1 toque
```

**Deep Link Betfair:**
```
https://www.betfair.com/exchange/plus/{market_id}/?price={odd}&size={stake}&selection={selection_id}
```

### FASE 3: Execução Automática (Mês 7+, só após 6 meses de lucro)
```
Sinal aprovado → API Betfair
                    ↓
              Limit Order com preço ligeiramente melhor
                    ↓
              Timeout 60 segundos
                    ↓
              Se preenchido → confirmação
              Se não preenchido → cancelar ou aceitar worse price (threshold)
              Se odd move > 2% contra → cancelar e gerar novo sinal
```

---

## 4. REGRAS DE EXECUÇÃO

| Regra | Fase 1 | Fase 2 | Fase 3 |
|-------|--------|--------|--------|
| Aceitar odd pior? | Nunca | Até -2% | Até -2% (automático) |
| Tempo máximo após sinal | 5 min | 3 min | 30 seg |
| Confirmação obrigatória | Sim (manual) | Sim (1 clique) | Automática |
| Partial fill handling | N/A | N/A | Aceitar se ≥ 80% |
| Reconciliation | Manual | Automático | Automático |

---

## 5. RECONCILIAÇÃO

Cada aposta real deve ser reconciliada com o sinal original:

```python
class BetReconciliation:
    signal_id: str
    odd_signal: float
    odd_executed: float
    slippage: float
    stake_signal: float
    stake_executed: float
    stake_diff_pct: float
    time_to_execution_seconds: float
    fill_status: str  # FILLED, PARTIAL, REJECTED, EXPIRED
    
    def validate(self) -> bool:
        if self.slippage > 0.02:  # 2%
            return False  # Alerta de execução ruim
        if self.stake_diff_pct > 0.10:  # 10%
            return False  # Divergência de sizing
        return True
```

**Relatório diário obrigatório:**
- Número de sinais gerados vs executados
- Slippage médio e máximo
- Tempo médio de execução
- Razões de rejeição

---

## 6. RISCOS DE EXECUÇÃO

| Risco | Mitigação | Fase |
|-------|-----------|------|
| Latência alta (odd muda antes de executar) | Sinais com expiry 5 min; execução rápida | Todas |
| Slippage excessivo | Limit orders (Fase 3); rejeição manual (Fase 1-2) | Todas |
| Erro humano (operador erra equipa/odd) | Checklist SOP-001; confirmação dupla | Fase 1 |
| Falha de API | Fallback para manual; circuit breaker Delta | Fase 3 |
| Execução parcial não detetada | Reconciliation automático | Fase 2-3 |
| Ban de conta Betfair | Uso de API licenciada; limites de frequência | Fase 3 |

---

## 7. BACKLOG TÉCNICO

- [x] Documentar CLI funcional para operações diárias
- [ ] Implementar Telegram Bot para envio de sinais (Fase 1)
- [ ] Criar web app simples para deep links (Fase 2)
- [ ] Integrar Betfair API para execução automática (Fase 3)
- [ ] Implementar reconciliation engine
- [ ] Criar SOP de execução manual (Fase 1)
- [ ] Implementar tracking de slippage real
- [ ] Criar dashboard de execução (fill rate, latência)

---

## 8. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[07_Value_Detection/INDEX]] → Motor que gera sinais
- [[08_Risk_Management/INDEX]] → Sizing e circuit breakers
- [[19_Telegram_System/INDEX]] → Delivery de sinais
- [[44_Exchange_Execution/INDEX]] → Execução em exchanges
- [[44_Exchange_Execution/INDEX]] → Execução em exchanges
