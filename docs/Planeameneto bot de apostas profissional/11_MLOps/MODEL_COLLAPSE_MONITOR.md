# Monitoramento de Colapso de Modelo Silencioso (Model Collapse)

**Versão:** 1.0.0  
**Status:** #status/active #priority/high  
**Área:** MLOps / Monitorização

---

## 🎯 OBJETIVO
Descrever os mecanismos e limites configurados para detectar a degradação silenciosa do modelo, caracterizada pela perda de diferenciação probabilística (previsões estacionárias em torno de 50%).

---

## 🔍 INDICADORES OPERACIONAIS DE COLAPSO

### 1. Entropia Binária de Shannon
Calculamos a entropia média das previsões de probabilidade para mensurar a incerteza útil produzida pelo classificador:
$$H(X) = - \frac{1}{N} \sum_{i=1}^N \left( p_i \log_2(p_i) + (1 - p_i) \log_2(1 - p_i) \right)$$
- **Limite de Alerta:** $H(X) < 0.50$.
- **Interpretação:** Valores muito baixos de entropia combinados com falta de vitórias sugerem que as probabilidades previstas colapsaram ou estão concentradas.

### 2. Ratio de Valores Únicos (Unique Ratio)
Mapeia a quantidade de valores probabilísticos distintos produzidos pelo modelo (arredondados a 3 casas decimais):
$$\text{Unique Ratio} = \frac{\text{Contagem de Probs Distintas}}{\text{Total de Previsões (N)}}$$
- **Limite de Alerta:** $\text{Unique Ratio} < 15\%$.
- **Interpretação:** Indica falta de poder preditivo discriminatório (o modelo devolve sempre o mesmo output genérico).

### 3. Desvio Padrão das Previsões
- Se $\sigma < 0.01$ (variabilidade nula no output do modelo), o pipeline operacional interrompe imediatamente a colocação automática de ordens.
