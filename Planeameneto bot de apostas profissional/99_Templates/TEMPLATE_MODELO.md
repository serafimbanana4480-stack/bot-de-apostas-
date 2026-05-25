# TEMPLATE_MODELO — Model Card

**ID:** `TMP-002` | **Fase:** #phase/1-15 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. IDENTIFICACAO

| Campo | Valor |
|-------|-------|
| Nome | [nome_modelo] |
| Versao | vX.Y.Z |
| Data | YYYY-MM-DD |
| Owner | [Nome] |
| Status | [Development / Staging / Production / Archived] |

---

## 2. DESCRICAO

[Para que serve este modelo? Que problema resolve?]

---

## 3. DADOS

| Campo | Valor |
|-------|-------|
| Dataset | [Epocas + jogos] |
| N amostras | X |
| N features | Y |
| Target | [Definicao] |

---

## 4. METRICAS

| Metrica | Treino | Validacao | Teste |
|---------|--------|-----------|-------|
| CLV | - | X% | Y% |
| ROI | - | X% | Y% |
| Sharpe | - | X | Y |
| Brier | - | X | Y |

---

## 5. LIMITACOES

- [Limitacao 1]
- [Limitacao 2]

---

## 6. USO

```python
model = xgb.Booster()
model.load_model("path/to/model.json")
predictions = model.predict(X)
```

---

## 7. LINKS CRUZADOS

- [[30_Model_Registry/INDEX]] → Registo MLflow
- [[99_Templates/INDEX]] ← Templates
