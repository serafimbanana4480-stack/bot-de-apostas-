# CENARIOS_FALHA — Mitigacao

**ID:** `FS-001` | **Fase:** #phase/1-15 | **Owner:** Chief Systems Architect | **Status:** #status/pending

---

## 1. CENARIO: BANCA A ZERO

| Aspecto | Detalhe |
|---------|---------|
| Causa | Drawdown > 100% (impossivel com limites, mas...) |
| Mitigacao | Kelly fracionado + limites de exposicao |
| Plano de contingencia | Parar operacao, revisar modelo, reiniciar com micro-banca |

---

## 2. CENARIO: MODELO PERDE EDGE

| Aspecto | Detalhe |
|---------|---------|
| Causa | Regime change, dados deteriorados |
| Deteccao | CLV 7d < 0% |
| Mitigacao | Circuit breaker Gamma + retraining triggered |
| Contingencia | Shadow mode com novo modelo; se melhorar, promover |

---

## 3. CENARIO: BAN DE CONTA BETFAIR

| Aspecto | Detalhe |
|---------|---------|
| Causa | Uso excessivo de API, violacao de ToS |
| Mitigacao | Rate limiting, API oficial licenciada |
| Contingencia | Mudar para outra exchange (Smarkets, Matchbook) |

---

## 4. CENARIO: PERDA DE DADOS

| Aspecto | Detalhe |
|---------|---------|
| Causa | Falha de disco, ataque ransomware |
| Mitigacao | Backups diarios para S3, snapshots PostgreSQL |
| Contingencia | Restore a partir do backup mais recente |

---

## 5. BACKLOG

- [ ] Documentar DR plan completo
- [ ] Testar restore de backup
- [ ] Criar runbooks para cada cenario

---

## 6. LINKS CRUZADOS

- [[28_Failure_Scenarios/INDEX]] ← Secao mae
- [[26_Runbooks/INDEX]] → Runbooks de resposta
