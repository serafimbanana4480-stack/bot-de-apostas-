# 12_DevOps — INDEX

**ID:** `SEC-12` | **Fase:** #phase/1-15 | **Owner:** DevOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Gerir o ciclo de vida do código: versionamento, integração contínua, deploy, rollback, e infraestrutura como código. Garantir que qualquer alteração no sistema é rastreável, testável e revertível.

---

## 2. NOTAS FUNDAMENTAIS

- [[GIT_WORKFLOW]] — Branching strategy, commits, PRs
- [[CI_CD_PIPELINE]] — GitHub Actions / GitLab CI para testes e deploy
- [[DEPLOY_ESTRATEGIA]] — Blue-green, canary, ou simples restart
- [[ROLLBACK_PROCEDURES]] — Como reverter deploys problemáticos
- [[INFRA_AS_CODE]] — Terraform / Ansible para VPS e serviços
- [[AMBIENTES]] — Dev, staging, production

---

## 3. GIT WORKFLOW

```
main        → Código de produção (só via PR aprovado)
  ├── staging → Shadow mode e testes
  ├── develop → Integração diária
  └── feature/XXX → Branches de trabalho individual
```

**Regras:**
- Commos atómicos (1 alteração lógica por commit)
- Mensagens em inglês, formato: `type(scope): description`
- PR obrigatório para main e staging
- Nunca fazer push direto para main

---

## 4. CI/CD PIPELINE

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python 3.11
        uses: actions/setup-python@v4
        with: { python-version: '3.11' }
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run data validation tests
        run: pytest tests/data/
      - name: Run model tests
        run: pytest tests/models/
      - name: Run backtest integrity
        run: pytest tests/backtest/
```

---

## 5. BACKLOG TÉCNICO

- [ ] Configurar repositório Git com branches protegidas
- [ ] Criar CI pipeline com testes automatizados
- [ ] Configurar deploy automático para staging
- [ ] Documentar procedimento de rollback
- [ ] Criar ambiente de staging isolado

---

## 6. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[13_Infrastructure/INDEX]] → Infraestrutura subjacente
- [[11_MLOps/INDEX]] → CI/CD específico de modelos
