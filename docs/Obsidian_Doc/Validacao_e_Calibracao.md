# ⚖️ Validação Contínua e Calibração

**Componente:** Validation & Risk  
**Status:** 🚧 Em desenvolvimento  
**Responsável:** Chief Systems Architect & Principal Quant Engineer  
**Última atualização:** 2026-05-19

---

## 🎯 Objetivo

Em apostas quantitativas profissionais, **Calibration > Accuracy**. O sistema tem de garantir que um modelo que estima 70% de probabilidade acerta, de facto, 70% das vezes a longo prazo. Além disso, as predições devem ser auditadas continuadamente para prever o fim do lucro antes de perdermos dinheiro.

---

## 📊 1. Monitorização de Calibration Drift

Não basta ver se a aposta "acertou ou falhou". O nosso foco é a calibração probabilística da resposta.

### Métricas-chave
- **Reliability Diagrams:** Plot das probabilidades estimadas contra a frequência real de vitória.
- **ECE (Expected Calibration Error):** A diferença média ponderada entre a probabilidade prevista e a precisão em cada bin.
- **Brier Score:** Medida de precisão das previsões probabilísticas.

**Ação:** Se o `ECE > threshold`, disparar `retrain()` automaticamente através do MLflow/Prefect.

---

## 📉 2. Deteção de CLV Drift (Métrica #1)

O Closed Line Value (CLV) normalmente precede o lucro sustentável ou a queda. 

### Monitorização
O sistema verifica se as odds fecham a nosso favor:
- **Entrada:** Odd 2.10
- **Closing Line:** Odd 1.92
- **Resultado:** Aposta ganha/perdida irrelevante. O processo foi positivo.

**Ação / Trigger:**
- `7-day rolling CLV < 0` => O modelo passa a *Shadow Mode* e desencadeia `retrain()`.

---

## 🎲 3. Prediction Confidence Drift

O sistema estuda a distribuição das probabilidades que o modelo emite e a sua estabilidade.
- **Exemplo de Alerta:** O modelo costumava dar probabilidades entre 0.52 e 0.61. Agora, repentinamente, começou a emitir predições extremas (0.82–0.93).
- **Diagnóstico:** Isto significa *Overconfidence* extrema causada por overfitting a uma nova regra ou rutura nas features de entrada.

---

## 🤝 4. Model Disagreement System (Ensemble Divergente)

Um gigante upgrade na estabilidade do lucro. Comparamos as opiniões de diversos algoritmos antes de assumir uma aposta.

### Os Agentes do Comité
- XGBoost (Árvores)
- LightGBM (Árvores Otimizadas)
- CatBoost (Categórico)
- Regressão Logística (Baseline linear simples)
- Market Model (Consenso do mercado)

### Regra de Confiança
- **HIGH CONFIDENCE:** Todos os modelos prevêem probabilidades similares (ex: 71%, 69%, 70%, 66%).
  - **Ação:** Permitir Kelly normal ou stake++.
- **LOW CONFIDENCE:** Grande variância na previsão (ex: 71%, 44%, 53%, 48%).
  - **Ação:** Stake reduzida brutalmente (`stake--`) ou SKIP total da aposta, por não haver estabilidade estatística.

---

## 📝 Próximos Passos

- Implementar `src/validation/calibration/` para gerar os reliability diagrams.
- Desenvolver a monitorização de Rolling CLV em `src/validation/clv/`.
- Construir a framework de comité de modelos em `src/mlops/model_disagreement.py`.

---

## 🔗 Links Relacionados

- [[MLOps e Retreinamento]] - Ação tomada quando há Drift.
- [[Motor de Edge]] - Cálculos base de Edge e CLV.
- [[Arquitetura de Experimentação]] - Modelos de mercado e simulações.
