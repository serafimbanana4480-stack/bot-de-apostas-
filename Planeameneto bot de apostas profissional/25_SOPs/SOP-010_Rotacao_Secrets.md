# SOP-010 — Rotação de Secrets

**ID:** `SOP-010` | **Fase:** Todas | **Owner:** DevOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Procedimento para rotação de secrets (API keys, passwords, tokens).

---

## 2. CHECKLIST

- [ ] Identificar secrets a rotacionar
- [ ] Gerar novos secrets
- [ ] Atualizar configuração
- [ ] Testar com novos secrets
- [ ] Deploy da atualização
- [ ] Invalidar secrets antigos
- [ ] Documentar rotação
- [ ] Notificar stakeholders

---

## 3. PROCEDIMENTO DETALHADO

### 3.1 Identificar Secrets a Rotacionar

Secrets que devem ser rotacionados regularmente:

| Secret | Frequência | Prioridade |
|--------|-----------|------------|
| `POSTGRES_PASSWORD` | 90 dias | HIGH |
| `BETFAIR_PASSWORD` | 90 dias | HIGH |
| `TELEGRAM_BOT_TOKEN` | 180 dias | MEDIUM |
| `SENDGRID_API_KEY` | 180 dias | MEDIUM |
| `GRAFANA_PASSWORD` | 90 dias | LOW |
| `REDIS_PASSWORD` | 90 dias | LOW |

**Nota:** `BETFAIR_APP_KEY` não pode ser rotacionada (emitida pela Betfair).

### 3.2 Gerar Novos Secrets

```bash
# Gerar password segura (22+ chars)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Ou usar pwgen (se instalado)
pwgen -s 32 1
```

### 3.3 Atualizar Configuração

1. Copiar `.env` atual para `.env.backup.$(date +%Y%m%d)`
2. Editar `.env` com novo secret
3. **Nunca** editar `.env.example` com secrets reais

```bash
# Backup do .env
cp .env .env.backup.$(date +%Y%m%d)

# Atualizar secret específico (exemplo: PostgreSQL)
sed -i 's/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=nova_password_aqui/' .env
```

### 3.4 Aplicar em Produção

```bash
# Copiar .env atualizado para VPS
scp .env vb_admin@vps-ip:/opt/valuebetting/.env

# Aplicar no container (sem restart completo)
docker compose exec api python -c "import os; print('ENV loaded:', os.getenv('POSTGRES_PASSWORD', 'NOT SET'))"

# Para PostgreSQL: requer restart do container postgres
docker compose restart postgres

# Para aplicação: reload da config (se suportado) ou restart
# FastAPI/Uvicorn: HUP signal ou restart
docker compose restart api
```

### 3.5 Testar com Novos Secrets

```bash
# Testar conexão PostgreSQL
docker compose exec -T postgres psql -U vb_admin -d valuebetting -c "SELECT 1;"

# Testar Betfair API
python scripts/test_betfair_api.py

# Testar Telegram Bot
python scripts/test_telegram_bot.py
```

**Critério de passagem:** Todos os testes passam, aplicação funcional.

### 3.6 Invalidar Secrets Antigos

- Betfair: password antiga fica inválida após mudança (lado servidor)
- PostgreSQL: password antiga já não funciona após restart
- Telegram: token antigo pode ser revogado via @BotFather
- SendGrid: API key antiga pode ser deletada no dashboard SendGrid

### 3.7 Documentar e Notificar

- Atualizar `34_Security/SECRETS_MANAGEMENT.md` com data da última rotação
- Notificar DevOps Lead via Telegram: `Secret [NOME] rotacionado em $(date)`
- Guardar `.env.backup.*` encriptado (GPG) por 30 dias, depois destruir

---

## 4. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
- [[34_Security/SECRETS_MANAGEMENT]] → Gestão de secrets
