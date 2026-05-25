# DISCIPLINA_OPERACIONAL — Psicologia das Apostas

**ID:** `BP-001` | **Fase:** #phase/4 | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. REGRAS DE OURO

1. **O sistema decide, nao o operador.** O operador so executa.
2. **Nunca apostar por emocao.** Tilt e o inimigo numero 1.
3. **Nunca aumentar stake para "recuperar" perdas.**
4. **Nunca apostar sem sinal aprovado.**
5. **Manter diario de operacoes.**

---

## 2. SINAIS DE TILT

| Sinal | Accao |
|-------|-------|
| Operador quer "justificar" uma aposta fora do sistema | Pausa imediata + revisao |
| Operador altera stake por "intuicao" | Pausa + conversa |
| Operador persegue perdas | Circuit breaker Beta ativado |
| Operador esta ansioso/irritado | Pausa de 24h |

---

## 3. OVERRIDE MANUAL

So permitido em casos excepcionais:
- Falha tecnica do sistema
- Lesao confirmada apos sinal (informacao nova)

**Processo:**
1. Documentar razao no audit log
2. Obter aprovacao do Risk Manager
3. Registar aposta como "manual override"

---

## 4. BACKLOG

- [ ] Criar checklist diario de estado mental
- [ ] Documentar casos de override
- [ ] Implementar pausa automatica apos sequencia de perdas

---

## 5. LINKS CRUZADOS

- [[38_Betting_Psychology/INDEX]] ← Secao mae
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Pausas automaticas
