# IMPOSTOS_PROVISAO — Guia Fiscal Completo para Apostas Desportivas

**ID:** `FIN-004` | **Versão:** v2.0 | **Data:** 2026-05-17  
**Fase:** #phase/10+ | **Owner:** Financial Analyst + Contabilista  
**Status:** #status/pending | **Custo:** 0€ (obrigações fiscais legais)

---

## 1. OVERVIEW

Obrigações fiscais para operações de apostas desportivas em Portugal: IRS, IVA, e provisões contabilísticas.

**⚠️ NOTA:** Informativo. Consultar sempre um contabilista para decisões fiscais.

---

## 2. REGIME FISCAL EM PORTUGAL

### 2.1 IRS — Categoria B

| Aspecto | Detalhe |
|---------|---------|
| **Classificação** | Categoria B — Prestação de serviços (tipster) + Rendimentos empresariais (apostas) |
| **NIF** | Necessário (pessoa singular ou empresa) |
| **Recibos Verdes** | Emitir para subscrições |
| **IRS Apostas** | Ficheiro Jogo (tributação autónoma 28%) |

### 2.2 Estrutura de Tributação

```
┌─────────────────────────────────────────────────────────────┐
│                    FONTES DE RENDIMENTO                      │
├─────────────────────────────────────────────────────────────┤
│  1. SUBSCRIÇÕES TIPSTER                                       │
│     └── IRS: Taxa progressiva (14.5% a 48%)                  │
│     └── Isenção IVA (até 12.500€/ano)                       │
│                                                              │
│  2. APOSTAS PRÓPRIAS (lucro)                                  │
│     └── Tributação autónoma: 28% (retido na fonte)          │
│                                                              │
│  3. PATROCÍNIOS / AFILIADOS                                   │
│     └── IRS progressivo + IVA se > 12.500€/ano               │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. IMPOSTO SOBRE APOSTAS (IES)

### 3.1 Taxas de Retenção (Portugal)

| Tipo de Jogo | Taxa |
|--------------|------|
| **Apostas Desportivas** | **28%** (retido pela casa) |
| Casino online | 25-28% |
| Poker | 20% |

### 3.2 Ficheiro Jogo — Declaração Anual

| Campo | Descrição |
|-------|-----------|
| **Anexo J** | Declaração de ganhos em jogos |
| **Prazo** | Até 30 de junho do ano seguinte |
| **Onde** | Portal das Finanças |

---

## 4. IVA — IMPOSTO SOBRE O VALOR ACRESCENTADO

### 4.1 Obrigatoriedade

| Situação | Obrigação |
|----------|-----------|
| Receitas < 12.500€/ano | **Isento** (art. 53.º CIVA) |
| Receitas > 12.500€/ano | **Obrigatório** (23%) |

### 4.2 Cálculo

```
Receita anual = 20.000€ (subscrições)
IVA = 20.000€ × 23% = 4.600€
Total a cobrar = 24.600€
```

---

## 5. PROVISÕES CONTABILÍSTICAS

### 5.1 Provisões Mensais

| Provisão | Fórmula |
|----------|---------|
| **IRS Apostas** | `PnL_bruto × 28%` |
| **IRS Tipster** | `Receita_subs × 25%` |
| **IVA** | `Receita_subs × 23%` (se aplicável) |
| **Segurança Social** | `Recibos verdes × 21.4%` |

### 5.2 Exemplo de Cálculo

```
Mês de exemplo:
├── Subscrições: 5.000€
├── Lucro apostas: 2.000€
└── Despesas: 1.000€

Provisões:
├── IRS Tipster: 5.000 × 25% = 1.250€
├── IRS Apostas: 2.000 × 28% = 560€
├── IVA: 0€ (isento)
└── SS: 5.000 × 21.4% = 1.070€

Total provisões: 2.880€
Lucro líquido estimado: 3.120€
```

---

## 6. OBRIGAÇÕES FISCAIS

### 6.1 Calendário

| Obrigação | Frequência | Prazo |
|-----------|------------|-------|
| **Retenções IRS** | Mensal | 20 do mês seguinte |
| **IVA** | Trimestral | 20 do mês seguinte |
| **Segurança Social** | Trimestral | 20 do mês seguinte |
| **IRS (pessoa)** | Anual | 30 de junho |

---

## 7. ESTRUTURA DE CONTAS

### 7.1 Contas de Provisão

| Código | Conta |
|--------|-------|
| 2.8.1 | Provisão IRS Apostas |
| 2.8.2 | Provisão IRS Tipster |
| 2.8.3 | Provisão IVA |
| 2.8.4 | Provisão Segurança Social |

---

## 8. BACKLOG

- [x] Definir taxas de imposto (28% apostas, 14.5-48% tipster)
- [x] Configurar provisões mensais
- [x] Documentar obrigações fiscais
- [ ] Implementar cálculo automático no sistema
- [ ] Consultar contabilista para validação

---

## 9. LINKS

- [[35_Financial_Tracking/PLANO_CONTAS]] → Plano de contas
- [[35_Financial_Tracking/INDEX]] ← Secção mãe

---

**Aviso:** Informação fiscal pode mudar. Sempre consultar contabilista.

**Custo:** 0€ (obrigações legais) + honorários de contabilista (150-300€/mês recomendado)
