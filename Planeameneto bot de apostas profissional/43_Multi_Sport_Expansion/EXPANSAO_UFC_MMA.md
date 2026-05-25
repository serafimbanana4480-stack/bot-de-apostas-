# EXPANSAO UFC E MMA: MODELAÇÃO E ESTRATÉGIA

## 1. Visão Geral
O UFC e o MMA são desportos caracterizados por uma menor liquidez, eventos esporádicos e uma imensa variância inerente a desportos de combate (ex: um "lucky punch" muda o resultado). Contudo, a ineficiência nos mercados secundários e nas odds de moneyline oferecem oportunidades significativas.

## 2. Features Específicas do UFC
Diferentemente de desportos coletivos, o UFC depende exclusivamente das caraterísticas dos indivíduos (matchup) e dos seus *training camps*.
- **Físicas e Demográficas:** Idade, Diferença de Idade, Alcance (Reach), Diferença de Alcance, Altura.
- **Histórico e Recordes:** Vitórias, Derrotas, Win Streak, Tempo de Inatividade (Ring Rust).
- **Estilos de Luta (Striker vs Grappler):** Takedown Defense, Takedowns per 15 min, Striking Accuracy, Strikes Landed/Absorbed.
- **Card e Localização:** Altitude (afeta o cardio), Tamanho do Octógono (pequeno favorece grapplers/brawlers).
- **Fator Intangível:** Camp changes, lesões recentes reportadas, "weight cut" drástico (miss weight).

## 3. Abordagem de Modelação (XGBoost / Random Forest)
A escassez de dados requer modelos que penalizem fortemente o *overfitting*. A utilização de regularização elevada é crucial.
- **Baseline:** Regressão Logística.
- **Avançado:** XGBoost com L1/L2 regularization altas.

## 4. Mercados de Aposta e Limitações
- **Moneyline:** Onde a liquidez está, mas altamente vigiado por *sharps*. Oportunidade foca-se em apostar cedo (early lines) ou explorar *overreaction* do público a pesagens.
- **Over/Under Rounds:** Mercado secundário interessante baseado em estatísticas de finalização.

## 5. Cuidados no Backtesting
- Dados de lutas antigas (ex: antes de 2015) podem não refletir o metagame atual do UFC (mais "well-rounded" fighters). Limitar a janela histórica de treino é fundamental.
