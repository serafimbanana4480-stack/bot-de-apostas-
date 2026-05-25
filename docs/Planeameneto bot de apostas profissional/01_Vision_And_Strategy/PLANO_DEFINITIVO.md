# PLANO_DEFINITIVO — SISTEMA DE VALUE BETTING ROBUSTO

**ID:** `PLN-001` | **Fase:** #phase/1-6 | **Owner:** Chief Systems Architect + Principal Quant Engineer | **Status:** #status/active
**Data de Criação:** `2026-05-13` | **Última Revisão:** `2026-05-13`

---

## 1. ÍNDICE

1. Visão Geral e Arquitetura Conceptual
2. Stack Tecnológica Definitiva
3. Desporto, Mercado e Dados
4. Feature Engineering Robusto
5. Modelação (Primário + Meta-Labeling)
6. Validação e Backtest Rigoroso
7. Gestão de Risco e Sizing
8. Funcionamento em Produção (Passo a Passo)
9. Execução Progressiva (Manual → One-Click → Auto)
10. Monitorização e MLOps Leves
11. Modelo de Negócio Tipster
12. Roadmap de Implementação (6 Meses)
13. Riscos, Mitigações e Plano de Contingência

---

## 2. VISÃO GERAL E ARQUITETURA CONCEPTUAL

O sistema é composto por seis módulos coesos que trocam dados através de PostgreSQL e Redis:

1. **Ingestão de Dados** – scripts em Python recolhem odds (contínuo), estatísticas, lesões e calendário. O motor de decisão corre a cada 2 horas em dias de jogo (08:00, 10:00, 12:00, 14:00, 16:00). Cada execução valida integridade e grava versões dos dados.
2. **Feature Engineering** – transforma dados brutos em variáveis de alta qualidade (decaimento temporal, métricas de mercado, contexto e interações no mesmo timestamp). Todo cálculo nasce com proteção contra look-ahead.
3. **Modelos** – um XGBoost primário estima a probabilidade do resultado; um meta-modelo XGBoost filtra sinais de baixa confiança.
4. **Motor de Decisão** – calcula edge, aplica thresholds mínimos (edge > 4%), chama o meta-modelo e decide stakes com limites de Kelly fracionado.
5. **Distribuição de Sinais** – escreve sinais aprovados no Redis, registra em PostgreSQL e dispara notificações via Telegram/email com deep links.
6. **Monitorização e Reporting** – dashboard Grafana + alertas Telegram recoge métricas de negócio e estabilidade.

**Princípio básico:** toda execução é batch síncrono (pré-jogo). Latência alvo: 2–5 segundos por evento, o que mantém a stack leve e previsível.

---

## 3. STACK TECNOLÓGICA DEFINITIVA

| Componente | Tecnologia | Justificação |
|------------|------------|--------------|
| Linguagem | Python 3.11 | Ecossistema ML maduro, async-friendly, compatível com todos os módulos. |
| Base de Dados | PostgreSQL 15 | ACID, window functions, JSONB, particionamento por época. |
| Cache | Redis | Odds quentes, filas de sinais e circuit breakers em memória. |
| ML | XGBoost 2.0 + scikit-learn | Melhor trade-off precisão/velocidade para dados tabulares e fácil integração com Optuna. |
| Calibração | Isotónica por regime (sklearn) | Simples, robusto e interpretável em três regimes. |
| Validação | Purged walk-forward CV (custom) | Evita look-ahead e garante consistência temporal. |
| Backend API | FastAPI | Leve, async, documentação automática, deploy monolito. |
| Tarefas periódicas | Prefect (self-hosted) ou Crontab + scripts Python | Orquestração simples sem complexidade desnecessária. |
| Deploy | 1 VPS (4 vCPU, 8 GB RAM, 100 GB SSD) | Processamento batch e inferência com latência ≤5s. |
| Frontend | Telegram Bot (python-telegram-bot) + emails (SendGrid) | Entrega imediata e custo zero. |
| Monitorização | Prometheus + Grafana (containers leves) | Métricas técnicas e de negócio com alertas. |

**Custo mensal estimado:** ~12€ VPS (Hetzner CPX31) + 0€ software = <15€/mês inicial.

---

## 4. DESPORTO, MERCADO E DADOS

### 4.1 Desporto e Mercados Iniciais
- **NBA** (apostas Moneyline e Point Spread, handicap asiático). 1230 jogos/época oferece significância estatística acelerada.
- **Porquê a NBA:** dados grátis (nba_api, Basketball-Reference), ineficiências conhecidas (back-to-back, viagens) e liquidez suficiente.

### 4.2 Fontes de Dados Gratuitas
- **Odds:** Betfair Exchange API (produção) + Pinnacle (fecho) via repositórios públicos para backtest.
- **Estatísticas:** nba_api (play-by-play, métricas avançadas), Basketball-Reference (Four Factors, pace, ratings).
- **Lesões:** feeds ESPN RSS + Twitter oficial; spaCy para extrair status e nomes.
- **Calendário/Viagens:** nba_api + geopy para calcular distâncias e fadiga.

### 4.3 Pipeline de Ingestão
- Odds Betfair: capturadas a cada 5 minutos (cache em Redis).
- Estatísticas e lesões: atualizadas a cada 2 horas em dias de jogo.
- Motor de decisão: executado a cada 2 horas (08:00, 10:00, 12:00, 14:00, 16:00) em dias de jogo NBA.
- Dados persistidos em PostgreSQL com checks de integridade e versionamento.

---

## 5. FEATURE ENGINEERING ROBUSTO

### A. Forma Recente com Decaimento Temporal
- Win rate ponderado com half-life de 5 jogos.
- Four Factors (eFG%, TOV%, ORB%, FT/FGA) com decaimento exponencial.
- Net Rating e momentum (diferença entre rating ofensivo atual e da época).

### B. Métricas de Mercado
- CLV implícito: diferença entre odd Betfair e odd de fecho Pinnacle.
- Percentagem de dinheiro vs. número de apostas (quando disponível).
- Dispersão de odds entre casas (desvio padrão) quando múltiplas fontes existem.

### C. Contexto de Jogo e Calendário
- Flags de back-to-back, dias de descanso e distância percorrida.
- Jogos em casa/fora e rivalidades premium quando aplicável.
- Rotação de plantel, idade média e história de viagens.

### D. Interações Não Lineares
- Pace da equipa × rating defensivo do adversário.
- eFG% ofensivo × eFG% defensivo do rival.
- Back-to-back × idade média do elenco.

**Total de features:** 80, perfeitamente geríveis pelo XGBoost (15 forma + 12 mercado + 18 contexto + 20 jogadores + 15 interações).

---

## 6. MODELAGEM (PRIMÁRIO + META-LABELING)

### 6.1 Modelo Primário
- Algoritmo: XGBoost com `binary:logistic` (Moneyline) e `multi:softmax` (Spread).
- Hiperparâmetros otimizados via Optuna dentro do walk-forward.
- Target: 1 para vitória/cobertura do spread, 0 caso contrário.
- Output: probabilidade calibrada `P_modelo`.

### 6.2 Meta-Labeling
- Algoritmo: XGBoost `binary:logistic`.
- Features: `P_modelo`, edge estimado, entropia das probabilidades, regime de jogo, quantidade de dados usados.
- Target: 1 se o CLV estimado é positivo (odd de fecho > odd usada).
- Output: `P_meta` (probabilidade do edge ser genuíno).

**Regra de aposta:** gerar sinal apenas se `edge > 4%` **e** `P_meta > 0.6`.

### 6.3 Calibração
- Calibradores isotónicos separados por regime (favorito ≥65%, equilibrado 35-65%, underdog <35%).
- Métricas: Brier Score, ECE e reliability diagrams por regime.

---

## 7. VALIDAÇÃO E BACKTEST RIGOROSO

### 7.1 Purged Walk-Forward CV
- Janelas: 3 épocas treino, 1 época validação, 1 época teste final (não usado em tuning).
- Embargo de 2 dias entre janelas para evitar leakage.
- Modelo retreinado mensalmente, incorporando dados recentes.

### 7.2 Métricas de Decisão
- **CLV médio:** alvo > 2% vs Pinnacle.
- **ROI simulado:** > 5% após comissões (5%) e slippage (0.5%).
- **Sharpe Ratio:** > 0.5.
- **Drawdown máximo** e tempo de recuperação também monitorados.

### 7.3 Simulações de Monte Carlo
- 10.000 sequências com probabilidades estimadas + stakes históricos.
- Estima distribuições de drawdown e probabilidade de ruína para frações de Kelly.
- Critério de passagem: `CLV > 2%`, `ROI > 5%`, `Sharpe > 0.5`.

---

## 8. GESTÃO DE RISCO E SIZING

### 8.1 Fórmula de Edge
```
edge = P_modelo × odd_betfair − 1
```
Edge deve ser > 4% e o meta-modelo precisa dar sinal verde.

### 8.2 Kelly Fracionado e Limites
- **Meio Kelly (K=0.5):** `fração = 0.5 × (P_modelo × odd − 1) / (odd − 1)`.
- **Stake:** `fração × bankroll`.
- **Limites fixos:** 2% do bankroll por aposta, 4% por jogo (vários mercados), 12% exposição diária.

### 8.3 Circuit Breakers
- Drawdown desde o pico > 15% → cortar stakes em 50% até drawdown < 10%.
- 5 perdas consecutivas → pausa de 1 hora + notificação manual.
- Falha de feed de odds > 5 minutos → nenhum novo sinal até retorno.

---

## 9. FUNCIONAMENTO EM PRODUÇÃO (PASSO A PASSO)

**Agenda diária (dias de jogos NBA):**
- 08:00 – Ingestão inicial de odds Betfair + atualização de estatísticas e lesões.
- 10:00 / 12:00 / 14:00 / 16:00 – Motor de decisão roda a cada 2 horas com features atualizadas.

**Fluxo:**
1. Calcular features atualizadas (inclui decay e contexto).
2. Inferência do modelo primário e calibração isotónica.
3. Capturar odd Betfair mais recente e calcular edge.
4. Se `edge > 4%`, chamar o meta-modelo.
5. Se `P_meta > 0.6`, gravar sinal em Redis + registrar em PostgreSQL.
6. Telegram Bot lê a cache e envia mensagem com jogo, mercado, odd, edge e stake (% do bankroll).
7. Operador aposta manualmente via Betfair.
8. Após o jogo, registrar resultados (PnL, slippage, fill rate) e alimentar módulo de monitorização.

---

## 10. EXECUÇÃO PROGRESSIVA

### Fase 1 – Manual (Mês 4)
- Sinais via Telegram.
- Usuário executa manualmente.
- Vantagens: compliance clara, zero risco de automação precoce.

### Fase 2 – One-Click Betting (Mês 6+)
- Frontend leve (React ou HTML+JS) gera deep links com mercado e odd pré-selecionados.
- API FastAPI monta links Betfair, operando como camada de interface.

### Fase 3 – Automática na Exchange (opcional)
- Integração Betfair API com limit orders, timeout de 60s e cancelamento se odd se mover.
- Requisitos: conta verificada, app key desenvolvedor, monitorização forte.

---

## 11. MONITORIZAÇÃO E MLOPS LEVES

### 11.1 Dashboard (Grafana)
- ROI acumulado, CLV médio das últimas 50/100 apostas.
- Win rate por regime (home/away, back-to-back).
- Drawdown atual + máximo.
- Status dos feeds (Betfair, NBA, lesões).

### 11.2 Alertas (Telegram para equipe técnica)
- CLV móvel 3 dias < 0%.
- Drawdown ultrapassa limites de risco.
- Feed de odds offline > 5 minutos.
- Modelo não atualizado há > 7 dias.

### 11.3 Retreino do Modelo
- Frequência: semanal (cada segunda-feira).
- Pipeline: coleta da semana, treino com walk-forward, comparação com modelo em produção.
- Promoção se melhoria > 1% no CLV; caso contrário, manter.

### 11.4 Detecção de Drift
- Calcular PSI para top 10 features semanalmente.
- PSI > 0.2 em múltiplas features dispara alerta e re-treina com peso em dados recentes.

---

## 12. MODELO DE NEGÓCIO TIPSTER

### 12.1 Estrutura de Subscrição
| Tier | Preço/Mês | Conteúdo | Máximo Subscritores |
|------|-----------|----------|---------------------|
| Único | 29€ | Todos os sinais via Telegram + edge estimado + CLV histórico | 100 |

**Nota:** Um único tier simplifica operações e garante exclusividade. Tiering pode ser revisitado após 50+ subscritores (Fase 8+).

### 12.2 Compliance e Jurídico
- Termos de Serviço (sem promessa de lucros, risco explícito).
- Política de Privacidade (GDPR).
- Disclaimer em todas as comunicações: “Apostas implicam risco. Aposte apenas o que pode perder.”
- Nunca prometer lucros, apenas publicar CLV histórico.

### 12.3 Métricas de Marketing
- CLV médio mensal.
- Número de apostas/mês.
- ROI médio de subscritores (com consentimento anônimo).
- Transparência total via site do tipster.

---

## 13. ROADMAP DE IMPLEMENTAÇÃO (6 MESES)

| Mês | Fase | Entregáveis-chave |
|-----|------|--------------------|
| 1 | Fundações e Dados | Servidor + DB + Git, ingestão histórica (5 épocas), purged CV e validações ADF/KPSS, pipeline de 80 features. |
| 2 | Modelo e Backtest | Treinar XGBoost primário + meta, calibração isotónica, backtest com comissões/slippage e métricas. |
| 3 | Shadow Mode e Tipster Beta | Shadow bets em 3 casas, canal Telegram beta, documentos legais, sinal automático sem dinheiro real. |
| 4 | Micro Banca e Validação Real | Banca 500-1000€ Betfair, apostas manuais, comparação com shadow mode, tracking diário. |
| 5 | Estabilização e Lançamento Comercial | Automação de relatórios/alertas, abrir subscrições limitadas (50), ajustar thresholds com dados reais. |
| 6 | Expansão e One-Click | Adicionar Player Props NBA, implementar deep links, documentar para parceiros/investidores. |

---

## 14. RISCOS, MITIGAÇÕES E PLANO DE CONTINGÊNCIA

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Modelo não encontra edge | Média | Alto | Foco NBA e shadow mode; pivot para tênis se necessário. |
| Backtest otimista | Alta | Crítico | Shadow mode obrigatório + micro banca antes de escalar. |
| Ban na Betfair | Baixa | Médio | Uso exclusivo da API oficial com rate limits. |
| Slippage maior | Média | Médio | Registrar slippage real e ajustar thresholds. |
| Drawdown psicológico | Alta | Alto | Decisões automatizadas, operador só executa. |
| Mudanças regulatórias | Baixa | Crítico | Modelo tipster defensável; consultor legal anual. |
| Concorrência | Média | Baixo | Focar em mercados menos escrutinados a médio prazo. |

---

## 15. CONCLUSÃO

Este plano trata o sistema como um fundo quantitativo: rigor, validação progressiva e gestão de risco implacável. Ao seguir o roadmap de 6 meses, a complexidade tecnológica cresce apenas quando o edge comprovado permite. Todo o sucesso sustentável passa por disciplina operacional e transparência com os subscritores.
