# APIs_ESPORTOS — APIs para Diferentes Desportos

**ID:** `MSE-008` | **Fase:** #phase/7-12 | **Owner:** Data Engineer | **Status:** #status/active | **Versão:** `2.0.0-VBQ-002`

---

## 1. OBJETIVO

Documentar as APIs disponíveis para ingestão de dados e execução de apostas em diferentes desportos, incluindo custos, limitações e estratégias de integração.

---

## 2. FRAMEWORK DE AVALIAÇÃO DE APIs

### 2.1 Critérios de Avaliação

Cada API é avaliada em 6 dimensões:

| Critério | Descrição |
|----------|-----------|
| **Custo** | Preço mensal, pay-per-call, gratuito |
| **Coverage** | Dados disponíveis (histórico, live, detalhe) |
| **Latency** | Velocidade de atualização de dados |
| **Reliability** | Uptime, qualidade de dados |
| **Documentation** | Qualidade da documentação, suporte |
| **Rate Limits** | Limites de chamadas por minuto/hora |

### 2.2 Escoring System
- **5 = Excelente** (gratuito, cobertura completa, baixa latência)
- **3 = Médio**
- **1 = Ruim** (caro, cobertura limitada, alta latência)

---

## 3. APIs DE DADOS

### 3.1 NBA APIs

#### 3.1.1 NBA Official API
- **Custo:** Gratuito
- **Coverage:** Dados oficiais, estatísticas completas
- **Latency:** Baixa (atualizações em tempo real)
- **Reliability:** Muito alta (oficial)
- **Documentation:** Excelente
- **Rate Limits:** Generosos
- **Score:** 5/5

**Endpoints Principais:**
- `https://stats.nba.com/stats/leaguegamelog` - Game logs
- `https://stats.nba.com/stats/boxscoretraditionalv2` - Box scores
- `https://stats.nba.com/stats/commonteamroster` - Rosters
- `https://stats.nba.com/stats/playercareerstats` - Player stats

**Notas:**
- Requer headers específicos (User-Agent, Referer)
- Rate limiting não documentado mas generoso
- Dados históricos disponíveis até 1996

#### 3.1.2 Basketball-Reference.com (Scraping)
- **Custo:** Gratuito
- **Coverage:** Dados históricos extensos
- **Latency:** Alta (atualização diária)
- **Reliability:** Média (pode mudar estrutura)
- **Documentation:** N/A (scraping)
- **Rate Limits:** Depende de implementação
- **Score:** 3/5

**Notas:**
- Backup para NBA API
- Estrutura HTML pode mudar (risco de breaking)
- Dados mais detalhados em alguns aspetos

---

### 3.2 Football APIs (VBQ-002)

#### 3.2.1 Football-Data.org
- **Custo:** Gratuito
- **Coverage:** Dados históricos extensos (top 5 ligas europeias)
- **Latency:** Média (atualização semanal)
- **Reliability:** Alta (fonte estável)
- **Documentation:** Excelente
- **Rate Limits:** Generosos
- **Score:** 4/5

**Dados Disponíveis:**
- Match results
- League standings
- Team statistics
- Odds históricos

**Notas:**
- Principal fonte gratuita para futebol
- Excelente para backtesting
- Cobertura limitada a top ligas

#### 3.2.2 API-Football
- **Custo:** Gratuito (tier gratuito) / Pago (tier premium)
- **Coverage:** Dados em tempo real, cobertura global
- **Latency:** Baixa (tempo real)
- **Reliability:** Alta
- **Documentation:** Boa
- **Rate Limits:** 100 calls/min (gratuito)
- **Score:** 4/5

**Dados Disponíveis:**
- Lineups
- Lesões
- Estatísticas detalhadas
- Odds ao vivo

**Notas:**
- Excelente para dados em tempo real
- Tier gratuito suficiente para início
- Tier premium necessário para dados avançados

#### 3.2.3 FBref
- **Custo:** Gratuito (scraping)
- **Coverage:** Estatísticas avançadas (xG, xA, etc.)
- **Latency:** Média (atualização diária)
- **Reliability:** Média (scraping)
- **Documentation:** N/A (site estático)
- **Rate Limits:** Depende de implementação
- **Score:** 3/5

**Dados Disponíveis:**
- xG (Expected Goals)
- xA (Expected Assists)
- Estatísticas avançadas
- Squad data

**Notas:**
- Fonte principal para xG
- Scraping necessário
- Risco de structure changes

#### 3.2.4 Sportmonks
- **Custo:** Pago
- **Coverage:** Dados completos em tempo real
- **Latency:** Muito baixa (tempo real)
- **Reliability:** Muito alta
- **Documentation:** Excelente
- **Rate Limits:** Definidos por plano
- **Score:** 4/5 (devido ao custo)

**Notas:**
- API profissional de futebol
- Dados de alta qualidade
- Considerar se APIs gratuitas insuficientes

---

### 3.3 MMA/UFC APIs (VBQ-002)

#### 3.3.1 UFC Stats API
- **Custo:** Gratuito
- **Coverage:** Dados oficiais UFC
- **Latency:** Baixa (tempo real)
- **Reliability:** Muito alta (oficial)
- **Documentation:** Média
- **Rate Limits:** Generosos
- **Score:** 5/5

**Dados Disponíveis:**
- Fighter statistics
- Match results
- Event data
- Fight metrics

**Notas:**
- Fonte oficial UFC
- Excelente para dados básicos
- Limitada em dados históricos extensos

#### 3.3.2 Sherdog
- **Custo:** Gratuito (scraping)
- **Coverage:** Histórico de lutas extensos
- **Latency:** Média (atualização diária)
- **Reliability:** Média (scraping)
- **Documentation:** N/A (site estático)
- **Rate Limits:** Depende de implementação
- **Score:** 3/5

**Dados Disponíveis:**
- Fighter records
- Histórico de lutas
- Opponent data

**Notas:**
- Principal fonte para histórico
- Scraping necessário
- Risco de structure changes

#### 3.3.3 Tapology
- **Custo:** Gratuito
- **Coverage:** Rankings e stats
- **Latency:** Média (atualização diária)
- **Reliability:** Alta
- **Documentation:** N/A (site estático)
- **Rate Limits:** Depende de implementação
- **Score:** 3/5

**Dados Disponíveis:**
- Fighter rankings
- Estatísticas básicas
- Upcoming fights

**Notas:**
- Excelente para rankings
- Scraping necessário
- Complementar a UFC Stats

---

### 3.4 NFL APIs (VBQ-003)

#### 3.4.1 nfl-data-py (Python Library)
- **Custo:** Gratuito
- **Coverage:** Dados completos NFL (2000-presente)
- **Latency:** Média (atualização semanal)
- **Reliability:** Alta
- **Documentation:** Boa
- **Rate Limits:** N/A (library local)
- **Score:** 4/5

**Dados Disponíveis:**
- Play-by-play data
- Team statistics
- Player statistics
- Injury reports
- Weather data

**Notas:**
- Agrega dados de múltiplas fontes
- Facilita feature engineering
- Atualizações regulares

#### 3.4.2 NFL Scraping (Backup)
- **Custo:** Gratuito
- **Coverage:** Dados históricos extensos
- **Latency:** Alta (atualização semanal)
- **Reliability:** Média (scraping)
- **Documentation:** N/A
- **Rate Limits:** Depende de implementação
- **Score:** 3/5

**Notas:**
- Backup para nfl-data-py
- Dados adicionais disponíveis
- Risco de structure changes

#### 3.4.3 NFLGSIS API (Official)
- **Custo:** Gratuito
- **Coverage:** Dados oficiais NFL
- **Latency:** Baixa (tempo real)
- **Reliability:** Muito alta
- **Documentation:** Boa
- **Rate Limits:** Generosos
- **Score:** 4/5

**Notas:**
- Requer registro
- Focada em dados de jogos
- Menos focada em estatísticas agregadas

---

### 3.5 Tennis APIs (VBQ-003)

#### 3.5.1 Tennis Abstract
- **Custo:** Gratuito
- **Coverage:** Estatísticas detalhadas ATP/WTA
- **Latency:** Média (atualização diária)
- **Reliability:** Alta
- **Documentation:** Boa
- **Rate Limits:** N/A (site estático)
- **Score:** 4/5

**Dados Disponíveis:**
- Match results
- Player statistics (serve, return)
- Surface-specific stats
- Head-to-head records
- Tournament results

**Notas:**
- Principal fonte para tennis
- Excelente para feature engineering
- Dados históricos extensos

#### 3.5.2 ATP Tour API
- **Custo:** Requer subscrição
- **Coverage:** Dados oficiais ATP
- **Latency:** Baixa (tempo real)
- **Reliability:** Muito alta
- **Documentation:** Excelente
- **Rate Limits:** Definidos por plano
- **Score:** 3/5 (devido ao custo)

**Notas:**
- Dados oficiais mais atualizados
- Custos podem ser altos
- Considerar apenas se Tennis Abstract insuficiente

#### 3.5.3 Flashscore
- **Custo:** Gratuito
- **Coverage:** Resultados e odds live
- **Latency:** Muito baixa (tempo real)
- **Reliability:** Alta
- **Documentation:** Média
- **Rate Limits:** Limitados na versão gratuita
- **Score:** 3/5

**Notas:**
- Excelente para odds live
- Rate limiting na versão gratuita
- Considerar versão premium se necessário

---

### 3.6 LoL Esports APIs (VBQ-003)

#### 3.6.1 Oracle's Elixir
- **Custo:** Gratuito (para research)
- **Coverage:** Estatísticas detalhadas LoL (todas as regiões)
- **Latency:** Média (atualização diária)
- **Reliability:** Alta
- **Documentation:** Excelente
- **Rate Limits:** N/A (download de CSVs)
- **Score:** 5/5

**Dados Disponíveis:**
- Match results
- Player statistics (KDA, CS, vision)
- Team statistics
- Champion pick/ban rates
- Regional data

**Notas:**
- Principal fonte para LoL research
- Gratuita para uso académico/research
- Excelente documentação

#### 3.6.2 Riot Games API
- **Custo:** Gratuito (com rate limits)
- **Coverage:** Dados oficiais Riot
- **Latency:** Baixa (tempo real)
- **Reliability:** Muito alta
- **Documentation:** Excelente
- **Rate Limits:** Definidos por tier de desenvolvedor
- **Score:** 4/5

**Endpoints Principais:**
- Summoner API - Dados de jogadores
- Match API - Dados de partidas
- League API - Dados de ligas
- Champion API - Dados de champions

**Notas:**
- Requer registro e API key
- Rate limits generosos para desenvolvimento
- Excelente para dados em tempo real

#### 3.6.3 PandaScore
- **Custo:** Freemium
- **Coverage:** Odds e dados de esports
- **Latency:** Baixa (tempo real)
- **Reliability:** Alta
- **Documentation:** Boa
- **Rate Limits:** Definidos por plano
- **Score:** 3/5

**Notas:**
- Excelente para odds de esports
- Versão gratuita com limites
- Considerar premium se necessário

---

### 3.5 Soccer APIs

#### 3.5.1 Football-Data.co.uk
- **Custo:** Gratuito
- **Coverage:** Dados históricos principais ligas
- **Latency:** Alta (atualização semanal)
- **Reliability:** Muito alta
- **Documentation:** Boa
- **Rate Limits:** N/A (download de CSVs)
- **Score:** 5/5

**Dados Disponíveis:**
- Match results
- Odds históricas
- League standings
- Team statistics

**Notas:**
- Principal fonte gratuita para soccer
- Excelente qualidade de dados
- Cobertura de principais ligas europeias

#### 3.5.2 Understat
- **Custo:** Gratuito
- **Coverage:** Advanced metrics (xG, xA)
- **Latency:** Média (atualização diária)
- **Reliability:** Alta
- **Documentation:** Boa
- **Rate Limits:** N/A (site estático/scraping)
- **Score:** 4/5

**Dados Disponíveis:**
- Expected Goals (xG)
- Expected Assists (xA)
- Player advanced stats
- Team advanced stats

**Notas:**
- Fonte principal para xG
- Scraping pode ser necessário
- Dados de alta qualidade

#### 3.5.3 FBref
- **Custo:** Gratuito
- **Coverage:** Estatísticas detalhadas
- **Latency:** Média (atualização diária)
- **Reliability:** Alta
- **Documentation:** Excelente
- **Rate Limits:** N/A (site estático)
- **Score:** 4/5

**Dados Disponíveis:**
- Player statistics
- Team statistics
- Advanced metrics
- Historical data

**Notas:**
- Excelente complemento a Football-Data
- Interface amigável
- Dados bem estruturados

#### 3.5.4 Opta (Stats Perform)
- **Custo:** Premium (caro)
- **Coverage:** Dados profissionais completos
- **Latency:** Muito baixa (tempo real)
- **Reliability:** Muito alta
- **Documentation:** Excelente
- **Rate Limits:** Definidos por contrato
- **Score:** 2/5 (devido ao custo)

**Notas:**
- Padrão da indústria
- Muito caro para MVP
- Considerar apenas se gratuito insuficiente

---

## 4. APIs DE EXECUÇÃO (BETTING)

### 4.1 Betfair API

#### 4.1.1 Betfair Sports API
- **Custo:** Gratuito (comissão em apostas)
- **Coverage:** Todos os mercados Betfair
- **Latency:** Muito baixa (tempo real)
- **Reliability:** Muito alta
- **Documentation:** Excelente
- **Rate Limits:** Definidos por plano
- **Score:** 5/5

**Endpoints Principais:**
- `SportsAPING/v1.0/listMarketCatalogue` - Lista mercados
- `SportsAPING/v1.0/listMarketBook` - Odds em tempo real
- `SportsAPING/v1.0/placeOrders` - Colocar apostas
- `SportsAPING/v1.0/cancelOrders` - Cancelar apostas

**Notas:**
- Principal exchange para betting
- Excelente documentação
- Requer aplicação e aprovação

#### 4.1.2 Betfair Stream API
- **Custo:** Gratuito (comissão em apostas)
- **Coverage:** Streaming de odds em tempo real
- **Latency:** Extremamente baixa (< 100ms)
- **Reliability:** Muito alta
- **Documentation:** Excelente
- **Rate Limits:** Definidos por plano
- **Score:** 5/5

**Notas:**
- Essencial para live betting
- Requer implementação de WebSocket
- Complexidade de implementação alta

---

### 4.2 Broker APIs

#### 4.2.1 Asian Connect (Broker)
- **Custo:** Comissão sobre apostas
- **Coverage:** Múltiplas casas asiáticas
- **Latency:** Baixa
- **Reliability:** Alta
- **Documentation:** Média
- **Rate Limits:** Definidos por broker
- **Score:** 4/5

**Notas:**
- Acesso a casas asiáticas (Pinnacle, SBO)
- Melhores odds que Betfair em alguns mercados
- Requer conta e verificação

#### 4.2.2 Sportmarket (Broker)
- **Custo:** Comissão sobre apostas
- **Coverage:** Múltiplas casas
- **Latency:** Baixa
- **Reliability:** Alta
- **Documentation:** Média
- **Rate Limits:** Definidos por broker
- **Score:** 4/5

**Notas:**
- Similar ao Asian Connect
- Bom para diversificação de casas
- Excelente para arbitragem

---

## 5. ESTRATÉGIA DE INTEGRAÇÃO

### 5.1 Arquitetura de Ingestão

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                        │
│  (Rate limiting, caching, error handling, retry logic)     │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                  Sport-Specific Adapters                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   NBA    │  │ Football │  │   MMA    │  │   NFL    │    │
│  │  Adapter │  │  Adapter │  │  Adapter │  │  Adapter │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                   Data Processing Layer                     │
│  (Normalization, validation, feature engineering)          │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                      Database Layer                         │
│  (PostgreSQL schemas por desporto)                         │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Padrões de Integração

#### 5.2.1 Retry Logic
```python
# Padrão de retry com exponential backoff
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException)
)
def fetch_api_data(url, params):
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()
```

#### 5.2.2 Rate Limiting
```python
# Rate limiting por API
rate_limits = {
    'nba_api': RateLimiter(max_calls=100, period=60),  # 100 calls/min
    'nfl_api': RateLimiter(max_calls=50, period=60),   # 50 calls/min
    'riot_api': RateLimiter(max_calls=20, period=1),   # 20 calls/sec
}

@rate_limit('nba_api')
def fetch_nba_data(endpoint):
    # Implementation
    pass
```

#### 5.2.3 Caching Strategy
```python
# Cache de dados que não mudam frequentemente
@cache(ttl=3600)  # 1 hour cache
def fetch_static_data(url):
    # Dados que mudam pouco (rosters, schedules)
    pass

@cache(ttl=300)  # 5 min cache
def fetch_dynamic_data(url):
    # Dados que mudam mais frequentemente (odds, injuries)
    pass
```

### 5.3 Error Handling

#### 5.3.1 Error Categories
- **Transient Errors:** Network issues, rate limits (retry)
- **Permanent Errors:** 404, invalid parameters (log and alert)
- **Data Quality Errors:** Missing data, invalid values (flag for review)

#### 5.3.2 Alerting
- Alertar se API down > 5 minutos
- Alertar se rate limit excedido consistentemente
- Alertar se data quality issues > threshold

---

## 6. GESTÃO DE CUSTOS

### 6.1 Custo Estimado por Desporto

| Desporto | APIs Gratuitas | APIs Pagas | Custo Mensal Estimado |
|----------|----------------|------------|----------------------|
| NBA | NBA API | Nenhuma | 0€ |
| NFL | nfl-data-py | Nenhuma | 0€ |
| Tennis | Tennis Abstract | ATP API (opcional) | 0-50€ |
| LoL | Oracle's Elixir, Riot API | PandaScore (opcional) | 0-30€ |
| Soccer | Football-Data, Understat, FBref | Opta (opcional) | 0-100€ |

### 6.2 Estratégia de Custos
1. **Começar com APIs Gratuitas:** Usar apenas APIs gratuitas inicialmente
2. **Avaliar Necessidade:** Adicionar APIs pagas apenas se gratuito insuficiente
3. **Negociar:** Alguns provedores oferecem descontos para research/académico
4. **Monitorizar Uso:** Tracking de custos mensalmente

---

## 7. RISCOS E MITIGAÇÃO

### 7.1 Risco: API Shutdown
**Mitigação:**
- Ter sempre backup APIs (scraping)
- Monitorizar status de APIs regularmente
- Arquivar dados históricos localmente

### 7.2 Risco: Rate Limits Excedidos
**Mitigação:**
- Implementar rate limiting robusto
- Caching agressivo de dados estáticos
- Priorizar endpoints críticos

### 7.3 Risco: Data Quality Issues
**Mitigação:**
- Cross-validation entre múltiplas fontes
- Data quality checks automatizados
- Manual review de outliers

### 7.4 Risco: Cost Overrun
**Mitigação:**
- Budget mensal definido
- Alerts quando接近 limite
- Review trimestral de necessidades

---

## 8. FUTURO EVOLUTION

### 8.1 APIs Emergentes
- **Machine Learning APIs:** Alguns provedores oferecem predictions como serviço
- **Alternative Data APIs:** Sentiment analysis, social media data
- **Blockchain APIs:** Dados on-chain para betting descentralizado

### 8.2 Self-Hosting
- Considerar self-hosting de dados críticos
- Reduz dependência de terceiros
- Maior controle sobre qualidade e latência

---

## 9. LINKS CRUZADOS

- [[43_Multi_Sport_Expansion/INDEX]] ← Secção mãe
- [[43_Multi_Sport_Expansion/FOOTBALL_INTEGRATION]] → APIs Football específicas (VBQ-002)
- [[43_Multi_Sport_Expansion/MMA_INTEGRATION]] → APIs MMA/UFC específicas (VBQ-002)
- [[43_Multi_Sport_Expansion/EXPANSAO_NFL]] → APIs NFL específicas (VBQ-003)
- [[43_Multi_Sport_Expansion/EXPANSAO_TENNIS_ATP]] → APIs Tennis específicas (VBQ-003)
- [[43_Multi_Sport_Expansion/EXPANSAO_ESPORTS_LOL]] → APIs LoL específicas (VBQ-003)
- [[43_Multi_Sport_Expansion/EXPANSAO_SOCCER_EPL]] → APIs Soccer específicas (VBQ-003)
- [[14_APIs/INDEX]] → Documentação geral de APIs
- [[04_Data_Engineering/INGESTAO_ODDS]] → Pipeline de ingestão de odds

---

**Data de Criação:** 2026-05-13
**Última Atualização:** 2026-05-13 (VBQ-002)
**Revisão Obrigatória:** Trimestral (próxima: 2026-08-13)
**Owner:** Data Engineer