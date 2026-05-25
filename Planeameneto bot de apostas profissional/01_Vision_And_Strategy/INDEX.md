# 01_Vision_And_Strategy — INDEX

**ID:** `SEC-01` | **Fase:** Todas | **Owner:** Chief Systems Architect | **Status:** #status/active

---

## 1. OBJETIVO DESTA SECÇÃO

Documentar a visão estratégica do projeto, os princípios de decisão que governam todas as escolhas técnicas e de negócio, e a filosofia central que impede a sobre-engenharia prematura.

---

## 2. NOTAS FUNDAMENTAIS

- [[FILOSOFIA_MVP]] — Filosofia central: MVP simples → validação → lucro real → automação → escala → sofisticação
- [[DECISOES_IRREVERSIVEIS]] — Decisões que, uma vez tomadas, não podem ser revertidas sem custo massivo
- [[TRADE_OFFS_ARQUITETURAIS]] — Registo de todos os trade-offs técnicos e justificações
- [[ESTADO_MENTAL_OPERACIONAL]] — Como o operador e a equipa devem pensar sobre o sistema
- [[CRITERIOS_SUCESSO_PROJETO]] — O que significa "sucesso" em cada fase

---

## 3. PRINCIPIOS DE DECISÃO

Toda a decisão técnica ou de negócio deve responder a estas 5 perguntas antes de ser aprovada:

1. **Valida ou impede o edge?** — Se impede, rejeitada.
2. **Reduz ou aumenta o time-to-validation?** — Se aumenta, precisa de justificação extraordinária.
3. **Aumenta ou reduz a variância do sistema?** — Aumentos de variância precisam de mitigação.
4. **Quanto custa em tempo e dinheiro?** — Qualquer custo > 1 semana ou > 200€ precisa de aprovação explícita.
5. **Pode ser revertido?** — Decisões irreversíveis precisam de consenso.

---

## 4. BACKLOG ESTRATÉGICO

| ID | Item | Prioridade | Fase Alvo | Risco |
|----|------|------------|-----------|-------|
| STR-001 | Manter foco NBA até validação completa | Critical | 1-6 | Alto se desviar |
| STR-002 | Nunca prometer retornos aos subscritores | Critical | 3-10 | Legal |
| STR-003 | Reinvestir 50% dos lucros em dados premium | High | 5+ | Médio |
| STR-004 | Documentar cada decisão técnica | High | Todas | Baixo |
| STR-005 | Preparar saída (exit strategy) desde o início | Medium | 8+ | Baixo |

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[02_Business_Model/INDEX]] → Modelo de negócio e monetização
- [[16_Compliance/INDEX]] → Restrições legais que moldam a estratégia
