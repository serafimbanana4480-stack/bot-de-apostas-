# VBQ-UNIFIED v4.0.0 — Relatório de Auditoria Crítica Final

**Data:** 2026-05-26  
**Auditor:** Kimi Code CLI (Software Auditor)  
**Scope:** End-to-end review de todo o codebase (278 ficheiros Python, 64 testes, infraestrutura, ML, segurança, compliance)  
**Estado dos Testes:** 263 passed, 1 failed, 14 skipped  
**Bandit:** 35 issues (2 High, 5 Medium, 28 Low)  
**Safety:** 9 vulnerabilidades (MLflow, skops)  

---

## 🚨 CRÍTICO — Must Fix Immediately

### C1. Paper Trading Determinístico Falso (Data Corruption)
**Ficheiro:** `src/pipeline/orchestrator.py:573-599`  
**Problema:** O paper trading não simula resultados reais. Usa `won_preview = opp.get("edge", 0) > 0.05` — isto é, se o edge > 5%, assume vitória. Isto é circular e completamente inválido. O P&L simulado é fictício e engana o operador.
```python
# BROKEN — linha 574
won_preview = opp.get("edge", 0) > 0.05
pnl = stake * 0.1 if won_preview else -stake * 0.1
```
**Impacto:** Qualquer backtest ou paper trading é inútil. Decisões baseadas nestes números são catastróficas.  
**Fix:** Substituir por lookup do resultado real (base de dados ou API) ou usar probabilidade modelada com amostragem Monte Carlo:
```python
# CORRETO
actual_result = self._get_actual_result(opp.get("match_id"))
if actual_result is None:
    logger.warning("Resultado desconhecido para %s — paper trade não liquidado", match_id)
    return False
won = (bet_side == "HOME" and actual_result == "H") or ...
pnl = stake * (odds - 1.0) if won else -stake
```

### C2. Shadow Challenger Treina em Dados Futuros (Look-Ahead Bias)
**Ficheiro:** `src/pipeline/orchestrator.py:173-184`  
**Problema:** O shadow deployment treina o challenger em `df.iloc[split:]` onde `split = 50%`. Como o dataframe está ordenado cronologicamente, o challenger treina em dados FUTUROS em relação ao champion. A comparação é injusta e inválida.
```python
split = int(len(df) * 0.5)
train = df.iloc[split:].copy()  # ← FUTURE DATA
```
**Impacto:** O challenger parece melhor do que é. Substituições de modelo baseadas nesta comparação degradam performance.  
**Fix:** Inverter o split:
```python
split = int(len(df) * 0.5)
train = df.iloc[:split].copy()   # ← dados passados
```

### C3. Database URL sem URL-Encoding (SQL Injection / Connection Failure)
**Ficheiro:** `src/database/connection.py:15-18`  
**Problema:** A password é interpolada diretamente na connection string sem encoding:
```python
database_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASS}@..."
```
Se a password contiver `@`, `:`, `/`, ou caracteres especiais, a string quebra ou permite injection.
**Impacto:** Falha de conexão em produção; potencial vetor de injection.  
**Fix:**
```python
from urllib.parse import quote_plus
database_url = (
    f"postgresql://{quote_plus(settings.DB_USER)}:{quote_plus(settings.DB_PASS)}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)
```

### C4. API Sem Validação de Schema no `features` Dict (Injection Vector)
**Ficheiro:** `src/api/router.py:49-54, 84-170`  
**Problema:** O endpoint `/api/v1/signals/generate` aceita `Dict[str, Any]` sem validação de schema. Qualquer chave/valor é passado diretamente para o prediction engine.
```python
class SignalGenerateRequest(BaseModel):
    game_id: str
    features: Dict[str, Any]   # ← sem schema
```
**Impacto:** Potencial injection de features maliciosas; unbounded keys podem causar DoS ou comportamento indefinido no modelo.  
**Fix:** Definir schema Pydantic estrito para features ou usar allow-list:
```python
class FeaturesSchema(BaseModel):
    elo_diff: float
    rest_diff: float
    win_rate_5_diff: float
    market_overround: float
    form_home: float
    form_away: float
    h2h_home_win_rate: float
    days_since_last: float
    # ... lista explícita
```

### C5. Segredos Padrão Não Bloqueiam em Dev/Test
**Ficheiro:** `src/core/config.py:106-128`  
**Problema:** `_check_default_secrets()` só levanta exceção em `production/staging/live`. Em `development` (default), apenas loga warning. Um developer pode commitar `.env` com secrets vazios e estes propagam-se para produção.
**Impacto:** Exposição de credenciais; deployments com JWT_SECRET_KEY="" são trivialmente comprometidos.  
**Fix:** Levantar exceção SEMPRE que secrets estiverem vazios, independentemente do ambiente. O ambiente deve ser configurado explicitamente.

### C6. Pickle Deserialization Sem Validação (RCE Risk)
**Ficheiro:** `src/engine/predict.py:36`, `src/models/train.py`  
**Problema:** `pickle.load()` é usado para carregar modelos sem validação de integridade ou assinatura.
**Impacto:** Se o ficheiro `.pkl` for comprometido, permite execução arbitrária de código (RCE).  
**Fix:** Migrar para `joblib` com checksum SHA-256, ou usar `skops` (com cuidado devido a CVE-2024-37065). Verificar hash antes de load.

### C7. MLflow SQLite em Produção (Concurrency Corruption)
**Ficheiro:** `src/core/config.py:100`, `src/models/train.py`  
**Problema:** `MLFLOW_TRACKING_URI` default é `sqlite:///mlflow.db`. SQLite não suporta acesso concorrente write-heavy.
**Impacto:** Corrupção de tracking em produção; race conditions entre workers.  
**Fix:** Usar PostgreSQL para MLflow em produção. Fallback para SQLite apenas quando `ZERO_COST_MODE=true` e com file locking.

### C8. SettlementRulesEngine Hardcoded "DRAW" para Todos os Empates
**Ficheiro:** `src/execution/settlement.py:55-57`  
**Problema:**
```python
else:
    winner = "DRAW"
```
Na NBA não há empates (overtime garantido). Um empate na NBA nunca deve ser "DRAW".
**Impacto:** Settlement incorreto para NBA; P&L errado.  
**Fix:** Adicionar parâmetro `sport` e lógica por desporto:
```python
if sport == "nba":
    winner = "HOME_OT" if home_a > away_a else "AWAY_OT"
else:
    winner = "DRAW"
```

---

## 🔴 HIGH — Fix Before Real Trading

### H1. Edge Calculation Ignora Comissão da Exchange
**Ficheiro:** `src/risk/value_filter_v2.py:101`  
**Problema:** `edge = model_prob - implied_prob` sem subtrair comissão Betfair (5%).  
**Impacto:** Overestima edge real; bets aparentemente lucrativas são perdedoras após comissão.  
**Fix:**
```python
net_odds = 1.0 + (odds - 1.0) * (1.0 - commission_rate)
implied_prob = 1.0 / net_odds
edge = model_prob - implied_prob
```

### H2. Transação Parcial na API (DB Inconsistency)
**Ficheiro:** `src/api/router.py:114-133`  
**Problema:** `db.commit()` após delete do signal existente, mas antes do signal novo ser adicionado. Se o Telegram falhar após o commit final, o signal existe mas o alerta falhou. Não há rollback coordenado.
**Impacto:** Inconsistência entre DB e notificações.  
**Fix:** Usar transação única que engloba prediction + signal + notificação (ou notificação fora da transação com retry queue).

### H3. OrderTracker JSONL Sem File Locking
**Ficheiro:** `src/execution/order_tracker.py:33-34`  
**Problema:**
```python
with open(self.audit_log_path, "a") as f:
    f.write(json.dumps(log_entry) + "\n")
```
**Impacto:** Execuções concorrentes corrompem o audit log (linhas intercaladas).  
**Fix:** Usar `filelock` ou `portalocker`:
```python
from filelock import FileLock
with FileLock(self.audit_log_path + ".lock"):
    with open(self.audit_log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

### H4. CORS Permite `["*"]` como Fallback
**Ficheiro:** `app/main.py:36`  
**Problema:** `allow_origins=allowed_origins or ["*"]` — se `ALLOWED_ORIGINS` estiver vazio, permite qualquer origem.
**Impacto:** CSRF/XSS risk em produção.  
**Fix:** Rejeitar startup se `ALLOWED_ORIGINS` estiver vazio em produção.

### H5. Polymarket Adapter Guarda Private Key em Instância
**Ficheiro:** `src/execution/adapters/polymarket.py:83`  
**Problema:** `self.private_key = private_key` guardado como string plain na instância.
**Impacto:** Exposição em memory dumps, logs, stack traces.  
**Fix:** Usar variável de ambiente diretamente; nunca persistir em atributo de instância.

### H6. Betfair SSL `check_hostname=True` com Certificados User-Supplied
**Ficheiro:** `src/execution/adapters/betfair_real.py:150`  
**Problema:** `ctx.check_hostname = True` com certificados que podem não corresponder ao hostname Betfair em certos setups.
**Impacto:** Falha de TLS em setups válidos; ou bypass inseguro se desligado.  
**Fix:** Validar certificados antes de inicializar; usar `ssl.create_default_context()` sem overrides desnecessários.

### H7. Telegram Bot Token em Variável Local Antes de Use
**Ficheiro:** `src/telegram/bot.py:148-149`  
**Problema:** `token = settings.TELEGRAM_BOT_TOKEN` — se exceção ocorrer antes de `Bot(token=token)`, o token pode aparecer em stack traces.
**Impacto:** Secret exposure em logs de erro.  
**Fix:** Passar `settings.TELEGRAM_BOT_TOKEN` diretamente para `Bot()` sem variável intermédia.

### H8. AccountManager Hardcodes Perfis bet365 (TOS Violation)
**Ficheiro:** `src/execution/account_manager.py:23-28`  
**Problema:** Mock database com perfis artificiais de soft books, limites artificiais, e proxy mapping.
**Impacto:** Violação dos Termos de Serviço da maioria dos bookmakers; risco de banning legal; potenciais consequências legais.  
**Fix:** Remover completamente o routing para soft books não-licenciados. Usar apenas exchanges licenciadas (Betfair Exchange onde legal).

### H9. OOF Calibration Pode Usar In-Sample Data
**Ficheiro:** `src/ml/models/football_poisson_v2.py:339-376`  
**Problema:** `_calibrate_model()` cria modelos temporários mas o modelo final é fit no dataset completo incluindo dados de calibração.
**Impacto:** Calibration overfitting; probabilidades não confiáveis.  
**Fix:** Garantir que o modelo final NUNCA vê dados de calibração. Usar hold-out temporal estrito.

### H10. Missing Transaction Isolation na API
**Ficheiro:** `src/api/router.py:97-133`  
**Problema:** Não há boundaries de transação explícitas em torno de prediction + signal creation.
**Impacto:** Race conditions em signal generation concorrente.  
**Fix:** Usar `@db.transactional` ou `db.begin()` / `db.commit()` / `db.rollback()` explícitos.

---

## 🟡 MEDIUM — Should Fix

### M1. LeakageDetector Threshold Correlation Muito Alto (0.8)
**Ficheiro:** `src/validation/leakage_detector.py:43-68`  
**Problema:** Apenas Pearson correlation; threshold 0.8 pode deixar passar leakage subtel (0.79). Sem deteção não-linear.
**Fix:** Adicionar Spearman, Mutual Information, e threshold adaptativo (e.g., top 5% correlations).

### M2. Logs Sem Rotação
**Ficheiro:** `logs/` (diretório), `src/monitoring/json_logging.py`  
**Problema:** `logging.FileHandler` sem `RotatingFileHandler`. Logs crescem indefinidamente.
**Fix:**
```python
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=5)
```

### M3. Pinnacle Password em Plaintext POST Body
**Ficheiro:** `src/execution/adapters/pinnacle_real.py:169`  
**Problema:** Password enviada em POST body sem encriptação adicional além de TLS.
**Fix:** Não há fix trivial — TLS é o mínimo. Documentar que a password nunca deve ser reutilizada.

### M4. Feature Pipeline File Não Existe mas Tests Importam
**Ficheiro:** `tests/test_features.py` (importa `src/ml/features/feature_pipeline.py`)  
**Problema:** O ficheiro `src/ml/features/feature_pipeline.py` não existe; o pipeline real está em `src/features/pipeline.py`.
**Fix:** Corrigir imports nos testes ou renomear o módulo.

### M5. NBA/Football/MMA Implementations são Scaffolds Vazios
**Ficheiro:** `src/sports/football/__init__.py`, `src/sports/nba/__init__.py`, `src/sports/mma/__init__.py`  
**Problema:** Todos têm `pass` nos métodos principais.
**Impacto:** Arquitetura modular não é utilizada; código morto.  
**Fix:** Implementar ou remover. Não deixar scaffolds vazios em produção.

### M6. `random` Importado Dentro de Método
**Ficheiro:** `src/execution/dynamic_rate_limiter.py:191`  
**Problema:** `import random` dentro de método — má prática, esconde dependências.
**Fix:** Mover para topo do ficheiro.

### M7. `print()` Statements em Código de Produção
**Ficheiro:** `src/execution/paper_trading_reconciliation.py:258-273`  
**Problema:** `print()` em vez de `logger.info()`.
**Fix:** Substituir por logging estruturado.

### M8. `PortfolioOptimizer.get_optimal_portfolio()` Referencia `datetime` Não Importado
**Ficheiro:** `src/risk/portfolio_optimizer.py:186`  
**Problema:** `datetime.now()` sem `import datetime`.
**Fix:** Adicionar import ou usar `from datetime import datetime`.

### M9. MLflow Vulnerabilities (9 CVEs)
**Ficheiro:** `pyproject.toml`  
**Problema:** MLflow 2.7.1 → atual 3.12.0 tem 9 vulnerabilidades de deserialization.
**Fix:** Atualizar para MLflow >= 2.12.2 (ou versão patched). Isolar MLflow em network segmentado.

### M10. AB Testing Engine Usa MD5 (Hash Fraco)
**Ficheiro:** `src/mlops/ab_testing/ab_engine.py:22`  
**Problema:** `hashlib.md5(event_id.encode("utf-8"))` — MD5 é criptograficamente quebrado.
**Impacto:** Baixo para routing, mas má prática.  
**Fix:** Usar `hashlib.sha256` com `usedforsecurity=False`.

---

## 🟢 LOW — Nice to Have

### L1. `.xgb.json` Extension Confusa
**Ficheiro:** `src/ml/models/football_hybrid.py:442`  
**Fix:** Usar `.json` ou documentar que é formato XGBoost native.

### L2. Teste Falhado: `test_hybrid_ewc_update`
**Ficheiro:** `tests/test_hybrid_model.py:123`  
**Problema:** `assert np.float64(0.07066) <= (np.float64(0.06884) + 1e-06)` — EWC update não está a funcionar como esperado.
**Fix:** Revisar a lógica EWC no `football_hybrid.py` ou ajustar o teste.

### L3. Código Duplicado em Pipelines
**Ficheiro:** `scripts/run_pipeline.py`, `scripts/run_full_pipeline.py`  
**Problema:** Lógica semelhante de orquestração duplicada.
**Fix:** Consolidar num módulo `pipeline.py` com sub-comandos.

### L4. Documentação Visual em Falta
**Problema:** Não há diagrama Mermaid de arquitetura.
**Fix:** Gerar `docs/ARCHITECTURE.md` com diagrama de fluxo de dados.

### L5. `assert` em Código de Produção
**Ficheiro:** `src/validation/walk_forward.py:95`  
**Problema:** `assert` é removido com `python -O`.
**Fix:** Substituir por `if` + `raise ValueError`.

---

## ⚖️ COMPLIANCE / LEGAL

### CL1. Gambling Legality Warning Logged Mas Não Enforced
**Ficheiro:** `src/pipeline/orchestrator.py:49-54`  
**Problema:** Apenas loga warning sobre SRIJ/Portugal. Não bloqueia execução real.
**Fix:** Verificar geolocalização IP e bloquear execução real se jurisdição não permitida.

### CL2. No Age Verification ou KYC
**Problema:** Sistema não integra verificação de idade ou KYC.
**Fix:** Para monetização/SaaS, exigir verificação de identidade antes de permitir execução real.

### CL3. Betfair Exchange Não Disponível em Portugal
**Problema:** O código menciona Betfair mas não está licenciado em Portugal.
**Fix:** Bloquear Betfair para IPs portugueses; usar apenas operadores licenciados pela SRIJ.

---

## 📊 ML ENGINEERING FLAWS

### ML1. Meta-Labeling Threshold Hardcoded (0.60)
**Ficheiro:** `src/engine/predict.py:153`  
**Problema:** `if meta_prob >= 0.60:` — threshold fixo sem calibração por regime.
**Fix:** Calibrar threshold dinamicamente por sport/regime usando validation set.

### ML2. Modelo Fallback Treinado em Dados Sintéticos Aleatórios
**Ficheiro:** `src/engine/predict.py:42-87`  
**Problema:** Se `.pkl` não existe, treina modelo em dados completamente aleatórios.
**Impacto:** Predições sem qualquer valor preditivo.  
**Fix:** Falhar gracefulmente com erro claro; nunca auto-treinar modelo de produção.

### ML3. Falta de Feature Store Versionado
**Problema:** Features são computadas ad-hoc sem versionamento.
**Fix:** Implementar feature store com versionamento (e.g., Feast ou Parquet versionado).

### ML4. Data Drift Detection é Scaffold
**Ficheiro:** `src/mlops/drift/drift.py`  
**Problema:** Implementação mínima; não há ação automática quando drift é detetado.
**Fix:** Integrar com auto-rollback e alerting.

---

## 🏗️ DEVOPS / DEPLOYMENT GAPS

### D1. Docker Compose Sem Health Checks
**Ficheiro:** `docker-compose.yml`, `docker-compose.minimal.yml`  
**Problema:** Nenhum serviço tem `healthcheck` definido.
**Fix:** Adicionar healthchecks para Postgres, Redis, API.

### D2. CI/CD GitHub Actions Não Verificado
**Problema:** `.github/workflows/` pode existir mas não foi validado se executa todos os checks.
**Fix:** Garantir que CI executa: ruff, pytest, bandit, safety, e build Docker.

### D3. Falta de Rate Limiting na API
**Ficheiro:** `app/main.py`  
**Problema:** `RATE_LIMIT_ENABLED` existe em config mas não está implementado.
**Fix:** Adicionar middleware `slowapi` ou `fastapi-limiter`.

---

## 💰 MONETIZATION READINESS

| Critério | Estado | Notas |
|----------|--------|-------|
| API REST funcional | ⚠️ Parcial | Sem rate limiting, sem schema validation |
| Billing/Subscriptions | ❌ Inexistente | Não há camada de pagamentos |
| Risk Manager integrado | ⚠️ Parcial | Scaffolds existem mas paper trading é falso |
| Modelo SaaS viável | ❌ Não | Necessita API estável, billing, KYC, compliance |
| Relatórios CLV premium | ⚠️ Parcial | `run_clv_report.py` existe mas sem automação PDF |
| Marketplace de modelos | ❌ Não | Não implementado |

**Veredicto:** O projeto NÃO está pronto para monetização. Os blockers são:
1. Paper trading determinístico falso → não se pode demonstrar ROI real
2. Falta de compliance (KYC, geoblocking, licenciamento)
3. API sem segurança adequada (rate limiting, schema validation)
4. Não há sistema de billing/subscrições

---

## 🎯 VEREDICTO FINAL

### É seguro correr com dinheiro real? **NÃO.**

**Blockers absolutos para paper trading:**
1. Paper trading falso (C1) — não se pode confiar em qualquer métrica
2. Shadow challenger com future data (C2) — comparações de modelo inválidas
3. Edge sem comissão (H1) — lucros são ilusórios para exchanges

**Blockers absolutos para dinheiro real:**
1. Todos os blockers de paper trading
2. Sem compliance legal (CL1-CL3)
3. Sem KYC/age verification
4. Pickle deserialization sem validação (C6)
5. Secrets defaults não bloqueantes (C5)
6. Database URL sem encoding (C3)

### Minimum Viable Bar antes de Paper Trading:
- [ ] Fix C1 (paper trading com resultados reais)
- [ ] Fix C2 (shadow deployment temporalmente correto)
- [ ] Fix H1 (edge com comissão)
- [ ] Fix M1 (leakage detector mais robusto)
- [ ] Fix M2 (log rotation)
- [ ] Todos os testes a passar

### Minimum Viable Bar antes de Dinheiro Real:
- [ ] Todos os fixes CRITICAL + HIGH
- [ ] Implementar compliance legal (geoblocking, KYC)
- [ ] Migrar de pickle para formato seguro (skops com verificação, ou ONNX)
- [ ] Rate limiting + schema validation na API
- [ ] File locking nos audit logs
- [ ] Atualizar MLflow (CVEs)
- [ ] Penetration test externo
- [ ] Legal review por advogado de gambling

---

## 📋 PRIORIDADE DE IMPLEMENTAÇÃO

| Prioridade | Issue | Esforço Estimado |
|------------|-------|------------------|
| P0 | C1 — Paper trading falso | 4h |
| P0 | C2 — Shadow future data | 1h |
| P0 | C3 — DB URL encoding | 30min |
| P0 | C5 — Secrets enforcement | 1h |
| P1 | H1 — Edge com comissão | 2h |
| P1 | H3 — File locking audit | 1h |
| P1 | H8 — Remover soft book routing | 2h |
| P1 | C6 — Pickle security | 4h |
| P2 | M1 — Leakage detector melhorado | 3h |
| P2 | M2 — Log rotation | 1h |
| P2 | M9 — Update MLflow | 2h |
| P3 | D3 — Rate limiting | 2h |
| P3 | L2 — Fix teste híbrido | 1h |
| P3 | L3 — Consolidar pipelines | 4h |
