# VBQ-003 — Institutional Quantitative Sports Betting Fund v3.1.0

**ID:** `VBQ-003` | **Fase:** #phase/13-60 | **Owner:** Chief Investment Officer | **Status:** #status/draft | **Versão:** `3.1.0-Institutional`

---

## 1. EXECUTIVE SUMMARY

VBQ-003 é o roadmap para transformar o sistema de value betting (VBQ-002) num fundo quantitativo de apostas desportivas de nível institucional. Este documento define a estratégia para escalar de um sistema operado por uma pessoa a uma organização que gere múltiplas estratégias, múltiplas casas de apostas e capital externo.

**Objetivo:** Atingir escala institucional (1M€+ em banca) com ROI consistente 8-12% anual, Sharpe ratio > 2.0, e drawdown máximo < 15%.

**Horizonte:** 48 meses (Fase 13-60)

---

## 2. ARQUITETURA MULTI-ESTRATÉGIA

### 2.1 Estratégias Primárias

| Estratégia | ROI Esperado | Risco | Liquidez | Fase |
|------------|--------------|-------|----------|------|
| Value Betting (Multi-Desporto) | 5-8% | Médio | Alta | 13-30 |
| Surebets (Multi-Casa) | 2-4% | Baixo | Média | 13-18 |
| Trading Pré-Jogo | 6-10% | Médio-Alto | Alta | 19-24 |
| Market Making (Betfair) | 4-6% | Alto | Alta | 25-30 |
| Lays (Short Positions) | 3-5% | Médio | Média | 31-36 |

### 2.2 Diversificação de Fontes de Lucro

A arquitetura multi-estratégia é fundamental para robustez sistémica:
- **Value betting:** Lucro através de edge em probabilidades
- **Surebets:** Lucro garantido através de arbitragem
- **Trading:** Lucro através de movimento de odds
- **Market making:** Lucro através de spread (bid-ask)
- **Lays:** Lucro através de posicionamento contrário

---

## 3. TEAM & RESOURCES REQUIRED

### 3.1 Dimensionamento de Equipa por Fase

#### Fase 5 (Mês 13-15): Surebets + Multi-Casa
- **1 Engenheiro Sénior Full-Time**
  - Responsável: Desenvolvimento de surebet scanner, integração multi-casa, automação
  - Skills: Python, APIs, automação, Betfair API
  - Salário: €3.000-4.000/mês

- **1 Suporte Part-Time (20h/semana)**
  - Responsável: Monitorização, suporte manual, KYC/contas
  - Skills: Excel, comunicação, atenção a detalhes
  - Salário: €800-1.000/mês

**Custo Total:** €3.800-5.000/mês

#### Fase 6 (Mês 16-18): Trading + A/B Testing
- **1 Engenheiro Sénior Full-Time** (continua)
- **1 Engenheiro de Dados / DevOps Full-Time**
  - Responsável: ETL pipelines, MLOps, CI/CD, monitoring
  - Skills: Airflow/Dagster, Docker, Kubernetes, MLflow
  - Salário: €3.500-4.500/mês

- **1 Suporte Part-Time** (continua)

**Custo Total:** €7.300-9.500/mês

#### Fase 7-8 (Mês 19-24): Market Making + Investidores
- **1 Engenheiro ML Full-Time**
  - Responsável: Modelos avançados, feature engineering, research
  - Skills: Python, XGBoost/LightGBM, estatística, research
  - Salário: €4.000-5.000/mês

- **1 Engenheiro de Software Full-Time**
  - Responsável: APIs, frontend, execution engine, risk management
  - Skills: Python, FastAPI, React, PostgreSQL
  - Salário: €3.500-4.500/mês

- **1 Operations / Risk Manager Full-Time**
  - Responsável: Gestão de risco, compliance, relatórios, comunicação com investidores
  - Skills: Excel, comunicação, gestão de risco, compliance
  - Salário: €2.500-3.500/mês

**Custo Total:** €10.000-13.000/mês

### 3.2 Custos de Infraestrutura

| Item | Fase 5 | Fase 6 | Fase 7-8 |
|------|--------|--------|----------|
| VPS/Cloud | €100/mês | €200/mês | €500/mês |
| Dados (APIs) | €300/mês | €500/mês | €800/mês |
| Software (MLflow, etc.) | €50/mês | €100/mês | €200/mês |
| Legal/Compliance | €0 | €200/mês | €500/mês |
| **Total** | **€450/mês** | **€1.000/mês** | **€2.000/mês** |

### 3.3 Custo Total por Fase

| Fase | Pessoal | Infraestrutura | Total Mensal | Total (12 meses) |
|------|---------|----------------|--------------|-------------------|
| 5 (13-15) | €4.400 | €450 | €4.850 | €14.550 |
| 6 (16-18) | €8.500 | €1.000 | €9.500 | €28.500 |
| 7-8 (19-24) | €11.000 | €2.000 | €13.000 | €78.000 |

---

## 4. SYSTEMIC RISK MANAGEMENT

### 4.1 Circuit Breakers Globais

**Regra:** Quando um circuit breaker global é ativado, TODAS as estratégias não-garantidas são pausadas imediatamente. Apenas surebets continuam operacionais.

| Trigger | Ação | Condição de Reativação |
|---------|-------|------------------------|
| Drawdown global > 20% | Pausar value betting, trading, market making, lays | Drawdown < 15% por 7 dias consecutivos |
| Falha de 2+ casas simultânea | Reduzir exposição global em 50% | Casas restauradas e estabilidade por 3 dias |
| ROI mensal < -10% | Pausar todas as estratégias exceto surebets | ROI > 0% no mês seguinte |
| Volatilidade P&L diária > 5% | Reduzir stake em 50% | Volatilidade < 2% por 5 dias |
| Evento de cauda (COVID, cancelamento) | Liquidação de posições abertas, pausa total | Mercado normalizado por 14 dias |

### 4.2 Gestão de Risco por Estratégia

#### Value Betting
- Max stake por aposta: 2% da banca
- Max exposição por desporto: 20% da banca
- Max exposição por casa: 15% da banca
- Min CLV: 2% (NBA/Football), 3% (MMA)

#### Surebets
- Max stake por surebet: €500
- Max exposição total em surebets: 10% da banca
- Min ROI surebet: 0.5%
- Volume por casa: < €1.000/mês

#### Trading Pré-Jogo
- Max stake por trade: 1% da banca
- Max trades abertos simultâneos: 10
- Min edge para entrar: 3%
- Stop loss: -2% ou 30 minutos

#### Market Making
- Max tamanho de ordem: €200
- Max ordens abertas: 20
- Min spread: 2 ticks
- Adverse selection filter ativo

#### Lays
- Max stake por lay: 1% da banca
- Max exposição em lays: 10% da banca
- Min CLV lay: 2%
- Max liability: 5% da banca

### 4.3 Disaster Recovery

#### Ciberataque
- Backup diário automatizado em cloud separada
- Redundância geográfica de servidores
- Protocolo de resposta a incidentes (24h)
- Seguro cibernético (opcional, Fase 7+)

#### Falha de Infraestrutura
- VPS backup ready-to-deploy (30 minutos)
- Manual fallback procedures documentados
- Comunicação com investidores em < 2 horas
- Sistema de alertas multi-canal (Telegram, SMS, Email)

#### Falha de Liquidez
- Reserva de emergência: 10% da banca em cash
- Linhas de crédito com casas (quando disponível)
- Protocolo de redução de exposição gradual
- Comunicação proativa com investidores

---

## 5. STEALTH BETTING PATTERNS

### 5.1 Estratégia para Casas que Limitam

A Bet365 limita agressivamente contas que mostram padrões de value betting. A seguinte estratégia "stealth" minimiza a probabilidade de limitação:

#### 5.1.1 Padrões de Apostas

**Apostas com Valores Redondos**
- Em vez de Kelly exato (€237.42), usar valores redondos (€200, €250)
- Parece mais "natural" para apostadores recreativos
- Reduz flags de algoritmo

**Apostas "Perdedoras" Deliberadas**
- Incluir 10-15% de apostas em mercados de baixa liquidez com edge negativo pequeno (-0.5% a -1%)
- Disfarça o padrão de value betting
- Custo: pequena redução de ROI global (0.2-0.3%)

**Rotação de Contas**
- 3-5 contas ativas por casa
- Documento KYC preparado para cada conta
- Distribuir volume uniformemente entre contas
- Pausar contas por 2-3 semanas após período de alta atividade

**Limitação de Volume por Casa**
- Max €500-1.000/mês por casa
- Evitar picos de volume (> €200 em 24h)
- Distribuir apostas ao longo do dia (não todas às 10:00)

#### 5.1.2 Comportamento de Navegação

**Simular Comportamento Humano**
- Navegar no site antes de apostar (30-60 segundos)
- Verificar outros mercados (não só o alvo)
- Fazer logout/login periódico
- Evitar apostas em horários não naturais (ex: 3:00 da manhã)

**Diversificação de Mercados**
- Não apostar sempre no mesmo tipo de mercado
- Misturar Moneyline, Spread, Totais
- Incluir apostas em ligas secundárias ocasionalmente

### 5.2 Monitorização de Limitação

**Indicadores de Limitação**
- Stake máximo reduzido drasticamente
- Mercado bloqueado
- Requisito de verificação adicional
- Atrasos no processamento de levantamentos

**Resposta à Limitação**
- Pausar imediatamente a casa
- Mover volume para outras casas
- Considerar "cooling off" por 30-60 dias
- Se persistir, encerrar conta e abrir nova (se possível)

---

## 6. SUREBET RISK MANAGEMENT

### 6.1 Risco de "Palpable Error"

Surebets são matematicamente lucro garantido, mas as casas anulam frequentemente apostas de arbitragem sob alegação de "erro palpável".

#### 6.1.1 Filtros de Detecção de Erro

**Verificação de Discrepância de Odds**
- Se discrepância > 10% da média do mercado → POSSÍVEL ERRO
- Se discrepância > 15% da média do mercado → ERRO PROVÁVEL
- Ação: Evitar surebet

**Verificação de Contexto**
- Se evento está em < 2 horas → Maior risco de erro
- Se mercado tem liquidez muito baixa (< €1.000) → Maior risco
- Se é mercado exótico (correct score, método de vitória) → Maior risco
- Ação: Evitar surebet

#### 6.1.2 Gestão de Volume

**Volume por Surebet**
- Max €200-500 por surebet
- Reduzir volume se discrepância > 5%
- Nunca > 10% da banca em surebets totais

**Reserva para Voided Bets**
- Reserva de emergência: 5% da banca
- Para cobrir apostas anuladas
- Para cobrir situações onde uma perna é anulada mas a outra não

### 6.2 Exclusões de Mercado

**Mercados a Evitar (Alto Risco de Erro)**
- Correct score (futebol)
- Método de vitória (MMA)
- Prop bets exóticos
- Markets com < 3 casas

**Mercados Preferidos (Baixo Risco de Erro)**
- Moneyline principal
- Spread principal
- Totais (Over/Under)
- Asian Handicap

---

## 7. ADVERSE SELECTION FILTER

### 7.1 Risco de Seleção Adversa no Market Making

Na Betfair, ordens limitadas que são correspondidas rapidamente são frequentemente as que estão "erradas" — ou seja, está a comprar algo que o mercado sabe que vale menos.

### 7.2 AdverseSelectionFilter

```python
class AdverseSelectionFilter:
    def __init__(self):
        self.min_fill_time = 30  # segundos
        self.max_fill_time = 300  # segundos
        self.max_adverse_move = 0.02  # 2%
    
    def check_fill(self, fill_time_seconds, price_before, price_after):
        """
        Verifica se a correspondência é válida ou adversa.
        """
        # Regra 1: Se correspondida muito rápido → provavelmente adversa
        if fill_time_seconds < 5:
            return False, "Fill too fast - adverse selection likely"
        
        # Regra 2: Se correspondida muito lentamente → pode ser legítima
        if fill_time_seconds > self.min_fill_time:
            return True, "Fill time acceptable"
        
        # Regra 3: Se preço piora significativamente após fill → adversa
        price_change = abs(price_after - price_before) / price_before
        if price_change > self.max_adverse_move:
            return False, f"Price moved {price_change:.1%} against us - adverse"
        
        return True, "Fill acceptable"
```

### 7.3 Monitorização Pós-Correspondência

**Regras de Monitoramento**
- Se odd piora > 2% em 1 minuto após fill → Fazer lay imediato
- Se odd piora > 5% em 5 minutos após fill → Fazer lay imediato
- Se odd melhora → Manter posição (legítimo)

**Cancelamento Imediato**
- Se fill < 5 segundos → Cancelar posição
- Se adverse selection detectado → Cancelar posição
- Se mercado move contra nós > 3% → Cancelar posição

---

## 8. KILL CRITERIA POR ESTRATÉGIA

### 8.1 Critérios de Desligamento

#### Surebets
- **ROI < 0.5% após 100 surebets** → Custo de oportunidade vs manter capital parado
- **Taxa de voided bets > 5%** → Risco de erro palpável muito alto
- **Volume disponível < €10.000/mês** → Mercado saturado, não escalável

#### Trading Pré-Jogo
- **Percentagem de trades hedged com sucesso < 60%** → Modelo de timing falhando
- **ROI médio por trade < 1%** → Edge insuficiente
- **Volatilidade de P&L > 10% diário** → Risco muito alto

#### Market Making
- **Fill rate < 30%** → Liquidez insuficiente
- **Adverse selection > 2%** → Mercado está contra nós
- **Spread médio < 1 tick** → Não compensa risco

#### Lays
- **CLV médio negativo após 50 lays** → Modelo errado
- **Taxa de eventos cancelados > 10%** → Risco de eventos não ocorrerem
- **Exposure máxima atingida > 80% da capacidade** → Risco catastrófico

### 8.2 Processo de Desligamento

**Quando um critério é atingido:**
1. Pausar imediatamente novas entradas
2. Fechar posições abertas (se aplicável)
3. Análise post-mortem (7 dias)
4. Decisão: desligar permanentemente ou ajustar e retestar

---

## 9. INVESTOR TERMS — EARLY STAGE VS MATURE

### 9.1 Estrutura de Fees

| Termo | Early Stage (Anos 1-2) | Mature (Anos 3+) |
|-------|------------------------|-----------------|
| Management Fee | 0% | 1-2% ao ano |
| Performance Fee | 10-15% | 20% |
| Hurdle Rate | 5% ao ano | 0% |
| High Watermark | Sim | Sim |
| Clawback Clause | Sim | Sim |
| Lock-up Period | 6 meses | 12 meses |
| Withdrawal Notice | 30 dias | 90 dias |

### 9.2 Hurdle Rate

**Early Stage:** Só cobrar performance fee se ROI > 5% ao ano
- Protege investidores de pagar fees em anos de baixo desempenho
- Alinha interesses: só ganhamos se investidores ganham significativamente

**Mature:** Sem hurdle rate
- Track record estabelecido
- Confiança na consistência

### 9.3 High Watermark

**Definição:** Só cobrar performance fee sobre lucros acima do pico anterior do NAV (Net Asset Value)

**Exemplo:**
- NAV inicial: €100.000
- Ano 1: +15% → NAV €115.000 → Performance fee calculada sobre €15.000
- Ano 2: -5% → NAV €109.250 → Sem performance fee
- Ano 3: +10% → NAV €120.175 → Performance fee só sobre €10.175 (diferença para €115.000)

### 9.4 Clawback Clause

**Definição:** Se perder dinheiro no ano seguinte, devolver parte da fee cobrada anteriormente

**Exemplo:**
- Ano 1: +20% → Performance fee €20.000
- Ano 2: -10% → NAV abaixo do pico do Ano 1
- Clawback: Devolver €5.000 da performance fee do Ano 1

---

## 10. LEGAL & TAX STRUCTURE

### 10.1 Estrutura Jurídica

**Opções de Estrutura:**

| Jurisdição | Entidade Legal | Vantagens | Desvantagens |
|------------|---------------|-----------|--------------|
| Portugal | LDA | Proteção de património pessoal, familiar | 23% IRC + 23% IRS sobre distribuições |
| UK | Ltd | Proteção limitada, reputação | 19% Corporation Tax |
| Malta | Limited | Tax-friendly para fundos | Requer licença específica |
| Cayman | LLC | 0% imposto, reputação hedge fund | Custo elevado, complexidade |

**Recomendação Inicial:** LDA em Portugal
- Proteção de património pessoal
- Familiaridade legal
- Custo razoável
- Pode migrar para Malta/Cayman quando escala > €1M

### 10.2 Licenciamento

**Dependência da Jurisdição:**
- **Portugal:** Gerir capital de terceiros pode exigir licença de gestão de ativos (CMVM)
- **Malta:** Requer licença MFSA (custo €50.000-100.000)
- **Caymans:** Requer licença CIMA (custo $50.000-100.000)

**Workaround Early Stage:**
- Operar como "tipster premium" (não fundo)
- Investidores pagam subscrição por sinais
- Evita requisitos de licenciamento
- Transição para fundo quando escala > €500k

### 10.3 Impostos

**Portugal:**
- Lucros de apostas em exchanges: 28% (mais-valias)
- Para investidores estrangeiros: Retenção na fonte 28%
- Possível benefício fiscal para fundos de investimento (ex: FIAGM)

**UK:**
- Corporation Tax: 19%
- Capital Gains Tax: 20% (para investidores)

**Malta:**
- Tax-friendly para fundos: 0-5%
- Para investidores estrangeiros: 0-15%

**Caymans:**
- 0% imposto sobre fundo
- 0% sobre investidores estrangeiros

### 10.4 KYC/AML

**Requisitos:**
- Identificação de investidores (passport, prova de residência)
- Source of funds (origem do capital)
- Screening de listas de sanções (PEP, OFAC)
- Manutenção de registros por 5 anos

**Processo:**
- Onboarding digital (initial)
- Verificação manual para investidores > €50k
- Re-verificação anual para investidores ativos

---

## 11. SCALABILITY CEILING & EDGE DECAY

### 11.1 Teto de Escalabilidade

**Limites Físicos:**

| Fator | Limite | Impacto |
|-------|--------|---------|
| Liquidez Betfair (nichos) | €500/aposta | Move odd, reduz edge |
| Limitação de casas | 6 casas | Todas eventualmente limitam |
| Subscritores tipster | 100-200 | Crowding effect |
| Capital total | €5M | Liquidez insuficiente |

**Plano quando atingir teto:**
- Diversificar para mais mercados
- Reduzir stakes por aposta
- Aumentar número de casas
- Transição para fundo institucional (diferente modelo)

### 11.2 Edge Decay

**Taxa de Decaimento Esperada:**
- CLV médio decai 0.2-0.5% por trimestre
- Após 18-24 meses, edge pode ser 30-50% do inicial

**Combate ao Edge Decay:**
- **Inovação contínua:** Novos mercados, novas features
- **Model refresh:** Retreino trimestral com dados recentes
- **Feature engineering:** Adicionar features novos regularmente
- **Pivot estratégico:** Se edge < 2% globalmente, mudar desporto/estratégia

**Monitorização:**
- CLV médio por trimestre
- ROI por desporto por mês
- Taxa de sucesso de modelo por mês
- Comparação vs baseline histórico

---

## 12. EXIT STRATEGY (ANO 3-5)

### 12.1 Opções de Saída

**Opção 1: Vender a Empresa de Apostas**
- Compradores potenciais: DraftKings, FanDuel, Bet365, Entain
- Valorização: 3-5x EBITDA
- Timing: Quando AUM > €5M e ROI consistente > 8%

**Opção 2: Continuar como Negócio de Rendimento Passivo**
- Manter operação com equipa reduzida
- ROI 6-8% com baixo esforço
- Timing: Quando atingir escala confortável

**Opção 3: Abrir a Investidores Institucionais**
- Family offices, fundos de pensões, wealth managers
- Capital: €10M-50M
- Timing: Quando track record > 3 anos e AUM > €1M

**Opção 4: IPO (Initial Public Offering)**
- Listar em bolsa (ex: AIM London)
- Aumentar capital significativamente
- Timing: Quando AUM > €50M e operação institucional

### 12.2 Visão de Longo Prazo

**Ano 3:**
- AUM: €1M-2M
- ROI: 8-10%
- Equipa: 3-4 pessoas
- Estratégias: 4-5

**Ano 4:**
- AUM: €2M-5M
- ROI: 7-9%
- Equipa: 5-7 pessoas
- Estratégias: 5-6
- Considerar venda ou expansão institucional

**Ano 5:**
- AUM: €5M-10M
- ROI: 6-8%
- Equipa: 7-10 pessoas
- Estratégias: 6-8
- Decisão de saída ou continuação

---

## 13. MELHORIAS PRIORITÁRIAS (STATUS)

| # | Melhoria | Status | Responsável | Prazo |
|---|----------|--------|-------------|-------|
| 1 | Team & Resources Required | ✅ COMPLETO | CIO | Fase 5 |
| 2 | Systemic Risk Management | ✅ COMPLETO | Risk Manager | Fase 5 |
| 3 | Stealth Betting Patterns | ✅ COMPLETO | Operations | Fase 5 |
| 4 | Surebet Risk Management | ✅ COMPLETO | Risk Manager | Fase 5 |
| 5 | Adverse Selection Filter | ✅ COMPLETO | Engenheiro Software | Fase 7 |
| 6 | Kill Criteria por estratégia | ✅ COMPLETO | Risk Manager | Fase 6 |
| 7 | Investor Terms realistas | ✅ COMPLETO | CIO | Fase 7 |
| 8 | Legal & Tax Structure | ✅ COMPLETO | Legal Advisor | Fase 7 |
| 9 | Scalability Ceiling & Edge Decay | ✅ COMPLETO | CIO | Fase 8 |
| 10 | Exit Strategy (ano 3-5) | ✅ COMPLETO | CIO | Fase 8 |

---

## 14. PRÓXIMOS PASSOS

### 14.1 Antes de Iniciar VBQ-003

**Pré-condições:**
- [ ] VBQ-002 estável com ROI > 12%
- [ ] NBA baseline validado por 6+ meses
- [ ] Football e MMA/UFC validados (VBQ-002 completo)
- [ ] Melhorias prioritárias 1-5 implementadas
- [ ] Equipa Fase 5 contratada
- [ ] Capital para 18 meses: €150k (pessoal + infraestrutura)

### 14.2 Fase 5 Kickoff (Mês 13)

**Mês 13:**
- Contratar engenheiro sénior e suporte part-time
- Implementar surebet scanner multi-casa
- Implementar stealth betting patterns
- Implementar gestão de risco sistémico
- Configurar infraestrutura (VPS, APIs)

**Mês 14:**
- Testar surebet scanner em produção
- Integrar 3 casas adicionais
- Implementar surebet risk management
- Documentar procedimentos operacionais

**Mês 15:**
- Validar surebets em produção (ROI > 2%)
- Avaliar necessidade de expansão de equipa
- Preparar para Fase 6 (trading)

---

## 15. APÊNDICE A: COMPARAÇÃO VBQ-002 VS VBQ-003

| Dimensão | VBQ-002 | VBQ-003 | Salto de Complexidade |
|----------|----------|----------|----------------------|
| Casas de Apostas | 1-2 | 4-6 | 3x |
| Estratégias | 1 (value betting) | 5 (multi-estratégia) | 5x |
| Equipa | 1 FTE | 2-3 FTE | 2-3x |
| Capital | €2k-10k | €100k-1M+ | 10-100x |
| ROI Esperado | 12-15% | 8-12% | -3-7% |
| Risco | Médio | Médio-Alto | + |
| Escalabilidade | Limitada | Alta | +++ |
| Tempo para Implementar | 12 meses | 48 meses | 4x |

---

## 16. APÊNDICE B: CHECKLIST PRÉ-FASE 5

**Financeiro:**
- [ ] Capital para 18 meses disponível (€150k)
- [ ] Reserva de emergência (10% da banca)
- [ ] Linha de crédito configurada (opcional)

**Pessoal:**
- [ ] Engenheiro sénior contratado
- [ ] Suporte part-time contratado
- [ ] Contratos de trabalho assinados
- [ ] NDA assinados por todos

**Técnico:**
- [ ] VPS configurado com backup
- [ ] APIs de dados contratadas
- [ ] Surebet scanner desenvolvido
- [ ] Sistema de monitorização configurado

**Legal:**
- [ ] Entidade legal constituída (LDA)
- [ ] Conta bancária separada
- [ ] Contratos de investidores preparados
- [ ] KYC/AML procedures documentados

**Operacional:**
- [ ] Procedimentos de stealth betting documentados
- [ ] Circuit breakers configurados
- [ ] Manual de operações completo
- [ ] Plano de disaster recovery pronto

---

**Data de Criação:** 2026-05-13
**Versão:** 3.1.0-Institutional
**Próxima Revisão:** Trimestral
**Owner:** Chief Investment Officer
**Status:** Pronto para revisão por investidores institucionais
