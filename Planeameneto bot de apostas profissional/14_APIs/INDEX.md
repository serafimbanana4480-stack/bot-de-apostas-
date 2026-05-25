# 14_APIs — INDEX

**ID:** `SEC-14` | **Fase:** #phase/1-7 | **Owner:** Lead Data Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar todas as APIs externas utilizadas pelo sistema: NBA, Betfair, fontes de odds, e quaisquer outras. Cada API deve ter rate limits, autenticação, endpoints, e estratégia de fallback.

---

## 2. NOTAS FUNDAMENTAIS

- [[NBA_API]] — NBA oficial API, endpoints, limites, dados disponíveis
- [[BETFAIR_API]] — Exchange API, licenciamento, ordens, custos
- [[API_INTERNAL]] — APIs FastAPI internas, endpoints, autenticação

---

## 3. APIs UTILIZADAS

| API | Dados | Custo | Rate Limit | Estado |
|-----|-------|-------|------------|--------|
| NBA API | Estatísticas, calendário, jogadores | Gratuito | N/A | Ativo |
| Basketball-Reference | Four Factors, avançadas | Gratuito (scraping) | Fair use | Ativo |
| Fanduel API | Odds live, Moneyline/Spread/Total | Gratuito | 100 req/min | Ativo |
| DraftKings API | Odds live, Moneyline/Spread/Total | Gratuito | 100 req/min | Ativo |
| BetMGM API | Odds live, Moneyline/Spread/Total | Gratuito | 50 req/min | Ativo |
| PointsBet API | Odds live, Moneyline/Spread/Total | Gratuito | 50 req/min | Ativo |
| Caesars API | Odds live, Moneyline/Spread/Total | Gratuito | 50 req/min | Ativo |
| Wynn API | Odds live, Moneyline/Spread/Total | Gratuito | 30 req/min | Ativo |
| BetRivers API | Odds live, Moneyline/Spread/Total | Gratuito | 30 req/min | Ativo |
| Betfair Exchange | Odds, execução | Gratuito (API) | 20 req/s | Fase 7+ |
| Odds-API (futuro) | Odds agregadas | Pago (~50€/mês) | 100 req/min | Fase 8+ |

---

## 4. BACKLOG TÉCNICO

- [ ] Criar wrapper Python para NBA API
- [ ] Implementar rate limiting com Redis
- [ ] Criar sistema de caching de respostas
- [ ] Documentar autenticação Betfair

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[04_Data_Engineering/INDEX]] → Pipelines que consomem APIs
- [[09_Execution_System/INDEX]] → Betfair API para execução
- [[09_Execution_System/INDEX]] → Betfair API para execução
