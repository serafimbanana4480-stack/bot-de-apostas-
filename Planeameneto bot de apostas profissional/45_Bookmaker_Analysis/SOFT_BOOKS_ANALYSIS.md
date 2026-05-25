# SOFT_BOOKS_ANALYSIS — Análise de Soft Books vs Sharp Books

**ID:** `BK-002` | **Fase:** #phase/3-6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Analisar as diferenças fundamentais entre soft books (recreacionais) e sharp books (profissionais), identificando oportunidades de value, riscos associados e estratégias ótimas para cada tipo.

**Princípio:** Sharp books definem o mercado; soft books seguem o mercado com atraso, criando oportunidades de arbitragem.

---

## 2. CONCEITOS FUNDAMENTAIS

### 2.1 Sharp Books

**Definição:** Casas de apostas que aceitam apostadores profissionais, têm limites altos, odds competitivas e ajustam linhas rapidamente.

**Características:**
- Odds próximas do mercado justo (low overround)
- Limites altos para vencedores
- Ajuste rápido de linhas (segundos a minutos)
- Foco em volume e margem pequena
- API disponível (embora restrita)
- Não limitam agressivamente vencedores

**Exemplos:**
- Pinnacle (referência global)
- 5Dimes
- Bookmaker (EU)
- Cris
- Heritage

**Filosofia:**
```
"Nós não perdemos dinheiro em apostas individuais.
Ganhamos no longo prazo através do overround.
Se você tem edge, continue apostando - nós ajustaremos as odds."
```

### 2.2 Soft Books

**Definição:** Casas de apostas focadas em apostadores recreacionais, com odds menos competitivas, limites baixos e ajuste lento de linhas.

**Características:**
- Odds com overround alto (5-8%)
- Limites baixos para vencedores
- Ajuste lento de linhas (minutos a horas)
- Foco em apostadores casuais
- API geralmente indisponível
- Limitam agressivamente vencedores

**Exemplos:**
- Bet365
- William Hill
- DraftKings
- FanDuel
- PointsBet
- Bwin

**Filosofia:**
```
"Nós queremos apostadores recreacionais que apostam por diversão.
Se você ganha consistentemente, você não é o nosso cliente.
Vamos limitar a sua conta ou fechá-la."
```

---

## 3. COMPARAÇÃO DETALHADA

### 3.1 Tabela Comparativa

| Característica | Sharp Books | Soft Books |
|----------------|-------------|------------|
| **Overround** | 2-4% | 5-8% |
| **Limites para Vencedores** | Altos (€10k-100k+) | Baixos (€50-500) |
| **Velocidade de Ajuste** | 30-90s | 5-30min |
| **API** | Disponível (restrita) | Indisponível |
| **Limitação de Contas** | Rara | Comum |
| **Liquidez** | Alta | Média-Alta |
| **Mercados** | Focados (principais) | Ampla variedade |
| **Target** | Profissionais | Recreacionais |
| **Método de Lucro** | Volume + margem pequena | Overround alto |

### 3.2 Análise por Critério

**Para Maximizar Edge:**
- Soft books: Odds menos eficientes = mais value
- Sharp books: Odds eficientes = menos value mas mais consistente

**Para Escalar Volume:**
- Sharp books: Limites altos = possível escalar
- Soft books: Limites baixos = impossível escalar

**Para Longo Prazo:**
- Sharp books: Contas não são limitadas = sustentável
- Soft books: Contas são limitadas = insustentável

**Para Arbitragem:**
- Sharp books: Referência de mercado (fecho)
- Soft books: Fonte de valor (abertura)

---

## 4. ESTRATÉGIAS PARA SHARP BOOKS

### 4.1 Como Sharp Books Operam

**Modelo de Negócio:**
1. Abrir linhas com base em modelos estatísticos
2. Ajustar linhas rapidamente baseado em volume e sharp action
3. Aceitar apostadores profissionais como "informação gratuita"
4. Ajustar odds até que não haja edge significativo
5. Lucrar através do overround em milhões de apostas

**Detecção de Sharp Action:**
- Stakes grandes
- Apostas em linhas que se movem
- Apostas em mercados menos populares
- Apostas consistentes em CLV positivo
- Padrões de apostas não recreacionais

### 4.2 Estratégia de Apostas em Sharp Books

**Quando Apostar:**
- Quando há CLV positivo vs closing line
- Quando há divergência entre sharp books
- Quando há informação privilegiada (injury news, etc.)
- Quando modelo tem edge comprovado

**Como Apostar:**
- Stakes proporcionais ao edge (Kelly)
- Focar em mercados onde modelo tem advantage
- Monitorizar CLV para validar edge
- Diversificar entre múltiplas sharp books

**O Que Evitar:**
- Apostar contra o movimento de linha (trend following)
- Apostar em mercados onde modelo não tem edge
- Stakes desproporcionais ao edge
- Churn excessivo (muitas apostas pequenas)

**Exemplo:**
```
Pinnacle: Lakers 2.10, Celtics 1.80
Modelo: Lakers tem 52% de probabilidade → Fair odd = 1.92
Edge no Lakers = (2.10 * 0.52) - 1 = 9.2%

Ação: Apostar Lakers no Pinnacle
Stake: Kelly com edge 9.2%
```

### 4.3 Vantagens de Sharp Books

1. **Sustentabilidade:** Contas não são limitadas
2. **Liquidez:** Pode apostar grandes valores
3. **Consistência:** Edge é mais estável
4. **Validação:** CLV é métrica confiável
5. **API:** Possível automatização

### 4.4 Desvantagens de Sharp Books

1. **Menos Edge:** Odds são mais eficientes
2. **Competição:** Muitos profissionais no mercado
3. **Overround:** Ainda existe margem (2-4%)
4. **API Restrita:** Acesso limitado
5. **Geografia:** Não disponível em todos os países

---

## 5. ESTRATÉGIAS PARA SOFT BOOKS

### 5.1 Como Soft Books Operam

**Modelo de Negócio:**
1. Copiar linhas de sharp books com atraso
2. Adicionar overround alto (5-8%)
3. Limitar agressivamente vencedores
4. Focar em apostadores recreacionais
5. Lucrar através de overround e perda dos recreacionais

**Detecção de Apostadores Profissionais:**
- CLV positivo consistente
- Apostas em linhas que se movem
- Stakes máximos frequentemente
- Apostas em mercados não populares
- Padrões de apostas não recreacionais
- Arbitragem entre casas

### 5.2 Estratégia de Apostas em Soft Books

**Quando Apostar:**
- Arbitragem garantida (surebets)
- CLV significativo (>3%) vs closing
- Linhas desatualizadas após news
- Promoções e bónus (com cuidado)

**Como Apostar:**
- Stakes máximos permitidos
- Apostas únicas (evitar padrões)
- Misturar apostas recreacionais
- Usar múltiplas contas/identidades
- Rotacionar entre soft books

**O Que Evitar:**
- Apostar consistentemente no mesmo tipo de aposta
- Apostar sempre no máximo
- Apostar imediatamente após news (suspicioso)
- Usar automação (detectável)
- Apenas apostas de value (padrão claro)

**Exemplo:**
```
Pinnacle (Sharp): Lakers 2.10, Celtics 1.80
Bet365 (Soft): Lakers 2.20, Celtics 1.70

Arbitragem:
Back Lakers 2.20 (Bet365)
Back Celtics 1.80 (Pinnacle)
Lucro garantido: ~4.5%

Ação: Apostar em Bet365 (stake máximo)
```

### 5.3 Vantagens de Soft Books

1. **Mais Edge:** Odds menos eficientes
2. **Arbitragem:** Oportunidades frequentes
3. **Promoções:** Bónus e ofertas
4. **Mercados:** Mais variedade
5. **Acesso:** Disponível globalmente

### 5.4 Desvantagens de Soft Books

1. **Limitação:** Contas são rapidamente limitadas
2. **Volume:** Impossível escalar
3. **Insustentável:** Modelo de negócio não funciona longo prazo
4. **Sem API:** Execução manual apenas
5. **Overround Alto:** Margem reduz edge

---

## 6. CICLO DE VIDA DE CONTA EM SOFT BOOKS

### 6.1 Fases de Limitação

**Fase 1: Nova Conta (0-2 semanas)**
- Limites normais
- Sem restrições
- Oportunidade de arbitragem

**Fase 2: Monitorização (2-4 semanas)**
- Casa monitoriza padrões
- CLV positivo é notado
- Primeiros sinais de alerta

**Fase 3: Limitação Parcial (1-2 meses)**
- Limites reduzidos (50-80%)
- Alguns mercados bloqueados
- Promoções removidas

**Fase 4: Limitação Total (2-3 meses)**
- Limites muito baixos (€5-20)
- Apenas mercados populares
- Sem promoções

**Fase 5: Encerramento (3-6 meses)**
- Conta fechada
- Saldo devolvido
- Banimento permanente

### 6.2 Estratégias para Prolongar Ciclo

**Técnicas de Camuflagem:**
- Misturar apostas recreacionais (favoritos populares)
- Apostar em diferentes mercados
- Variar stakes (não sempre máximo)
- Evitar arbitragem óbvia
- Usar cash-out ocasionalmente
- Apostar em horários variados

**Técnicas de Rotação:**
- Múltiplas contas por soft book
- Múltiplas identidades (legalmente)
- Rotação entre soft books
- Pausas entre apostas

**Limitações:**
- Camuflagem prolonga mas não evita limitação
- Soft books são sofisticadas na detecção
- Risco de banimento se detectado
- Aspectos legais a considerar

---

## 7. ESTRATÉGIA HÍBRIDA

### 7.1 Abordagem Recomendada

**Fase Inicial (Micro Banca):**
- Focar em soft books para maximizar edge
- Arbitragem para lucro garantido
- Construir banca rapidamente

**Fase Intermediária (Medium Banca):**
- Transição gradual para sharp books
- Reduzir dependência de soft books
- Começar automação com sharp books

**Fase Avançada (Large Banca):**
- Primariamente sharp books
- Soft books apenas para oportunidades únicas
- Foco em escala e consistência

### 7.2 Distribuição de Volume

| Fase | Sharp Books | Soft Books |
|------|-------------|------------|
| 4-6 (€100-1k) | 20% | 80% |
| 7-9 (€1k-10k) | 50% | 50% |
| 10+ (€10k+) | 80% | 20% |

### 7.3 Justificação

**Por que não apenas Soft Books?**
- Insustentável longo prazo
- Impossível escalar
- Limitação inevitável
- Sem API para automação

**Por que não apenas Sharp Books?**
- Menos edge inicial
- Mais competição
- Requer modelo superior
- Dificuldade em começar

**Por que Híbrida?**
- Aproveita vantagens de ambos
- Transição suave entre fases
- Maximiza edge em todas as fases
- Sustentável longo prazo

---

## 8. CONSIDERAÇÕES ÉTICAS E LEGAIS

### 8.1 Ética

**É ético apostar em soft books?**
- Sim: É jogo legítimo com base em informação
- Não: Explorar vulnerabilidades de sistema

**Perspectiva:**
- Soft books aceitam o risco de apostadores profissionais
- É parte do modelo de negócio
- Apostadores recreacionais subsidiam sharp action

### 8.2 Legalidade

**Aspectos Legais:**
- Múltiplas contas: Verificar T&C de cada casa
- Identidades falsas: Ilegal
- Arbitragem: Geralmente legal
- VPN/Proxy: Pode violar T&C

**Recomendação:**
- Consultar advogado local
- Seguir T&C de cada casa
- Evitar práticas ilegais
- Documentar todas as atividades

---

## 9. MÉTRICAS DE MONITORIZAÇÃO

### 9.1 KPIs por Tipo de Casa

| KPI | Sharp Books | Soft Books |
|-----|-------------|------------|
| Edge Médio | 2-4% | 5-10% |
| CLV Médio | 1-2% | 3-5% |
| Stake Médio | €100-5,000 | €50-500 |
| Vida Média da Conta | Permanente | 2-4 meses |
| ROI | 3-5% | 10-20% |

### 9.2 Alertas

**Para Sharp Books:**
- CLV médio < 0% por 7 dias → Revisar modelo
- ROI < 2% por 30 dias → Revisar estratégia
- Taxa de rejeição > 10% → Verificar API

**Para Soft Books:**
- Limites reduzidos > 50% → Preparar rotação
- Conta encerrada → Ativar nova conta
- ROI < 5% → Mudar estratégia

---

## 10. BACKLOG TÉCNICO

- [ ] Implementar sistema de deteção de soft vs sharp books
- [ ] Criar monitorização de CLV por tipo de casa
- [ ] Desenvolver sistema de rotação de contas soft books
- [ ] Implementar alertas de limitação de contas
- [ ] Criar histórico de vida de contas por soft book
- [ ] Documentar T&C de cada soft book
- [ ] Desenvolver estratégias de camuflagem de padrões
- [ ] Criar dashboard comparativo sharp vs soft

---

## 11. LINKS CRUZADOS

- [[45_Bookmaker_Analysis/INDEX]] ← Secção mãe
- [[BOOKMAKER_COMPARISON]] → Comparação detalhada de casas
- [[LIQUIDEZ_ODDS]] → Análise de liquidez e odds
- [[ARBITRAGEM_BOOKMAKERS]] → Estratégias de arbitragem
- [[RISCOS_LIMITACAO]] → Riscos de limitação/banimento
- [[DIVERSIFICACAO_CONTAS]] → Estratégias de diversificação