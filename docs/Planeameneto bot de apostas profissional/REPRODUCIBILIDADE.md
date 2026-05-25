# REPRODUCIBILIDADE

**ID:** `DOC-REP` | **Fase:** Todas | **Owner:** Chief Systems Architect | **Status:** #status/active

---

## 1. OBJETIVO

Garantir que qualquer execução do sistema (treino, backtest, aposta) possa ser reproduzida exatamente, bit a bit, usando as mesmas entradas e parâmetros. Reprodutibilidade é a base da confiança estatística.

---

## 2. PRINCÍPIOS

1. **Seed aleatória fixa:** Todo treino usa `random_state` fixo e documentado
2. **Versões bloqueadas:** `requirements.txt` com versões exatas (ex: `numpy==1.26.4`, não `numpy>=1.26`)
3. **Dados versionados:** Hash SHA-256 de cada dataset de input
4. **Parâmetros auditáveis:** Todos os hiperparâmetros logados em MLflow
5. **Ambiente containerizado:** Docker garante ambiente idêntico

---

## 3. CHECKLIST DE REPRODUCIBILIDADE

### 3.1 Antes de Treinar um Modelo
- [ ] Definir `random_state` (ex: 42) e registar em MLflow
- [ ] Fixar versões de todas as dependências (`pip freeze > requirements.lock`)
- [ ] Documentar hash SHA-256 do dataset de treino
- [ ] Guardar configuração completa (YAML/JSON) no artifact store

### 3.2 Durante o Treino
- [ ] Logar hiperparâmetros em MLflow
- [ ] Logar métricas a cada fold do CV
- [ ] Guardar artefato do modelo (.pkl/.json) com hash
- [ ] Registar versão do código (git commit SHA)

### 3.3 Após o Treino
- [ ] Validar que re-execução com mesmos inputs produz métricas idênticas (±0.001)
- [ ] Documentar qualquer não-determinismo encontrado
- [ ] Arquivar config em `30_Model_Registry/`

---

## 4. FERRAMENTAS

| Ferramenta | Uso |
|------------|-----|
| `requirements.lock` | Versões exatas de todas as deps |
| MLflow | Tracking de experimentos, parâmetros, métricas |
| Git | Versionamento do código (tag por release) |
| Docker | Ambiente idêntico em dev/staging/prod |
| SHA-256 | Hashing de datasets para verificação |

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[29_Experiment_Tracking/INDEX]] → Tracking de experimentos
- [[30_Model_Registry/INDEX]] → Registo de modelos
