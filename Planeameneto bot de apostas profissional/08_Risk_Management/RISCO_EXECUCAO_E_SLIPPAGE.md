# Gestão de Risco de Execução e Slippage em Produção

**Versão:** 1.0.0  
**Status:** #status/active #priority/critical  
**Área:** Risco / Execução

---

## 🎯 OBJETIVO
Documentar as salvaguardas implementadas no sistema de execução real (`src/execution/`) para mitigar a disparidade entre o ROI simulado (teórico) e os lucros reais (slippage), bem como tratar rejeições de stake por limites impostos por bookmakers.

---

## 🔍 PRINCÍPIOS DE MITIGAÇÃO OPERACIONAL

### 1. Rastreamento e Log de Slippage
Slippage é a diferença entre a odd esperada pelo modelo no momento da decisão e a odd de fato obtida no momento em que a aposta é colocada no mercado:
$$\text{Slippage} = \text{Odds}_{\text{executada}} - \text{Odds}_{\text{prevista}}$$
- O sistema audita todas as apostas gravando o log estruturado JSON no caminho `models/execution_audit.jsonl`.
- Desvios acumulados de slippage médios negativos inferiores a -0.05 disparam alertas preventivos no canal de monitorização do Telegram.

### 2. Políticas de Tratamento de Rejeições de Stake
Quando uma casa de apostas limita a stake recomendada, o módulo `order_tracker.py` avalia:
- **Redução Aceitável:** Se a stake máxima permitida for pelo menos 30% da aposta original, executa o valor reduzido.
- **Aborto da Ordem:** Se for inferior a 30% ou se as odds caírem abaixo do piso mínimo aceitável, a ordem é abortada para evitar perdas de EV esperadas.

### 3. Distribuição de Stake (Stake Splitting)
Para contornar limites individuais, o `limits_tracker.py` monitoriza o volume acumulado wagered por casa. O `splitter` pode fatiar stakes maiores entre múltiplas bookmakers que fornecem cotações favoráveis no mesmo evento.
