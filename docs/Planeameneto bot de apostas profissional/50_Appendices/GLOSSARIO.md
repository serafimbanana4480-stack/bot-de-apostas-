# GLOSSÁRIO — Termos Técnicos e de Negócio

**ID:** `APP-001` | **Fase:** Todas | **Owner:** Chief Systems Architect | **Status:** #status/active

---

## A

**ADF Test** — Augmented Dickey-Fuller test. Teste estatístico para verificar se uma série temporal é estacionária (tem média e variância constantes). Crítico para features em séries temporais.

**API** — Application Programming Interface. Conjunto de regras que permite que aplicações comuniquem entre si. No nosso caso: NBA API, Betfair API.

**Arbitrage** — Situação onde é possível apostar em todos os outcomes de um evento e garantir lucro independentemente do resultado. Raro em mercados eficientes.

---

## B

**Backtest** — Simulação de estratégia de apostas usando dados históricos. Crítico para validar edge antes de dinheiro real.

**Back-to-Back** — Quando uma equipa joga em dias consecutivos. Fator de fadiga que afeta performance.

**Bankroll** — Valor total disponível para apostas. Base para cálculo de stakes via Kelly Criterion.

**Betfair** — Exchange de apostas onde utilizadores apostam entre si. Odds são determinadas pelo mercado, não pela casa.

**Brier Score** — Métrica de calibração de probabilidades. Quanto menor, melhor calibradas estão as previsões. Range [0, 1].

**Bronze/Silver/Gold** — Camadas de dados: Bronze (raw), Silver (limpo), Gold (features prontas para ML).

---

## C

**Calibration** — Processo de ajustar probabilidades brutas do modelo para refletir verdadeiras frequências de ocorrência.

**Circuit Breaker** — Mecanismo automático que para novas apostas quando certas condições são atingidas (ex: drawdown > 15%).

**CLV** — Closed Line Value. Diferença entre a odd no momento da aposta e a odd de fecho. Mede se "batemos" o mercado.

**Commission** — Taxa cobrada pela exchange (Betfair: ~5%). Reduz lucro real.

**Confidence Score** — Medida agregada de confiança numa aposta (combinação de edge, meta-modelo, regime).

**Cross-Validation** — Técnica de validação de modelos. No nosso caso: Purged Walk-Forward CV para evitar leakage temporal.

---

## D

**Data Drift** — Mudança na distribuição dos dados ao longo do tempo. Pode degradar performance do modelo.

**Drawdown** — Queda máxima desde o pico de bankroll. Mede risco de perda.

---

## E

**ECE** — Expected Calibration Error. Média ponderada da diferença entre probabilidade prevista e frequência observada.

**Edge** — Vantagem matemática. Calculado como (probabilidade × odd) - 1. Edge > 0 indica valor positivo.

**Embargo** — Período de exclusão entre sets de treino e validação para evitar leakage temporal.

**Exchange** — Mercado de apostas peer-to-peer (ex: Betfair). Usuários apostam entre si, não contra a casa.

---

## F

**Feature** — Variável de entrada para um modelo de ML. Ex: win rate últimos 5 jogos, eFG%, back-to-back flag.

**Feature Engineering** — Processo de criar features a partir de dados brutos. Crítico para performance de ML.

**Feature Store** — Sistema centralizado para armazenar, versionar e servir features.

**Fill Rate** — Percentagem de sinais que foram efetivamente apostados. Baixo fill rate indica problemas operacionais.

**Four Factors** — Métricas avançadas de basquetebol: eFG%, TOV%, ORB%, FT/FGA. Explicam ~96% da variação de eficiência.

---

## G

**Great Expectations** — Biblioteca Python para validação de dados. Define regras de qualidade e testa automaticamente.

---

## I

**Inference** — Processo de usar um modelo treinado para fazer previsões em novos dados.

**ISO** — Isotonic Calibration. Método não-paramétrico para calibrar probabilidades. Divide em regimes e calibra separadamente.

---

## K

**Kelly Criterion** — Fórmula matemática para determinar stake ótimo baseado em edge e bankroll. Maximiza crescimento esperado.

**KPSS Test** — Kwiatkowski-Phillips-Schmidt-Shin test. Teste de estacionariedade complementar ao ADF.

---

## L

**Late Arriving Data** — Dados que chegam após o evento ter ocorrido. Devem ser tratados para não afetar previsões futuras.

**Leakage** — Quando o modelo acede a informações que não estariam disponíveis em produção. Fatal para backtests.

**Line** — Odd oferecida por uma casa. "Closed line" = odd de fecho.

**Liquidity** — Volume de dinheiro disponível num mercado. Baixa liquidez = difícil executar grandes apostas sem mover odd.

**Look-ahead Bias** — Usar dados do futuro para prever o passado. Erro comum em backtests.

---

## M

**Market** — Tipo de aposta: Moneyline (vitória), Spread (handicap), Totais (over/under), Player Props.

**Meta-labeling** — Modelo secundário que filtra predições do modelo primário. Responde: "Este edge é real?"

**Moneyline** — Aposta simples na vitória de uma equipa.

**Monte Carlo** — Simulação de muitos cenários possíveis para estimar distribuição de resultados.

---

## O

**Observability** — Capacidade de entender o estado interno de um sistema através de logs, métricas e traces.

**Odd** — Probabilidade implícita de um outcome, expressa como retorno. Odd 2.0 = 50% de probabilidade (antes de overround).

**Overround** — Margem de lucro da casa incorporada nas odds. Soma de probabilidades implícitas > 100%.

**Overfitting** — Modelo que se ajusta demasiado aos dados de treino e falha em generalizar.

---

## P

**Paper Trading** — Simulação de apostas sem dinheiro real. Testa operacionalidade antes de capital real.

**Pinnacle** — Casa de apostas considerada "sharp" (mais eficiente). Odds de fecho são proxy de "true probability".

**Pipeline** — Sequência de operações de dados. Ex: ingestão → limpeza → feature engineering → modelo → decisão.

**PostgreSQL** — Sistema de gestão de bases de dados relacional open-source. Nossa BD principal.

**Prefect** — Framework Python para orquestração de workflows de dados.

**Probabilidade Implícita** — Probabilidade derivada da odd: 1/odd. Antes de remover overround.

**Purged CV** — Cross-validation com remoção de dados adjacentes no tempo para evitar leakage.

---

## R

**Randomization Test** — Teste que permuta targets aleatoriamente para verificar se modelo é melhor que aleatório.

**Redis** — Store de dados em memória. Usado para cache, filas, rate limiting.

**Regression** — Tarefa de ML para prever valores contínuos. (Não usamos diretamente, usamos classificação).

**Reliability Diagram** — Gráfico que mostra calibração de probabilidades (previsto vs. observado).

**ROI** — Return on Investment. (Lucro / Investimento) × 100.

**Rolling** — Métricas calculadas sobre janela deslizante (ex: ROI rolling 50 apostas).

---

## S

**Schema** — Estrutura da base de dados: tabelas, colunas, tipos, relações.

**Sharpe Ratio** — Métrica risk-adjusted: ROI médio / desvio padrão dos retornos. > 0.5 é aceitável.

**Shadow Mode** — Simulação de apostas em produção sem execução real. Mede True CLV.

**Slippage** — Diferença entre odd pretendida e odd obtida na execução.

**Spread** — Handicap aplicado a uma equipa para equilibrar a aposta.

**Stake** — Valor apostado. Calculado via Kelly fracionado com limites de segurança.

**Staging** — Ambiente de teste que replica produção. Para validar antes de deploy.

---

## T

**Target** — Variável que o modelo tenta prever. No nosso caso: resultado do jogo (vitória/derrota).

**Time Series** — Dados sequenciais indexados por tempo. Ex: performance de equipa ao longo da época.

**Tipster** — Pessoa/sistema que fornece sinais de apostas a subscritores. Nosso modelo de negócio.

**Trading** — No contexto de apostas: executar apostas baseado em sinais do sistema.

**Transaction** — Aposta individual no sistema.

---

## V

**Validation** — Processo de verificar que modelo generaliza para dados não vistos.

**Value Betting** — Apostar quando odd oferecida é maior que probabilidade real implicaria (edge positivo).

**VPS** — Virtual Private Server. Servidor virtual na cloud. Nossa infraestrutura base.

---

## W

**Walk-Forward CV** — Cross-validation temporal onde janela de treino avança no tempo. Única forma válida para dados desportivos.

**White's Reality Check** — Teste estatístico para verificar se performance é significativamente melhor que aleatório.

**Window Function** — Função SQL que calcula valores sobre janela de linhas (ex: média móvel).

---

## X

**XGBoost** — Algoritmo de gradient boosting extremamente eficiente para dados tabulares. Nosso modelo primário.

---

## SIGLAS COMUNS

- **API** → Application Programming Interface
- **BD** → Base de Dados
- **CLV** → Closed Line Value
- **CV** → Cross-Validation
- **ECE** → Expected Calibration Error
- **ML** → Machine Learning
- **MVP** → Minimum Viable Product
- **NBA** → National Basketball Association
- **RTO** → Recovery Time Objective
- **RPO** → Recovery Point Objective
- **SQL** → Structured Query Language
- **VPS** → Virtual Private Server

---

## LINKS CRUZADOS

- [[50_Appendices/INDEX]] ← Secção mãe
- [[FORMULARIO_MATEMATICO]] → Fórmulas chave
- [[00_Master_Index/INDEX]] ← Cérebro do sistema