# Gestão de Correlação entre Apostas Concorrentes

**Versão:** 1.0.0  
**Status:** #status/active #priority/high  
**Área:** Quant Research / Risco

---

## 🎯 RACIONAL
Apostar em múltiplos jogos que ocorrem em simultâneo no mesmo dia expõe a banca a correlações ocultas. Por exemplo, se apostarmos na vitória de 3 equipes favoritas diferentes fora de casa na mesma noite, os resultados individuais não são estatisticamente independentes. Variações no ritmo da liga, fadiga geral da arbitragem, ou surtos de gripe nas viagens afetam todo o grupo.

Este documento define limites de correlação de carteira para proteger o capital durante rodadas extensas de jogos.

---

## 🛠️ ANÁLISE DE CORRELAÇÃO DE PORTFÓLIO

A variância de um portfólio de apostas com $M$ posições é expressa por:
$$\sigma^2_p = \sum_{i=1}^M w_i^2 \sigma_i^2 + 2 \sum_{i=1}^M \sum_{j < i} w_i w_j \sigma_i \sigma_j \rho_{ij}$$
onde:
- $w_i$ é a stake aplicada no jogo $i$.
- $\sigma_i$ é a variância inerente à probabilidade da aposta.
- $\rho_{ij}$ é o coeficiente de correlação entre os resultados das duas equipes.

### Matriz de Correlação Empírica baseada em Metadados:
Os coeficientes $\rho_{ij}$ são estimados com base em proximidades geográficas e divisões da NBA:

1. **Mesma Divisão (ex: Atlantic Division):** $\rho \approx 0.15$ (Times jogam frequentemente e compartilham adversários comuns recentes).
2. **Mesma Conferência (Leste / Oeste):** $\rho \approx 0.08$.
3. **Conferências Opostas:** $\rho \approx 0.02$ (Praticamente independentes).

---

## 🛑 REGRAS DE CONTROLE DE EXPOSIÇÃO (CIRCUIT BREAKERS)

Para mitigar a variância acumulada de portfólio, aplicamos os seguintes limites operacionais rígidos:

1. **Cap por Conferência:** No máximo 3 apostas ativas na mesma noite na mesma conferência (Leste ou Oeste).
2. **Correlação de Linha (Moneyline vs. Spread):** Proibido apostar na Moneyline de uma equipe e no Spread contra a mesma equipe noutro jogo na mesma rodada (efeito hedge ineficiente).
3. **Cap de Exposição Agregada Diária:** A soma total das stakes expostas numa única noite não pode exceder **8.0%** da banca total sob regime Kelly, ou **4.0%** sob regime Flat Staking.
