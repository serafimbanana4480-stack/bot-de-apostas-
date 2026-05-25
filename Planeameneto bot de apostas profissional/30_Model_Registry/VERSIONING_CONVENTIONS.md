# Versioning Conventions

**ID:** MLOPS-004 | **Fase:** #phase/2-15 | **Owner:** MLOps Engineer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Convenções de versionamento para modelos de ML. Define como versionar modelos, quando incrementar versões, e como manter consistência entre código e modelo.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Convenções de versionamento de modelos |
| **Custo** | 0€ (documentação) |

---

## 2. ESQUEMA DE VERSIONAMENTO

### 2.1 SemVer (Semantic Versioning)

```
MAJOR.MINOR.PATCH

MAJOR: Mudança incompatível na API ou arquitetura
MINOR: Nova funcionalidade compatível
PATCH: Bug fix compatível
```

### 2.2 Exemplo

```
v1.0.0 - Modelo baseline XGBoost
v1.1.0 - Adição de features de contexto
v1.1.1 - Bug fix no cálculo de CLV
v2.0.0 - Mudança para ensemble de modelos
```

---

## 3. CRITÉRIOS DE INCREMENTO

### 3.1 MAJOR (X.0.0)

**Condições:**
- Mudança de algoritmo (ex: XGBoost → Ensemble)
- Mudança de arquitetura de features
- Mudança incompatível na API de predição
- Refactor completo do pipeline

**Exemplo:**
```python
# v1.0.0 → v2.0.0
# XGBoost → Ensemble (XGBoost + LightGBM)
```

### 3.2 MINOR (0.X.0)

**Condições:**
- Adição de novas features
- Adição de novo tipo de dados
- Melhoria de performance significativa (>5% CLV)
- Nova funcionalidade compatível

**Exemplo:**
```python
# v1.0.0 → v1.1.0
# Adição de features de lesões (injury context)
```

### 3.3 PATCH (0.0.X)

**Condições:**
- Bug fix
- Correção de pequeno erro
- Melhoria de performance menor (<5% CLV)
- Atualização de dependências

**Exemplo:**
```python
# v1.1.0 → v1.1.1
# Bug fix no cálculo de CLV (divisão por zero)
```

---

## 4. GIT TAGGING

### 4.1 Tags de Versão

```bash
# Criar tag de versão
git tag -a v1.0.0 -m "Modelo baseline XGBoost"

# Push tag
git push origin v1.0.0

# Listar tags
git tag -l
```

### 4.2 Integração com MLflow

```python
# vbq/mlops/versioning/git_integration.py
import mlflow
import subprocess

def tag_model_with_git(version: str, run_id: str):
    """Cria tag Git para versão do modelo"""
    
    # Criar tag
    subprocess.run(['git', 'tag', '-a', version, '-m', f'Model version {version}'])
    
    # Push tag
    subprocess.run(['git', 'push', 'origin', version])
    
    # Log tag no MLflow
    mlflow.log_param("git_tag", version)
```

---

## 5. NAMING DE RUNS

### 5.1 Convenção de Nomes

```
{model_type}_{date}_{hash}

Exemplos:
- xgboost_20260518_abc123
- ensemble_20260518_def456
- lightgbm_20260518_ghi789
```

### 5.2 Exemplo

```python
# vbq/mlops/versioning/run_naming.py
import hashlib
from datetime import datetime

def generate_run_name(model_type: str) -> str:
    """Gera nome de run único"""
    
    date_str = datetime.now().strftime('%Y%m%d')
    hash_str = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
    
    return f"{model_type}_{date_str}_{hash_str}"
```

---

## 6. REGISTRO DE MUDANÇAS

### 6.1 CHANGELOG

```markdown
# CHANGELOG.md

## [Unreleased]

### Added
- Features de lesões (injury context)
- Suporte a ensemble de modelos

### Changed
- Atualizado XGBoost para versão 2.0.0
- Melhorada calibração isotônica

### Fixed
- Bug no cálculo de CLV (divisão por zero)
- Correção de memory leak em feature engineering

### Deprecated
- Modelo baseline v0.9.0 (use v1.0.0)

## [1.1.0] - 2026-05-15

### Added
- Features de dias de descanso

### Changed
- Melhorada performance de feature engineering

## [1.0.0] - 2026-05-01

### Added
- Modelo baseline XGBoost
- Pipeline de treino inicial
```

### 6.2 Atualização Automática

```python
# vbq/mlops/versioning/changelog.py
def update_changelog(version: str, changes: dict):
    """Atualiza CHANGELOG automaticamente"""
    
    changelog_path = "CHANGELOG.md"
    
    # Ler changelog atual
    with open(changelog_path, 'r') as f:
        changelog = f.read()
    
    # Adicionar nova versão
    new_section = f"""
## [{version}] - {datetime.now().strftime('%Y-%m-%d')}

### Added
{chr(10).join(f"- {c}" for c in changes.get('added', []))}

### Changed
{chr(10).join(f"- {c}" for c in changes.get('changed', []))}

### Fixed
{chr(10).join(f"- {c}" for c in changes.get('fixed', []))}
"""
    
    # Inserir no início
    updated_changelog = new_section + chr(10) + chr(10) + changelog
    
    # Escrever
    with open(changelog_path, 'w') as f:
        f.write(updated_changelog)
```

---

## 7. COMPATIBILIDADE

### 7.1 Matriz de Compatibilidade

| Versão | Python | XGBoost | Features | API |
|--------|--------|--------|----------|-----|
| v1.0.0 | 3.11 | 1.7.0 | Base | v1 |
| v1.1.0 | 3.11 | 1.7.0 | +Injury | v1 |
| v2.0.0 | 3.11 | Ensemble | +Injury+Context | v2 |

### 7.2 Migração

```python
# vbq/mlops/versioning/migration.py
def migrate_api(old_version: str, new_version: str):
    """Migra API de uma versão para outra"""
    
    if old_version.startswith('v1.') and new_version.startswith('v2.0.0'):
        # Mudança incompatível
        logger.warning(f"API incompatível entre {old_version} e {new_version}")
        return False
    
    # Compatível
    return True
```

---

## 8. AMBIENTES

### 8.1 Versões por Ambiente

```
Development: v1.2.0-dev (experimental features)
Staging: v1.1.0 (testado, pronto para produção)
Production: v1.0.0 (estável, validado)
```

### 8.2 Estratégia de Deploy

```
1. Development → v1.2.0-dev (testar features novas)
2. Staging → v1.1.0 (validar shadow mode)
3. Production → v1.0.0 → v1.1.0 (após validação)
```

---

## 9. ROLLBACK

### 9.1 Procedimento de Rollback

```python
# vbq/mlops/versioning/rollback.py
def rollback_to_version(target_version: str):
    """Rollback para versão específica"""
    
    # Verificar se versão existe
    if not version_exists(target_version):
        logger.error(f"Versão {target_version} não existe")
        return False
    
    # Rollback no MLflow
    rollback_model(target_version)
    
    # Rollback no código (git checkout)
    subprocess.run(['git', 'checkout', f'tags/{target_version}'])
    
    # Redeploy
    deploy_model(target_version)
    
    return True
```

---

## 10. DOCUMENTAÇÃO

### 10.1 README por Versão

```markdown
# Model v1.1.0

## Descrição
Modelo XGBoost com features de contexto de lesões.

## Mudanças vs v1.0.0
- Adicionado features de lesões
- Melhorada calibração isotônica
- CLV médio: 1.2% → 1.4%

## Performance
- CLV médio: 1.4%
- ROI médio: 3.2%
- Sharpe: 0.8

## Treino
- Dados: 3 temporadas NBA
- Features: 45 features
- Hiperparâmetros: ver MLflow

## Deploy
- Data: 2026-05-15
- Ambiente: Production
- Status: Ativo
```

---

## 11. LINKS CRUZADOS

- [[30_Model_Registry/INDEX]] ← Secção mãe
- [[30_Model_Registry/REGISTRY_GESTAO]] → Gestão de registry
- [[30_Model_Registry/ROLLBACK_MODELO]] → Rollback de modelo
- [[12_DevOps/GIT_WORKFLOW]] → Git workflow

---

**Custo de implementação:** 0€ (documentação)  
**Tempo estimado de implementação:** 3 dias  
**Prioridade:** MÉDIA (importante para consistência)
