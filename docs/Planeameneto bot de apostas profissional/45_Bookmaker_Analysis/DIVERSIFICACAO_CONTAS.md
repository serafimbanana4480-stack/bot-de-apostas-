# DIVERSIFICACAO_CONTAS — Estratégias de Diversificação de Contas

**ID:** `BK-007` | **Fase:** #phase/3-6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar estratégias abrangentes de diversificação de contas e casas de apostas para minimizar riscos operacionais, maximizar capacidade de escala e garantir sustentabilidade longo prazo da operação de value betting.

**Princípio:** Diversificação é o único seguro gratuito em apostas - reduz risco sem reduzir retorno esperado.

---

## 2. CONCEITOS FUNDAMENTAIS

### 2.1 Por Que Diversificar?

**Benefícios de Diversificação:**

1. **Redução de Risco Operacional**
   - Se uma casa falha, outras compensam
   - Se uma conta é limitada, operação continua
   - Reduz dependência de único ponto de falha

2. **Aumento de Capacidade de Escala**
   - Múltiplas contas = múltiplos limites
   - Distribuir volume entre casas
   - Não mover mercado em única casa

3. **Melhoria de ROI**
   - Line shopping entre casas
   - Aproveitar melhores odds
   - Reduzir slippage

4. **Resiliência a Mudanças**
   - Se uma casa muda regras, outras mantêm
   - Se uma casa sai do mercado, alternativas disponíveis
   - Adaptação a mudanças regulatórias

5. **Oportunidades Únicas**
   - Promoções específicas por casa
   - Arbitragem entre contas
   - Ineficiências de mercado específicas

### 2.2 Tipos de Diversificação

**Por Dimensão:**

| Dimensão | Descrição | Exemplo |
|----------|-----------|---------|
| **Geográfica** | Casas em diferentes países/regiões | Betfair (UK), Pinnacle (Curacao) |
| **Tipo de Casa** | Exchange vs Sharp vs Soft | Betfair, Pinnacle, Bet365 |
| **Jurisdição** | Diferentes reguladores | UKGC, MGA, Curacao |
| **Método de Pagamento** | Diferentes opções | Banco, Crypto, E-wallet |
| **Mercado** | Diferentes focos de mercado | NBA, NFL, Soccer |
| **Estratégia** | Diferentes abordagens | Value, Arbitragem, Misto |

---

## 3. ESTRATÉGIA DE DIVERSIFICAÇÃO

### 3.1 Matriz de Diversificação

**Estrutura Recomendada:**

```
NÍVEL 1: Exchanges (50% do volume)
├── Betfair Exchange (30%)
│   ├── Conta Primária (20%)
│   └── Conta Backup (10%)
├── Smarkets (15%)
│   ├── Conta Primária (10%)
│   └── Conta Backup (5%)
└── Matchbook (5%)
    └── Conta Única (5%)

NÍVEL 2: Sharp Books (25% do volume)
├── Pinnacle (20%)
│   └── Conta Primária (20%)
└── Outros Sharp (5%)
    └── Conta Única (5%)

NÍVEL 3: Soft Books (25% do volume)
├── Soft Book A (10%)
│   ├── Conta 1 (4%)
│   ├── Conta 2 (3%)
│   └── Conta 3 (3%)
├── Soft Book B (8%)
│   ├── Conta 1 (4%)
│   └── Conta 2 (4%)
└── Soft Book C (7%)
    ├── Conta 1 (4%)
    └── Conta 2 (3%)
```

### 3.2 Diversificação por Tipo de Casa

**Exchanges (Foco Principal):**

| Casa | % Volume | Contas | Justificação |
|------|----------|--------|--------------|
| **Betfair** | 30% | 2 | Liquidez máxima, API excelente |
| **Smarkets** | 15% | 2 | Comissão baixa, alternativa |
| **Matchbook** | 5% | 1-2 | Niche, comissão muito baixa |

**Sharp Books (Referência e Diversificação):**

| Casa | % Volume | Contas | Justificação |
|------|----------|--------|--------------|
| **Pinnacle** | 20% | 1-2 | Referência de mercado, não limita |
| **5Dimes** | 3% | 1 | Alternativa geográfica |
| **Bookmaker** | 2% | 1 | Diversificação adicional |

**Soft Books (Oportunidades e Arbitragem):**

| Casa | % Volume | Contas | Vida Esperada |
|------|----------|--------|---------------|
| **Soft A** | 10% | 3 | 2-3 meses |
| **Soft B** | 8% | 2 | 3-4 meses |
| **Soft C** | 7% | 2 | 2-3 meses |

### 3.3 Diversificação Geográfica

**Por Região Regulatória:**

| Região | Características | Casas Exemplo |
|--------|-----------------|---------------|
| **UK/EU (UKGC/MGA)** | Regulação forte, proteção consumidor | Betfair, William Hill |
| **Curacao** | Regulação leve, menos proteção | Pinnacle, 5Dimes |
| **Offshore** | Regulação variável | Diversas soft books |
| **Asia** | Mercados específicos | SBObet, 188Bet |

**Estratégia:**
- 60% em reguladores fortes (UK/EU)
- 30% em reguladores médios (Curacao)
- 10% em offshore (com cuidado)

**Riscos:**
- Reguladores fracos = menos proteção
- Offshore = risco de não-pagamento
- Verificar reputação antes de depositar

---

## 4. GESTÃO DE RISCO ATRAVÉS DE DIVERSIFICAÇÃO

### 4.1 Análise de Correlação

**Princípio:** Diversificar entre casas com baixa correlação de risco

**Matriz de Correlação de Risco:**

```
           Betfair  Pinnacle  Soft A  Soft B
Betfair     1.00      0.30     0.10    0.10
Pinnacle    0.30      1.00     0.15    0.15
Soft A      0.10      0.15     1.00    0.40
Soft B      0.10      0.15     0.40    1.00
```

**Interpretação:**
- Betfair e Pinnacle: Baixa correlação (sistemas diferentes)
- Soft A e Soft B: Média correlação (mesmo tipo de casa)
- Betfair e Soft A: Muito baixa correlação (tipos diferentes)

**Estratégia:**
- Maximizar exposição a casas com baixa correlação
- Limitar exposição a casas com alta correlação
- Diversificar entre tipos, não apenas casas

### 4.2 Cálculo de Risco de Concentração

**Fórmula de Herfindahl-Hirschman (HHI):**
```
HHI = Σ (si)²

Onde:
- si = % de volume na casa i
- HHI varia de 0 (perfeita diversificação) a 10,000 (concentração total)

Níveis:
- HHI < 1,500: Diversificação boa
- HHI 1,500-2,500: Diversificação moderada
- HHI > 2,500: Concentração alta
```

**Exemplo:**
```
Distribuição:
Betfair: 30%
Pinnacle: 20%
Smarkets: 15%
Soft A: 10%
Soft B: 8%
Soft C: 7%
Outros: 10%

HHI = 0.30² + 0.20² + 0.15² + 0.10² + 0.08² + 0.07² + 0.10²
    = 0.09 + 0.04 + 0.0225 + 0.01 + 0.0064 + 0.0049 + 0.01
    = 0.1838 (1,838)

Conclusão: Diversificação moderada (aceitável)
```

### 4.3 Limites de Exposição

**Regras de Exposição:**

| Tipo de Limite | Valor | Justificação |
|----------------|-------|--------------|
| **Máximo por casa** | 30% do volume | Evitar concentração |
| **Máximo por tipo** | 50% do volume | Diversificar tipos |
| **Máximo por regulador** | 60% do volume | Diversificar jurisdição |
| **Mínimo de casas** | 5 casas ativas | Garantir diversificação |
| **Mínimo de tipos** | 2 tipos (exchange + sharp) | Reduzir risco sistémico |

---

## 5. OTIMIZAÇÃO DE DIVERSIFICAÇÃO

### 5.1 Alocação Dinâmica

**Princípio:** Ajustar alocação baseado em performance e risco

**Fatores de Ajuste:**

1. **Performance da Casa**
   - ROI alto → aumentar alocação
   - ROI baixo → reduzir alocação
   - Slippage alto → reduzir alocação

2. **Risco de Limitação**
   - Sinais de limitação → reduzir alocação
   - Conta nova → aumentar alocação
   - Vida de conta curta → reduzir alocação

3. **Condições de Mercado**
   - Liquidez alta → aumentar alocação
   - Liquidez baixa → reduzir alocação
   - Volatilidade alta → reduzir alocação

**Algoritmo de Ajuste:**
```python
def adjust_allocation(current_allocation, performance_metrics, risk_metrics):
    """
    Ajusta alocação baseado em performance e risco
    """
    new_allocation = {}

    for house in current_allocation:
        # Fator de performance (0.5-1.5)
        perf_factor = normalize(performance_metrics[house]['roi'])

        # Fator de risco (0.5-1.5)
        risk_factor = normalize(risk_metrics[house]['limitation_risk'])

        # Ajuste
        adjustment = perf_factor * risk_factor
        new_allocation[house] = current_allocation[house] * adjustment

    # Normalizar para 100%
    total = sum(new_allocation.values())
    for house in new_allocation:
        new_allocation[house] = new_allocation[house] / total

    return new_allocation
```

### 5.2 Rebalanceamento

**Frequência:**
- Mensal: Rebalanceamento completo
- Semanal: Ajustes menores
- Diário: Ajustes emergenciais

**Processo:**
1. Analisar performance de cada casa
2. Avaliar risco de limitação
3. Calcular nova alocação ótima
4. Executar transferências de bankroll
5. Atualizar estratégia de apostas

**Regras de Rebalanceamento:**
- Não mover mais de 20% do bankroll por mês
- Manter mínimo de 10x stake em cada conta
- Considerar custos de transação
- Documentar todas as mudanças

---

## 6. DIVERSIFICAÇÃO POR FASE

### 6.1 Fase 4-6 (Micro-Small Banca: €100-1,000)

**Estratégia:**
- 2-3 casas (Betfair + Pinnacle + 1 soft)
- 100% em casa primária inicialmente
- Adicionar segunda casa quando banca > €500
- Foco em aprender, não diversificação

**Distribuição:**
```
€100-300: Betfair 100%
€300-500: Betfair 80%, Pinnacle 20%
€500-1,000: Betfair 70%, Pinnacle 20%, Soft 10%
```

### 6.2 Fase 7-9 (Medium Banca: €1,000-10,000)

**Estratégia:**
- 5-7 casas (2 exchanges + 1 sharp + 2-3 soft)
- Diversificação moderada
- Começar rotação de contas soft books
- Foco em crescimento sustentável

**Distribuição:**
```
€1,000-3,000:
├── Betfair: 60%
├── Pinnacle: 20%
├── Smarkets: 10%
└── Soft A: 10%

€3,000-10,000:
├── Betfair: 40%
├── Pinnacle: 20%
├── Smarkets: 15%
├── Soft A: 15%
└── Soft B: 10%
```

### 6.3 Fase 10+ (Large Banca: €10,000+)

**Estratégia:**
- 8-15 casas (3 exchanges + 2 sharp + 3-5 soft)
- Diversificação completa
- Rotação sofisticada de contas
- Foco em escala e sustentabilidade

**Distribuição:**
```
€10,000-50,000:
├── Betfair: 30%
├── Pinnacle: 20%
├── Smarkets: 15%
├── Matchbook: 5%
├── Sharp adicionais: 5%
├── Soft A: 10%
├── Soft B: 8%
└── Soft C: 7%

€50,000+:
├── Exchanges: 50%
├── Sharp books: 25%
├── Soft books: 20%
└── Reserva: 5%
```

---

## 7. MONITORIZAÇÃO DE DIVERSIFICAÇÃO

### 7.1 Métricas de Diversificação

**KPIs:**

| KPI | Descrição | Target |
|-----|-----------|--------|
| **HHI** | Índice de concentração | < 1,500 |
| **Nº de Casas Ativas** | Casas com volume > 0 | > 5 |
| **Diversificação por Tipo** | % em cada tipo | Balanceado |
| **Correlação de Risco** | Correlação média entre casas | < 0.3 |
| **Resiliência** | % de volume mantido se 1 casa falha | > 80% |

### 7.2 Dashboard de Diversificação

**Componentes:**

```
┌─────────────────────────────────────┐
│  DASHBOARD DE DIVERSIFICAÇÃO       │
├─────────────────────────────────────┤
│  Resumo                            │
│  - HHI: 1,238 ✓                   │
│  - Casas Ativas: 8/10 ✓            │
│  - Resiliência: 85% ✓             │
├─────────────────────────────────────┤
│  Distribuição por Tipo             │
│  - Exchanges: 50%                  │
│  - Sharp: 25%                      │
│  - Soft: 25%                       │
├─────────────────────────────────────┤
│  Top 5 Casas por Volume            │
│  1. Betfair: 30%                   │
│  2. Pinnacle: 20%                  │
│  3. Smarkets: 15%                  │
│  4. Soft A: 10%                    │
│  5. Soft B: 8%                     │
├─────────────────────────────────────┤
│  Alertas                           │
│  - Soft A: Alocação acima do limite│
│  - HHI aumentando 5% este mês     │
└─────────────────────────────────────┘
```

### 7.3 Alertas

**Gerar Alerta Se:**
- HHI > 2,000 (concentração alta)
- Nº de casas ativas < 4 (pouca diversificação)
- Uma casa > 40% do volume (concentração)
- Correlação de risco > 0.5 (alta correlação)
- Resiliência < 70% (baixa resiliência)

---

## 8. CENÁRIOS DE STRESS

### 8.1 Cenário 1: Casa Principal Falha

**Situação:** Betfair fica indisponível por 48h

**Impacto:**
- Perda de 30% do volume
- Redução temporária de capacidade
- Necessidade de redistribuir

**Resposta:**
1. Redirecionar volume para Pinnacle e Smarkets
2. Aumentar alocação temporariamente
3. Activar contas backup
4. Monitorizar liquidez nas casas alternativas

**Recuperação:**
- Quando Betfair voltar: restabelecer alocação normal
- Analisar causa da falha
- Implementar melhorias de resiliência

### 8.2 Cenário 2: Múltiplas Soft Books Limitam

**Situação:** 3 soft books limitam contas no mesmo mês

**Impacto:**
- Perda de 25% do volume
- Redução de oportunidades de arbitragem
- Necessidade de novas contas

**Resposta:**
1. Activar contas backup em soft books
2. Aumentar volume em exchanges e sharp books
3. Abrir novas contas em soft books alternativas
4. Revisar estratégia de camuflagem

**Recuperação:**
- Diversificar adicionalmente
- Melhorar técnicas de mitigação
- Considerar reduzir dependência de soft books

### 8.3 Cenário 3: Mudança Regulatória

**Situação:** Regulador proíbe certas casas no país

**Impacto:**
- Perda de acesso a casas específicas
- Necessidade de encontrar alternativas
- Potencial perda de bankroll

**Resposta:**
1. Levantar fundos imediatamente
2. Activar casas em outras jurisdições
3. Consultar advogado sobre legalidade
4. Documentar todas as transações

**Recuperação:**
- Diversificar geograficamente
- Reduzir dependência de único regulador
- Implementar VPN/proxies se legal

---

## 9. MELHORES PRÁTICAS

### 9.1 Princípios Fundamentais

1. **Nunca Concentrar Excessivamente**
   - Máximo 30% por casa
   - Mínimo 5 casas ativas
   - Diversificar por tipo

2. **Monitorizar Continuamente**
   - Métricas de diversificação
   - Performance por casa
   - Sinais de risco

3. **Ajustar Dinamicamente**
   - Rebalancear mensalmente
   - Ajustar baseado em performance
   - Responder a mudanças de mercado

4. **Manter Reserva de Liquidez**
   - 10% do bankroll em reserva
   - Acessível rapidamente
   - Para emergências

### 9.2 O Que Evitar

❌ **Nunca:**
- Colocar > 50% do bankroll em única casa
- Depender exclusivamente de soft books
- Ignorar sinais de limitação
- Esquecer de diversificar geograficamente

⚠️ **Evitar:**
- Diversificação excessiva (> 15 casas)
- Gestão manual de muitas contas
- Ignorar custos de transação
- Diversificar sem análise de correlação

---

## 10. BACKLOG TÉCNICO

- [ ] Implementar sistema de cálculo de HHI
- [ ] Desenvolver dashboard de diversificação
- [ ] Criar algoritmo de alocação dinâmica
- [ ] Implementar sistema de rebalanceamento automático
- [ ] Desenvolver análise de correlação de risco
- [ ] Criar sistema de alertas de concentração
- [ ] Implementar simulação de cenários de stress
- [ ] Desenvolver relatórios de diversificação mensais

---

## 11. LINKS CRUZADOS

- [[45_Bookmaker_Analysis/INDEX]] ← Secção mãe
- [[BOOKMAKER_COMPARISON]] → Comparação detalhada de casas
- [[GESTAO_MULTIPLAS_CONTAS]] → Gestão de contas múltiplas
- [[RISCOS_LIMITACAO]] → Riscos de limitação/banimento
- [[SOFT_BOOKS_ANALYSIS]] → Análise soft vs sharp books