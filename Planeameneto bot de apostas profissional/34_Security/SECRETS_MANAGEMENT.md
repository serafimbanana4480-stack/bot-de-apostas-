# SECRETS_MANAGEMENT — Gestao de Credenciais

**ID:** `SEC-001` | **Fase:** #phase/1 | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. REGRAS ABSOLUTAS

1. **Nunca hardcode secrets em codigo.**
2. **Nunca commitar .env files.**
3. **Nunca partilhar tokens no Telegram/email.**
4. **Rotar tokens a cada 90 dias.**
5. **Usar variaveis de ambiente em producao.**

---

## 2. VARIAVEIS DE AMBIENTE

```bash
# .env (adicionado ao .gitignore!)
POSTGRES_USER=vb_user
POSTGRES_PASSWORD=<senha_forte>
POSTGRES_DB=valuebetting

REDIS_PASSWORD=<senha_forte>

BETFAIR_APP_KEY=<app_key>
BETFAIR_USERNAME=<username>
BETFAIR_PASSWORD=<password>

TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_CHAT_ID=<chat_id>

MLFLOW_TRACKING_URI=http://localhost:5000
```

---

## 3. ENCRIPTACAO EM REPO

```bash
# Usar git-secrets para prevenir commits acidentais
pip install git-secrets
git-secrets --install
git-secrets --register-aws  # ou regras custom
```

---

## 4. ROTACAO DE CREDENCIAIS

### 4.1 Frequência de Rotação

| Tipo | Frequência | Procedimento |
|------|-----------|--------------|
| Betfair API password | 90 dias | Alterar em betfair.com → atualizar .env |
| Betfair App Key | 180 dias | Gerar novo em developers.betfair.com |
| Telegram Bot Token | 180 dias | @BotFather → /revoke → novo token |
| PostgreSQL Password | 90 dias | ALTER USER + atualizar .env + restart |
| Redis Password | 90 dias | CONFIG SET + atualizar .env + restart |
| VPS Root Password | 30 dias | Alterar via provider |
| SSH Keys | Anual | Gerar novo par, distribuir, revogar antigo |

### 4.2 Script de Rotação PostgreSQL

```bash
#!/bin/bash
# rotate_postgres_password.sh
set -euo pipefail

NEW_PASSWORD=$(openssl rand -base64 32)
OLD_PASSWORD=$POSTGRES_PASSWORD

# Atualizar no PostgreSQL
docker exec postgres psql -U vb_admin -c "ALTER USER vb_admin WITH PASSWORD '${NEW_PASSWORD}';"
docker exec postgres psql -U vb_admin -c "ALTER USER app_user WITH PASSWORD '${NEW_PASSWORD}app';"

# Atualizar .env
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${NEW_PASSWORD}/" .env

# Restart aplicação (não PostgreSQL — password muda em runtime)
docker compose restart api

echo "Password PostgreSQL rotacionada. Nova password no .env"
```

---

## 5. ENCRIPTACAO EM REPO

### 5.1 Git-Secrets

```bash
# Instalar e configurar
pip install git-secrets
git secrets --install
git secrets --register-aws

# Adicionar regras customizadas para o projeto
git secrets --add 'token\s*=\s*["\']?[a-zA-Z0-9_-]{40,}["\']?'
git secrets --add 'password\s*=\s*["\'][^"\']{8,}["\']'
git secrets --add 'api_key\s*=\s*["\']?[a-zA-Z0-9_-]{20,}["\']?'

# Verificar antes de commit
git secrets --scan
```

### 5.2 SOPS (Secrets OPerationS)

Para repositórios que precisam de secrets versionados (ex: configurações de deploy):

```bash
# Instalar SOPS
wget https://github.com/getsops/sops/releases/download/v3.8.1/sops-v3.8.1.linux.amd64 -O /usr/local/bin/sops
chmod +x /usr/local/bin/sops

# Encriptar .env para versionar
cp .env .env.enc
sops --encrypt --in-place .env.enc

# .env.enc pode ser commitado — só quem tem a chave GPG pode decriptar
sops --decrypt .env.enc > .env
```

---

## 6. AUDIT DE ACESSO

### 6.1 Log de Acesso a Secrets

```python
import structlog
from datetime import datetime

logger = structlog.get_logger()

def get_secret(key: str) -> str:
    """Obtém secret com audit trail."""
    value = os.environ.get(key)
    if value:
        logger.info(
            "Secret accessed",
            secret_key=key,
            timestamp=datetime.now().isoformat(),
            process=os.path.basename(sys.argv[0])
        )
    return value
```

### 6.2 Verificação de Leaks

```bash
# Verificar se há secrets no histórico do git
git log --all --source --full-history -S "BETFAIR_APP_KEY" -- .env

# Verificar se há secrets em código atual
grep -r "password\|token\|secret" --include="*.py" src/ | grep -v "__pycache__"
```

---

## 7. BACKLOG

- [x] Definir 5 regras absolutas de secrets
- [x] Documentar todas as variáveis de ambiente
- [x] Documentar frequência de rotação por tipo
- [x] Implementar script de rotação PostgreSQL
- [x] Documentar git-secrets e regras customizadas
- [x] Documentar SOPS para secrets versionados
- [x] Implementar audit de acesso a secrets
- [ ] Configurar git-secrets em CI/CD
- [ ] Implementar alerta se secret for commitado

---

## 8. LINKS CRUZADOS

- [[34_Security/INDEX]] ← Secção mãe
- [[34_Security/POSTGRES_SEGURANCA]] → Segurança PostgreSQL
- [[13_Infrastructure/INDEX]] → Configuração do servidor
- [[12_DevOps/CI_CD_SETUP]] → CI/CD e secrets em pipeline
