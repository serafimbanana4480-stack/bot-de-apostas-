# BOOKMAKER_COMPARISON — Comparação de Casas de Apostas

**ID:** `BA-001` | **Fase:** #phase/3-6 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Analisar e comparar casas de apostas (bookmakers e exchanges) para identificar a melhor opção para cada fase e mercado. A escolha da casa impacta diretamente edge, liquidez e capacidade de escala.

**Princípio:** Diversificar risco operacional usando múltiplas casas, mas focar edge na casa principal.

---

## 2. EXCHANGES

### 2.1 Betfair Exchange

**Visão Geral:**
- **Tipo:** Exchange peer-to-peer
- **Liquidez NBA:** Alta (€10k+ em principais jogos)
- **Comissão:** 5% (reduzível com volume)
- **API:** Excelente, REST + Streaming
- **Países:** Global (exclui alguns)
- **Score:** 9/10

**Prós:**
- ✓ Liquidez superior em quase todos os mercados
- ✓ API robusta e bem documentada
- ✓ Odds peer-to-peer (sem margem da casa)
- ✓ Trading avançado disponível
- ✓ Aceita grandes stakes
- ✓ Histórico de odds disponível

**Contras:**
- ✗ Comissão alta (5%)
- ✗ Requer KYC rigoroso
- ✗ Limitado em alguns países
- ✗ Curva de aprendizado para trading

**Melhor Para:**
- Operação principal (todas as fases)
- Mercados de alta liquidez
- Stakes grandes
- Trading avançado

**Estratégia de Uso:**
```
Fase 4-6 (Micro-Small Banca):
  → Casa primária (única)
  → Focar em NBA Moneyline/Spread
  → Aproveitar liquidez

Fase 7+ (Medium+ Banca):
  → Casa primária (70% do volume)
  → Diversificar para outras exchanges
  → Negociar redução de comissão
```

### 2.2 Smarkets

**Visão Geral:**
- **Tipo:** Exchange peer-to-peer
- **Liquidez NBA:** Média (€1-5k em principais jogos)
- **Comissão:** 2% (fixa)
- **API:** Boa, REST
- **Países:** UK, Irlanda, Alemanha, Áustria
- **Score:** 7/10

**Prós:**
- ✓ Comissão baixa (2% vs 5% Betfair)
- ✓ Interface simples
- ✓ API funcional
- ✓ Good para apostas simples

**Contras:**
- ✗ Liquidez limitada
- ✗ Menos mercados disponíveis
- ✗ Geograficamente limitado
- ✗ Menos volume geral

**Melhor Para:**
- Diversificação de risco
- Apostas de menor stake
- Mercados onde Betfair tem baixa liquidez
- Redução de custos (comissão)

**Estratégia de Uso:**
```
Fase 7+ (Medium Banca):
  → Casa secundária (20% do volume)
  → Focar em mercados com liquidez suficiente
  → Aproveitar comissão mais baixa
```

### 2.3 Matchbook

**Visão Geral:**
- **Tipo:** Exchange peer-to-peer
- **Liquidez NBA:** Baixa-Média (€500-2k)
- **Comissão:** 1.5% (fixa)
- **API:** Básica, REST
- **Países:** Global (limitado)
- **Score:** 6/10

**Prós:**
- ✓ Comissão muito baixa (1.5%)
- ✓ Interface limpa
- ✓ Niche para certos mercados

**Contras:**
- ✗ Liquidez muito limitada
- ✗ Poucos mercados
- ✗ API básica
- ✗ Volume insuficiente para escala

**Melhor Para:**
- Niche específicos
- Apostas muito pequenas
- Mercados alternativos

**Estratégia de Uso:**
```
Fase 10+ (Large Banca):
  → Casa terciária (5-10% do volume)
  → Apenas se liquidez suficiente
  → Niche específicos
```

---

## 3. BOOKMAKERS TRADICIONAIS (SHARP)

### 3.1 Pinnacle

**Visão Geral:**
- **Tipo:** Bookmaker sharp
- **Liquidez NBA:** Muito Alta (€50k+)
- **Margem:** ~2% (muito baixa para bookmaker)
- **API:** Limitada, REST (requer aprovação)
- **Países:** Global (exclui EUA, UK)
- **Score:** 8/10 (para odds reference)

**Prós:**
- ✓ Liquidez excelente
- ✓ Odds muito competitivas (reference market)
- ✓ Aceita grandes stakes
- ✓ Limites altos para vencedores
- ✓ Rápido ajuste de odds

**Contras:**
- ✗ Não aceita apostadores de todos os países
- ✗ API limitada e requer aprovação
- ✗ Margem da casa (2% vs 0% exchange)
- ✗ Sem trading peer-to-peer

**Melhor Para:**
- Referência de odds (fecho)
- Validação de CLV
- Shadow betting
- Apostas quando exchange tem baixa liquidez

**Estratégia de Uso:**
```
Todas as Fases:
  → Referência de odds (não execução)
  → Shadow betting para validação de CLV
  → Comparação com exchange

Fase 10+ (se disponível no país):
  → Diversificação (10-20% do volume)
  → Apenas se API disponível
```

### 3.2 5Dimes

**Visão Geral:**
- **Tipo:** Bookmaker sharp
- **Liquidez NBA:** Alta (€10-20k)
- **Margem:** ~3-4%
- **API:** Não disponível publicamente
- **Países:** Global (restrito)
- **Score:** 6/10

**Prós:**
- ✓ Limites altos para vencedores
- ✓ Odds competitivas
- ✓ Aceita grandes stakes

**Contras:**
- ✗ API não disponível
- ✗ Execução manual apenas
- ✗ Geograficamente restrito
- ✗ Margem mais alta que Pinnacle

**Melhor Para:**
- Diversificação geográfica
- Apostas manuais (se não tem API)
- Niche específicos

**Estratégia de Uso:**
```
Fase 10+ (Large Banca):
  → Execução manual apenas
  → Apenas se disponível no país
  → Volume limitado (5%)
```

---

## 4. BOOKMAKERS TRADICIONAIS (RECREATIONAL)

### 4.1 Bet365

**Visão Geral:**
- **Tipo:** Bookmaker recreational
- **Liquidez NBA:** Alta
- **Margem:** ~5-7%
- **API:** Não disponível publicamente
- **Países:** Global
- **Score:** 5/10 (para apostadores quant)

**Prós:**
- ✓ Muitos mercados disponíveis
- ✓ Interface excelente
- ✓ Cash-out disponível
- ✓ Live betting avançado

**Contras:**
- ✗ Limite rapidamente vencedores
- ✗ Margem alta
- ✗ API não disponível
- ✗ Não adequado para operação quant

**Melhor Para:**
- N/A (não recomendado para operação quant)

**Estratégia de Uso:**
```
NÃO RECOMENDADO para operação quant
→ Limita vencedores agressivamente
→ Margem alta reduz edge
→ Sem API para automação
```

### 4.2 William Hill

**Visão Geral:**
- **Tipo:** Bookmaker recreational
- **Liquidez NBA:** Alta
- **Margem:** ~5-7%
- **API:** Limitada (parceria apenas)
- **Países:** UK, Europa
- **Score:** 4/10

**Prós:**
- ✓ Marca estabelecida
- ✓ Muitos mercados

**Contras:**
- ✗ Limite vencedores
- ✗ Margem alta
- ✗ API limitada
- ✗ Não adequado para quant

**Melhor Para:**
- N/A (não recomendado)

---

## 5. COMPARAÇÃO DETALHADA

### 5.1 Tabela Comparativa

| Casa | Tipo | Comissão | Liquidez NBA | API | Limites para Vencedores | Score |
|------|------|----------|--------------|-----|------------------------|-------|
| Betfair Exchange | Exchange | 5% | Alta | Excelente | Ilimitados | 9/10 |
| Smarkets | Exchange | 2% | Média | Boa | Altos | 7/10 |
| Matchbook | Exchange | 1.5% | Baixa-Média | Básica | Médios | 6/10 |
| Pinnacle | Sharp | ~2% margem | Muito Alta | Limitada | Altos | 8/10 |
| 5Dimes | Sharp | ~3% margem | Alta | N/A | Altos | 6/10 |
| Bet365 | Recreational | ~6% margem | Alta | N/A | Baixos | 5/10 |

### 5.2 Análise por Critério

**Liquidez:**
1. Pinnacle (★★★★★)
2. Betfair Exchange (★★★★★)
3. Bet365 (★★★★)
4. Smarkets (★★★)
5. Matchbook (★★)

**Custo (Comissão/Margem):**
1. Matchbook (1.5%)
2. Smarkets (2%)
3. Pinnacle (~2%)
4. Betfair (5%)
5. Bet365 (~6%)

**API:**
1. Betfair (★★★★★)
2. Smarkets (★★★★)
3. Matchbook (★★★)
4. Pinnacle (★★)
5. Outros (★)

**Capacidade de Escala:**
1. Betfair (★★★★★)
2. Pinnacle (★★★★★)
3. Smarkets (★★★)
4. Matchbook (★★)
5. Recreational (★)

---

## 6. ESTRATÉGIA MULTI-CASA

### 6.1 Fase 4-6 (Micro-Small Banca)

**Estratégia:**
- Casa única: Betfair Exchange
- Justificação: Simplificar operação, maximizar liquidez
- Volume: 100% Betfair

**Critérios:**
- Liquidez suficiente para stakes até 40€
- API funcional
- Operação manual ou semi-automática

### 6.2 Fase 7-9 (Medium Banca)

**Estratégia:**
- Casa primária: Betfair Exchange (70%)
- Casa secundária: Smarkets (20%)
- Casa terciária: Pinnacle (10% - shadow only)

**Justificação:**
- Diversificar risco operacional
- Aproveitar comissão mais baixa Smarkets
- Validar CLV com Pinnacle

**Volume:**
- Betfair: 70%
- Smarkets: 20%
- Pinnacle: 10% (shadow)

### 6.3 Fase 10+ (Large Banca)

**Estratégia:**
- Casa primária: Betfair Exchange (60%)
- Casa secundária: Smarkets (20%)
- Casa terciária: Matchbook (10%)
- Casa shadow: Pinnacle (10%)

**Justificação:**
- Maximizar diversificação
- Otimizar custos de comissão
- Reduzir risco de limite

**Volume:**
- Betfair: 60%
- Smarkets: 20%
- Matchbook: 10%
- Pinnacle: 10% (shadow)

---

## 7. SELEÇÃO DE CASA POR MERCADO

### 7.1 NBA Moneyline

| Casa | Liquidez | Recomendação |
|------|----------|--------------|
| Betfair | €10k+ | Primária |
| Pinnacle | €50k+ | Referência/Shadow |
| Smarkets | €2-5k | Secundária |

### 7.2 NBA Spread

| Casa | Liquidez | Recomendação |
|------|----------|--------------|
| Betfair | €5-10k | Primária |
| Pinnacle | €30k+ | Referência/Shadow |
| Smarkets | €1-3k | Secundária |

### 7.3 NBA Totals

| Casa | Liquidez | Recomendação |
|------|----------|--------------|
| Betfair | €3-8k | Primária |
| Pinnacle | €20k+ | Referência/Shadow |
| Smarkets | €1-2k | Secundária |

### 7.4 NBA Player Props

| Casa | Liquidez | Recomendação |
|------|----------|--------------|
| Betfair | €500-2k | Primária |
| Smarkets | €100-500 | Secundária |
| Pinnacle | €5k+ | Referência/Shadow |

---

## 8. RISCOS E MITIGAÇÃO

### 8.1 Risco de Limite

**Sintoma:** Casa limita stakes ou fecha conta

**Mitigação:**
- Diversificar entre múltiplas casas
- Nunca concentrar > 50% em uma casa
- Manter operação discreta
- Negociar com casas para high-rollers

### 8.2 Risco de API

**Sintoma:** API falha ou é descontinuada

**Mitigação:**
- Ter backup manual de execução
- Usar múltiplas APIs
- Monitorizar uptime de API
- Ter planos de contingência

### 8.3 Risco de Liquidez

**Sintoma:** Liquidez insuficiente para stake desejado

**Mitigação:**
- Monitorizar liquidez em tempo real
- Ajustar stake dinamicamente
- Distribuir por múltiplas casas
- Evitar mercados de baixa liquidez

---

## 9. LINKS CRUZADOS

- [[45_Bookmaker_Analysis/INDEX]] ← Seção mãe
- [[45_Bookmaker_Analysis/SHARP_MONEY_TRACKING]] → Rastreamento sharp money
- [[47_Shadow_Betting/INDEX]] → Shadow mode multi-casa
- [[09_Execution_System/INDEX]] → Sistema de execução