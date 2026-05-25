# PLANO_FINANCEIRO_6_MESES

**ID:** `BM-001` | **Fase:** #phase/1-6 | **Owner:** Product Owner | **Status:** #status/pending  
**Última Atualização:** `2026-05-13`

---

## 1. PREMISSAS

| Premissa | Valor | Fonte |
|----------|-------|-------|
| VPS base (Hetzner CX21) | 5€/mês | Hetzner pricing |
| VPS produção (Hetzner CX31) | 15€/mês | Hetzner pricing |
| Domínio + SSL | 15€/ano ≈ 1.25€/mês | Registar.pt |
| Dados NBA (gratuito) | 0€ | balldontlie API, nba_api |
| Dados Betfair (gratuito) | 0€ | Betfair Exchange API |
| Legal/consultoria (Mês 3) | 150€ | Consultor SRIJ |
| Dados premium Mês 6 | 50€ | The Odds API Standard |
| Telegram Bot hosting | 0€ | Incluído no VPS |
| Micro-banca inicial (Mês 4) | 500–1000€ | Capital próprio |

---

## 2. PROJEÇÃO DE CUSTOS OPERACIONAIS

| Mês | Fase | VPS | Dados | Legal/Tools | Total Opex | Notas |
|-----|------|-----|-------|-------------|-----------|-------|
| 1 | Fundações | 10€ | 0€ | 0€ | **10€** | VPS dev apenas |
| 2 | Modelo | 20€ | 0€ | 0€ | **20€** | VPS dev + staging |
| 3 | Shadow Mode | 35€ | 0€ | 150€ | **185€** | Consultor SRIJ + VPS prod |
| 4 | Micro-Banca | 35€ | 0€ | 0€ | **35€** | VPS prod |
| 5 | Estabilização | 35€ | 0€ | 30€ | **65€** | Ferramentas tipster |
| 6 | Expansão | 35€ | 50€ | 0€ | **85€** | Dados premium |
| **TOTAL** | | **170€** | **50€** | **180€** | **400€** | |

**Capital inicial necessário:** ~500–1500€ (400€ opex + 500–1000€ micro-banca + buffer)

---

## 3. PROJEÇÃO DE RECEITA — TIPSTER

### 3.1 Estrutura de Subscrição (Alinhado com Plano Definitivo)
| Tier | Preço/Mês | Conteúdo | Máximo Subscritores |
|------|-----------|----------|---------------------|
| Único | 29€ | Todos os sinais via Telegram + edge estimado + CLV histórico | 100 |

### 3.2 Cenários de MRR (Mês 5-6)
| Cenário | Subscritores | MRR | ROI Tipster |
|---------|--------------|-----|-------------|
| Pessimista | 20 | **580€** | Cobre custos |
| Realista | 50 | **1.450€** | ~1.000€ lucro |
| Otimista | 100 | **2.900€** | ~2.500€ lucro |

### 3.3 Projeção de Crescimento de Subscritores
| Mês | Fase | Meta Subscritores | MRR Est. |
|-----|------|------------------|----------|
| 4 | Lançamento soft | 5 | 145€ |
| 5 | Estabilização | 20 | 580€ |
| 6 | Crescimento | 50 | 1.450€ |
| 9 | Escala | 100 | 2.900€ |
| 12 | Maturidade | 100 (cap) | 2.900€ |

---

## 4. RECEITA DE APOSTAS (PROJEÇÃO CONSERVADORA)

| Fase | Banca | ROI Alvo | PnL Mensal Est. | Notas |
|------|-------|----------|-----------------|-------|
| Mês 4 | 500€ | 3% | 15€ | Micro-banca validação |
| Mês 5 | 750€ | 3% | 22€ | Ajustes com dados reais |
| Mês 6 | 1.000€ | 4% | 40€ | Modelo estabilizado |
| Mês 9 | 3.000€ | 5% | 150€ | Escala pós-validação |
| Mês 12 | 8.000€ | 5% | 400€ | Banca crescida |

**⚠️ Conservador por design.** ROI real depende de edge validado em produção.

---

## 5. BREAK-EVEN

| Tipo | Threshold | Data Esperada |
|------|-----------|---------------|
| Opex (custos infra) | 6 subscritores Base | Mês 4 |
| Opex + capital pessoal | 20 subscritores pagos | Mês 5 |
| Break-even total (inclui banca) | 50 subscritores pagos + ROI 3% | Mês 6 |

---

## 6. RISCOS FINANCEIROS

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Modelo sem edge real | Médio | Alto | Shadow mode 1 mês antes de dinheiro real |
| Subscritores abaixo do esperado | Médio | Médio | Custos baixos permitem operar sem tipster |
| Betfair limitar conta | Baixo | Alto | Multi-casa (Pinnacle, SBK) desde o início |
| Mudança regulatória SRIJ | Baixo | Médio | Consultor legal no Mês 3 |
| Drawdown micro-banca > 30% | Médio | Médio | Stop loss automático a -20% |

---

## 7. CASH FLOW RESUMIDO (6 MESES)

| Mês | Saídas (€) | Entradas Tipster (€) | Entradas Apostas (€) | Saldo Mês (€) | Saldo Acum. (€) |
|-----|-----------|---------------------|---------------------|--------------|----------------|
| 1 | -10 | 0 | 0 | -10 | -10 |
| 2 | -20 | 0 | 0 | -20 | -30 |
| 3 | -185 | 0 | 0 | -185 | -215 |
| 4 | -535 | 145 | 15 | -375 | -590 |
| 5 | -65 | 580 | 22 | +537 | -53 |
| 6 | -85 | 1.450 | 40 | +1.405 | +1.352 |

*Cenário Realista. Inclui 500€ de banca no Mês 4.*

---

## 8. BACKLOG

- [ ] Actualizar projeções com dados reais (mensal a partir do Mês 4)
- [ ] Criar planilha de cash flow detalhada (Google Sheets / LibreOffice)
- [ ] Documentar critérios de investimento para escala de banca
- [ ] Implementar tracking automático de MRR no dashboard
- [ ] Definir política de reinvestimento de lucros (% banca vs % tipster)

---

## 9. LINKS CRUZADOS

- [[02_Business_Model/INDEX]] ← Secção mãe
- [[35_Financial_Tracking/INDEX]] → Tracking real de PnL e custos
- [[36_KPIs/INDEX]] → KPIs financeiros
- [[19_Telegram_System/INDEX]] → Sistema tipster e subscrições
- [[22_Real_Money_Operations/INDEX]] → Operações com banca real
