# SIMULAÇÃO RIGOROSA DE BACKTESTING COM DADOS 2019-2025

## 1. O Problema Histórico
A maioria das simulações antigas do projeto assumia condições irrealistas, como "odd 2.0" fixa ou slippages fictícias. Este novo protocolo define a forma **real** como testaremos se o sistema funciona, usando o histórico completo até 2025.

## 2. Metodologia: Flat Staking e Walk-Forward Real
Para cada simulação a correr, aplicaremos as seguintes regras rigorosas:

1. **Janela de Treino e Embargo:**
   - O modelo é treinado em $T_1$ a $T_{atual-1}$. Não existe conhecimento do dia da aposta no modelo.
2. **Avaliação contra Closing Lines Reais:**
   - A previsão do modelo ($Prob$) é multiplicada pela $Odd$ de Fecho da Pinnacle (Closing Line) real daquele dia.
   - O cálculo do Edge é real: $Edge = Prob \times Odd - 1$.
3. **Flat Staking (Para validação do Edge):**
   - Independentemente da força do sinal, aplicamos uma aposta fixa de **1% da banca**. 
   - A complexidade do Kelly Criterion só máscara *drawdowns* sistémicos. O Flat Staking expõe a real qualidade de seleção das apostas.

## 3. Filtros do Simulador
Para considerar uma aposta válida na simulação histórica:
- O *Edge* estimado tem que ser superior a 3%.
- A *Odd* Pinnacle de Fecho estava disponível e líquida.
- Máximo de apostas por dia: as Top 5 apostas ordenadas por EV.

## 4. Métricas de Sucesso da Simulação (O que medir)
- **CLV Real:** Fechar sistematicamente melhor que as linhas Pinnacle de Fecho.
- **ROI em Flat Stake:** Retorno real com base num risco fixo. Se for negativo após 10,000 apostas, o modelo não funciona.
- **P-Value do ROI:** Probabilidade de termos atingido esse ROI usando escolhas puramente aleatórias, utilizando simulações de *Monte Carlo*.
