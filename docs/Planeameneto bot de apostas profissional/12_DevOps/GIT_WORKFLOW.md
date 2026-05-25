# GIT_WORKFLOW — Estratégia Git, Branches, Code Review e Commits

**ID:** `DEV-001` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir uma estratégia Git clara e consistente que garanta colaboração eficiente, histórico limpo, rastreabilidade de mudanças e capacidade de rollback. Um bom workflow Git é fundamental para manter a qualidade do código e facilitar a integração contínua.

---

## 2. ESTRATÉGIA DE BRANCHING

### 2.1 Estrutura de Branches

```
main (production)
├── Código de produção (só via PR aprovado)
├── Protegido: não permite push direto
├── Requer: 1 approval + CI pass
└── Tags: v1.0.0, v1.1.0, etc.

staging
├── Ambiente de staging (shadow mode)
├── Merge de develop após validação
├── Protegido: não permite push direto
└── Requer: 1 approval + CI pass

develop
├── Integração diária de features
├── Merge de feature branches
├── Protegido: não permite push direto
└── Requer: CI pass

feature/XXX
├── Branches de trabalho individual
├── Criadas a partir de develop
├── Merge de volta para develop via PR
└── Deletadas após merge

bugfix/XXX
├── Correções de bugs em produção
├── Criadas a partir de main
├── Merge para main + develop
└── Deletadas após merge

hotfix/XXX
├── Correções críticas urgentes
├── Criadas a partir de main
├── Merge direto para main (bypass develop)
└── Deletadas após merge
```

### 2.2 Fluxo de Trabalho

```
1. DESENVOLVIMENTO
   ├── Criar feature/nome-da-feature a partir de develop
   ├── Desenvolver e fazer commits
   ├── Push para origin
   └── Criar PR para develop

2. CODE REVIEW
   ├── Peer review do código
   ├── CI/CD executa testes automaticamente
   ├── Solicitar alterações se necessário
   └── Aprovar se tudo OK

3. MERGE PARA DEVELOP
   ├── Squash merge (histórico limpo)
   ├── Delete branch automaticamente
   └── CI/CD executa testes de integração

4. PROMOÇÃO PARA STAGING
   ├── Criar PR de develop → staging
   ├── Deploy automático para staging
   └── Testes manuais em staging

5. PROMOÇÃO PARA PRODUÇÃO
   ├── Criar PR de staging → main
   ├── Deploy automático para produção
   └── Tag release (v1.X.X)
```

---

## 3. CONVENÇÕES DE COMMITS

### 3.1 Formato de Mensagens

**Formato:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Tipos permitidos:**
- `feat`: Nova feature
- `fix`: Correção de bug
- `docs`: Mudanças na documentação
- `style`: Formatação, missing semicolons, etc (sem lógica)
- `refactor`: Refactoring que não é nem feature nem fix
- `test`: Adicionando ou modificando testes
- `chore`: Mudanças no build process ou ferramentas auxiliares
- `perf`: Melhoria de performance

**Scopes comuns:**
- `api`: API endpoints
- `models`: Modelos de ML
- `data`: Pipeline de dados
- `ui`: Interface de utilizador
- `infra`: Infraestrutura
- `ci`: CI/CD
- `docs`: Documentação

**Exemplos:**

```bash
# Feature simples
feat(api): add user authentication endpoint

# Fix com detalhes
fix(models): handle missing values in feature engineering
- Added imputation for NaN values
- Updated tests to cover edge cases
- Fixes #123

# Refactoring
refactor(data): optimize data loading pipeline
- Reduced memory usage by 30%
- Improved loading speed by 2x

# Breaking change
feat(api): change response format for predictions

BREAKING CHANGE: Response format changed from list to object
with additional metadata. Update clients accordingly.
```

### 3.2 Regras de Commits

1. **Commits atómicos:** Um commit deve fazer uma única mudança lógica
2. **Mensagem imperativa:** Use "add" não "added" ou "adds"
3. **Primeira linha < 72 caracteres:** Para legibilidade em git log
4. **Corpo explicativo:** Explique PORQUÊ, não apenas O QUÊ
5. **Referenciar issues:** Use #123 para referenciar issue
6. **Não commite:** Secrets, binaries, dependencies, IDE files

### 3.3 Exemplo de Commit Histórico Limpo

```bash
$ git log --oneline -10

a1b2c3d (HEAD -> main, tag: v1.2.0) chore(release): v1.2.0
d4e5f6g feat(api): add odds comparison endpoint
h7i8j9k fix(models): correct probability calibration
l1m2n3o docs(readme): update installation instructions
p4q5r6s refactor(data): optimize feature caching
t7u8v9w test(api): add integration tests for predictions
x1y2z3a feat(models): implement new ensemble model
```

---

## 4. PULL REQUESTS

### 4.1 Template de PR

```markdown
## Description
[Descrição breve do que esta PR faz]

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Related Issues
Fixes #123
Related to #456

## Changes Made
- [ ] List changes made
- [ ] List changes made
- [ ] List changes made

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Tests added for new functionality

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Commented complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Added/updated tests
- [ ] All tests passing

## Screenshots (if applicable)
[Screenshots of UI changes]

## Additional Notes
[Any additional context or considerations]
```

### 4.2 Processo de Code Review

**Para o autor:**
1. Self-review antes de pedir review
2. Garantir que CI passa
3. Adicionar descrição clara no PR
4. Referenciar issues relacionadas
5. Responder a todos os comentários

**Para o reviewer:**
1. Revisar dentro de 24 horas (SLA)
2. Focar em: lógica, performance, segurança, testes
3. Ser construtivo, não crítico
4. Explicar PORQUÊ das sugestões
5. Aprovar apenas quando satisfeito

**Critérios de aprovação:**
- Código legível e maintainable
- Testes adequados
- Documentação atualizada
- Sem vulnerabilidades de segurança
- Performance aceitável
- Segue convenções do projeto

---

## 5. PROTEÇÃO DE BRANCHES

### 5.1 Configuração de Branches Protegidos

**Branch main:**
- [x] Require pull request before merging
- [x] Require approvals: 1
- [x] Dismiss stale PR approvals when new commits are pushed
- [x] Require status checks to pass before merging
  - [x] CI/CD Tests
  - [x] Linting
  - [x] Security scan
- [x] Require branches to be up to date before merging
- [x] Do not allow bypassing the above settings

**Branch staging:**
- [x] Require pull request before merging
- [x] Require approvals: 1
- [x] Require status checks to pass before merging
  - [x] CI/CD Tests
  - [x] Linting
- [x] Require branches to be up to date before merging

**Branch develop:**
- [x] Require pull request before merging
- [x] Require approvals: 1
- [x] Require status checks to pass before merging
  - [x] CI/CD Tests
  - [x] Linting
- [x] Require branches to be up to date before merging

### 5.2 Configuração via GitHub CLI

```bash
# Proteger branch main
gh api repos/:owner/:repo/branches/main/protection \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  -d '{
    "required_pull_request_reviews": {
      "required_approving_review_count": 1,
      "dismiss_stale_reviews": true,
      "require_code_owner_reviews": false
    },
    "required_status_checks": {
      "strict": true,
      "contexts": ["CI/CD Tests", "Linting", "Security Scan"]
    },
    "enforce_admins": true,
    "restrictions": null
  }'
```

---

## 6. RESOLUÇÃO DE CONFLITOS

### 6.1 Prevenção de Conflitos

1. **Manter branches atualizados:**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout feature/my-feature
   git rebase develop
   ```

2. **Commits frequentes:** Pequenos commits = menos conflitos
3. **Comunicação:** Avisar equipe quando trabalhar em mesmo código
4. **Feature flags:** Usar flags para desacoplar deploy de feature

### 6.2 Resolução de Conflitos

```bash
# 1. Atualizar branch
git checkout feature/my-feature
git fetch origin
git rebase origin/develop

# 2. Se houver conflitos, resolver manualmente
# Editar arquivos com conflitos
# Remover marcadores <<<<<<<, =======, >>>>>>>

# 3. Marcar como resolvido
git add <arquivo>
git rebase --continue

# 4. Se quiser abortar
git rebase --abort

# 5. Push force (com cuidado!)
git push origin feature/my-feature --force-with-lease
```

---

## 7. TAGGING E RELEASES

### 7.1 Convenção de Versionamento (SemVer)

```
MAJOR.MINOR.PATCH

MAJOR: Mudanças incompatíveis na API
MINOR: Funcionalidades novas backward-compatible
PATCH: Correções de bugs backward-compatible

Exemplos:
v1.0.0 → Primeira release estável
v1.1.0 → Nova feature (backward-compatible)
v1.1.1 → Bug fix
v2.0.0 → Breaking change
```

### 7.2 Criação de Tags

```bash
# Criar tag anotada
git tag -a v1.0.0 -m "Release v1.0.0: Initial stable release"

# Push tags para remote
git push origin v1.0.0
git push origin --tags

# Listar tags
git tag -l

# Ver detalhes de tag
git show v1.0.0

# Deletar tag (local)
git tag -d v1.0.0

# Deletar tag (remote)
git push origin :refs/tags/v1.0.0
```

### 7.3 Automation de Releases com GitHub Actions

```yaml
# .github/workflows/release.yml
name: Create Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          body: |
            Changes in this Release
            - Change 1
            - Change 2
          draft: false
          prerelease: false
```

---

## 8. HOOKS DO GIT

### 8.1 Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Run linter
echo "Running linter..."
python -m flake8 src/

# Run type checker
echo "Running type checker..."
python -m mypy src/

# Run tests
echo "Running tests..."
python -m pytest tests/

# If any fail, prevent commit
if [ $? -ne 0 ]; then
    echo "❌ Pre-commit checks failed. Commit aborted."
    exit 1
fi

echo "✅ All checks passed."
```

### 8.2 Pre-push Hook

```bash
# .git/hooks/pre-push
#!/bin/bash

# Run integration tests
echo "Running integration tests..."
python -m pytest tests/integration/

# Check for secrets
echo "Checking for secrets..."
if git diff --cached --name-only | xargs grep -l "API_KEY\|SECRET\|PASSWORD"; then
    echo "❌ Potential secrets found. Push aborted."
    exit 1
fi

echo "✅ Pre-push checks passed."
```

### 8.3 Instalar Hooks com pre-commit

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100']

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
EOF

# Install hooks
pre-commit install
```

---

## 9. GITIGNORE

### 9.1 Exemplo Completo

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Jupyter Notebook
.ipynb_checkpoints

# Environment variables
.env
.env.local
.env.*.local

# MLflow
mlflow-artifacts/
mlruns/

# Data files
data/raw/
data/processed/
*.csv
*.parquet
*.pkl
*.joblib

# Model files
models/
*.pkl
*.h5
*.pt
*.pth

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Secrets
secrets/
*.key
*.pem
credentials.json
```

---

## 10. BOAS PRÁTICAS

### 10.1 Diárias

- Pull do develop/start antes de começar
- Commits frequentes e pequenos
- Push regular para backup
- Resolver conflitos assim que aparecem

### 10.2 Semanais

- Rebase de feature branches com develop
- Review de PRs pendentes
- Limpeza de branches antigos
- Atualização de dependências

### 10.3 Mensais

- Review de histórico de commits
- Limpeza de tags antigas
- Análise de métricas de PR (tempo de review, etc)
- Atualização de documentação de workflow

---

## 11. FERRAMENTAS

### 11.1 Recomendadas

- **GitHub CLI (gh):** Interface de linha de comando para GitHub
- **GitKraken/SourceTree:** GUI para Git (opcional)
- **Pre-commit:** Gerenciamento de hooks
- **Commitlint:** Validação de mensagens de commit
- **Semantic Release:** Automatização de releases

### 11.2 Comandos Úteis

```bash
# Ver quem alterou uma linha
git blame <file>

# Ver histórico de um arquivo
git log --follow <file>

# Encontrar commit que introduziu bug
git bisect start
git bisect bad HEAD
git bisect good <commit-antigo>
git bisect run <test-script>

# Stash mudanças temporariamente
git stash
git stash pop

# Undo último commit (mantendo mudanças)
git reset --soft HEAD~1

# Undo último commit (descartando mudanças)
git reset --hard HEAD~1

# Ver diferença entre branches
git diff develop main

# Cherry-pick commit de outro branch
git cherry-pick <commit-hash>

# Squash últimos N commits
git rebase -i HEAD~N
```

---

## 12. BACKLOG TÉCNICO

- [ ] Configurar branch protection rules
- [ ] Implementar pre-commit hooks
- [ ] Configurar semantic release automation
- [ ] Criar dashboard de métricas de PR
- [ ] Implementar automerge para PRs triviais
- [ ] Configurar dependabot para updates automáticos

---

## 13. LINKS CRUZADOS

- [[12_DevOps/INDEX]] ← Secção mãe
- [[12_DevOps/CI_CD_SETUP]] → Configuração de CI/CD
- [[12_DevOps/DEPLOYMENT_STRATEGY]] → Estratégias de deploy
- [[12_DevOps/INFRASTRUCTURE_AS_CODE]] → Infraestrutura como código