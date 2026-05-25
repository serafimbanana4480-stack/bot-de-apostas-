# SOP_EXECUCAO_MANUAL — Procedimento Operacional

**ID:** `SOP-001` | **Fase:** #phase/4 | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. PRE-OPERACAO (15 min antes)

- [ ] Verificar se sistema esta online (dashboard Grafana)
- [ ] Confirmar que nao ha circuit breakers activos
- [ ] Verificar banca disponivel na Betfair
- [ ] Confirmar que Telegram esta a receber notificacoes

---

## 2. DURANTE OPERACAO

### Receber Sinal
1. Abrir notificacao Telegram imediatamente
2. Ler odd minima aceitavel
3. Abrir Betfair Exchange
4. Procurar mercado indicado

### Validar e Colocar
1. Verificar odd atual >= odd minima
2. Verificar liquidez suficiente (volume > stake * 1.5)
3. Inserir stake exacta (nao arredondar!)
4. Confirmar aposta

### Confirmar
1. Tirar screenshot (opcional mas recomendado)
2. Enviar `/confirm <signal_id>` no Telegram
3. Registar odd obtida se diferente da sinalizada

---

## 3. POS-OPERACAO

- [ ] Reconciliar apostas do dia com sinais gerados
- [ ] Verificar se ha apostas nao confirmadas
- [ ] Enviar resumo diario (se aplicavel)

---

## 4. EM CASO DE PROBLEMA

| Problema | Accao |
|----------|-------|
| Odd < minima | NAO APOSTAR. Enviar `/skip <id> reason:odd_moved` |
| Erro na Betfair | Tentar novamente em 30s. Se persistir, notificar |
| Sinal expirou | NAO APOSTAR. Sinais expirados sao invalidos |
| Duvida sobre mercado | NAO APOSTAR. Pedir clarificacao |

---

## 5. TEMPO MAXIMO POR ETAPA

| Etapa | Tempo Maximo | Justificativa |
|-------|-------------|---------------|
| Receber sinal | 30 segundos | O mercado move-se rapidamente |
| Validar odd | 15 segundos | Cada segundo conta para odds em movimento |
| Colocar aposta | 45 segundos | Inclui navegacao Betfair |
| Confirmar | 30 segundos | Screenshot + comando Telegram |
| **Total** | **2 min 30 seg** | Target: < 3 min por sinal |

**Nota:** Se ultrapassar 3 minutos, revalidar a odd antes de apostar.

---

## 6. EXEMPLO DE FLUXO COMPLETO

### Cenário 1: Sinal Padrão (Odd Disponível)

```
[14:32:15] Telegram: "🎯 SINAL VBQ-2024-0315-001 | Lakers ML @ 1.85 | Stake: 12.50€"
[14:32:20] Operador abre Betfair Exchange
[14:32:25] Encontra mercado "Moneyline - Lakers vs Celtics"
[14:32:30] Odd atual: 1.84 (>= 1.85? NÃO — mas dentro de 2% slippage)
[14:32:35] Verifica liquidez: 2,500€ disponível (>= 12.50€ * 1.5 = 18.75€ ✓)
[14:32:40] Insere stake: 12.50€ (exato, não arredonda)
[14:32:45] Confirma aposta na Betfair
[14:32:50] Tira screenshot do slip
[14:32:55] Telegram: "/confirm VBQ-2024-0315-001 odd_executed=1.84"
[14:33:00] Sistema registra aposta com odd real
```

### Cenário 2: Odd Movimentou (Não Executar)

```
[14:32:15] Telegram: "🎯 SINAL VBQ-2024-0315-002 | Over 215.5 @ 1.90 | Stake: 10.00€"
[14:32:20] Operador abre Betfair
[14:32:25] Odd atual: 1.75 (>= 1.90? NÃO — slippage 7.9% > 2%)
[14:32:30] Telegram: "/skip VBQ-2024-0315-002 reason:odd_moved_below_threshold"
[14:32:35] NÃO APOSTAR. Sinal expirado.
```

### Cenário 3: Mercado Fechou

```
[14:32:15] Telegram: "🎯 SINAL VBQ-2024-0315-003 | Celtics +5.5 @ 1.95"
[14:32:20] Betfair: "Market Suspended" (jogo já começou)
[14:32:25] Telegram: "/skip VBQ-2024-0315-003 reason:market_closed"
[14:32:30] NÃO TENTAR ABRIR OUTRO MERCADO. Sinal expirou.
```

---

## 7. REGRAS DE OURO

1. **Nunca apostar sem sinal aprovado.**
2. **Nunca arredondar stake.** Kelly calculou 12.47€? Aposte 12.47€, não 12.50€.
3. **Nunca apostar se odd < odd mínima.** Mesmo que "pareça boa".
4. **Nunca apostar em mercado diferente do indicado.**
5. **Sempre confirmar no Telegram em < 1 minuto após aposta.**
6. **Sempre tirar screenshot se for a primeira vez.**
7. **Nunca apostar se não há liquidez suficiente.**
8. **Nunca apostar se estiver em dúvida.** Skip é sempre preferível a erro.

---

## 8. METRICAS DE QUALIDADE DO OPERADOR

| Métrica | Target | Como Medir |
|---------|--------|------------|
| Tempo médio de execução | < 2.5 min | Timestamp sinal vs /confirm |
| Slippage médio | < 1% | (odd_sinal - odd_executado) / odd_sinal |
| Taxa de skip válido | < 20% | Skips por odd_moved / total sinais |
| Taxa de erro | < 2% | Apostas em mercado/errada / total |
| Confirmação em < 1 min | > 95% | Timestamp aposta vs /confirm |

---

## 9. BACKLOG

- [x] Documentar fluxo completo pré/durante/pós operação
- [x] Definir tempos máximos por etapa
- [x] Documentar 3 cenários práticos (padrão, skip, fechado)
- [x] Definir 8 regras de ouro
- [x] Documentar métricas de qualidade do operador
- [ ] Treinar operador com este SOP
- [ ] Criar versão em PDF para impressão
- [ ] Revisar mensalmente

---

## 10. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
- [[09_Execution_System/EXECUCAO_MANUAL]] → Detalhes técnicos
- [[08_Risk_Management/KELLY_FRACIONADO]] → Cálculo de stakes
- [[09_Execution_System/ONE_CLICK_BETTING]] → Execução semi-automática
