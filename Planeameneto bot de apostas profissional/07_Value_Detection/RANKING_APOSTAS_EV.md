# RANKING DE APOSTAS: MAXIMIZAR VALOR E ODD (OTIMIZAÇÃO DE PORTFÓLIO)

## 1. A Ilusão da Aposta Única
Um erro comum é assumir que todas as apostas com *Edge > 0* devem ser efetuadas. Em fins-de-semana preenchidos (Futebol) ou *cards* completos (UFC), o modelo pode sugerir 20 apostas. Apostar em todas dilui a banca, aumenta o *drawdown* e introduz correlações perigosas.

## 2. Algoritmo de Ranking e Seleção
O sistema deve ranquear diariamente as oportunidades antes de interagir com o mercado.

### Passo A: Cálculo de EV (Expected Value)
- O motor já fornece: Probabilidade ($P$) e *Odd* Ofertada ($O$).
- $EV = P \times (O - 1) - (1 - P)$

### Passo B: Penalização por Correlação e Risco (Sharpe/Variância)
- Uma aposta a *odd* 10.0 tem alta variância (muito risco). Uma aposta a *odd* 1.50 tem baixa variância.
- O Sharpe simplificado da aposta = $EV / Variância_{aposta}$
- A lista de *Edge* positivo é ordenada primeiramente por este "Sharpe Ratio" individual.

### Passo C: Limite Máximo Diário e de Correlatos
- Selecionar apenas o **Top $N$ apostas** (onde $N$ depende do desporto, ex: máximo de 3 apostas de UFC por card; máximo de 5 de Futebol por dia).
- O sistema varre o Ranking do 1º ao N-ésimo. Se o jogo 3 for altamente correlacionado com o jogo 1 (ex: mesma equipa, torneio a decorrer), salta o jogo 3 e avalia o jogo 4.

## 3. Integração com a Execução
Ao "saber as melhores apostas com maior certeza de ganhar e maior odd", estamos essencialmente a procurar as apostas com o rácio de Sharpe mais elevado: um *Edge* substancial, uma confiança de modelo muito alta (pouca incerteza ou margem de erro nos dados), num mercado líquido. A execução deve agir automaticamente apenas no percentil 90 desta lista diária.
