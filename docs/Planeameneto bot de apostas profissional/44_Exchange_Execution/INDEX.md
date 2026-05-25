# 44_Exchange_Execution — INDEX

**ID:** `SEC-44` | **Fase:** #phase/7-12 | **Owner:** Operations Lead + Dev | **Status:** #status/active

---

## 1. OBJETIVO

Especificar a execução automática via Betfair API: gestão de ordens, slippage, latência, e reconciliação. Só ativar após 6 meses de lucro consistente.

---

## 2. TIPOS DE ORDEM

| Tipo | Uso | Risco |
|------|-----|-------|
| Limit Order | Padrão; colocar a odd alvo ou melhor | Não preenchimento |
| Market Order | Emergência; aceitar odd atual | Slippage imprevisível |
| Stop Order | Proteção de posição (futuro) | Gapping |

---

## 3. GESTÃO DE ORDENS

```
1. Sinal aprovado → API Betfair
2. Verificar liquidez na odd alvo
3. Colocar Limit Order a odd alvo - 0.01 (ligeiramente melhor)
4. Timeout: 60 segundos
5. Se preenchido → registo e confirmação
6. Se não preenchido:
   ├── Tentar odd alvo (0% slippage aceitável)
   ├── Tentar odd alvo + 1% (se configurado)
   └── Cancelar e gerar alerta
```

---

## 4. DOCUMENTAÇÃO DE REFERÊNCIA

- [[BETFAIR_EXECUTION]] — Execução automática via API (arquitetura completa)
- [[BETFAIR_API_EXECUTION]] — Integração com Betfair API (código e fluxo)
- [[LATENCY_OPTIMIZATION]] — Otimização de latência e proximity hosting
- [[EXCHANGE_VS_BOOKMAKERS]] — Diferenças fundamentais entre exchanges e bookmakers
- [[EXCHANGE_TRADING]] — Estratégias de trading (back/lay, hedging, trading out)
- [[LIQUIDITY_DEPTH]] — Liquidez e profundidade de mercado
- [[POSITION_MANAGEMENT]] — Gestão de posição (unmatched bets, partial fills)
- [[EXCHANGE_COSTS]] — Custos de exchange (comissão, premium charges)

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[09_Execution_System/INDEX]] → Execução geral
- [[14_APIs/BETFAIR_API]] ← API Betfair base
