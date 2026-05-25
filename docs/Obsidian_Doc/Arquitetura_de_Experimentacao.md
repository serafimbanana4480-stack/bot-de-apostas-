# 🧪 Arquitetura de Experimentação e Regimes

**Componente:** Research & Experimentation  
**Status:** 🚧 Em desenvolvimento  
**Responsável:** Chief Systems Architect & Data Engineer  
**Última atualização:** 2026-05-19

---

## 🎯 Objetivo

Implementar os verdadeiros diferenciadores competitivos do VBQ-UNIFIED. O sistema passa a possuir inteligência para detetar o clima atual do mercado desportivo, controlar estritamente as *Features* e usar simulações automatizadas para se treinar e questionar autonomamente (Automated Hypothesis Engine).

---

## 📦 1. Feature Store Versionada (Top Tier)

A "Single Source of Truth" para o ML. Reproduzir um treino passado torna-se instantâneo e à prova de balas.

### Estrutura Base
- `feature_version` (ex: v14)
- `created_at`
- `league` / `sport`
- `dependencies`
- `source`

**Impacto:** Permite responder rapidamente com que *feature set* o modelo *v0.92* foi treinado. O caos de data-leakage desaparece.

---

## 🌩️ 2. Market Regime Detection (Modelos Dinâmicos)

O comportamento dos desportos muda drasticamente ao longo do tempo. O nosso meta-modelo irá possuir um classificador para decidir em que regime estamos antes de acionar um modelo.

### Regimes por Desporto
**🏀 NBA:**
- Playoffs vs Regular Season.
- Injury-heavy regime.
- Trade deadline.
- Back-to-back clusters.

**⚽ Futebol:**
- Champions League congestion.
- Relegation fight (Fim de temporada).
- International break hangover.

**🥋 UFC / MMA:**
- Short notice fights.
- Age mismatch.
- Long layoff returns.

**Pipeline:** `Regime_Classifier` -> Seleciona o Modelo específico otimizado para esse ambiente.

---

## 🚦 3. Meta-Model (Decisor BET / SKIP)

Expandir o atual Meta-Labeling. O foco não é só adivinhar a vitória/derrota, mas prever se **vale a pena apostar**.

### Inputs para a Rede Neural de Classificação:
- Confidence do Modelo Preditivo.
- Histórico de CLV atual.
- Liquidez de mercado (Betfair / Pinnacle).
- Velocidade de movimento das Odds (Sharp Money).
- Dispersão entre as casas de apostas.
- Confiança/Certez no relatório de lesões (News).

### Output:
- **BET:** O Edge justifica o risco.
- **SKIP:** O Edge estatístico existe, mas fatores exógenos corrompem o valor da aposta.

*(Melhora o ROI muito mais do que subir a Accuracy primária do modelo)*.

---

## 🔮 4. Counterfactual Simulator

Um módulo gigantesco que permite responder à pergunta: **"E se?"**

### Simulação de Estratégias
O sistema cria uma grelha de cenários e gera 100k simulações através de Monte Carlo para avaliar Bankrolls em universos paralelos:
- E se o *threshold* mínimo de Edge for 4% em vez de 2%?
- E se usarmos *Half-Kelly* em vez de *Quarter-Kelly*?
- E se limitarmos apostas a *odds movements* > 5%?

---

## 🤖 5. Automated Hypothesis Engine

A verdadeira IA avançada de fundo quantitativo. O sistema levanta hipóteses automaticamente durante a noite, testa e guarda relatórios (MLflow Tracking).

**Exemplo Prático (Hypothesis #144):**
- *"O travel fatigue da Costa Este para a Costa Oeste na NBA afeta o Over/Under?"*
  1. A IA submete o query de treino.
  2. Valida o *CLV* histórico e o *ROI* deste sub-filtro.
  3. Aceita ou Rejeita a hipótese na base de conhecimento.

---

## 📝 Próximos Passos

- Configurar o `src/feature_store/` com versão e serialização.
- Construir o `src/experimentation/hypothesis_engine/` usando base de testes LLM.
- Implementar as rotinas Monte Carlo em `src/validation/monte_carlo/`.

---

## 🔗 Links Relacionados

- [[MLOps e Retreinamento]] - Usado para treinar as hipóteses.
- [[Validação e Calibração]] - Usado para validar o Meta-Model.
