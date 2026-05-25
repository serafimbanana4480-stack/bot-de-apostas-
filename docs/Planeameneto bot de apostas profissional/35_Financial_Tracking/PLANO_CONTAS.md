# PLANO_CONTAS — Plano de Contas

**ID:** `FIN-003` | **Fase:** Todas | **Owner:** Financial Analyst | **Status:** #status/pending

---

## 1. OBJETIVO

Definir o plano de contas para tracking financeiro.

---

## 2. PLANO DE CONTAS

### 2.1 Receitas
| Código | Conta | Descrição |
|--------|-------|-----------|
| 7.1 | Subscrições Tipster | Receita mensal de subscritores (29€/mês) |
| 7.2 | Apostas Próprias | Lucro de apostas com bankroll própria |
| 7.3 | Serviços Consultoria | Consultoria pontual (futuro) |
| 7.9 | Outras Receitas | Juros, reembolsos, etc. |

### 2.2 Despesas Operacionais
| Código | Conta | Descrição |
|--------|-------|-----------|
| 6.1 | Infraestrutura | VPS, domínio, certificados SSL |
| 6.2 | Dados e APIs | Odds premium, dados desportivos (futuro) |
| 6.3 | Comunicação | Telegram Bot, SendGrid, SMS |
| 6.4 | Software e Ferramentas | GitHub, Grafana Cloud (se aplicável) |
| 6.5 | Legal e Compliance | Advogado, consultoria fiscal |
| 6.6 | Marketing | Ads, landing page, SEO |

### 2.3 Despesas Financeiras
| Código | Conta | Descrição |
|--------|-------|-----------|
| 6.7 | Taxas de Pagamento | Stripe/PayPal (tipicamente 2.9% + 0.30€) |
| 6.8 | Impostos | IVA, IRS (conforme regime fiscal) |

### 2.4 Tracking
- Utilizar planilha `PLANILHA_PnL.md` para tracking mensal
- Reconciliação mensal obrigatória
- Relatório fiscal trimestral

## 3. BACKLOG

- [x] Definir categorias de receitas
- [x] Definir categorias de despesas
- [ ] Configurar integração contabilística (Fase 5+)
- [ ] Definir relatórios fiscais (Fase 5+, com contabilista)

---

## 4. LINKS CRUZADOS

- [[35_Financial_Tracking/INDEX]] ← Secção mãe
- [[35_Financial_Tracking/PLANILHA_PnL]] → Planilha de PnL mensal
